import unittest
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

from elifearticle.article import Article, Component, Citation, Dataset, Contributor, Affiliation, License

from elifecrossref import generate
from elifecrossref.conf import raw_config, parse_raw_config


class TestGenerateComponentList(unittest.TestCase):

    def setUp(self):
        pass

    def test_component_subtitle_no_face_markup(self):
        "build an article object and component, generate Crossref XML"
        doi = "10.7554/eLife.00666"
        title = "Test article"
        article = Article(doi, title)
        component = Component()
        component.title = "A component"
        component.subtitle = "A <sc>STRANGE</sc> <italic>subtitle</italic>, and this tag is <not_allowed>!</not_allowed>"
        expected_subtitle = "A STRANGE subtitle, and this tag is &lt;not_allowed&gt;!&lt;/not_allowed&gt;"
        article.component_list = [component]
        # generate the crossrefXML
        c_xml = generate.build_crossref_xml([article])
        crossref_xml_string = c_xml.output_xml()
        self.assertIsNotNone(crossref_xml_string)
        # A quick test just look for the expected string to test for tags and escape characters
        self.assertTrue(expected_subtitle in crossref_xml_string)


    def test_component_subtitle_with_face_markup(self):
        "build an article object and component, generate Crossref XML"
        doi = "10.7554/eLife.00666"
        title = "Test article"
        article = Article(doi, title)
        component = Component()
        component.title = "A component"
        component.subtitle = "A <sc>STRANGE</sc> <italic>subtitle</italic>, and this tag is <not_allowed>!</not_allowed>"
        expected_subtitle = "A <sc>STRANGE</sc> <i>subtitle</i>, and this tag is &lt;not_allowed&gt;!&lt;/not_allowed&gt;"
        article.component_list = [component]
        # load a config and override the value
        raw_config_object = raw_config('elife')
        face_markup = raw_config_object.get('face_markup')
        raw_config_object['face_markup'] = 'true'
        crossref_config = parse_raw_config(raw_config_object)
        # generate the crossrefXML
        c_xml = generate.CrossrefXML([article], crossref_config, None, True)
        crossref_xml_string = c_xml.output_xml()
        self.assertIsNotNone(crossref_xml_string)
        # A quick test just look for the expected string to test for tags and escape characters
        self.assertTrue(expected_subtitle in crossref_xml_string)
        # now set the config back to normal
        raw_config_object['face_markup'] = face_markup


class TestGenerateContributors(unittest.TestCase):

    def setUp(self):
        pass

    def test_generate_no_contributors(self):
        "Test when an article has no contributors"
        "build an article object and component, generate Crossref XML"
        doi = "10.7554/eLife.00666"
        title = "Test article"
        article = Article(doi, title)
        # generate the crossrefXML
        c_xml = generate.build_crossref_xml([article])
        crossref_xml_string = c_xml.output_xml()
        self.assertIsNotNone(crossref_xml_string)
        # A quick test just look for a string value to test
        self.assertTrue('<contributors' not in crossref_xml_string)

    def test_generate_blank_affiliation(self):
        "Test when a contributor has a blank affiliation"
        doi = "10.7554/eLife.00666"
        title = "Test article"
        article = Article(doi, title)
        author = Contributor('author', 'Surname', 'Given names')
        aff = Affiliation()
        aff.text = ''
        author.set_affiliation(aff)
        # generate the crossrefXML
        c_xml = generate.build_crossref_xml([article])
        crossref_xml_string = c_xml.output_xml()
        self.assertIsNotNone(crossref_xml_string)
        # A quick test just look for a string value to test
        self.assertTrue('<affiliation>' not in crossref_xml_string)

