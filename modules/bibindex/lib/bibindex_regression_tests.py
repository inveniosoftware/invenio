# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2010, 2011, 2013 CERN.
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

"""BibIndex Regression Test Suite."""

__revision__ = "$Id$"

import unittest

from invenio.testutils import make_test_suite, run_test_suite, nottest
from invenio.dbquery import run_sql
from invenio.bibindex_engine import WordTable, get_words_from_phrase, \
                                    get_nothing_from_phrase, get_index_tags, \
                                    get_index_id_from_index_name
from invenio.intbitset import intbitset

def prepare_for_index_update(index_id, remove_stopwords = '',
                                       remove_html_markup = '',
                                       remove_latex_markup = ''):
    """Prepares SQL query for an update of a index in the idxINDEX table. Takes
       into account remove_stopwords, remove_html_markup, remove_latex_markup
       and tokenizer as parameters to change.
       remove_html_markup and remove_latex_markup accepts these values:
                                        '' to leave it unchanged
       @param index_id: id of the index to change
    """

    if remove_stopwords == '' and remove_html_markup == '' and remove_latex_markup == '':
        return ''

    parameter_set = False
    query_update = "UPDATE idxINDEX SET "
    params = {'remove_stopwords':remove_stopwords,
              'remove_html_markup':remove_html_markup,
              'remove_latex_markup':remove_latex_markup}
    for key in params:
        if params[key]:
            query_update += parameter_set and ", " or ""
            query_update += "%s='%s'" % (key, params[key])
            parameter_set = True
    query_update += " WHERE id=%s" % index_id
    return query_update


@nottest
def reindex_word_tables_into_testtables(index_name, recids = None, prefix = 'test', remove_stopwords = '',
                                                                                    remove_html_markup = '',
                                                                                    remove_latex_markup = ''):
    """Function for setting up a test enviroment. Reindexes an index with a given name to a
       new temporary table with a given prefix. During the reindexation it changes some parameters
       of chosen index. It's useful for conducting tests concerning the reindexation.
       Reindexes only idxWORDxxx tables.
       @param index_name: name of the index we want to reindex
       @param prefix: prefix for the new tabels
       @param recids: None means reindexing all records, set ids of the records to update only part of them
       @param prefix: prefix for the new tabels, if it's set to boolean False function will reindex to original table
       @param remove_stopwords: name of the stopwords knowledge base, 'No' to set it to 'No'
       @param remove_html_markup: 'Yes' to set remove_html_markup to 'Yes', 'No' to set it to 'No'
       @param remove_latex_markup: 'Yes' to set remove_latex_markup to 'Yes', 'No' to set it to 'No'
    """
    index_id = get_index_id_from_index_name(index_name)
    query_update = prepare_for_index_update(index_id, remove_stopwords,
                                                      remove_html_markup,
                                                      remove_latex_markup)

    query_last_updated = "UPDATE idxINDEX SET last_updated='0000-00-00 00:00:00' WHERE id=%s" % index_id

    test_tablename = "%s_idxWORD%02d" % (prefix, index_id)
    query_drop_forward_index_table = """DROP TABLE IF EXISTS %sF""" % test_tablename
    query_drop_reversed_index_table = """DROP TABLE IF EXISTS %sR""" % test_tablename

    query_create_forward_index_table = """CREATE TABLE %sF (
                                          id mediumint(9) unsigned NOT NULL auto_increment,
                                          term varchar(50) default NULL,
                                          hitlist longblob,
                                          PRIMARY KEY  (id),
                                          UNIQUE KEY term (term)
                                          ) ENGINE=MyISAM""" % test_tablename
    query_create_reversed_index_table = """CREATE TABLE %sR (
                                           id_bibrec mediumint(9) unsigned NOT NULL,
                                           termlist longblob,
                                           type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
                                           PRIMARY KEY (id_bibrec,type)
                                           ) ENGINE=MyISAM""" % test_tablename

    run_sql(query_drop_forward_index_table)
    run_sql(query_drop_reversed_index_table)
    run_sql(query_create_forward_index_table)
    run_sql(query_create_reversed_index_table)
    run_sql(query_update)
    run_sql(query_last_updated)

    pattern = '%s_idxWORD' % prefix
    wordTable = WordTable(index_name=index_name,
                          index_id=index_id,
                          fields_to_index=get_index_tags(index_name),
                          table_name_pattern= pattern + '%02dF',
                          default_get_words_fnc=get_words_from_phrase,
                          tag_to_words_fnc_map={'8564_u': get_nothing_from_phrase},
                          is_fulltext_index=False,
                          wash_index_terms=50)
    wordTable.add_recIDs_by_date([],10000)


