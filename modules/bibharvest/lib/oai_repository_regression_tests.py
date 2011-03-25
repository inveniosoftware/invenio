# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

"""OAI Repository Regression Test Suite."""

__revision__ = "$Id$"

import unittest
import time
import re

from invenio.config import CFG_SITE_URL, \
     CFG_OAI_SLEEP, \
     CFG_OAI_LOAD, \
     CFG_OAI_ID_FIELD
from invenio import oai_repository_server, search_engine, oai_repository_updater
from invenio.testutils import make_test_suite, run_test_suite, \
                              test_web_page_content, merge_error_messages

class OAIRepositoryWebPagesAvailabilityTest(unittest.TestCase):
    """Check OAI Repository web pages whether they are up or not."""

    def test_your_baskets_pages_availability(self):
        """oairepository - availability of OAI server pages"""

        baseurl = CFG_SITE_URL + '/oai2d'

        _exports = [#fast commands first:
                    '?verb=Identify',
                    '?verb=ListMetadataFormats',
                    # sleepy commands now:
                    '?verb=ListSets',
                    '?verb=ListRecords',
                    '?verb=GetRecord']

        error_messages = []
        for url in [baseurl + page for page in _exports]:
            if url.endswith('Identify') or \
               url.endswith('ListMetadataFormats'):
                pass
            else:
                # some sleep required for verbs other than Identify
                # and ListMetadataFormats, since oai2d refuses too
                # frequent access:
                time.sleep(CFG_OAI_SLEEP)
            error_messages.extend(test_web_page_content(url,
                                                        expected_text=
                                                        '</OAI-PMH>'))
        if error_messages:
            self.fail(merge_error_messages(error_messages))
        return

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


class TestOAIRepositoryUpdater(unittest.TestCase):
    """Test functions in OAI_repository_updater"""

    def test_marcxml_filtering(self):
        """oairepository - test MARCXML filtering"""
        self.assertEqual(oai_repository_updater.marcxml_filter_out_tags(98, ['088__a']),
                         '  <datafield tag="088" ind1=" " ind2=" ">\n    <subfield code="9">SCAN-9709037</subfield>\n  </datafield>\n')

        self.assertEqual(oai_repository_updater.marcxml_filter_out_tags(98, ['088__c']),
                         '  <datafield tag="088" ind1=" " ind2=" ">\n    <subfield code="9">SCAN-9709037</subfield>\n  </datafield>\n  <datafield tag="088" ind1=" " ind2=" ">\n    <subfield code="a">UCRL-8417</subfield>\n  </datafield>\n')

        self.assertEqual(oai_repository_updater.marcxml_filter_out_tags(98, ['0248_p']),
                         '  <datafield tag="024" ind1="8" ind2=" ">\n    <subfield code="a">oai:cds.cern.ch:SCAN-9709037</subfield>\n  </datafield>\n')

TEST_SUITE = make_test_suite(OAIRepositoryWebPagesAvailabilityTest,
                             TestSelectiveHarvesting,
                             TestPerformance,
                             TestOAIRepositoryUpdater)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)
