## $Id$
## CDSware Search Engine in mod_python.

## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002 CERN.
##
## The CDSware is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## The CDSware is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.  
##
## You should have received a copy of the GNU General Public License
## along with CDSware; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

<protect># -*- coding: utf-8 -*-</protect>

"""Unit tests for the ranking engine."""

__lastupdated__ = """<: print `date +"%d %b %Y %H:%M:%S %Z"`; :>"""

<protect> ## okay, rest of the Python code goes below #######

__version__ = "$Id$"

import bibrank_record_sorter
import unittest
from cdsware.search_engine import HitSet

class TestListSetOperations(unittest.TestCase):
    """Test list set operations."""

    def test_record_sorter(self):
        """bibrank_record_sorter sort_record_relevance"""
        self.assertEqual([(1, 71), (3, 100)], bibrank_record_sorter.sort_record_relevance({1: 50, 2:30, 3:70, 4:10}, 50, 0))
    def test_calculate_record_relevance(self):
        """bibrank_record_sorter calculate_record_relevance"""
        hitset = HitSet()
        hitset.addlist((1,2,5))
        self.assertEqual(({1: 839, 2: 1193, 5: 350}, {1: 1, 2: 1, 5: 1}),  bibrank_record_sorter.calculate_record_relevance(("testterm", 2.0), {"Gi":(0, 50.0), 1: (3, 4.0), 2: (4, 5.0), 5: (1, 3.5)}, hitset, {}, {}, 0, None))

    def test_post_calculate_record_relevance(self):
        """bibrank_record_sorter post_calculate_record_relevance"""
        hitset = HitSet()
        hitset.addlist((1,2,5))
        (returned_dict, returned_hitset) = bibrank_record_sorter.post_calculate_record_relevance({1: 839, 2: 1193, 5: 350}, {1: 1, 2: 1, 5: 1}, hitset, 0)
        self.assertEqual(({1: 6.7322107064672059, 2: 7.0842264220979159, 5: 5.857933154483459}, []), (returned_dict, returned_hitset.tolist()))

def create_test_suite():
    """Return test suite for the indexing engine."""
    return unittest.TestSuite((unittest.makeSuite(TestListSetOperations,'test'),))

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(create_test_suite())
