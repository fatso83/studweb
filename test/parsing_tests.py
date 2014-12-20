# -*- coding: utf-8 -*-
################################################################################
# Tests for studweb - testdata held back for privacy reasons ...
# Carl-Erik Kopseng <carlerik@ifi.uio.no>
################################################################################
import unittest, re, codecs
from studweb import * 
import studweb

class TestSubjectResult(unittest.TestCase):

    def test_results_are_equal(self):
        r1 = SubjectResult('inf101', 'beregningsorientert matematikk', 'A', 'V2014')
        r2 = SubjectResult('inf101', 'beregningsorientert matematikk', 'A', 'V2014')
        self.assertEqual(r1,r2)

class TestResultPageParser(unittest.TestCase):

    def test_parses_returns_expected_result_set_for_uio2013(self):
        with codecs.open('testdata/v2013_uio.html', 'r', encoding='utf-8') as f:
            html = f.read()

        parser = studweb.get_parser('studweb.uio.no')
        result_set = parser.parse_result_page_for_results(html)
        expected_set = result_set_uio_v13()

        diff = (expected_set.difference(result_set))
        self.assertEqual(diff, set())

    def test_can_parse_ntnu2014(self):
        with codecs.open('testdata/NTNU_2014/Innsyn Vurderingsresultater.html', 'r', encoding='utf-8', errors='ignore') as f:
            html = f.read()

        parser = studweb.get_parser('studweb.ntnu.no')
        result_set = parser.parse_result_page_for_results(html)

        self.assertEqual(len(result_set), 55)

    def test_can_parse_uio2014(self):
        with codecs.open('testdata/UIO_2014/Innsyn Vurderingsresultater.html', 'r', encoding='utf-8', errors='ignore') as f:
            html = f.read()

        parser = studweb.get_parser('studweb.uio.no')
        result_set = parser.parse_result_page_for_results(html)

        self.assertEqual(len(result_set), 7)

    def test_parse_page_with_expanded_link_section_for_logout_url(self):
        expected = "/as/WebObjects/studentweb2.woa/wo/3.0.23.24.6.0.1.1"

        with codecs.open('testdata/UIO_2014/Innsyn Vurderingsresultater.html', 'r', encoding='utf-8', errors='ignore') as f:
        # with codecs.open('/Users/carl-erik.kopseng/.studweb.latest_error.html', 'r', encoding='utf-8', errors='ignore') as f:
            html = f.read()

        parser = studweb.get_parser('studweb.uio.no')
        link = parser.parse_page_with_expanded_link_section_for_logout_url(html)

        self.assertTrue(expected in link)

class TestStudWeb(unittest.TestCase):

    def test_url_to_result_page_NTNU(self):
        host = 'studweb.ntnu.no'
        uri_path = '/cgi-bin/WebObjects/studentweb2.woa/wo/6.0.23.24.6.16.1.1'
        dir = 'NTNU_2014'

        url_to_result_page(self, host, uri_path, dir)

    def test_url_to_result_page_UIO(self):
        host = 'studweb.uio.no'
        uri_path = '/as/WebObjects/studentweb2.woa/wo/3.0.23.24.6.12.1.1'
        dir = 'UIO_2014'

        url_to_result_page(self, host, uri_path, dir)


    def test_diff_returns_new_results(self):
        old = set()
        new = set()

        old.add(SubjectResult('INF1820', u'desc', 'Godkjent', u'Vår 2013'))
        old.add(SubjectResult('INF2810', u'Funksjonell programmering', 'Godkjent', u'Vår 2013'))
        old.add(SubjectResult('MAT100B', u'Grunnkurs i matematisk analyse med beregninger', 'B', u'Høst 2002'))
        r1=SubjectResult('INF1820', u'desc', 'A', u'Vår 2013')
        r2=SubjectResult('INF2810', u'Funksjonell programmering', 'B', u'Vår 2013')
        new.add(r1)
        new.add(r2)
        new.add(SubjectResult('MAT100B', u'Grunnkurs i matematisk analyse med beregninger', 'B', u'Høst 2002'))

        self.assertEqual(studweb.diff(old, new), set([r1,r2]))


    def test_stores_results_in_dotfile(self):
        html = '<html>something</html>'
        studweb.store(html)
        with open(studweb.data_file) as f:
            content = f.read()

        self.assertEqual(content, html)

    def test_regex_parsing(self):
        text_and_img_in_a_tag = """
        <td>
            <a href="https://alink.com">
                <img src="dummy.gif" >
                Foo Some text Bar
            </a>
        </td>
        """

        soup = BeautifulSoup(text_and_img_in_a_tag)
        links = soup.find_all(text=re.compile('Some text'))
        href = links[0].parent['href']

        self.assertEqual(href, 'https://alink.com')


    def tearDown(self):
        import os
        try:
            os.remove(studweb.data_file)
        except OSError:
            pass


def result_set_uio_v13():
    results = set()

    results.add(SubjectResult('INF1820', u'Introduksjon til språk- og kommunikasjonsteknologi', 'Godkjent', u'Vår 2013'))
    results.add(SubjectResult('INF2810', u'Funksjonell programmering', 'Godkjent', u'Vår 2013'))
    results.add(SubjectResult('MAT100B', u'Grunnkurs i matematisk analyse med beregninger', 'B', u'Høst 2002'))
    results.add(SubjectResult('INF101', u'Grunnkurs i objektorientert programmering', 'B', u'Høst 2002'))

    return results

def url_to_result_page(self, host, uri_path, dir):

    with codecs.open('testdata/' + dir + '/Startside Opplysninger.html', 'r', encoding='utf-8', errors='ignore') as f:
        html = f.read()

    parser = studweb.get_parser(host)
    found_url = parser.parse_page_with_expanded_link_section_for_results_url(html)

    self.assertTrue(uri_path in found_url)


if __name__ == "__main__":    

  unittest.main()
