# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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

"""BibRank Regression Test Suite."""

__revision__ = "$Id$"

import unittest

from invenio.config import weburl
from invenio.testutils import make_test_suite, warn_user_about_tests_and_run, \
                              test_web_page_content, merge_error_messages

class BibRankWebPagesAvailabilityTest(unittest.TestCase):
    """Check BibRank web pages whether they are up or not."""

    def test_rank_by_word_similarity_pages_availability(self):
        """bibrank - availability of ranking search results pages"""

        baseurl = weburl + '/search'

        _exports = ['?p=ellis&r=wrd']

        error_messages = []
        for url in [baseurl + page for page in _exports]:
            error_messages.extend(test_web_page_content(url))
        if error_messages:
            self.fail(merge_error_messages(error_messages))
        return

    def test_similar_records_pages_availability(self):
        """bibrank - availability of similar records results pages"""

        baseurl = weburl + '/search'

        _exports = ['?p=recid%3A18&rm=wrd']

        error_messages = []
        for url in [baseurl + page for page in _exports]:
            error_messages.extend(test_web_page_content(url))
        if error_messages:
            self.fail(merge_error_messages(error_messages))
        return

class BibRankWordSimilarityRankingTest(unittest.TestCase):
    """Check BibRank word similarity ranking tools."""

    def test_search_results_ranked_by_citations(self):
        """bibrank - search results ranked by word similarity"""
	self.assertEqual([],
                         test_web_page_content(weburl + '/search?p=ellis&rm=wrd&of=id',
                                               expected_text="[10, 8, 11, 12, 13, 15, 17, 47, 16, 18, 9, 14]"))

    def test_similar_records_link(self):
        """bibrank - 'Similar records' link"""
	self.assertEqual([],
                         test_web_page_content(weburl + '/search?p=recid%3A5&rm=wrd&of=id',
                                               expected_text="[86, 5]"))

class BibRankCitationRankingTest(unittest.TestCase):
    """Check BibRank citation ranking tools."""

    def test_search_results_ranked_by_citations(self):
        """bibrank - search results ranked by number of citations"""
	self.assertEqual([],
                         test_web_page_content(weburl + '/search?cc=Articles+%26+Preprints&p=Klebanov&rm=citation&of=id',
                                               expected_text="[85, 77, 84]"))

    def test_search_results_ranked_by_citations_verbose(self):
        """bibrank - search results ranked by number of citations, verbose output"""
	self.assertEqual([],
                         test_web_page_content(weburl + '/search?cc=Articles+%26+Preprints&p=Klebanov&rm=citation&verbose=2',
                                               expected_text="find_citations retlist [[85, 0], [77, 2], [84, 3]]"))

test_suite = make_test_suite(BibRankWebPagesAvailabilityTest,
                             BibRankWordSimilarityRankingTest,
                             BibRankCitationRankingTest)

if __name__ == "__main__":
    warn_user_about_tests_and_run(test_suite)
