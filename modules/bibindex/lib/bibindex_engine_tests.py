# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002, 2003, 2004, 2005 CERN.
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

"""Unit tests for the indexing engine."""

__version__ = "$Id$"

import bibindex_engine
import unittest

class TestListSetOperations(unittest.TestCase):
    """Test list set operations."""

    def test_list_union(self):
        """bibindex engine - list union"""
        self.assertEqual([1,2,3,4], bibindex_engine.list_union([1,2,3],[1,3,4]))

def create_test_suite():
    """Return test suite for the indexing engine."""
    return unittest.TestSuite((unittest.makeSuite(TestListSetOperations,'test'),))

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(create_test_suite())
