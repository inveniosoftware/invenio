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

"""Unit tests for the search engine."""

__lastupdated__ = """<: print `date +"%d %b %Y %H:%M:%S %Z"`; :>"""

<protect> ## okay, rest of the Python code goes below #######

__version__ = "$Id$"

import search_engine
import unittest

class TestWashQueryParameters(unittest.TestCase):
    """Test for washing of search query parameters."""

    def test_wash_url_argument(self):
        """search engine washing of URL arguments"""
        self.assertEqual(1, search_engine.wash_url_argument(['1'],'int'))
        self.assertEqual("1", search_engine.wash_url_argument(['1'],'str'))
        self.assertEqual(['1'], search_engine.wash_url_argument(['1'],'list'))
        self.assertEqual(0, search_engine.wash_url_argument('ellis','int'))
        self.assertEqual("ellis", search_engine.wash_url_argument('ellis','str'))
        self.assertEqual(["ellis"], search_engine.wash_url_argument('ellis','list'))
        self.assertEqual(0, search_engine.wash_url_argument(['ellis'],'int'))
        self.assertEqual("ellis", search_engine.wash_url_argument(['ellis'],'str'))
        self.assertEqual(["ellis"], search_engine.wash_url_argument(['ellis'],'list'))

    def test_wash_pattern(self):
        """search engine washing of query patterns"""
        self.assertEqual("Ellis, J", search_engine.wash_pattern('Ellis, J'))
        self.assertEqual("ell", search_engine.wash_pattern('ell*'))


class TestStripAccents(unittest.TestCase):
    """Test for handling of UTF-8 accents."""

    def test_strip_accents(self):
        """search engine stripping of accented letters"""
        self.assertEqual("memememe", search_engine.wash_pattern('mémêmëmè'))
        self.assertEqual("MEMEMEME", search_engine.wash_pattern('MÉMÊMËMÈ'))


def create_test_suite():
    """Return test suite for the search engine."""
    return unittest.TestSuite((unittest.makeSuite(TestWashQueryParameters,'test'),
                               unittest.makeSuite(TestStripAccents,'test')))

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(create_test_suite())
