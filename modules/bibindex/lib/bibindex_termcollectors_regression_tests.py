# -*- coding:utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
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

from invenio.testutils import make_test_suite, run_test_suite
from invenio.bibindex_termcollectors import TermCollector, \
    NonmarcTermCollector
from invenio.bibindex_engine import detect_tokenizer_type
from invenio.bibindex_engine_utils import get_index_id_from_index_name, \
    get_index_remove_stopwords, \
    get_index_remove_html_markup, \
    get_index_remove_latex_markup, \
    get_index_tags
from invenio.bibindex_engine_config import CFG_BIBINDEX_INDEX_TABLE_TYPE
from invenio.bibindex_engine import get_index_tokenizer
from invenio.bibsort_engine import get_max_recid
from invenio.search_engine import get_index_stemming_language


def initialise_term_collector(index_name,
                              collector_type=TermCollector,
                              table_type=CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"]):
    """Initialise any term collector for given index and WORD index table"""
    index_id = get_index_id_from_index_name(index_name)
    remove_stopwords = get_index_remove_stopwords(index_id)
    remove_html_markup = get_index_remove_html_markup(index_id)
    remove_latex_markup = get_index_remove_latex_markup(index_id)
    stemming = get_index_stemming_language(index_id)
    tokenizer = get_index_tokenizer(index_id)(stemming,
                                              remove_stopwords,
                                              remove_html_markup,
                                              remove_latex_markup)

    args = [tokenizer,
            detect_tokenizer_type(tokenizer),
            table_type]
    tagtype = collector_type == TermCollector and "marc" or "nonmarc"
    args.append(get_index_tags(index_name, tagtype=tagtype))
    args.append([1, get_max_recid()])
    return collector_type(*args)


class BibIndexTermCollectorTest(unittest.TestCase):

    def test_correct_terms_for_title_index_rec_10(self):
        """bibindex - checks correct terms for title index, record 10"""
        mtc = initialise_term_collector("title")
        terms = mtc.collect([10], {})
        self.assertEqual(
            terms[10], ['r-pariti', 'pariti', 'at', 'in', 'sneutrino',
                        '$\\sqrt{s}$', 'for', 'violat', 'sqrt', 'collis',
                        '189', '=', 'singl', 'product', 'gev', '209', 'search',
                        'e', 'of', '189-209', 's', 'r', '$e^{+}e^{-}$'])

    def test_correct_terms_for_year_index_rec_9(self):
        """bibindex - checks correct terms for year index, record 9"""
        mtc = initialise_term_collector("year")
        terms = mtc.collect([9, 10], {})
        self.assertEqual(terms[9], ["1982"])

    def test_correct_terms_for_affiliation_index_rec_11(self):
        """bibindex - checks correct terms for affiliation index, record 11"""
        mtc = initialise_term_collector("affiliation")
        terms = mtc.collect([9, 10, 11], {})
        self.assertEqual(terms[11], ["university", "cambridge"])

    def test_correct_terms_for_author_index_rec_14_with_authority_rec(self):
        """bibindex - checks if terms from authority record are also found"""
        mtc = initialise_term_collector("simpleauthor", table_type="PHRASE")
        terms = mtc.collect([14], {})
        self.assertEqual('Ellis, John' in terms[14], True)
        self.assertEqual('CERN Geneva' in terms[14], True)

    def test_correct_amount_of_marc_recids_keyword(self):
        """bibindex - checks if correct number of records was processed for keyword index"""
        mtc = initialise_term_collector("keyword")
        terms = mtc.collect([4, 5, 6, 7, 8], {})
        self.assertEqual(len(terms), 1)

    def test_correct_amount_of_marc_recids_title(self):
        """bibindex - checks if correct number of records was processed for title index"""
        mtc = initialise_term_collector("title")
        terms = mtc.collect([4, 5, 6, 7, 8], {})
        self.assertEqual(len(terms), 5)

    def test_correct_amount_of_items_journal_index_rec_7(self):
        """bibindex - checks if correct number of records was processed for journal index"""
        mtc = initialise_term_collector("journal")
        terms = mtc.collect([6, 7, 8, 22], {})
        self.assertEqual(len(terms[7]), 8)


class BibIndexNonmarcTermCollectorTest(unittest.TestCase):

    def test_correct_terms_for_title_index_rec_10_non_marc(self):
        """bibindex - checks correct terms for title index, record 10 - non MarcTermCollector"""
        mtc = initialise_term_collector("title", NonmarcTermCollector)
        terms = mtc.collect([10], {})
        self.assertEqual(
            terms[10], ['r-pariti', 'pariti', 'at', 'in', 'sneutrino',
                        '$\\sqrt{s}$', 'for', 'violat', 'sqrt', 'collis',
                        '189', '=', 'singl', 'product', 'gev', '209', 'search',
                        'e', 'of', '189-209', 's', 'r', '$e^{+}e^{-}$'])

    def test_correct_terms_for_year_index_rec_9_non_marc(self):
        """bibindex - checks correct terms for year index, record 9 - non marc"""
        mtc = initialise_term_collector("year", NonmarcTermCollector)
        terms = mtc.collect([9, 10], {})
        self.assertEqual(terms[9], ["1982"])

    def test_correct_terms_for_affiliation_index_rec_11_non_marc(self):
        """bibindex - checks correct terms for affiliation index, record 11 - non marc"""
        mtc = initialise_term_collector("affiliation", NonmarcTermCollector)
        terms = mtc.collect([9, 10, 11], {})
        self.assertEqual(terms[11], ["university", "cambridge"])

    def test_correct_amount_of_marc_recids_keyword(self):
        """bibindex - checks if correct number of records was processed for keyword index"""
        mtc = initialise_term_collector("keyword", NonmarcTermCollector)
        terms = mtc.collect([4, 5, 6, 7, 8], {})
        self.assertEqual(len(terms), 1)

TEST_SUITE = make_test_suite(BibIndexTermCollectorTest,
                             BibIndexNonmarcTermCollectorTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)
