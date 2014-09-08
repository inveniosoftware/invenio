# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013 CERN.
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

"""BibRank Regression Test Suite."""

__revision__ = "$Id$"

from invenio.testutils import InvenioTestCase

from invenio.config import CFG_SITE_URL, CFG_SITE_RECORD
from invenio.dbquery import run_sql
from invenio.testutils import make_test_suite, run_test_suite, \
                              test_web_page_content, merge_error_messages
from invenio.bibrank_bridge_utils import get_external_word_similarity_ranker

class BibRankWebPagesAvailabilityTest(InvenioTestCase):
    """Check BibRank web pages whether they are up or not."""

    def test_rank_by_word_similarity_pages_availability(self):
        """bibrank - availability of ranking search results pages"""

        baseurl = CFG_SITE_URL + '/search'

        _exports = ['?p=ellis&r=wrd']

        error_messages = []
        for url in [baseurl + page for page in _exports]:
            error_messages.extend(test_web_page_content(url))
        if error_messages:
            self.fail(merge_error_messages(error_messages))
        return

    def test_similar_records_pages_availability(self):
        """bibrank - availability of similar records results pages"""

        baseurl = CFG_SITE_URL + '/search'

        _exports = ['?p=recid%3A18&rm=wrd']

        error_messages = []
        for url in [baseurl + page for page in _exports]:
            error_messages.extend(test_web_page_content(url))
        if error_messages:
            self.fail(merge_error_messages(error_messages))
        return

class BibRankIntlMethodNames(InvenioTestCase):
    """Check BibRank I18N ranking method names."""

    def test_i18n_ranking_method_names(self):
        """bibrank - I18N ranking method names"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/collection/Articles%20%26%20Preprints?as=1',
                                               expected_text="times cited"))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/collection/Articles%20%26%20Preprints?as=1',
                                               expected_text="journal impact factor"))

class BibRankWordSimilarityRankingTest(InvenioTestCase):
    """Check BibRank word similarity ranking tools."""

    def test_search_results_ranked_by_similarity(self):
        """bibrank - search results ranked by word similarity"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=ellis&rm=wrd&of=id&rg=0',
                                               expected_text="[15, 18, 14, 9, 16, 13, 47, 17, 12, 11, 10, 8]"))

    def test_similar_records_link(self):
        """bibrank - 'Similar records' link"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=recid%3A77&rm=wrd&of=id',
                                               expected_text="[77, 85, 95, 96]"))

class BibRankCitationRankingTest(InvenioTestCase):
    """Check BibRank citation ranking tools."""

    def test_search_results_ranked_by_citations(self):
        """bibrank - search results ranked by number of citations"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?cc=Articles+%26+Preprints&p=Klebanov&rm=citation&of=id',
                                               username="admin",
                                               expected_text="[84, 77, 85]"))

    def test_search_results_ranked_by_citations_verbose(self):
        """bibrank - search results ranked by number of citations, verbose output"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?cc=Articles+%26+Preprints&p=Klebanov&rm=citation&verbose=2',
                                               username="admin",
                                               expected_text="rank_by_citations ret [[85, 0], [77, 2L], [84, 3L]]"))

    def test_detailed_record_citations_tab(self):
        """bibrank - detailed record, citations tab"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/'+ CFG_SITE_RECORD +'/79/citations',
                                               expected_text=["Cited by: 1 records",
                                                              "Co-cited with: 2 records"]))

class BibRankExtCitesTest(InvenioTestCase):
    """Check BibRank citation ranking tools with respect to the external cites."""

    def _detect_extcite_info(self, extcitepubinfo):
        """
        Helper function to return list of recIDs citing given
        extcitepubinfo.  Could be move to the business logic, if
        interesting for other callers.
        """
        res = run_sql("""SELECT id_bibrec FROM rnkCITATIONDATAEXT
                          WHERE extcitepubinfo=%s""",
                      (extcitepubinfo,))
        return [int(x[0]) for x in res]

    def test_extcite_via_report_number(self):
        """bibrank - external cites, via report number"""
        # The external paper hep-th/0112258 is cited by 9 demo
        # records: you can find out via 999:"hep-th/0112258", and we
        # could eventually automatize this query, but it is maybe
        # safer to leave it manual in case queries fail for some
        # reason.
        test_case_repno = "hep-th/0112258"
        test_case_repno_cited_by = [77, 78, 81, 82, 85, 86, 88, 90, 91]
        self.assertEqual(self._detect_extcite_info(test_case_repno),
                         test_case_repno_cited_by)

    def test_extcite_via_publication_reference(self):
        """bibrank - external cites, via publication reference"""
        # The external paper "J. Math. Phys. 4 (1963) 915" does not
        # have any report number, and is cited by 1 demo record.
        test_case_pubinfo = "J. Math. Phys. 4 (1963) 915"
        test_case_pubinfo_cited_by = [90]
        self.assertEqual(self._detect_extcite_info(test_case_pubinfo),
                         test_case_pubinfo_cited_by)

    def test_intcite_via_report_number(self):
        """bibrank - external cites, no internal papers via report number"""
        # The internal paper hep-th/9809057 is cited by 2 demo
        # records, but it also exists as a demo record, so it should
        # not be found in the extcite table.
        test_case_repno = "hep-th/9809057"
        test_case_repno_cited_by = []
        self.assertEqual(self._detect_extcite_info(test_case_repno),
                         test_case_repno_cited_by)

    def test_intcite_via_publication_reference(self):
        """bibrank - external cites, no internal papers via publication reference"""
        # The internal paper #18 has only pubinfo, no repno, and is
        # cited by internal paper #96 via its pubinfo, so should not
        # be present in the extcite list:
        test_case_repno = "Phys. Lett., B 151 (1985) 357"
        test_case_repno_cited_by = []
        self.assertEqual(self._detect_extcite_info(test_case_repno),
                         test_case_repno_cited_by)


TESTS = [BibRankWebPagesAvailabilityTest,
         BibRankIntlMethodNames,
         BibRankCitationRankingTest,
         BibRankExtCitesTest]


if not get_external_word_similarity_ranker():
    TESTS.append(BibRankWordSimilarityRankingTest)


TEST_SUITE = make_test_suite(*TESTS)


if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)
