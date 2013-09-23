# This file is part of Invenio.
# Copyright (C) 2010, 2011, 2013 CERN.
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

from invenio.testutils import InvenioTestCase
from invenio.config import CFG_SOLR_URL, CFG_SITE_URL, CFG_SITE_NAME
from invenio.testutils import make_test_suite, \
                              run_test_suite, \
                              test_web_page_content, \
                              nottest
from invenio import intbitset
from invenio.solrutils_bibindex_searcher import solr_get_bitset
from invenio.solrutils_bibrank_searcher import solr_get_ranked, solr_get_similar_ranked
from invenio.solrutils_bibrank_indexer import solr_add, SOLR_CONNECTION
from invenio.search_engine import get_collection_reclist
from invenio.bibrank_bridge_utils import get_external_word_similarity_ranker, \
                                         get_logical_fields, \
                                         get_tags, \
                                         get_field_content_in_utf8


ROWS = 100


HITSETS = {
    'Willnotfind': intbitset.intbitset([]),
    'of': intbitset.intbitset([1, 2, 7, 8, 10]),
    '"of the"': intbitset.intbitset([1, 2, 7, 8, 10])
}


RECORDS = xrange(1, 11)


TAGS = {'abstract': ['520__%'],
        'author': ['100__a', '700__a'],
        'keyword': ['6531_a'],
        'title': ['245__%', '246__%']}


def init_Solr():
    _delete_all()
    _index_records()
    SOLR_CONNECTION.commit()


def _delete_all():
    SOLR_CONNECTION.delete_query('*:*')


def _index_records():
    for recid in RECORDS:
        fulltext = abstract = get_field_content_in_utf8(recid, 'abstract', TAGS)
        author   = get_field_content_in_utf8(recid, 'author', TAGS)
        keyword  = get_field_content_in_utf8(recid, 'keyword', TAGS)
        title    = get_field_content_in_utf8(recid, 'title', TAGS)
        solr_add(recid, abstract, author, fulltext, keyword, title)


class TestSolrSearch(InvenioTestCase):
    """Test for Solr search. Requires:
    make install-solrutils
    CFG_SOLR_URL set
    fulltext index in idxINDEX containing 'SOLR' in indexer column
    """
    def get_result(self, query, index='fulltext'):
        return solr_get_bitset(index, query)

    def setUp(self):
        init_Solr()

    @nottest
    def test_get_bitset(self):
        """solrutils - search results"""
        self.assertEqual(self.get_result('Willnotfind'), HITSETS['Willnotfind'])
        self.assertEqual(self.get_result('of'), HITSETS['of'])
        self.assertEqual(self.get_result('"of the"'), HITSETS['"of the"'])


class TestSolrRanking(InvenioTestCase):
    """Test for Solr ranking. Requires:
    make install-solrutils
    CFG_SOLR_URL set
    fulltext index in idxINDEX containing 'SOLR' in indexer column
    """
    def get_ranked_result_sequence(self, query, index='fulltext', rows=ROWS):
        ranked_result = solr_get_ranked('%s:%s' % (index, query),
                                        HITSETS[query],
                                        {'cutoff_amount': 10000,
                                         'cutoff_time_ms': 2000
                                        },
                                        rows)
        return tuple([pair[0] for pair in ranked_result[0]])

    def setUp(self):
        init_Solr()

    @nottest
    def test_get_ranked(self):
        """solrutils - ranking results"""
        self.assertEqual(self.get_ranked_result_sequence(query='Willnotfind'), tuple())
        self.assertEqual(self.get_ranked_result_sequence(query='of'), (8, 2, 1, 10, 7))
        self.assertEqual(self.get_ranked_result_sequence(query='"of the"'), (8, 10, 1, 2, 7))


class TestSolrSimilarToRecid(InvenioTestCase):
    """Test for Solr similar ranking. Requires:
    make install-solrutils
    CFG_SOLR_URL set
    fulltext index in idxINDEX containing 'SOLR' in indexer column
    WRD method referring to Solr: <invenio installation>/etc/bibrank$ cp template_word_similarity_solr.cfg wrd.cfg
    """
    def get_similar_result_sequence(self, recid, rows=ROWS):
        similar_result = solr_get_similar_ranked(recid,
                                                 self._all_records,
                                                 {'cutoff_amount': 10000,
                                                  'cutoff_time_ms': 2000,
                                                  'find_similar_to_recid': {
                                                    'more_results_factor': 5,
                                                    'mlt_fl': 'mlt',
                                                    'mlt_mintf': 0,
                                                    'mlt_mindf': 0,
                                                    'mlt_minwl': 0,
                                                    'mlt_maxwl': 0,
                                                    'mlt_maxqt': 25,
                                                    'mlt_maxntp': 1000,
                                                    'mlt_boost': 'false'
                                                    }
                                                  },
                                                 rows)
        return tuple([pair[0] for pair in similar_result[0]])[-rows:]

    _all_records = get_collection_reclist(CFG_SITE_NAME)

    def setUp(self):
        init_Solr()

    @nottest
    def test_get_similar_ranked(self):
        """solrutils - similar results"""
        self.assertEqual(self.get_similar_result_sequence(1), (5, 4, 7, 8, 3, 6, 2, 10, 1))
        self.assertEqual(self.get_similar_result_sequence(8), (3, 6, 9, 7, 2, 4, 5, 1, 10, 8))


