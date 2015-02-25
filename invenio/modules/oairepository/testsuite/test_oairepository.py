# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2013, 2015 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Unit tests for the OAI-PMH repository."""

import re
from xml.etree import ElementTree as ET
from six import StringIO

from invenio.base.wrappers import lazy_import
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase

oai_repository_server = lazy_import('invenio.legacy.oairepository.server')


class TestVerbs(InvenioTestCase):
    """Test for OAI verb functionality."""

    def test_verbs(self):
        """oairepository - testing verbs"""
        self.assertNotEqual(None, re.search("Identify", oai_repository_server.oai_identify({'verb': 'Identify'})))
        ret = StringIO()
        oai_repository_server.oai_list_records_or_identifiers(ret, {'verb': 'ListIdentifiers', 'metadataPrefix': 'marcxml'})
        self.assertNotEqual(None, re.search("ListIdentifiers", ret.getvalue()))
        ret = StringIO()
        oai_repository_server.oai_list_records_or_identifiers(ret, {'verb': 'ListRecords', 'metadataPrefix': 'marcxml'})
        self.assertNotEqual(None, re.search("ListRecords", ret.getvalue()))
        self.assertNotEqual(None, re.search("ListMetadataFormats", oai_repository_server.oai_list_metadata_formats({'verb': 'ListMetadataFormats'})))
        self.assertNotEqual(None, re.search("ListSets", oai_repository_server.oai_list_sets({'verb': 'ListSets'})))
        self.assertNotEqual(None, re.search("GetRecord", oai_repository_server.oai_get_record({'identifier': 'oai:atlantis.cern.ch:1', 'verb': 'GetRecord'})))

    def test_metadataprefix_namespace(self):
        """Test for schema and namespaces."""
        elem = ET.fromstring(
            oai_repository_server.oai_list_metadata_formats(
                {'verb': 'ListMetadataFormats'}
            )).find(
                '{http://www.openarchives.org/OAI/2.0/}ListMetadataFormats'
            )

        formats = dict()
        for n in elem:
            ns = n.find(
                '{http://www.openarchives.org/OAI/2.0/}metadataNamespace').text
            prefix = n.find(
                '{http://www.openarchives.org/OAI/2.0/}metadataPrefix').text
            schema = n.find(
                '{http://www.openarchives.org/OAI/2.0/}schema').text
            formats[prefix] = (ns, schema)

        assert 'oai_dc' in formats
        self.assertEqual(
            formats['oai_dc'][0], 'http://purl.org/dc/elements/1.1/'
        )
        self.assertEqual(
            formats['oai_dc'][1], 'http://www.openarchives.org/OAI/1.1/dc.xsd'
        )
        assert 'marcxml' in formats
        self.assertEqual(
            formats['marcxml'][0], 'http://www.loc.gov/MARC21/slim'
        )
        self.assertEqual(
            formats['marcxml'][1],
            'http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd'
        )


class TestErrorCodes(InvenioTestCase):
    """Test for handling OAI error codes."""

    def test_issue_error_identify(self):
        """oairepository - testing error codes"""

        self.assertNotEqual([], [code for (code, dummy_text) in oai_repository_server.check_argd({'verb':"IllegalVerb"}) if code == 'badVerb'])
        self.assertNotEqual([], [code for (code, dummy_text) in oai_repository_server.check_argd({'verb':"Identify",
                                                                                      'test':"test"}) if code == 'badArgument'])
        self.assertNotEqual([], [code for (code, dummy_text) in oai_repository_server.check_argd({'verb':"ListIdentifiers",
                                                                                      'metadataPrefix':"oai_dc",
                                                                                      'from':"some_random_date",
                                                                                      'until':"some_random_date"}) if code == 'badArgument'])
        self.assertNotEqual([], [code for (code, dummy_text) in oai_repository_server.check_argd({'verb':"ListIdentifiers",
                                                                                      'metadataPrefix':"oai_dc",
                                                                                      'from':"2001-01-01",
                                                                                      'until':"2002-01-01T00:00:00Z"}) if code == 'badArgument'])
        self.assertNotEqual([], [code for (code, dummy_text) in oai_repository_server.check_argd({'verb':"ListIdentifiers"}) if code == 'badArgument'])
        self.assertNotEqual([], [code for (code, dummy_text) in oai_repository_server.check_argd({'verb':"ListIdentifiers",
                                                                                                  'metadataPrefix':"illegal_mdp"}) if code == 'cannotDisseminateFormat'])

        self.assertNotEqual([], [code for (code, dummy_text) in oai_repository_server.check_argd({'verb':"ListIdentifiers",
                                                                                      'metadataPrefix':"oai_dc",
                                                                                      'metadataPrefix':"oai_dc"}) if code == 'badArgument'])
        self.assertNotEqual([], [code for (code, dummy_text) in oai_repository_server.check_argd({'verb':"ListRecords",
                                                                                      'metadataPrefix':"oai_dc",
                                                                                      'set':"really_wrong_set",
                                                                                      'from':"some_random_date",
                                                                                      'until':"some_random_date"}) if code == 'badArgument'])
        self.assertNotEqual([], [code for (code, dummy_text) in oai_repository_server.check_argd({'verb':"ListRecords"}) if code == 'badArgument'])

        self.assertNotEqual([], [code for (code, dummy_text) in oai_repository_server.check_argd({'verb': 'ListRecords', 'resumptionToken': ''}) if code == 'badResumptionToken'])

TEST_SUITE = make_test_suite(TestVerbs,
                             TestErrorCodes)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
