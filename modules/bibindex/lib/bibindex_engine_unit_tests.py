# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011, 2014 CERN.
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

"""Unit tests for the indexing engine."""

__revision__ = \
    "$Id$"

from invenio.testutils import InvenioTestCase

from invenio import bibindex_engine
from invenio.bibindex_engine_utils import load_tokenizers, list_union
from invenio.testutils import make_test_suite, run_test_suite
from invenio.bibindex_engine_utils import get_values_recursively

_TOKENIZERS = load_tokenizers()


class TestListSetOperations(InvenioTestCase):

    """Tests for list set operations."""

    def test_list_union(self):
        """bibindex engine utils - list union"""
        self.assertEqual([1, 2, 3, 4],
                         list_union([1, 2, 3],
                                    [1, 3, 4]))

    def test_list_unique(self):
        """bibindex engine - list unique"""
        self.assertEqual([1, 2, 3],
                         bibindex_engine.list_unique([1, 2, 3, 3, 1, 2]))


class TestWashIndexTerm(InvenioTestCase):

    """Tests for washing index terms, useful for both searching and indexing."""

    def test_wash_index_term_short(self):
        """bibindex engine - wash index term, short word"""
        self.assertEqual("ellis",
                         bibindex_engine.wash_index_term("ellis"))

    def test_wash_index_term_long(self):
        """bibindex engine - wash index term, long word"""
        self.assertEqual(50 * "e",
                         bibindex_engine.wash_index_term(1234 * "e"))

    def test_wash_index_term_case(self):
        """bibindex engine - wash index term, lower the case"""
        self.assertEqual("ellis",
                         bibindex_engine.wash_index_term("Ellis"))

    def test_wash_index_term_unicode(self):
        """bibindex engine - wash index term, unicode"""
        self.assertEqual("ελληνικό αλφάβητο",
                         bibindex_engine.wash_index_term("Ελληνικό αλφάβητο"))


class TestGetWordsFromPhrase(InvenioTestCase):

    """Tests for getting words from phrase."""

    def test_easy_phrase(self):
        """bibindex engine - getting words from `word1 word2' phrase"""
        test_phrase = 'word1 word2'
        l_words_expected = ['word1', 'word2']
        tokenizer = _TOKENIZERS["BibIndexDefaultTokenizer"]()
        l_words_obtained = tokenizer.tokenize_for_words(test_phrase)
        l_words_obtained.sort()
        self.assertEqual(l_words_obtained, l_words_expected)

    def test_stemming_phrase(self):
        """bibindex engine - getting stemmed words from l'anthropologie"""
        test_phrase = "l'anthropologie"
        l_words_not_expected = [
            'anthropolog', 'l', "l'anthropolog", "l'anthropologi"]
        l_words_expected = ['anthropologi', 'l', "l'anthropologi"]
        tokenizer = _TOKENIZERS["BibIndexDefaultTokenizer"]('en')
        l_words_obtained = tokenizer.tokenize_for_words(test_phrase)
        l_words_obtained.sort()
        self.assertNotEqual(l_words_obtained, l_words_not_expected)
        self.assertEqual(l_words_obtained, l_words_expected)

    def test_remove_stopwords_phrase(self):
        """bibindex engine - test for removing stopwords from 'theory of' """
        test_phrase = 'theory of'
        tokenizer = _TOKENIZERS["BibIndexDefaultTokenizer"](
            remove_stopwords='stopwords.kb')
        words_obtained = tokenizer.tokenize_for_words(test_phrase)
        words_expected = ['theory']
        self.assertEqual(words_expected, words_obtained)

    def test_stemming_and_remove_stopwords_phrase(self):
        """bibindex engine - test for removing stopwords and stemming from 'beams of photons' """
        test_phrase = 'beams of photons'
        tokenizer = _TOKENIZERS["BibIndexDefaultTokenizer"](
            'en', remove_stopwords='stopwords.kb')
        words_obtained = tokenizer.tokenize_for_words(test_phrase)
        words_expected = ['beam', 'photon']
        self.assertEqual(words_expected, words_obtained)

    def test_dashed_phrase(self):
        """bibindex engine - getting words from `word1-word2' phrase"""
        test_phrase = 'word1-word2'
        l_words_expected = ['word1', 'word1-word2', 'word2']
        tokenizer = _TOKENIZERS["BibIndexDefaultTokenizer"]()
        l_words_obtained = tokenizer.tokenize_for_words(test_phrase)
        l_words_obtained.sort()
        self.assertEqual(l_words_obtained, l_words_expected)

    def test_arXiv_good(self):
        """bibindex engine - getting words from `arXiv:1007.5048' phrase"""
        test_phrase = 'arXiv:1007.5048'
        l_words_expected = [
            '1007', '1007.5048', '5048', 'arxiv', 'arxiv:1007.5048']
        tokenizer = _TOKENIZERS["BibIndexDefaultTokenizer"]()
        l_words_obtained = tokenizer.tokenize_for_words(test_phrase)
        l_words_obtained.sort()
        self.assertEqual(l_words_obtained, l_words_expected)

    def test_arXiv_bad(self):
        """bibindex engine - getting words from `arXiv:1xy7.5z48' phrase"""
        test_phrase = 'arXiv:1xy7.5z48'
        l_words_expected = ['1xy7', '5z48', 'arxiv', 'arxiv:1xy7.5z48']
        tokenizer = _TOKENIZERS["BibIndexDefaultTokenizer"]()
        l_words_obtained = tokenizer.tokenize_for_words(test_phrase)
        l_words_obtained.sort()
        self.assertEqual(l_words_obtained, l_words_expected)