class TestGenerateCrossrefSchemaVersion(unittest.TestCase):

    def setUp(self):
        pass

    def test_generate_crossref_schema_version_4_3_5(self):
        self.generate_crossref_schema_version(
            '4.3.5',
            'xmlns="http://www.crossref.org/schema/4.3.5"'
        )

    def test_generate_crossref_schema_version_4_3_7(self):
        self.generate_crossref_schema_version(
            '4.3.7',
            'xmlns="http://www.crossref.org/schema/4.3.7"'
        )

    def test_generate_crossref_schema_version_4_4_0(self):
        self.generate_crossref_schema_version(
            '4.4.0',
            'xmlns="http://www.crossref.org/schema/4.4.0"'
        )

    def generate_crossref_schema_version(self, crossref_schema_version, expected_snippet):
        "Test non-default crossref schema version"
        "build an article object and component, generate Crossref XML"
        doi = "10.7554/eLife.00666"
        title = "Test article"
        article = Article(doi, title)
        # load a config and override the value
        raw_config_object = raw_config('elife')
        original_crossref_schema_version = raw_config_object.get('crossref_schema_version')
        raw_config_object['crossref_schema_version'] = crossref_schema_version
        crossref_config = parse_raw_config(raw_config_object)
        # generate the crossrefXML
        c_xml = generate.CrossrefXML([article], crossref_config, None, True)
        crossref_xml_string = c_xml.output_xml()
        self.assertIsNotNone(crossref_xml_string)
        # A quick test just look for a string value to test
        self.assertTrue(expected_snippet in crossref_xml_string)
        # now set the config back to normal
        raw_config_object['crossref_schema_version'] = original_crossref_schema_version


class TestGenerateCrossrefCitationPublisher(unittest.TestCase):

    def setUp(self):
        self.publisher_loc = "Nijmegen, The Netherlands"
        self.publisher_name = "Radboud University Nijmegen Medical Centre"

    def test_generate_citation_publisher_none(self):
        "no publisher name concatenation"
        citation = Citation()
        c_xml = generate.CrossrefXML([], {})
        self.assertIsNone(c_xml.citation_publisher(citation))

    def test_generate_citation_publisher_loc_only(self):
        "no publisher name concatenation"
        citation = Citation()
        citation.publisher_loc = self.publisher_loc
        c_xml = generate.CrossrefXML([], {})
        self.assertEqual(
            c_xml.citation_publisher(citation),
            "Nijmegen, The Netherlands")

    def test_generate_citation_publisher_name_only(self):
        "no publisher name concatenation"
        citation = Citation()
        citation.publisher_name = self.publisher_name
        c_xml = generate.CrossrefXML([], {})
        self.assertEqual(
            c_xml.citation_publisher(citation),
            "Radboud University Nijmegen Medical Centre")

    def test_generate_citation_publisher_all(self):
        "no publisher name concatenation"
        citation = Citation()
        citation.publisher_loc = self.publisher_loc
        citation.publisher_name = self.publisher_name
        c_xml = generate.CrossrefXML([], {})
        self.assertEqual(
            c_xml.citation_publisher(citation),
            "Nijmegen, The Netherlands: Radboud University Nijmegen Medical Centre")


class TestGenerateCrossrefUnstructuredCitation(unittest.TestCase):

    def setUp(self):
        pass

    def test_set_unstructured_citation_no_face_markup(self):
        "unstructured citation example with no face markup"
        article_title = 'PhD thesis: Submicroscopic <italic>Plasmodium falciparum</italic> gametocytaemia and the contribution to malaria transmission'
        expected = '<citation><unstructured_citation>PhD thesis: Submicroscopic Plasmodium falciparum gametocytaemia and the contribution to malaria transmission.</unstructured_citation></citation>'
        crossref_config = {}
        citation = Citation()
        citation.article_title = article_title
        citation.publication_type = 'patent'
        c_xml = generate.CrossrefXML([], crossref_config)
        parent = Element('citation')
        citation_element = c_xml.set_unstructured_citation(parent, citation)
        rough_string = ElementTree.tostring(citation_element).decode('utf-8')
        self.assertEqual(rough_string, expected)

    def test_set_unstructured_citation_face_markup(self):
        "unstructured citation example which does include face markup"
        article_title = 'PhD thesis: Submicroscopic <italic>Plasmodium falciparum</italic> gametocytaemia and the contribution to malaria transmission'
        expected = '<citation><unstructured_citation>PhD thesis: Submicroscopic <i>Plasmodium falciparum</i> gametocytaemia and the contribution to malaria transmission.</unstructured_citation></citation>'
        # load a config and override the value
        raw_config_object = raw_config('elife')
        original_face_markup = raw_config_object.get('face_markup')
        raw_config_object['face_markup'] = 'true'
        crossref_config = parse_raw_config(raw_config_object)
        # continue
        citation = Citation()
        citation.article_title = article_title
        citation.publication_type = 'patent'
        c_xml = generate.CrossrefXML([], crossref_config)
        parent = Element('citation')
        citation_element = c_xml.set_unstructured_citation(parent, citation)
        rough_string = ElementTree.tostring(citation_element).decode('utf-8')
        self.assertEqual(rough_string, expected)
        # now set the config back to normal
        raw_config_object['face_markup'] = original_face_markup


