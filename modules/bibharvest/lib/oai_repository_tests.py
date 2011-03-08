# -*- coding: utf-8 -*-
## Invenio OAI repository unit tests.
##
## This file is part of Invenio.
## Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Unit tests for the oai repository."""

__revision__ = "$Id$"

import unittest
import re

from invenio import oai_repository_server
from invenio.testutils import make_test_suite, run_test_suite

class TestVerbs(unittest.TestCase):
    """Test for OAI verb functionality."""

    def test_verbs(self):
        """oairepository - testing verbs"""
        self.assertNotEqual(None, re.search("Identify", oai_repository_server.oaiidentify("", None)))
        self.assertNotEqual(None, re.search("ListIdentifiers", oai_repository_server.oailistidentifiers("")))
        self.assertNotEqual(None, re.search("ListRecords", oai_repository_server.oailistrecords("")))
        self.assertNotEqual(None, re.search("ListMetadataFormats", oai_repository_server.oailistmetadataformats("")))
        self.assertNotEqual(None, re.search("ListSets", oai_repository_server.oailistsets("")))
        self.assertNotEqual(None, re.search("GetRecord", oai_repository_server.oaigetrecord("")))


class TestErrorCodes(unittest.TestCase):
    """Test for handling OAI error codes."""

    def test_issue_error_identify(self):
        """oairepository - testing error codes"""

        self.assertNotEqual(None, re.search("badVerb", oai_repository_server.check_argd({'verb':"IllegalVerb"})))
        self.assertNotEqual(None, re.search("badArgument", oai_repository_server.check_argd({'verb':"Identify",
                                                                                      'test':"test"})))
        self.assertNotEqual(None, re.search("badArgument", oai_repository_server.check_argd({'verb':"ListIdentifiers",
                                                                                      'metadataPrefix':"oai_dc",
                                                                                      'from':"some_random_date",
                                                                                      'until':"some_random_date"})))
        self.assertNotEqual(None, re.search("badArgument", oai_repository_server.check_argd({'verb':"ListIdentifiers",
                                                                                      'metadataPrefix':"oai_dc",
                                                                                      'from':"2001-01-01",
                                                                                      'until':"2002-01-01T00:00:00Z"})))
        self.assertNotEqual(None, re.search("badArgument", oai_repository_server.check_argd({'verb':"ListIdentifiers"})))
        self.assertNotEqual(None, re.search("cannotDisseminateFormat", oai_repository_server.check_argd({'verb':"ListIdentifiers",
                                                                                                  'metadataPrefix':"illegal_mdp"})))

        self.assertNotEqual(None, re.search("badArgument", oai_repository_server.check_argd({'verb':"ListIdentifiers",
                                                                                      'metadataPrefix':"oai_dc",
                                                                                      'metadataPrefix':"oai_dc"})))
        self.assertNotEqual(None, re.search("badArgument", oai_repository_server.check_argd({'verb':"ListRecords",
                                                                                      'metadataPrefix':"oai_dc",
                                                                                      'set':"really_wrong_set",
                                                                                      'from':"some_random_date",
                                                                                      'until':"some_random_date"})))
        self.assertNotEqual(None, re.search("badArgument", oai_repository_server.check_argd({'verb':"ListRecords"})))

class TestEncodings(unittest.TestCase):
    """Test for OAI response encodings."""

    def test_encoding(self):
        """oairepository - testing encodings"""

        self.assertEqual("&lt;&amp;>", oai_repository_server.encode_for_xml("<&>"))
        self.assertEqual("%20", oai_repository_server.escape_space(" "))
        self.assertEqual("%25%20%3F%23%3D%26%2F%3A%3B%2B", oai_repository_server.encode_for_url("% ?#=&/:;+"))



TEST_SUITE = make_test_suite(TestVerbs,
                             TestErrorCodes,
                             TestEncodings,)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
