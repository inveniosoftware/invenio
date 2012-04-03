# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

"""Unit tests for the search engine."""

__revision__ = \
    "$Id$"

import unittest

from invenio import search_engine
from invenio.testutils import make_test_suite, run_test_suite

class TestMiscUtilityFunctions(unittest.TestCase):
    """Test whatever non-data-specific utility functions are essential."""

    def test_ziplist2x2(self):
        """search engine - ziplist 2 x 2"""
        self.assertEqual(search_engine.ziplist([1, 2], [3, 4]), [[1, 3], [2, 4]])

    def test_ziplist3x3(self):
        """search engine - ziplist 3 x 3"""
        self.assertEqual(search_engine.ziplist([1, 2, 3], ['a', 'b', 'c'], [9, 8, 7]),
                         [[1, 'a', 9], [2, 'b', 8], [3, 'c', 7]])


class TestWashQueryParameters(unittest.TestCase):
    """Test for washing of search query parameters."""

    def test_wash_pattern(self):
        """search engine - washing of query patterns"""
        self.assertEqual("Ellis, J", search_engine.wash_pattern('Ellis, J'))
        #self.assertEqual("ell", search_engine.wash_pattern('ell*'))

    def test_wash_dates_from_tuples(self):
        """search engine - washing of date arguments from (year,month,day) tuples"""
        self.assertEqual(search_engine.wash_dates(d1y=1980, d1m=1, d1d=28, d2y=2003, d2m=2, d2d=3),
                         ('1980-01-28 00:00:00', '2003-02-03 00:00:00'))
        self.assertEqual(search_engine.wash_dates(d1y=1980, d1m=0, d1d=28, d2y=2003, d2m=2, d2d=0),
                         ('1980-01-28 00:00:00', '2003-02-31 00:00:00'))

    def test_wash_dates_from_datetexts(self):
        """search engine - washing of date arguments from datetext strings"""
        self.assertEqual(search_engine.wash_dates(d1="1980-01-28 01:02:03", d2="1980-01-29 12:34:56"),
                         ('1980-01-28 01:02:03', '1980-01-29 12:34:56'))
        self.assertEqual(search_engine.wash_dates(d1="1980-01-28 01:02:03"),
                         ('1980-01-28 01:02:03', '9999-12-31 00:00:00'))
        self.assertEqual(search_engine.wash_dates(d2="1980-01-29 12:34:56"),
                         ('0000-01-01 00:00:00', '1980-01-29 12:34:56'))

    def test_wash_dates_from_both(self):
        """search engine - washing of date arguments from both datetext strings and (year,month,day) tuples"""
        # datetext mode takes precedence, d1* should be ignored
        self.assertEqual(search_engine.wash_dates(d1="1980-01-28 01:02:03", d1y=1980, d1m=1, d1d=28),
                         ('1980-01-28 01:02:03', '9999-12-31 00:00:00'))
        # datetext mode takes precedence, d2 missing, d2* should be ignored
        self.assertEqual(search_engine.wash_dates(d1="1980-01-28 01:02:03", d2y=2003, d2m=2, d2d=3),
                         ('1980-01-28 01:02:03', '2003-02-03 00:00:00'))

