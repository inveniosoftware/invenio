## $Id$
## CDSware OAI repository unit tests.

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

<protect># -*- coding: utf-8 -*-</protect>

"""Unit tests for the oai repository."""

__lastupdated__ = """<: print `date +"%d %b %Y %H:%M:%S %Z"`; :>"""

<protect> ## okay, rest of the Python code goes below #######

__version__ = "$Id$"

import oai_repository
import unittest

class TestVerb(unittest.TestCase):
    """Test for OAI verb functionality."""

    def test_issue_verb(self):
        """"""
        self.assertEqual("", "");
        self.assertEqual("", "");
        self.assertEqual("", "");
        self.assertEqual("", "");
        self.assertEqual("", "");

class TestErrorCodes(unittest.TestCase):
    """Test for handling OAI error codes."""

    def test_strip_accents(self):
        """"""
        self.assertEqual("","")
        self.assertEqual("","")
        
        
def create_test_suite():
    """Return test suite for the oai repository."""
    return unittest.TestSuite((unittest.makeSuite(TestVerb,'test'),
                               unittest.makeSuite(TestErrorCodes,'test'))

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(create_test_suite())
