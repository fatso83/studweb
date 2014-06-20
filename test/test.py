# -*- coding: utf-8 -*-
################################################################################
# Tests for studweb
# Carl-Erik Kopseng <carlerik@ifi.uio.no>
################################################################################
import unittest, re;
from studweb import Result
  
class TestStudweb(unittest.TestCase):

    def test_results_are_equal(self):
        r1 = Result('inf101', 'beregningsorientert matematikk', 'A')
        r2 = Result('inf101', 'beregningsorientert matematikk', 'A')
        self.assertEquals(r1,r2)

if __name__ == "__main__":    
  import locale
  locale.setlocale(locale.LC_ALL, 'nb_NO')

  unittest.main()
  