class TestGenerateCrossrefCitationId(unittest.TestCase):

    def setUp(self):
        pass

    def test_ref_list_citation_with_no_id(self):
        "for test coverage an article with a ref_list with a citation that has no id attribute"
        doi = "10.7554/eLife.00666"
        title = "Test article"
        article = Article(doi, title)
        citation = Citation()
        citation.article_title = "An article title"
        article.ref_list = [citation]
        c_xml = generate.build_crossref_xml([article])
        crossref_xml_string = c_xml.output_xml()
        self.assertTrue('<citation key="1">' in crossref_xml_string)


class TestGenerateCrossrefDatasets(unittest.TestCase):

    def setUp(self):
        pass

    def test_set_datasets(self):
        "a basic non-XML example for set_datasets"
        doi = "10.7554/eLife.00666"
        title = "Test article"
        article = Article(doi, title)
        # dataset_1 example with a uri
        dataset_1 = Dataset()
        dataset_1.dataset_type = "datasets"
        dataset_1.uri = "https://github.com/elifesciences/XML-mapping/blob/master/elife-00666.xml"
        dataset_1.title = "Kitchen sink"
        # dataset_2 example with accession_id
        dataset_2 = Dataset()
        dataset_2.dataset_type = "prev_published_datasets"
        dataset_2.accession_id = "EGAS00001000968"
        # dataset_3 example with doi
        dataset_3 = Dataset()
        dataset_3.dataset_type = "prev_published_datasets"
        dataset_3.doi = "10.5061/dryad.cv323"
        # dataset_4 example with no dataset_type will be treated as a generated dataset by default
        dataset_4 = Dataset()
        dataset_4.uri = "http://cghub.ucsc.edu"
        # dataset_5 example with an unsupported dataset_type
        dataset_5 = Dataset()
        dataset_5.dataset_type = "foo"
        dataset_5.uri = "https://elifesciences.org"
        # dataset_6 example with no identifier, not get added to the XML output, for test coverage
        dataset_6 = Dataset()
        dataset_6.dataset_type = "prev_published_datasets"
        # add the datasets to the article object
        article.add_dataset(dataset_1)
        article.add_dataset(dataset_2)
        article.add_dataset(dataset_3)
        article.add_dataset(dataset_4)
        article.add_dataset(dataset_5)
        article.add_dataset(dataset_6)
        # expected values
        expected_xml_snippet_1 = '<rel:program><rel:related_item><rel:description>Kitchen sink</rel:description><rel:inter_work_relation identifier-type="uri" relationship-type="isSupplementedBy">https://github.com/elifesciences/XML-mapping/blob/master/elife-00666.xml</rel:inter_work_relation></rel:related_item>'
        expected_xml_snippet_2 = '<rel:related_item><rel:inter_work_relation identifier-type="accession" relationship-type="references">EGAS00001000968</rel:inter_work_relation></rel:related_item>'
        expected_xml_snippet_3 = '<rel:related_item><rel:inter_work_relation identifier-type="doi" relationship-type="references">10.5061/dryad.cv323</rel:inter_work_relation></rel:related_item>'
        expected_xml_snippet_4 = '<rel:related_item><rel:inter_work_relation identifier-type="uri" relationship-type="isSupplementedBy">http://cghub.ucsc.edu</rel:inter_work_relation></rel:related_item>'
        expected_xml_snippet_5 = '<rel:related_item><rel:inter_work_relation identifier-type="uri" relationship-type="isSupplementedBy">https://elifesciences.org</rel:inter_work_relation></rel:related_item>'
        # generate output
        c_xml = generate.build_crossref_xml([article])
        crossref_xml_string = c_xml.output_xml()
        self.assertIsNotNone(crossref_xml_string)
        # Test for expected strings in the XML output
        self.assertTrue(expected_xml_snippet_1 in crossref_xml_string)
        self.assertTrue(expected_xml_snippet_2 in crossref_xml_string)
        self.assertTrue(expected_xml_snippet_3 in crossref_xml_string)
        self.assertTrue(expected_xml_snippet_4 in crossref_xml_string)
        self.assertTrue(expected_xml_snippet_5 in crossref_xml_string)


