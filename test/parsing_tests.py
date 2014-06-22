# -*- coding: utf-8 -*-
################################################################################
# Tests for studweb - testdata held back for privacy reasons ...
# Carl-Erik Kopseng <carlerik@ifi.uio.no>
################################################################################
import unittest, re, codecs;
from studweb import * 
import studweb

class TestStudweb(unittest.TestCase):

    def test_results_are_equal(self):
        r1 = SubjectResult('inf101', 'beregningsorientert matematikk', 'A', 'V2014')
        r2 = SubjectResult('inf101', 'beregningsorientert matematikk', 'A', 'V2014')
        self.assertEqual(r1,r2)

    def test_parses_returns_expected_result_set_for_uio2013(self):
        with codecs.open('testdata/v2013_uio.html', 'r', encoding='utf-8') as f:
            html = f.read();

        parser = ResultParser('Semester')
        result_set = parser.parse(html)
        expected_set = result_set_uio_v13()

        diff = (expected_set.difference(result_set));
        self.assertEqual(diff, set())

    def test_can_parse_ntnu2014(self):
        with codecs.open('testdata/NTNU_2014/Innsyn Vurderingsresultater.html', 'r', encoding='utf-8', errors='ignore') as f:
            html = f.read();

        parser = ResultParser('Termin')
        result_set = parser.parse(html)

        self.assertEqual(len(result_set), 55)

    def test_can_parse_uio2014(self):
        with codecs.open('testdata/UIO_2014/Innsyn Vurderingsresultater.html', 'r', encoding='utf-8', errors='ignore') as f:
            html = f.read();

        parser = ResultParser('Semester')
        result_set = parser.parse(html)

        self.assertEqual(len(result_set), 7)

    def test_returns_new_results(self):
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

    def tearDown(self):
        import os
        try:
            os.remove(studweb.data_file)
        except OSError:
            pass


def result_set_uio_v13():
    results = set();

    results.add(SubjectResult('INF1820', u'Introduksjon til språk- og kommunikasjonsteknologi', 'Godkjent', u'Vår 2013'))
    results.add(SubjectResult('INF2810', u'Funksjonell programmering', 'Godkjent', u'Vår 2013'))
    results.add(SubjectResult('MAT100B', u'Grunnkurs i matematisk analyse med beregninger', 'B', u'Høst 2002'))
    results.add(SubjectResult('INF101', u'Grunnkurs i objektorientert programmering', 'B', u'Høst 2002'))

    return results

if __name__ == "__main__":    

  unittest.main()
