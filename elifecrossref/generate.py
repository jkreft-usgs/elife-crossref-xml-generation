from elifearticle import utils as eautils
import utils
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement, Comment
from xml.dom import minidom
import time
import os
from conf import config

TMP_DIR = 'tmp'

class crossrefXML(object):

    def __init__(self, poa_articles, crossref_config, pub_date=None, add_comment=True):
        """
        set the root node
        get the article type from the object passed in to the class
        set default values for items that are boilder plate for this XML
        """
        self.root = Element('doi_batch')

        # set the boiler plate values
        self.config_contrib_types = crossref_config.get("contrib_types")
        self.config_journal_id = crossref_config.get("journal_id")
        self.config_journal_title = crossref_config.get("journal_title")
        self.config_email_address = crossref_config.get("email_address")
        self.config_epub_issn = crossref_config.get("epub_issn")
        self.config_publisher_name = crossref_config.get("publisher_name")
        self.config_crossmark_policy = crossref_config.get("crossmark_policy")
        self.config_crossmark_domain = crossref_config.get("crossmark_domain")

        self.root.set('version', "4.3.5")
        self.root.set('xmlns', 'http://www.crossref.org/schema/4.3.5')
        self.root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        self.root.set('xmlns:fr', 'http://www.crossref.org/fundref.xsd')
        self.root.set('xmlns:ai', 'http://www.crossref.org/AccessIndicators.xsd')
        self.root.set('xsi:schemaLocation', ('http://www.crossref.org/schema/4.3.5 ' +
                                             'http://www.crossref.org/schemas/crossref4.3.5.xsd'))
        self.root.set('xmlns:mml', 'http://www.w3.org/1998/Math/MathML')
        self.root.set('xmlns:jats', 'http://www.ncbi.nlm.nih.gov/JATS1')

        # Publication date
        if pub_date is None:
            self.pub_date = time.gmtime()
        else:
            self.pub_date = pub_date

        # Generate batch id
        batch_doi = ''
        if len(poa_articles) == 1:
            # If only one article is supplied, then add the doi to the batch file name
            batch_doi = str(poa_articles[0].manuscript).zfill(5) + '-'
        self.batch_id = (str(crossref_config.get('batch_file_prefix')) + batch_doi +
                                   time.strftime("%Y%m%d%H%M%S", self.pub_date))

        # set comment
        if add_comment:
            self.generated = time.strftime("%Y-%m-%d %H:%M:%S")
            self.last_commit = utils.get_last_commit_to_master()
            self.comment = Comment('generated by ' + str(crossref_config.get('generator')) +
                                   ' at ' + self.generated +
                                   ' from version ' + self.last_commit)
            self.root.append(self.comment)

        self.build(self.root, poa_articles)

    def build(self, root, poa_articles):
        self.set_head(self.root)
        self.set_body(self.root, poa_articles)

    def set_head(self, parent):
        self.head = SubElement(parent, 'head')
        self.doi_batch_id = SubElement(self.head, 'doi_batch_id')
        self.doi_batch_id.text = self.batch_id
        self.timestamp = SubElement(self.head, 'timestamp')
        self.timestamp.text = time.strftime("%Y%m%d%H%M%S", self.pub_date)
        self.set_depositor(self.head)
        self.registrant = SubElement(self.head, 'registrant')
        self.registrant.text = self.config_journal_title

    def set_depositor(self, parent):
        self.depositor = SubElement(parent, 'depositor')
        self.name = SubElement(self.depositor, 'depositor_name')
        self.name.text = self.config_journal_title
        self.email_address = SubElement(self.depositor, 'email_address')
        self.email_address.text = self.config_email_address

    def set_body(self, parent, poa_articles):
        self.body = SubElement(parent, 'body')

        for poa_article in poa_articles:
            # Create a new journal record for each article
            # Use a list of one for now
            poa_article_list = [poa_article]
            self.set_journal(self.body, poa_article_list)

    def get_pub_date(self, poa_article):
        """
        For using in XML generation, use the article pub date
        or by default use the run time pub date
        """
        pub_date = None
        try:
            pub_date = poa_article.get_date("pub").date
        except:
            # Default use the run time date
            pub_date = self.pub_date
        return pub_date

    def set_journal(self, parent, poa_articles):

        # Add journal for each article
        for poa_article in poa_articles:
            self.journal = SubElement(parent, 'journal')
            self.set_journal_metadata(self.journal)

            self.journal_issue = SubElement(self.journal, 'journal_issue')

            #self.publication_date = self.set_date(self.journal_issue,
            #                                      poa_article, 'publication_date')

            # Get the issue date from the first article in the list when doing one article per issue
            pub_date = self.get_pub_date(poa_articles[0])
            self.set_publication_date(self.journal_issue, pub_date)

            self.journal_volume = SubElement(self.journal_issue, 'journal_volume')
            self.volume = SubElement(self.journal_volume, 'volume')
            # Use volume from the article unless not present then use the default
            if poa_article.volume:
                self.volume.text = poa_article.volume
            else:
                self.volume.text = utils.elife_journal_volume(pub_date)

            # Add journal article
            self.set_journal_article(self.journal, poa_article)

    def set_journal_metadata(self, parent):
        # journal_metadata
        journal_metadata = SubElement(parent, 'journal_metadata')
        journal_metadata.set("language", "en")
        self.full_title = SubElement(journal_metadata, 'full_title')
        self.full_title.text = self.config_journal_title
        self.issn = SubElement(journal_metadata, 'issn')
        self.issn.set("media_type", "electronic")
        self.issn.text = self.config_epub_issn

    def set_journal_article(self, parent, poa_article):
        self.journal_article = SubElement(parent, 'journal_article')
        self.journal_article.set("publication_type", "full_text")

        # Set the title with italic tag support
        self.set_titles(self.journal_article, poa_article)

        self.set_contributors(self.journal_article, poa_article, self.config_contrib_types)

        self.set_abstract(self.journal_article, poa_article)
        self.set_digest(self.journal_article, poa_article)

        # Journal publication date
        pub_date = self.get_pub_date(poa_article)
        self.set_publication_date(self.journal_article, pub_date)

        self.publisher_item = SubElement(self.journal_article, 'publisher_item')
        self.identifier = SubElement(self.publisher_item, 'identifier')
        self.identifier.set("id_type", "doi")
        self.identifier.text = poa_article.doi

        # Disable crossmark for now
        #self.set_crossmark(self.journal_article, poa_article)

        #self.archive_locations = SubElement(self.journal_article, 'archive_locations')
        #self.archive = SubElement(self.archive_locations, 'archive')
        #self.archive.set("name", "CLOCKSS")

        self.set_fundref(self.journal_article, poa_article)

        self.set_access_indicators(self.journal_article, poa_article)

        self.set_archive_locations(self.journal_article, poa_article)

        self.set_doi_data(self.journal_article, poa_article)

        self.set_citation_list(self.journal_article, poa_article)

        self.set_component_list(self.journal_article, poa_article)

    def set_titles(self, parent, poa_article):
        """
        Set the titles and title tags allowing sub tags within title
        """
        root_tag_name = 'titles'
        tag_name = 'title'
        root_xml_element = Element(root_tag_name)
        # Crossref allows <i> tags, not <italic> tags
        tag_converted_title = poa_article.title
        tag_converted_title = eautils.replace_tags(tag_converted_title, 'italic', 'i')
        tag_converted_title = eautils.replace_tags(tag_converted_title, 'bold', 'b')
        tag_converted_title = eautils.replace_tags(tag_converted_title, 'underline', 'u')
        tagged_string = '<' + tag_name + '>' + tag_converted_title + '</' + tag_name + '>'
        reparsed = minidom.parseString(eautils.xml_escape_ampersand(tagged_string).encode('utf-8'))

        root_xml_element = utils.append_minidom_xml_to_elementtree_xml(
            root_xml_element, reparsed
            )

        parent.append(root_xml_element)

    def set_doi_data(self, parent, poa_article):
        self.doi_data = SubElement(parent, 'doi_data')

        self.doi = SubElement(self.doi_data, 'doi')
        self.doi.text = poa_article.doi

        self.resource = SubElement(self.doi_data, 'resource')

        resource = 'http://elifesciences.org/lookup/doi/' + poa_article.doi
        self.resource.text = resource

    def set_contributors(self, parent, poa_article, contrib_types=None):
        # If contrib_type is None, all contributors will be added regardless of their type
        self.contributors = SubElement(parent, "contributors")

        # Ready to add to XML
        # Use the natural list order of contributors when setting the first author
        sequence = "first"
        for contributor in poa_article.contributors:
            if contrib_types:
                # Filter by contrib_type if supplied
                if contributor.contrib_type not in contrib_types:
                    continue

            if contributor.contrib_type == "on-behalf-of":
                contributor_role = "author"
            else:
                contributor_role = contributor.contrib_type

            # Skip contributors with no surname
            if contributor.surname == "" or contributor.surname is None:
                # Most likely a group author
                if contributor.collab:
                    self.organization = SubElement(self.contributors, "organization")
                    self.organization.text = contributor.collab
                    self.organization.set("contributor_role", contributor_role)
                    self.organization.set("sequence", sequence)

            else:
                self.person_name = SubElement(self.contributors, "person_name")

                self.person_name.set("contributor_role", contributor_role)

                if contributor.corresp == True or contributor.equal_contrib == True:
                    self.person_name.set("sequence", sequence)
                else:
                    self.person_name.set("sequence", sequence)

                self.given_name = SubElement(self.person_name, "given_name")
                self.given_name.text = contributor.given_name

                self.surname = SubElement(self.person_name, "surname")
                self.surname.text = contributor.surname

                if contributor.orcid:
                    self.orcid = SubElement(self.person_name, "ORCID")
                    self.orcid.set("authenticated", "true")
                    self.orcid.text = contributor.orcid

            # Reset sequence value after the first sucessful loop
            sequence = "additional"

    def set_abstract(self, parent, poa_article):
        if poa_article.abstract:
            abstract = poa_article.abstract
            self.set_abstract_tag(parent, abstract, type="abstract")

    def set_digest(self, parent, poa_article):
        if poa_article.digest:
            self.set_abstract_tag(parent, poa_article.digest, type="executive-summary")

    def set_abstract_tag(self, parent, abstract, type):

        tag_name = 'jats:abstract'
        namespaces = ' xmlns:jats="http://www.ncbi.nlm.nih.gov/JATS1" '

        attributes = []
        attributes_text = ''
        if type == 'executive-summary':
            attributes = ['abstract-type']
            attributes_text = ' abstract-type="executive-summary" '

        tag_converted_abstract = abstract
        tag_converted_abstract = eautils.xml_escape_ampersand(tag_converted_abstract)
        tag_converted_abstract = eautils.escape_unmatched_angle_brackets(tag_converted_abstract)
        tag_converted_abstract = eautils.replace_tags(tag_converted_abstract, 'p', 'jats:p')
        tag_converted_abstract = eautils.replace_tags(tag_converted_abstract, 'italic', 'jats:italic')
        tag_converted_abstract = eautils.replace_tags(tag_converted_abstract, 'bold', 'jats:bold')
        tag_converted_abstract = eautils.replace_tags(tag_converted_abstract, 'underline', 'jats:underline')
        tag_converted_abstract = eautils.replace_tags(tag_converted_abstract, 'sub', 'jats:sub')
        tag_converted_abstract = eautils.replace_tags(tag_converted_abstract, 'sup', 'jats:sup')
        tag_converted_abstract = eautils.replace_tags(tag_converted_abstract, 'sc', 'jats:sc')

        tagged_string = '<' + tag_name + namespaces + attributes_text + '>'
        tagged_string += tag_converted_abstract
        tagged_string += '</' + tag_name + '>'
        reparsed = minidom.parseString(tagged_string.encode('utf-8'))

        recursive = False
        root_xml_element = utils.append_minidom_xml_to_elementtree_xml(
            parent, reparsed, recursive, attributes
        )

    def set_publication_date(self, parent, pub_date):
        # pub_date is a python time object
        if pub_date:
            self.publication_date = SubElement(parent, 'publication_date')
            self.publication_date.set("media_type", "online")
            month = SubElement(self.publication_date, "month")
            month.text = str(pub_date.tm_mon).zfill(2)
            day = SubElement(self.publication_date, "day")
            day.text = str(pub_date.tm_mday).zfill(2)
            year = SubElement(self.publication_date, "year")
            year.text = str(pub_date.tm_year)

    def set_fundref(self, parent, poa_article):
        """
        Set the fundref data from the article funding_awards list
        """
        if len(poa_article.funding_awards) > 0:
            self.fr_program = SubElement(parent, 'fr:program')
            self.fr_program.set("name", "fundref")
            for award in poa_article.funding_awards:
                self.fr_fundgroup = SubElement(self.fr_program, 'fr:assertion')
                self.fr_fundgroup.set("name", "fundgroup")

                if award.get_funder_name():
                    self.fr_funder_name = SubElement(self.fr_fundgroup, 'fr:assertion')
                    self.fr_funder_name.set("name", "funder_name")
                    self.fr_funder_name.text = award.get_funder_name()

                if award.get_funder_name() and award.get_funder_identifier():
                    self.fr_funder_identifier = SubElement(self.fr_funder_name, 'fr:assertion')
                    self.fr_funder_identifier.set("name", "funder_identifier")
                    self.fr_funder_identifier.text = award.get_funder_identifier()

                if len(award.award_ids) > 0:
                    for award_id in award.award_ids:
                        self.fr_award_number = SubElement(self.fr_fundgroup, 'fr:assertion')
                        self.fr_award_number.set("name", "award_number")
                        self.fr_award_number.text = award_id

    def set_access_indicators(self, parent, poa_article):
        """
        Set the AccessIndicators
        """

        applies_to = ['vor', 'am', 'tdm']

        if poa_article.license.href:

            self.ai_program = SubElement(parent, 'ai:program')
            self.ai_program.set('name', 'AccessIndicators')

            for applies_to in applies_to:
                self.ai_program_ref = SubElement(self.ai_program, 'ai:license_ref')
                self.ai_program_ref.set('applies_to', applies_to)
                self.ai_program_ref.text = poa_article.license.href

    def set_archive_locations(self, parent, poa_article):
        self.archive_locations = SubElement(parent, 'archive_locations')
        self.archive = SubElement(self.archive_locations, 'archive')
        self.archive.set('name', 'CLOCKSS')

    def set_citation_list(self, parent, poa_article):
        """
        Set the citation_list from the article object ref_list objects
        """
        if len(poa_article.ref_list) > 0:
            self.citation_list = SubElement(parent, 'citation_list')
            ref_index = 0
            for ref in poa_article.ref_list:
                # Increment
                ref_index = ref_index + 1
                self.citation = SubElement(self.citation_list, 'citation')
                self.citation.set("key", str(ref_index))

                if ref.source:
                    if ref.publication_type == "journal":
                        self.journal_title = SubElement(self.citation, 'journal_title')
                        self.journal_title.text = ref.source
                    else:
                        self.volume_title = SubElement(self.citation, 'volume_title')
                        self.volume_title.text = ref.source

                # Only set the first author surname
                if len(ref.authors) > 0:
                    if ref.authors[0].get("surname"):
                        self.author = SubElement(self.citation, 'author')
                        self.author.text = ref.authors[0].get("surname")
                    elif ref.authors[0].get("collab"):
                        self.author = SubElement(self.citation, 'author')
                        self.author.text = ref.authors[0].get("collab")

                if ref.volume:
                    self.volume = SubElement(self.citation, 'volume')
                    self.volume.text = ref.volume[0:31]

                if ref.fpage:
                    self.first_page = SubElement(self.citation, 'first_page')
                    self.first_page.text = ref.fpage

                if ref.year:
                    self.cyear = SubElement(self.citation, 'cYear')
                    self.cyear.text = ref.year

                if ref.doi:
                    self.doi = SubElement(self.citation, 'doi')
                    self.doi.text = ref.doi

                if ref.elocation_id:
                    # Until an alternate tag is available, elocation-id goes into the first_page tag
                    self.first_page = SubElement(self.citation, 'first_page')
                    self.first_page.text = ref.elocation_id

    def set_component_list(self, parent, poa_article):
        """
        Set the component_list from the article object component_list objects
        """
        if len(poa_article.component_list) <= 0:
            return

        self.component_list = SubElement(parent, 'component_list')
        for comp in poa_article.component_list:
            self.component = SubElement(self.component_list, 'component')
            self.component.set("parent_relation", "isPartOf")

            self.titles = SubElement(self.component, 'titles')

            self.title = SubElement(self.titles, 'title')
            self.title.text = comp.title

            if comp.subtitle:
                self.set_subtitle(self.titles, comp)

            if comp.mime_type:
                # Convert to allowed mime types for Crossref, if found
                if self.crossref_mime_type(comp.mime_type):
                    self.format = SubElement(self.component, 'format')
                    self.format.set("mime_type", self.crossref_mime_type(comp.mime_type))

            if comp.permissions:
                self.set_component_permissions(self.component, comp.permissions)

            if comp.doi:
                self.doi_data = SubElement(self.component, 'doi_data')
                self.doi_tag = SubElement(self.doi_data, 'doi')
                self.doi_tag.text = comp.doi
                if comp.doi_resource:
                    self.resource = SubElement(self.doi_data, 'resource')
                    self.resource.text = comp.doi_resource

    def set_component_permissions(self, parent, permissions):
        # Specific license to the component

        # TODO !!!
        #self.component_ai_program = SubElement(parent, 'ai:program')

        for permission in permissions:
            text_parts = []

            if permission.get('copyright_statement'):
                text_parts.append(permission.get('copyright_statement'))
            if permission.get('license'):
                text_parts.append(permission.get('license'))

            if len(text_parts) > 0:
                # TODO !!! Add this text somewhere. Issue #53
                text = " ".join(text_parts)

    def set_subtitle(self, parent, component):
        tag_name = 'subtitle'
        # Use <i> tags, not <italic> tags, <b> tags not <bold>
        if component.subtitle:
            tag_converted_string = eautils.xml_escape_ampersand(component.subtitle)
            tag_converted_string = eautils.escape_unmatched_angle_brackets(tag_converted_string)
            tag_converted_string = eautils.replace_tags(tag_converted_string, 'italic', 'i')
            tag_converted_string = eautils.replace_tags(tag_converted_string, 'bold', 'b')
            tag_converted_string = eautils.replace_tags(tag_converted_string, 'underline', 'u')
            tagged_string = '<' + tag_name + '>' + tag_converted_string + '</' + tag_name + '>'
            reparsed = minidom.parseString(tagged_string.encode('utf-8'))

            root_xml_element = utils.append_minidom_xml_to_elementtree_xml(
                parent, reparsed
            )

    def crossref_mime_type(self, jats_mime_type):
        """
        Dictionary of lower case JATS mime type to crossRef schema mime type
        """
        mime_types = {}

        mime_types['application/eps'] = 'application/eps'
        mime_types['application/gz'] = 'application/gzip'
        mime_types['application/tar.gz'] = 'application/gzip'
        mime_types['application/doc'] = 'application/msword'
        mime_types['application/pdf'] = 'application/pdf'
        mime_types['application/rtf'] = 'application/rtf'
        mime_types['application/xls'] = 'application/vnd.ms-excel'
        mime_types['application/pptx'] = (
            'application/vnd.openxmlformats-officedocument.presentationml.presentation')
        mime_types['application/xlsx'] = (
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        mime_types['application/docx'] = (
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        mime_types['application/xml'] = 'application/xml'

        mime_types['chemical/pdb'] = 'chemical/x-pdb'

        mime_types['image/tif'] = 'image/tiff'
        mime_types['image/tiff'] = 'image/tiff'
        mime_types['application/png'] = 'image/png'

        mime_types['text/plain'] = 'text/plain'
        mime_types['application/csv'] = 'text/plain'
        mime_types['application/txt'] = 'text/plain'
        mime_types['text/pl'] = 'text/plain'
        mime_types['text/py'] = 'text/plain'
        mime_types['text/txt'] = 'text/plain'
        mime_types['text/rtf'] = 'text/rtf'

        mime_types['video/avi'] = 'video/avi'
        mime_types['video/mp4'] = 'video/mp4'
        mime_types['video/mpeg'] = 'video/mpeg'
        mime_types['video/mpg'] = 'video/mpeg'
        mime_types['video/mov'] = 'video/quicktime'
        mime_types['video/wmv'] = 'video/x-ms-wmv'
        mime_types['video/gif'] = 'image/gif'

        return mime_types.get(jats_mime_type.lower())

    def prettyXML(self):
        encoding = 'utf-8'

        rough_string = ElementTree.tostring(self.root, encoding)
        reparsed = minidom.parseString(rough_string)

        #return reparsed.toprettyxml(indent="\t", encoding = encoding)
        return reparsed.toxml(encoding=encoding)

def build_crossref_xml_for_articles(poa_articles, config_section="elife", pub_date=None, add_comment=True):
    """
    Given a list of article article objects,
    and then generate crossref XML from them
    """

    crossref_config = config[config_section]

    # test the XML generator
    eXML = crossrefXML(poa_articles, crossref_config, pub_date, add_comment)
    prettyXML = eXML.prettyXML()

    # Write to file
    f = open(TMP_DIR + os.sep + eXML.batch_id + '.xml', "wb")
    f.write(prettyXML)
    f.close()

    return prettyXML
    #print prettyXML