class TestQueryParser(unittest.TestCase):
    """Test of search pattern (or query) parser."""

    def _check(self, p, f, m, result_wanted):
        "Internal checking function calling create_basic_search_units."
        result_obtained = search_engine.create_basic_search_units(None, p, f, m)
        assert result_obtained == result_wanted, \
               'obtained %s instead of %s' % (repr(result_obtained),
                                              repr(result_wanted))
        return

    def test_parsing_single_word_query(self):
        "search engine - parsing single word queries"
        self._check('word', '', None, [['+', 'word', '', 'w']])

    def test_parsing_single_word_with_boolean_operators(self):
        "search engine - parsing single word queries"
        self._check('+word', '', None, [['+', 'word', '', 'w']])
        self._check('-word', '', None, [['-', 'word', '', 'w']])
        self._check('|word', '', None, [['|', 'word', '', 'w']])

    def test_parsing_single_word_in_field(self):
        "search engine - parsing single word queries in a logical field"
        self._check('word', 'title', None, [['+', 'word', 'title', 'w']])

    def test_parsing_single_word_in_tag(self):
        "search engine - parsing single word queries in a physical tag"
        self._check('word', '500', None, [['+', 'word', '500', 'a']])

    def test_parsing_query_with_commas(self):
        "search engine - parsing queries with commas"
        self._check('word,word', 'title', None,
                    [['+', 'word,word', 'title', 'a']])

    def test_parsing_exact_phrase_query(self):
        "search engine - parsing exact phrase"
        self._check('"the word"', 'title', None,
                    [['+', 'the word', 'title', 'a']])

    def test_parsing_exact_phrase_query_unbalanced(self):
        "search engine - parsing unbalanced exact phrase"
        self._check('"the word', 'title', None,
                    [['+', '"the', 'title', 'w'],
                     ['+', 'word', 'title', 'w']])

    def test_parsing_exact_phrase_query_in_any_field(self):
        "search engine - parsing exact phrase in any field"
        self._check('"the word"', '', None,
                    [['+', 'the word', '', 'a']])

    def test_parsing_partial_phrase_query(self):
        "search engine - parsing partial phrase"
        self._check("'the word'", 'title', None,
                    [['+', '%the word%', 'title', 'a']])

    def test_parsing_partial_phrase_query_unbalanced(self):
        "search engine - parsing unbalanced partial phrase"
        self._check("'the word", 'title', None,
                    [['+', "'the", 'title', 'w'],
                     ['+', "word", 'title', 'w']])

    def test_parsing_partial_phrase_query_in_any_field(self):
        "search engine - parsing partial phrase in any field"
        self._check("'the word'", '', None,
                    [['+', '%the word%', '', 'a']])

    def test_parsing_regexp_query(self):
        "search engine - parsing regex matches"
        self._check("/the word/", 'title', None,
                    [['+', 'the word', 'title', 'r']])

    def test_parsing_regexp_query_unbalanced(self):
        "search engine - parsing unbalanced regexp"
        self._check("/the word", 'title', None,
                    [['+', '/the', 'title', 'w'],
                     ['+', 'word', 'title', 'w']])

    def test_parsing_regexp_query_in_any_field(self):
        "search engine - parsing regexp searches in any field"
        self._check("/the word/", '', None,
                    [['+', 'the word', '', 'r']])

    def test_parsing_boolean_query(self):
        "search engine - parsing boolean query with several words"
        self._check("muon kaon ellis cern", '', None,
                    [['+', 'muon', '', 'w'],
                     ['+', 'kaon', '', 'w'],
                     ['+', 'ellis', '', 'w'],
                     ['+', 'cern', '', 'w']])

    def test_parsing_boolean_query_with_word_operators(self):
        "search engine - parsing boolean query with word operators"
        self._check("muon and kaon or ellis not cern", '', None,
                    [['+', 'muon', '', 'w'],
                     ['+', 'kaon', '', 'w'],
                     ['|', 'ellis', '', 'w'],
                     ['-', 'cern', '', 'w']])

    def test_parsing_boolean_query_with_symbol_operators(self):
        "search engine - parsing boolean query with symbol operators"
        self._check("muon +kaon |ellis -cern", '', None,
                    [['+', 'muon', '', 'w'],
                     ['+', 'kaon', '', 'w'],
                     ['|', 'ellis', '', 'w'],
                     ['-', 'cern', '', 'w']])

    def test_parsing_boolean_query_with_symbol_operators_and_spaces(self):
        "search engine - parsing boolean query with operators and spaces"
        self._check("muon + kaon | ellis - cern", '', None,
                    [['+', 'muon', '', 'w'],
                     ['+', 'kaon', '', 'w'],
                     ['|', 'ellis', '', 'w'],
                     ['-', 'cern', '', 'w']])

    def test_parsing_boolean_query_with_symbol_operators_and_no_spaces(self):
        "search engine - parsing boolean query with operators and no spaces"
        self._check("muon+kaon|ellis-cern", '', None,
                    [['+', 'muon+kaon|ellis-cern', '', 'w']])

    def test_parsing_structured_query_existing(self):
        "search engine - parsing structured query, existing index"
        self._check("title:muon", '', None,
                    [['+', 'muon', 'title', 'w']])

    def test_parsing_structured_query_existing_field(self):
        "search engine - parsing structured query, existing field, but no word index"
        self._check("division:IT", '', None,
                    [['+', 'IT', 'division', 'a']])

    def test_parsing_structured_query_nonexisting(self):
        "search engine - parsing structured query, non-existing index"
        self._check("foo:muon", '', None,
                    [['+', 'foo:muon', '', 'w']])

    def test_parsing_structured_query_marc(self):
        "search engine - parsing structured query, MARC-tag defined index"
        self._check("245:muon", '', None,
                    [['+', 'muon', '245', 'a']])

    def test_parsing_combined_structured_query(self):
        "search engine - parsing combined structured query"
        self._check("title:muon author:ellis", '', None,
                    [['+', 'muon', 'title', 'w'],
                     ['+', 'ellis', 'author', 'w']])

    def test_parsing_structured_regexp_query(self):
        "search engine - parsing structured regexp query"
        self._check("title:/(one|two)/", '', None,
                    [['+', '(one|two)', 'title', 'r']])

    def test_parsing_structured_regexp_marc_query(self):
        "search engine - parsing structured regexp MARC query"
        self._check("245__a:/(one|two)/", '', None,
                    [['+', '(one|two)', '245__a', 'r']])

    def test_parsing_structured_regexp_refersto_query(self):
        "search engine - parsing structured regexp refersto query"
        self._check("refersto:/(one|two)/", '', None,
                    [['+', '(one|two)', 'refersto', 'r']])

    def test_parsing_combined_structured_query_in_a_field(self):
        "search engine - parsing structured query in a field"
        self._check("title:muon author:ellis", 'abstract', None,
                    [['+', 'muon', 'title', 'w'],
                     ['+', 'ellis', 'author', 'w']])

    def test_parsing_colons_and_spaces_well_struuctured(self):
        "search engine - parsing query with colons and spaces, well structured"
        self._check("title: muon author:ellis keyword:   kaon", 'abstract', None,
                    [['+', 'muon', 'title', 'w'],
                     ['+', 'ellis', 'author', 'w'],
                     ['+', 'kaon', 'keyword', 'w']])

    def test_parsing_colons_and_spaces_badly_struuctured(self):
        "search engine - parsing query with colons and spaces, badly structured"
        self._check("foo: bar", 'abstract', None,
                    [['+', 'bar', 'abstract', 'w'],
                     ['+', 'foo:', 'abstract', 'w']])

    def test_parsing_colons_and_spaces_for_phrase_query(self):
        "search engine - parsing query with colons and spaces, phrase query"
        self._check('author:  "Ellis, J"', None, None,
                    [['+', 'Ellis, J', 'author', 'a']])


TEST_SUITE = make_test_suite(TestWashQueryParameters,
                             TestQueryParser,
                             TestMiscUtilityFunctions)


if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
