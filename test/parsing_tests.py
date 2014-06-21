# -*- coding: utf-8 -*-
################################################################################
# Tests for studweb
# Carl-Erik Kopseng <carlerik@ifi.uio.no>
################################################################################
import unittest, re, codecs;
from studweb import * #SubjectResult
import studweb

class TestStudweb(unittest.TestCase):

    def test_results_are_equal(self):
        r1 = SubjectResult('inf101', 'beregningsorientert matematikk', 'A', 'V2014')
        r2 = SubjectResult('inf101', 'beregningsorientert matematikk', 'A', 'V2014')
        self.assertEqual(r1,r2)

    def test_parse_results_returns_expected_result_set_for_uio2013(self):
        with codecs.open('testdata/v2013_uio.html', 'r', encoding='utf-8') as f:
            html = f.read();

        parser = ResultParser('Semester')
        result_set = parser.parse_result(html)
        expected_set = result_set_uio_v13()

        diff = (expected_set.difference(result_set));
        self.assertEqual(diff, set())

    def test_can_parse_ntnu2014(self):
        with codecs.open('testdata/NTNU_2014/Innsyn Vurderingsresultater.html', 'r', encoding='utf-8', errors='ignore') as f:
            html = f.read();

        parser = ResultParser('Termin')
        result_set = parser.parse_result(html)

        self.assertEqual(len(result_set), 55)

    def test_can_parse_uio2014(self):
        with codecs.open('testdata/UIO_2014/Innsyn Vurderingsresultater.html', 'r', encoding='utf-8', errors='ignore') as f:
            html = f.read();

        parser = ResultParser('Semester')
        result_set = parser.parse_result(html)

        self.assertEqual(len(result_set), 7)

def result_set_uio_v13():
    results = set();

    results.add(SubjectResult('INF1820', u'Introduksjon til språk- og kommunikasjonsteknologi', 'Godkjent', u'Vår 2013'))
    results.add(SubjectResult('INF2810', u'Funksjonell programmering', 'Godkjent', u'Vår 2013'))
    results.add(SubjectResult('MAT100B', u'Grunnkurs i matematisk analyse med beregninger', 'B', u'Høst 2002'))
    results.add(SubjectResult('INF101', u'Grunnkurs i objektorientert programmering', 'B', u'Høst 2002'))

    return results

if __name__ == "__main__":    
#  import locale
#  locale.setlocale(locale.LC_ALL, 'nb_NO')

  unittest.main()
