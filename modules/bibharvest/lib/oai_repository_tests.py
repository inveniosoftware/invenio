# -*- coding: utf-8 -*-
## Invenio OAI repository unit tests.
##
## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 CERN.
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
import time

from invenio import oai_repository_server, search_engine
from invenio.testutils import make_test_suite, run_test_suite

from invenio.config import \
     CFG_OAI_LOAD, \
     CFG_OAI_ID_FIELD

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

class TestSelectiveHarvesting(unittest.TestCase):
    """Test set, from and until parameters used to do selective harvesting."""

    def test_set(self):
        """oairepository - testing selective harvesting with 'set' parameter"""
        self.assertNotEqual([], oai_repository_server.oaigetsysnolist(set="cern:experiment"))
        self.assert_("Multifractal analysis of minimum bias events" in \
                     ''.join([oai_repository_server.print_record(recID) for recID in \
                              oai_repository_server.oaigetsysnolist(set="cern:experiment")]))
        self.assert_("Multifractal analysis of minimum bias events" not in \
                     ''.join([oai_repository_server.print_record(recID) for recID in \
                              oai_repository_server.oaigetsysnolist(set="cern:theory")]))
        self.assertEqual([], oai_repository_server.oaigetsysnolist(set="nonExistingSet"))

    def test_from_and_until(self):
        """oairepository - testing selective harvesting with 'from' and 'until' parameters"""

        # List available records, get datestamps and play with them
        identifiers = oai_repository_server.oailistidentifiers("")
        datestamps = re.findall('<identifier>(?P<id>.*)</identifier>\s*<datestamp>(?P<date>.*)</datestamp>', identifiers)

        sample_datestamp = datestamps[0][1] # Take one datestamp
        sample_oai_id = datestamps[0][0] # Take corresponding oai id
        sample_id = search_engine.perform_request_search(p=sample_oai_id,
                                                         f=CFG_OAI_ID_FIELD)[0] # Find corresponding system number id

        # There must be some datestamps
        self.assertNotEqual([], datestamps)

        # We must be able to retrieve an id with the date we have just found
        self.assert_(sample_id in oai_repository_server.oaigetsysnolist(fromdate=sample_datestamp))
        self.assert_(sample_id in oai_repository_server.oaigetsysnolist(untildate=sample_datestamp))
        self.assert_(sample_id in oai_repository_server.oaigetsysnolist(untildate=sample_datestamp, \
                                                                 fromdate=sample_datestamp))

        # Same, with short format date. Eg 2007-12-13
        self.assert_(sample_id in oai_repository_server.oaigetsysnolist(fromdate=sample_datestamp.split('T')[0]))
        self.assert_(sample_id in oai_repository_server.oaigetsysnolist(untildate=sample_datestamp.split('T')[0]))
        self.assert_(sample_id in oai_repository_server.oaigetsysnolist(fromdate=sample_datestamp.split('T')[0], \
                                                                 untildate=sample_datestamp.split('T')[0]))

        # At later date (year after) we should not find our id again
        sample_datestamp_year = int(sample_datestamp[0:4])
        sample_datestamp_rest = sample_datestamp[4:]
        later_datestamp = str(sample_datestamp_year + 1) + sample_datestamp_rest
        self.assert_(sample_id not in oai_repository_server.oaigetsysnolist(fromdate=later_datestamp))

        # At earlier date (year before) we should not find our id again
        earlier_datestamp = str(sample_datestamp_year - 1) + sample_datestamp_rest
        self.assert_(sample_id not in oai_repository_server.oaigetsysnolist(untildate=earlier_datestamp))

        # From earliest date to latest date must include all oai records
        dates = [(time.mktime(time.strptime(date[1], "%Y-%m-%dT%H:%M:%SZ")), date[1]) for date in datestamps]
        dates = dict(dates)
        sorted_times = dates.keys()
        sorted_times.sort()
        earliest_datestamp = dates[sorted_times[0]]
        latest_datestamp = dates[sorted_times[-1]]
        self.assertEqual(len(oai_repository_server.oaigetsysnolist()), \
                         len(oai_repository_server.oaigetsysnolist(fromdate=earliest_datestamp, \
                                                            untildate=latest_datestamp)))

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

class TestPerformance(unittest.TestCase):
    """Test performance of the repository """

    def setUp(self):
        """Setting up some variables"""
        # Determine how many records are served
        self.number_of_records = oai_repository_server.oaigetsysnolist("", "", "")
        if CFG_OAI_LOAD < self.number_of_records:
            self.number_of_records = CFG_OAI_LOAD

    def test_response_speed_oai(self):
        """oairepository - speed of response for oai_dc output"""
        allowed_seconds_per_record_oai = 0.02

        # Test oai ListRecords performance
        t0 = time.time()
        oai_repository_server.oailistrecords('metadataPrefix=oai_dc&verb=ListRecords')
        t = time.time() - t0
        if t > self.number_of_records * allowed_seconds_per_record_oai:
            self.fail("""Response for ListRecords with metadataPrefix=oai_dc took too much time:
%s seconds.
Limit: %s seconds""" % (t, self.number_of_records * allowed_seconds_per_record_oai))

    def test_response_speed_marcxml(self):
        """oairepository - speed of response for marcxml output"""
        allowed_seconds_per_record_marcxml = 0.05

        # Test marcxml ListRecords performance
        t0 = time.time()
        oai_repository_server.oailistrecords('metadataPrefix=marcxml&verb=ListRecords')
        t = time.time() - t0
        if t > self.number_of_records * allowed_seconds_per_record_marcxml:
            self.fail("""Response for ListRecords with metadataPrefix=marcxml took too much time:\n
%s seconds.
Limit: %s seconds""" % (t, self.number_of_records * allowed_seconds_per_record_marcxml))

TEST_SUITE = make_test_suite(TestVerbs,
                             TestErrorCodes,
                             TestEncodings,
                             TestSelectiveHarvesting,
                             TestPerformance,)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