class TestGenerateCrossrefDataCitation(unittest.TestCase):

    def setUp(self):
        pass

    def test_ref_list_data_citation_with_pmid(self):
        "for test coverage an article with a ref_list with a data citation that has a pmid attribute"
        doi = "10.7554/eLife.00666"
        title = "Test article"
        article = Article(doi, title)
        citation = Citation()
        citation.data_title = "An data title"
        citation.publication_type = "data"
        citation.pmid = "pmid"
        article.ref_list = [citation]
        expected_contains = '<rel:program><rel:related_item><rel:description>An data title</rel:description><rel:inter_work_relation identifier-type="pmid" relationship-type="references">pmid</rel:inter_work_relation></rel:related_item></rel:program>'
        # generate
        c_xml = generate.build_crossref_xml([article])
        crossref_xml_string = c_xml.output_xml()
        # test assertion
        self.assertTrue(expected_contains in crossref_xml_string)


class TestGenerateAbstract(unittest.TestCase):

    def setUp(self):
        self.abstract = '<p><bold><italic><underline><sub><sup>An abstract. <ext-link ext-link-type="uri" xlink:href="http://dx.doi.org/10.1601/nm.3602">Desulfocapsa sulfexigens</ext-link>.</sup></sub></underline></italic></bold></p>'

    def test_set_abstract(self):
        "test stripping unwanted tags from abstract"
        doi = "10.7554/eLife.00666"
        title = "Test article"
        article = Article(doi, title)
        article.abstract = self.abstract
        expected_contains = '<jats:abstract><jats:p>An abstract. Desulfocapsa sulfexigens.</jats:p></jats:abstract>'
        # generate
        crossref_object = generate.build_crossref_xml([article])
        crossref_xml_string = crossref_object.output_xml()
        # test assertion
        self.assertTrue(expected_contains in crossref_xml_string)

    def test_set_abstract_jats_abstract_format(self):
        "test the abstract using jats abstract format set to true"
        doi = "10.7554/eLife.00666"
        title = "Test article"
        article = Article(doi, title)
        article.abstract = self.abstract
        expected_contains = '<jats:abstract><jats:p><jats:bold><jats:italic><jats:underline><jats:sub><jats:sup>An abstract. Desulfocapsa sulfexigens.</jats:sup></jats:sub></jats:underline></jats:italic></jats:bold></jats:p></jats:abstract>'
        # generate
        raw_config_object = raw_config('elife')
        jats_abstract = raw_config_object.get('jats_abstract')
        face_markup = raw_config_object.get('face_markup')
        raw_config_object['jats_abstract'] = 'true'
        raw_config_object['face_markup'] = 'true'
        crossref_config = parse_raw_config(raw_config_object)
        crossref_object = generate.CrossrefXML([article], crossref_config, None, True)
        crossref_xml_string = crossref_object.output_xml()
        # test assertion
        self.assertTrue(expected_contains in crossref_xml_string)
        # now set the config back to normal
        raw_config_object['jats_abstract'] = jats_abstract
        raw_config_object['face_markup'] = face_markup