class TestSolrWebSearch(InvenioTestCase):
    """Test for webbased Solr search. Requires:
    make install-solrutils
    CFG_SOLR_URL set
    fulltext index in idxINDEX containing 'SOLR' in indexer column
    """
    def setUp(self):
        init_Solr()

    @nottest
    def test_get_result(self):
        """solrutils - web search results"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=fulltext%3AWillnotfind&rg=100',
                                               expected_text='[]'))

        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=fulltext%3Aof&rg=100',
                                               expected_text='[1, 2, 7, 8, 10]'))

        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=fulltext%3A%22of+the%22&rg=100',
                                               expected_text='[1, 2, 7, 8, 10]'))


class TestSolrWebRanking(InvenioTestCase):
    """Test for webbased Solr ranking. Requires:
    make install-solrutils
    CFG_SOLR_URL set
    fulltext index in idxINDEX containing 'SOLR' in indexer column
    WRD method referring to Solr: <invenio installation>/etc/bibrank$ cp template_word_similarity_solr.cfg wrd.cfg
    """
    def setUp(self):
        init_Solr()

    @nottest
    def test_get_ranked(self):
        """solrutils - web ranking results"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=fulltext%3AWillnotfind&rg=100&rm=wrd',
                                               expected_text='[]'))

        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=fulltext%3Aof&rm=wrd',
                                               expected_text='[8, 2, 1, 10, 7]'))

        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=fulltext%3A%22of+the%22&rg=100&rm=wrd',
                                               expected_text='[8, 10, 1, 2, 7]'))


class TestSolrWebSimilarToRecid(InvenioTestCase):
    """Test for webbased Solr similar ranking. Requires:
    make install-solrutils
    CFG_SOLR_URL set
    fulltext index in idxINDEX containing 'SOLR' in indexer column
    WRD method referring to Solr: <invenio installation>/etc/bibrank$ cp template_word_similarity_solr.cfg wrd.cfg
    """
    def setUp(self):
        init_Solr()

    @nottest
    def test_get_similar_ranked(self):
        """solrutils - web similar results"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=recid%3A1&rm=wrd',
                                               expected_text='[9, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 107, 108, 109, 113, 5, 4, 7, 8, 3, 6, 2, 10, 1]'))

        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=recid%3A8&rg=100&rm=wrd',
                                               expected_text='[11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 107, 108, 109, 113, 3, 6, 9, 7, 2, 4, 5, 1, 10, 8]'))


class TestSolrLoadLogicalFieldSettings(InvenioTestCase):
    """Test for loading Solr logical field settings. Requires:
    make install-solrutils
    CFG_SOLR_URL set
    WRD method referring to Solr: <invenio installation>/etc/bibrank$ cp template_word_similarity_solr.cfg wrd.cfg
    """
    @nottest
    def test_load_logical_fields(self):
        """solrutils - load logical fields"""
        self.assertEqual({'abstract': ['abstract'], 'author': ['author'], 'title': ['title'], 'keyword': ['keyword']},
                         get_logical_fields())

    @nottest
    def test_load_tags(self):
        """solrutils - load tags"""
        self.assertEqual({'abstract': ['520__%'], 'author': ['100__a', '700__a'], 'title': ['245__%', '246__%'], 'keyword': ['6531_a']},
                         get_tags())


class TestSolrBuildFieldContent(InvenioTestCase):
    """Test for building Solr field content. Requires:
    make install-solrutils
    CFG_SOLR_URL set
    WRD method referring to Solr: <invenio installation>/etc/bibrank$ cp template_word_similarity_solr.cfg wrd.cfg
    """
    @nottest
    def test_build_default_field_content(self):
        """solrutils - build default field content"""
        tags = get_tags()

        self.assertEqual(u'Ellis, J Enqvist, K Nanopoulos, D V',
                         get_field_content_in_utf8(18, 'author', tags))

        self.assertEqual(u'Kahler manifolds gravitinos axions constraints noscale',
                         get_field_content_in_utf8(18, 'keyword', tags))

        self.assertEqual(u'In 1962, CERN hosted the 11th International Conference on High Energy Physics. Among the distinguished visitors were eight Nobel prizewinners.Left to right: Cecil F. Powell, Isidor I. Rabi, Werner Heisenberg, Edwin M. McMillan, Emile Segre, Tsung Dao Lee, Chen Ning Yang and Robert Hofstadter.',
                         get_field_content_in_utf8(6, 'abstract', tags))

    @nottest
    def test_build_custom_field_content(self):
        """solrutils - build custom field content"""
        tags = {'abstract': ['520__%', '590__%']}

        self.assertEqual(u"""In 1962, CERN hosted the 11th International Conference on High Energy Physics. Among the distinguished visitors were eight Nobel prizewinners.Left to right: Cecil F. Powell, Isidor I. Rabi, Werner Heisenberg, Edwin M. McMillan, Emile Segre, Tsung Dao Lee, Chen Ning Yang and Robert Hofstadter. En 1962, le CERN est l'hote de la onzieme Conference Internationale de Physique des Hautes Energies. Parmi les visiteurs eminents se trouvaient huit laureats du prix Nobel.De gauche a droite: Cecil F. Powell, Isidor I. Rabi, Werner Heisenberg, Edwin M. McMillan, Emile Segre, Tsung Dao Lee, Chen Ning Yang et Robert Hofstadter.""",
                         get_field_content_in_utf8(6, 'abstract', tags))

TESTS = []


if CFG_SOLR_URL:
    TESTS.extend((TestSolrSearch, TestSolrWebSearch))
    if get_external_word_similarity_ranker() == 'solr':
        TESTS.extend((TestSolrRanking,
                      TestSolrSimilarToRecid,
                      TestSolrWebRanking,
                      TestSolrWebSimilarToRecid,
                      TestSolrLoadLogicalFieldSettings,
                      TestSolrBuildFieldContent,
                      ))


TEST_SUITE = make_test_suite(*TESTS)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)
