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

"""Unit tests for the document impact hit parade tests."""

__lastupdated__ = """<: print `date +"%d %b %Y %H:%M:%S %Z"`; :>"""

<protect> ## okay, rest of the Python code goes below #######

__version__ = "$Id$"

import bibrank_citation_searcher
import unittest

class TestListSetOperations(unittest.TestCase):

    def setUp(self):
        self.recid = 339705
        self.recids = [339705, 339706]
        self.rank_method_code = 'cit'
       
    def test_init_cited_by_dictionary(self):
        self.assert_(bibrank_citation_searcher.init_cited_by_dictionary()) 
    def test_init_reference_list_dictionary(self):
        self.assert_(bibrank_citation_searcher.init_reference_list_dictionary())
    def test_get_citing_recidrelevanc(self):
        self.assert_(bibrank_citation_searcher.get_citing_recidrelevance(self.rank_method_code, self.recids))    
    def test_get_co_cited_with_list(self):
        self.assert_(bibrank_citation_searcher.get_co_cited_with_list(self.recid))    
            
def create_test_suite():
    """Return test suite for the indexing engine.""" 
    return unittest.TestSuite((unittest.makeSuite(TestListSetOperations,'test'),))

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(create_test_suite())

