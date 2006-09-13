# -*- coding: utf-8 -*-
##
## $Id$
## CDS Invenio OAI repository unit tests.
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.  
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Unit tests for the oai repository."""

__revision__ = "$Id$"

import unittest
import re

from invenio import oai_repository

class TestVerbs(unittest.TestCase):
    """Test for OAI verb functionality."""

    def test_verbs(self):
        """bibharvest oai repository - testing verbs"""
        self.assertNotEqual(None, re.search("Identify", oai_repository.oaiidentify("")))
        self.assertNotEqual(None, re.search("ListIdentifiers", oai_repository.oailistidentifiers("")))
        self.assertNotEqual(None, re.search("ListRecords", oai_repository.oailistrecords("")))
        self.assertNotEqual(None, re.search("ListMetadataFormats", oai_repository.oailistmetadataformats("")))
        self.assertNotEqual(None, re.search("ListSets", oai_repository.oailistsets("")))
        self.assertNotEqual(None, re.search("GetRecord", oai_repository.oaigetrecord("")))


class TestErrorCodes(unittest.TestCase):
    """Test for handling OAI error codes."""

    def test_issue_error_identify(self):
        """bibharvest oai repository - testing error codes"""
        
        self.assertNotEqual(None, re.search("badVerb", oai_repository.check_args(oai_repository.parse_args("junk"))))
        self.assertNotEqual(None, re.search("badVerb", oai_repository.check_args(oai_repository.parse_args("verb=IllegalVerb"))))
        self.assertNotEqual(None, re.search("badArgument", oai_repository.check_args(oai_repository.parse_args("verb=Identify&test=test"))))
        self.assertNotEqual(None, re.search("badArgument", oai_repository.check_args(oai_repository.parse_args("verb=ListIdentifiers&metadataPrefix=oai_dc&from=some_random_date&until=some_random_date"))))
        self.assertNotEqual(None, re.search("badArgument", oai_repository.check_args(oai_repository.parse_args("verb=ListIdentifiers&metadataPrefix=oai_dc&from=2001-01-01&until=2002-01-01T00:00:00Z"))))
        self.assertNotEqual(None, re.search("badArgument", oai_repository.check_args(oai_repository.parse_args("verb=ListIdentifiers"))))
        self.assertNotEqual(None, re.search("badArgument", oai_repository.check_args(oai_repository.parse_args("verb=ListIdentifiers&metadataPrefix=illegal_mdp"))))
        self.assertNotEqual(None, re.search("badArgument", oai_repository.check_args(oai_repository.parse_args("verb=ListIdentifiers&metadataPrefix=oai_dc&metadataPrefix=oai_dc"))))
        self.assertNotEqual(None, re.search("badArgument", oai_repository.check_args(oai_repository.parse_args("verb=ListRecords&metadataPrefix=oai_dc&set=really_wrong_set&from=some_random_date&until=some_random_date"))))
        self.assertNotEqual(None, re.search("badArgument", oai_repository.check_args(oai_repository.parse_args("verb=ListRecords"))))

class TestEncodings(unittest.TestCase):
    """Test for OAI response encodings."""

    def test_encoding(self):
        """bibharvest oai repository - testing encodings"""

        self.assertEqual("&lt;&amp;>", oai_repository.encode_for_xml("<&>"))
        self.assertEqual("%20", oai_repository.escape_space(" "))
        self.assertEqual("%25%20%3F%23%3D%26%2F%3A%3B%2B", oai_repository.encode_for_url("% ?#=&/:;+"))

def create_test_suite():
    """Return test suite for the oai repository."""


    return unittest.TestSuite((unittest.makeSuite(TestVerbs, 'test'),
                               unittest.makeSuite(TestErrorCodes, 'test'),
                               unittest.makeSuite(TestEncodings, 'test')))

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(create_test_suite())