@nottest
def remove_reindexed_word_testtables(index_name, prefix = 'test'):
    """
        Removes prefix_idxWORDxxx tables created during tests.
        @param index_name: name of the index
        @param prefix: prefix for the tables
    """
    index_id = get_index_id_from_index_name(index_name)
    test_tablename = "%s_idxWORD%02d" % (prefix, index_id)
    query_drop_forward_index_table = """DROP TABLE IF EXISTS %sF""" % test_tablename
    query_drop_reversed_index_table = """DROP TABLE IF EXISTS %sR""" % test_tablename
    run_sql(query_drop_forward_index_table)
    run_sql(query_drop_reversed_index_table)


class BibIndexRemoveStopwordsTest(unittest.TestCase):
    """Tests remove_stopwords parameter of an index. Changes it in the database
       and reindexes from scratch into a new table to see the diffrence which is brought
       by change. Uses 'title' index.
    """

    test_counter = 0
    reindexed = False

    @classmethod
    def setUp(self):
        """reindexation to new table"""
        if not self.reindexed:
            reindex_word_tables_into_testtables('title', remove_stopwords = 'Yes')
            self.reindexed = True

    @classmethod
    def tearDown(self):
        """cleaning up"""
        self.test_counter += 1
        if self.test_counter == 4:
            remove_reindexed_word_testtables('title')
            reverse_changes = prepare_for_index_update(get_index_id_from_index_name('title'), remove_stopwords = 'No')
            run_sql(reverse_changes)

    def test_check_occurances_of_stopwords_in_testable_word_of(self):
        """Tests if term 'of' is in the new reindexed table"""

        query = "SELECT hitlist FROM test_idxWORD08F WHERE term='of'"
        res = run_sql(query)
        self.assertEqual(0, len(res))

    def test_check_occurances_of_stopwords_in_testable_word_everything(self):
        """Tests if term 'everything' is in the new reindexed table"""

        query = "SELECT hitlist FROM test_idxWORD08F WHERE term='everything'"
        res = run_sql(query)
        self.assertEqual(0, len(res))

    def test_compare_non_stopwords_occurances_in_original_and_test_tables_word_theory(self):
        """Checks if stopwords removing has no influence on indexation of word 'theory' """

        word = "theori" #theori not theory, because of default stemming for title index
        query = "SELECT hitlist FROM test_idxWORD08F WHERE term='%s'" % word
        iset_removed = "iset_removed"
        iset_original = "iset_original"
        res = run_sql(query)
        if res:
            iset_removed = intbitset(res[0][0])
        query = "SELECT hitlist FROM idxWORD08F WHERE term='%s'" % word
        res = run_sql(query)
        if res:
            iset_original = intbitset(res[0][0])
        self.assertEqual(len(iset_removed), len(iset_original))

    def test_compare_non_stopwords_occurances_in_original_and_test_tables_word_on(self):
        """Checks if stopwords removing has no influence on indexation of word 'o(n)' """

        word = "o(n)"
        query = "SELECT hitlist FROM test_idxWORD08F WHERE term='%s'" % word
        iset_removed = "iset_removed"
        iset_original = "iset_original"
        res = run_sql(query)
        if res:
            iset_removed = intbitset(res[0][0])
        query = "SELECT hitlist FROM idxWORD08F WHERE term='%s'" % word
        res = run_sql(query)
        if res:
            iset_original = intbitset(res[0][0])
        self.assertEqual(len(iset_removed), len(iset_original))