class TestGetPairsFromPhrase(InvenioTestCase):

    """Tests for getting pairs from phrase."""

    def test_remove_stopwords_phrase_first(self):
        """bibindex engine - getting pairs from phrase with stopwords removed first"""
        test_phrase = 'Matrices on a point as the theory of everything'
        tokenizer = _TOKENIZERS["BibIndexDefaultTokenizer"](
            remove_stopwords='stopwords.kb')
        pairs_obtained = tokenizer.tokenize_for_pairs(test_phrase)
        pairs_expected = ['matrices theory']
        self.assertEqual(pairs_expected, pairs_obtained)

    def test_remove_stopwords_phrase_second(self):
        """bibindex engine - getting pairs from phrase with stopwords removed second"""
        test_phrase = 'Nonlocal action for long-distance'
        tokenizer = _TOKENIZERS["BibIndexDefaultTokenizer"](
            remove_stopwords='stopwords.kb')
        pairs_obtained = tokenizer.tokenize_for_pairs(test_phrase)
        pairs_expected = ['nonlocal action', 'long distance', 'action long']
        self.assertEqual(pairs_expected, pairs_obtained)


class TestGetWordsFromDateTag(InvenioTestCase):

    """Tests for getting words for date-like tag."""

    def test_dateindex_yyyy(self):
        """bibindex engine - index date-like tag, yyyy"""
        tokenizer = _TOKENIZERS["BibIndexYearTokenizer"]()
        self.assertEqual(["2010"],
                         tokenizer.get_words_from_date_tag("2010"))

    def test_dateindex_yyyy_mm(self):
        """bibindex engine - index date-like tag, yyyy-mm"""
        tokenizer = _TOKENIZERS["BibIndexYearTokenizer"]()
        self.assertEqual(["2010-03", "2010"],
                         tokenizer.get_words_from_date_tag("2010-03"))

    def test_dateindex_yyyy_mm_dd(self):
        """bibindex engine - index date-like tag, yyyy-mm-dd"""
        tokenizer = _TOKENIZERS["BibIndexYearTokenizer"]()
        self.assertEqual(["2010-03-08", "2010", "2010-03", ],
                         tokenizer.get_words_from_date_tag("2010-03-08"))

    def test_dateindex_freetext(self):
        """bibindex engine - index date-like tag, yyyy-mm-dd"""
        tokenizer = _TOKENIZERS["BibIndexYearTokenizer"]()
        self.assertEqual(["dd", "mon", "yyyy"],
                         tokenizer.get_words_from_date_tag("dd mon yyyy"))


class TestGetAuthorFamilyNameWords(InvenioTestCase):

    """Tests for getting family name words from author names."""

    def test_authornames_john_doe(self):
        """bibindex engine - get author family name words for John Doe"""
        tokenizer = _TOKENIZERS["BibIndexAuthorTokenizer"]()
        self.assertEqual(['doe', ],
                         tokenizer.get_author_family_name_words_from_phrase('John Doe'))

    def test_authornames_doe_john(self):
        """bibindex engine - get author family name words for Doe, John"""
        tokenizer = _TOKENIZERS["BibIndexAuthorTokenizer"]()
        self.assertEqual(['doe', ],
                         tokenizer.get_author_family_name_words_from_phrase('Doe, John'))

    def test_authornames_campbell_wilson(self):
        """bibindex engine - get author family name words for Campbell-Wilson, D"""
        tokenizer = _TOKENIZERS["BibIndexAuthorTokenizer"]()
        self.assertEqual(['campbell', 'wilson', 'campbell-wilson'],
                         tokenizer.get_author_family_name_words_from_phrase('Campbell-Wilson, D'))


class TestGetValuesFromRecjson(InvenioTestCase):

    """Tests for get_values_recursively function which finds values for tokenization
       in recjson record"""

    @classmethod
    def setUp(self):
        self.dict1 = {
            'all': {
                'vehicles': {
                    'cars': {
                        'car1': ('flat tyre', 'windscreen'),
                        'car2': ('engine',)
                    },
                    'planes': ['Airplane', 'x,y - plane'],
                    'ufo': {}
                },
                'people': ['Frank', 'Theodor', 'Richard'],
                'vikings': ['Odin', 'Eric'],
            }
        }
        self.dict2 = {
            'all': {'name': ([(['name1', 'name2', {'name3': 'name4'}], )], )}}

    def test_dict1_all_fields(self):
        """bibindex termcollectors - get_field_values - complicated field"""
        fields = self.dict1
        phrases = []
        get_values_recursively(fields['all'], phrases)
        self.assertEqual(
            phrases, [
                'engine', 'flat tyre', 'windscreen', 'Airplane', 'x,y - plane',
                'Odin', 'Eric', 'Frank', 'Theodor', 'Richard'
            ]
        )

    def test_dict1_subfield(self):
        """bibindex termcollectors - get_field_values - simple field"""
        fields = self.dict1
        phrases = []
        get_values_recursively(fields['all']['people'], phrases)
        self.assertEqual(phrases, ['Frank', 'Theodor', 'Richard'])

    def test_dict2_all_fields(self):
        """bibindex termcollectors - get_field_values - nested field"""
        fields = self.dict2
        phrases = []
        get_values_recursively(fields['all'], phrases)
        self.assertEqual(phrases, ['name1', 'name2', 'name4'])


TEST_SUITE = make_test_suite(TestListSetOperations,
                             TestWashIndexTerm,
                             TestGetWordsFromPhrase,
                             TestGetPairsFromPhrase,
                             TestGetWordsFromDateTag,
                             TestGetAuthorFamilyNameWords,
                             TestGetValuesFromRecjson,)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