class TestGenerateTitles(unittest.TestCase):

    def setUp(self):
        self.title = '<bold>Test article</bold> for <ext-link ext-link-type="uri" xlink:href="http://dx.doi.org/10.1601/nm.3602">Desulfocapsa sulfexigens</ext-link>'

    def test_set_titles(self):
        "test stripping unwanted tags from title"
        doi = "10.7554/eLife.00666"
        article = Article(doi, self.title)
        expected_contains = '<titles><title>Test article for Desulfocapsa sulfexigens</title></titles>'
        # generate
        crossref_object = generate.build_crossref_xml([article])
        crossref_xml_string = crossref_object.output_xml()
        # test assertion
        self.assertTrue(expected_contains in crossref_xml_string)

    def test_set_titles_face_markup_format(self):
        "test the title using face markup set to true"
        doi = "10.7554/eLife.00666"
        article = Article(doi, self.title)
        expected_contains = '<titles><title><b>Test article</b> for Desulfocapsa sulfexigens</title></titles>'
        # generate
        raw_config_object = raw_config('elife')
        face_markup = raw_config_object.get('face_markup')
        raw_config_object['face_markup'] = 'true'
        crossref_config = parse_raw_config(raw_config_object)
        crossref_object = generate.CrossrefXML([article], crossref_config, None, True)
        crossref_xml_string = crossref_object.output_xml()
        # test assertion
        self.assertTrue(expected_contains in crossref_xml_string)
        # now set the config back to normal
        raw_config_object['face_markup'] = face_markup


class TestSetCollection(unittest.TestCase):

    def setUp(self):
        pass

    def create_aricle_object(self):
        "create a basic article object"
        doi = "10.7554/eLife.00666"
        title = "Test article"
        article = Article(doi, title)
        return article

    def create_crossref_object(self, article):
        "utility to create the crossref object"
        raw_config_object = raw_config('elife')
        crossref_config = parse_raw_config(raw_config_object)
        crossref_object = generate.CrossrefXML([article], crossref_config, None, True)
        return crossref_object

    def test_do_set_collection_no_license(self):
        "test when an article has no license"
        # create CrossrefXML object to test
        article = self.create_aricle_object()
        crossref_object = self.create_crossref_object(article)
        # test assertion
        collection_property = "text-mining"
        self.assertFalse(crossref_object.do_set_collection(article, collection_property))

    def test_do_set_collection_empty_license(self):
        "test when an article has no license"
        article = self.create_aricle_object()
        # create an empty license
        license_object = License()
        article.license = license_object
        # create CrossrefXML object to test
        crossref_object = self.create_crossref_object(article)
        # test assertion
        collection_property = "text-mining"
        self.assertFalse(crossref_object.do_set_collection(article, collection_property))

    def test_do_set_collection_with_license(self):
        "test when an article has no license"
        article = self.create_aricle_object()
        # create a license with a href value
        license_object = License()
        license_object.href = "http://example.org/license.txt"
        article.license = license_object
        # create CrossrefXML object to test
        crossref_object = self.create_crossref_object(article)
        # test assertion
        collection_property = "text-mining"
        self.assertTrue(crossref_object.do_set_collection(article, collection_property))


class TestAddCleanTag(unittest.TestCase):

    def setUp(self):
        pass

    def test_add_clean_tag(self):
        "test add_clean_tag to check edge cases"
        # start with creating a Crossref object with a basic article object
        doi = "10.7554/eLife.00666"
        title = "Test article"
        article = Article(doi, title)
        c_xml = generate.build_crossref_xml([article])
        root = Element('root')
        # add the element
        c_xml.add_clean_tag(root, 'p', '<test>')
        self.assertEqual(ElementTree.tostring(root).decode('utf-8'), '<root><p>&lt;test&gt;</p></root>')
        # strange example based on eLife 28716 v2 Figure 2 caption
        root = Element('root')
        c_xml.add_clean_tag(root, 'subtitle', '...polarization, <<italic>p</italic>>, and its variance...')
        self.assertEqual(ElementTree.tostring(root).decode('utf-8'), '<root><subtitle>...polarization, &lt;p&gt;, and its variance...</subtitle></root>')


if __name__ == '__main__':
    unittest.main()
