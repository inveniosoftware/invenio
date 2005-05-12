# -*- coding: utf-8 -*-
##
## $Id$
##
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

"""Unit tests for the citation searcher."""

__version__ = "$Id$"

import bibrank_citation_searcher
import unittest

class TestCitationSearcher(unittest.TestCase):
    def setUp(self):
        self.recid = 339705
        self.recids = [339705, 339706]
        self.rank_method_code = 'cit'
       
    def test_init_cited_by_dictionary(self):
        """bibrank citation searcher - init cited-by data"""
        # FIXME: test postponed
        #self.assert_(bibrank_citation_searcher.init_cited_by_dictionary()) 

    def test_init_reference_list_dictionary(self):
        """bibrank citation searcher - init reference data"""
        # FIXME: test postponed
        #self.assert_(bibrank_citation_searcher.init_reference_list_dictionary())

    def test_calculate_cited_by_list(self):
        """bibrank citation searcher - get citing relevance"""
        # FIXME: test postponed

    def test_calculate_co_cited_with_list(self):
        """bibrank citation searcher - get co-cited-with data"""
        # FIXME: test postponed
            
def create_test_suite():
    """Return test suite for the citation searcher.""" 
    return unittest.TestSuite((unittest.makeSuite(TestCitationSearcher,'test'),))

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(create_test_suite())

