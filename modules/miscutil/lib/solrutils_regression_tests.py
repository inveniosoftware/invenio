## This file is part of Invenio.
## Copyright (C) 2010, 2011, 2013 CERN.
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

import unittest
from invenio.config import CFG_SOLR_URL, CFG_SITE_URL
from invenio.testutils import make_test_suite, \
                              run_test_suite, \
                              test_web_page_content
from invenio.bibrank_bridge_utils import get_external_word_similarity_ranker


class TestSolrWebSearch(unittest.TestCase):
    """Test for webbased Solr search. Requires:
    make install-solrutils
    CFG_SOLR_URL set
    fulltext index in idxINDEX containing 'SOLR' in indexer column
    AND EITHER
      Solr index built: ./bibindex -w fulltext for all records
     OR
      WRD method referring to Solr: <invenio installation>/etc/bibrank$ cp template_word_similarity_solr.cfg wrd.cfg
      and ./bibrank -w wrd for all records
    """

    def test_get_result(self):
        """solrutils - web search results"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=fulltext%3AWillnotfind&rg=100',
                                               expected_text="[]"))

        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=fulltext%3Ahiggs&rg=100',
                                               expected_text="[47, 48, 51, 52, 55, 56, 58, 68, 79, 85, 89, 96]"))

        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=fulltext%3Aof&rg=100',
                                               expected_text="[8, 10, 11, 12, 15, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 64, 68, 74, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97]"))

        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=fulltext%3A%22higgs+boson%22&rg=100',
                                               expected_text="[55, 56]"))


class TestSolrWebRanking(unittest.TestCase):
    """Test for webbased Solr ranking. Requires:
    make install-solrutils
    CFG_SOLR_URL set
    fulltext index in idxINDEX containing 'SOLR' in indexer column
    AND EITHER
      Solr index built: ./bibindex -w fulltext for all records
     OR
      WRD method referring to Solr: <invenio installation>/etc/bibrank$ cp template_word_similarity_solr.cfg wrd.cfg
      and ./bibrank -w wrd for all records
    """

    def test_get_ranked(self):
        """solrutils - web ranking results"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=fulltext%3AWillnotfind&rg=100&rm=wrd',
                                               expected_text="[]"))

        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=fulltext%3Ahiggs&rm=wrd',
                                               expected_text="[51, 79, 55, 47, 56, 96, 58, 68, 52, 48, 89, 85]"))

        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=fulltext%3Ahiggs&rg=100&rm=wrd',
                                               expected_text="[79, 51, 55, 47, 56, 96, 58, 68, 52, 48, 89, 85]"))

        # Record 77 is restricted
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=fulltext%3Aof&rm=wrd',
                                               expected_text="[8, 10, 15, 43, 44, 45, 46, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 60, 61, 62, 64, 68, 74, 78, 79, 81, 82, 83, 84, 85, 88, 89, 90, 91, 92, 95, 96, 97, 86, 11, 80, 93, 77, 12, 59, 87, 47, 94]",
                                               username='admin'))

        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=fulltext%3Aof&rg=100&rm=wrd',
                                               expected_text="[50, 61, 60, 54, 56, 53, 10, 68, 44, 57, 83, 95, 92, 91, 74, 45, 48, 62, 82, 49, 51, 89, 90, 96, 43, 8, 64, 97, 15, 85, 78, 46, 55, 79, 84, 88, 81, 52, 58, 86, 11, 80, 93, 77, 12, 59, 87, 47, 94]",
                                               username='admin'))

        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=fulltext%3A%22higgs+boson%22&rg=100&rm=wrd',
                                               expected_text="[55, 56]"))


class TestSolrWebSimilarToRecid(unittest.TestCase):
    """Test for webbased Solr similar ranking. Requires:
    make install-solrutils
    CFG_SOLR_URL set
    fulltext index in idxINDEX containing 'SOLR' in indexer column
    WRD method referring to Solr: <invenio installation>/etc/bibrank$ cp template_word_similarity_solr.cfg wrd.cfg
    ./bibrank -w wrd for all records
    """

    def test_get_similar_ranked(self):
        """solrutils - web similar results"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=recid%3A30&rm=wrd',
                                               expected_text="[1, 3, 4, 8, 9, 12, 13, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 31, 34, 43, 44, 49, 50, 56, 58, 61, 64, 66, 67, 69, 71, 73, 75, 76, 77, 78, 82, 85, 86, 87, 89, 90, 95, 96, 98, 104, 107, 109, 113, 65, 62, 60, 47, 46, 100, 99, 102, 91, 80, 7, 92, 88, 74, 57, 55, 108, 84, 81, 79, 54, 101, 11, 103, 94, 48, 83, 72, 63, 2, 68, 51, 5, 53, 97, 93, 70, 45, 52, 14, 59, 6, 10, 32, 33, 29, 30]"))

        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=recid%3A30&rg=100&rm=wrd',
                                               expected_text="[3, 4, 8, 9, 13, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 31, 34, 43, 49, 56, 66, 67, 69, 71, 73, 75, 76, 87, 90, 98, 104, 107, 109, 113, 12, 95, 85, 82, 44, 1, 89, 64, 58, 15, 96, 61, 50, 86, 78, 77, 65, 62, 60, 47, 46, 100, 99, 102, 91, 80, 7, 92, 88, 74, 57, 55, 108, 84, 81, 79, 54, 101, 11, 103, 94, 48, 83, 72, 63, 2, 68, 51, 5, 53, 97, 93, 70, 45, 52, 14, 59, 6, 10, 32, 33, 29, 30]"))


TESTS = []


if CFG_SOLR_URL:
    TESTS.append(TestSolrWebSearch)
    if get_external_word_similarity_ranker() == 'solr':
        TESTS.extend((TestSolrWebRanking, TestSolrWebSimilarToRecid))


TEST_SUITE = make_test_suite(*TESTS)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)