class BibIndexRemoveLatexTest(unittest.TestCase):
    """Tests remove_latex_markup parameter of an index. Changes it in the database
       and reindexes from scratch into a new table to see the diffrence which is brought
       by change. Uses 'abstract' index.
    """

    test_counter = 0
    reindexed = False

    @classmethod
    def setUp(self):
        """reindexation to new table"""
        if not self.reindexed:
            reindex_word_tables_into_testtables('abstract', remove_latex_markup = 'Yes')
            self.reindexed = True

    @classmethod
    def tearDown(self):
        """cleaning up"""
        self.test_counter += 1
        if self.test_counter == 4:
            remove_reindexed_word_testtables('abstract')
            reverse_changes = prepare_for_index_update(get_index_id_from_index_name('abstract'), remove_latex_markup = 'No')
            run_sql(reverse_changes)


    def test_check_occurances_after_latex_removal_word_u1(self):
        """Tests how many times experssion 'u(1)' occures"""

        word = "u(1)"
        query = "SELECT hitlist FROM test_idxWORD%02dF WHERE term='%s'" % (get_index_id_from_index_name('abstract'), word)
        res = run_sql(query)
        iset = "iset_change"
        if res:
            iset = intbitset(res[0][0])
        self.assertEqual(3, len(iset))

    def test_check_exact_occurances_after_latex_removal_word_theta(self):
        """Tests where experssion 'theta' occures"""

        word = "theta"
        query = "SELECT hitlist FROM test_idxWORD%02dF WHERE term='%s'" % (get_index_id_from_index_name('abstract'), word)
        res = run_sql(query)
        iset = []
        if res:
            iset = intbitset(res[0][0])
            ilist = iset.tolist()
        self.assertEqual([12], ilist)

    def test_compare_occurances_after_and_before_latex_removal_math_expression(self):
        """Checks if latex removal has no influence on indexation of expression 's(u(n_1)*u(n_2))' """

        word = 's(u(n_1)*u(n_2))'
        query = "SELECT hitlist FROM test_idxWORD%02dF WHERE term='%s'" % (get_index_id_from_index_name('abstract'), word)
        res = run_sql(query)
        ilist_test = []
        if res:
            iset = intbitset(res[0][0])
            ilist_test = iset.tolist()
        word = 's(u(n_1)*u(n_2))'
        query = "SELECT hitlist FROM idxWORD%02dF WHERE term='%s'" % (get_index_id_from_index_name('abstract'), word)
        res = run_sql(query)
        ilist = ["default_not_equal"]
        if res:
            iset = intbitset(res[0][0])
            ilist = iset.tolist()
        self.assertEqual(ilist, ilist_test)

    def test_check_occurances_latex_expression_with_u1(self):
        """Tests influence of latex removal on record 80"""

        word = '%over u(1)%'
        query = "SELECT hitlist FROM test_idxWORD%02dF WHERE term LIKE '%s'" % (get_index_id_from_index_name('abstract'), word)
        res = run_sql(query)
        ilist = []
        if res:
            iset = intbitset(res[0][0])
            ilist = iset.tolist()
        self.assertEqual([80], ilist)


class BibIndexRemoveHtmlTest(unittest.TestCase):
    """Tests remove_html_markup parameter of an index. Changes it in the database
       and reindexes from scratch into a new table to see the diffrence which is brought
       by change. Uses 'abstract' index.
    """

    test_counter = 0
    reindexed = False

    @classmethod
    def setUp(self):
        """reindexation to new table"""
        if not self.reindexed:
            reindex_word_tables_into_testtables('abstract', remove_html_markup = 'Yes')
            self.reindexed = True

    @classmethod
    def tearDown(self):
        """cleaning up"""
        self.test_counter += 1
        if self.test_counter == 2:
            remove_reindexed_word_testtables('abstract')
            reverse_changes = prepare_for_index_update(get_index_id_from_index_name('abstract'), remove_html_markup = 'No')
            run_sql(reverse_changes)


    def test_check_occurances_after_html_removal_tag_p(self):
        """Tests if expression 'water-hog</p>' is not indexed after html markup removal"""

        word = 'water-hog</p>'
        query = "SELECT hitlist FROM test_idxWORD%02dF WHERE term='%s'" % (get_index_id_from_index_name('abstract'), word)
        res = run_sql(query)
        ilist = []
        if res:
            iset = intbitset(res[0][0])
            ilist = iset.tolist()
        self.assertEqual(0, len(ilist))


    def test_check_occurances_after_and_before_html_removal_word_style(self):
        """Tests html markup removal influence on expression 'style="width' """

        word = 'style="width'
        query = "SELECT hitlist FROM test_idxWORD%02dF WHERE term='%s'" % (get_index_id_from_index_name('abstract'), word)
        res = run_sql(query)
        ilist_test = []
        if res:
            iset = intbitset(res[0][0])
            ilist_test = iset.tolist()
        query = "SELECT hitlist FROM idxWORD%02dF WHERE term='%s'" % (get_index_id_from_index_name('abstract'), word)
        res = run_sql(query)
        ilist = []
        if res:
            iset = intbitset(res[0][0])
            ilist = iset.tolist()
        self.assertNotEqual(ilist, ilist_test)


TEST_SUITE = make_test_suite(BibIndexRemoveStopwordsTest,
                             BibIndexRemoveLatexTest,
                             BibIndexRemoveHtmlTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)
