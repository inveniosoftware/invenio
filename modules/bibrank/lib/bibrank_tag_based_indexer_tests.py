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

import bibrank_tag_based_indexer
import unittest

class TestListSetOperations(unittest.TestCase):
    """Test list set operations."""

    def test_union_dicts(self):
        """bibrank tag based indexer - union dicts"""
        self.assertEqual({1: 5, 2: 6, 3: 9, 4: 10, 10: 1}, bibrank_tag_based_indexer.union_dicts({1: 5, 2: 6, 3: 9}, {3:9, 4:10, 10: 1}))

    def test_split_ranges(self):
        """bibrank tag based indexer - split ranges"""
        self.assertEqual([[0, 500], [600, 1000]], bibrank_tag_based_indexer.split_ranges("0-500,600-1000"))

def create_test_suite():
    """Return test suite for the indexing engine."""
    return unittest.TestSuite((unittest.makeSuite(TestListSetOperations,'test'),))

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(create_test_suite())
