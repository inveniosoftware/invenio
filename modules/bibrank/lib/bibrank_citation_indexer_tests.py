## $Id$

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

"""Unit tests for the citation indexer."""

__lastupdated__ = """<: print `date +"%d %b %Y %H:%M:%S %Z"`; :>"""

<protect> ## okay, rest of the Python code goes below #######

__version__ = "$Id$"

import unittest
from bibrank_citation_indexer import last_updated_result

class TestListSetOperations(unittest.TestCase):

    def setUp(self):
        self.rank_method_code = 'cit'
        self.updated_recid_list = [339705, 339704, 339708]

    def test_last_updated_result(self):
        """bibrank citation indexer - last updated result"""
        self.assert_(last_updated_result(self.rank_method_code, self.updated_recid_list))

def create_test_suite():
    """Return test suite for the bibrank citation indexer."""
    return unittest.TestSuite((unittest.makeSuite(TestListSetOperations, 'test'),))

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(create_test_suite())


