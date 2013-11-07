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
import os

from invenio.bibauthority_config import CFG_BIBAUTHORITY_BIBINDEX_UPDATE_MESSAGE
from invenio.bibindex_engine_config import CFG_BIBINDEX_ADDING_RECORDS_STARTED_STR, \
    CFG_BIBINDEX_INDEX_TABLE_TYPE
from invenio.bibtask import task_low_level_submission
from invenio.config import CFG_BINDIR, CFG_LOGDIR
from invenio.testutils import make_test_suite, run_test_suite, nottest
from invenio.dbquery import run_sql, deserialize_via_marshal
from invenio.bibindex_engine import WordTable, get_index_id_from_index_name, get_index_tags
from invenio.intbitset import intbitset
from invenio.search_engine_utils import get_fieldvalues
from invenio.bibauthority_engine import get_index_strings_by_control_no, get_control_nos_from_recID
from invenio.bibindex_engine_utils import run_sql_drop_silently


def reindex_for_type_with_bibsched(_type):
    """runs bibindex for the index '_type' and returns the task_id"""
    program = os.path.join(CFG_BINDIR, 'bibindex')
    task_id = task_low_level_submission('bibindex', 'bibindex_regression_tests', '-w', _type, '-u', 'admin')
    COMMAND = "%s %s > /dev/null 2> /dev/null" % (program, str(task_id))
    os.system(COMMAND)
    return task_id


def prepare_for_index_update(index_id, remove_stopwords = '',
                                       remove_html_markup = '',
                                       remove_latex_markup = '',
                                       tokenizer=''):
    """ Prepares SQL query for an update of a index in the idxINDEX table. Takes
        into account remove_stopwords, remove_html_markup, remove_latex_markup
        as parameters to change.
        remove_html_markup and remove_latex_markup accepts these values:
                                        '' to leave it unchanged
                                        'Yes' to change it to 'Yes'
                                        'No' to change it to 'No'.
        For remove_stopwords instead of 'Yes' one must give the name of the file (for example: 'stopwords.kb')
        from CFG_ETCDIR/bibrank/ directory pointing at stopwords knowledge base.
        For tokenizer please specify the name of the tokenizer.
        @param index_id: id of the index to change
    """


    if remove_stopwords == '' and remove_html_markup == '' and remove_latex_markup == '' and tokenizer == '':
        return ''

    parameter_set = False
    query_update = "UPDATE idxINDEX SET "
    params = {'remove_stopwords':remove_stopwords,
              'remove_html_markup':remove_html_markup,
              'remove_latex_markup':remove_latex_markup,
              'tokenizer':tokenizer}
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
                                                                                    remove_latex_markup = '',
                                                                                    tokenizer = ''):
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
       @param tokenizer: name of the tokenizer
    """
    index_id = get_index_id_from_index_name(index_name)
    query_update = prepare_for_index_update(index_id, remove_stopwords,
                                                      remove_html_markup,
                                                      remove_latex_markup,
                                                      tokenizer)

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

    run_sql_drop_silently(query_drop_forward_index_table)
    run_sql_drop_silently(query_drop_reversed_index_table)
    run_sql(query_create_forward_index_table)
    run_sql(query_create_reversed_index_table)
    if query_update:
        run_sql(query_update)
    run_sql(query_last_updated)

    pattern = 'idxWORD'
    if prefix:
        pattern = '%s_idxWORD' % prefix
    wordTable = WordTable(index_name=index_name,
                          index_id=index_id,
                          fields_to_index=get_index_tags(index_name),
                          table_name_pattern= pattern + '%02dF',
                          wordtable_type = CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"],
                          tag_to_tokenizer_map={'8564_u': "BibIndexEmptyTokenizer"},
                          is_fulltext_index=False,
                          wash_index_terms=50)
    if recids:
        wordTable.add_recIDs(recids, 10000)
    else:
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
            reindex_word_tables_into_testtables('title', remove_stopwords = 'stopwords.kb')
            self.reindexed = True

    @classmethod
    def tearDown(self):
        """cleaning up"""
        self.test_counter += 1
        if self.test_counter == 4:
            remove_reindexed_word_testtables('title')
            reverse_changes = prepare_for_index_update(get_index_id_from_index_name('title'), remove_stopwords = 'No')
            run_sql(reverse_changes)

    def test_check_occurrences_of_stopwords_in_testable_word_of(self):
        """Tests if term 'of' is in the new reindexed table"""

        query = "SELECT hitlist FROM test_idxWORD08F WHERE term='of'"
        res = run_sql(query)
        self.assertEqual(0, len(res))

    def test_check_occurrences_of_stopwords_in_testable_word_everything(self):
        """Tests if term 'everything' is in the new reindexed table"""

        query = "SELECT hitlist FROM test_idxWORD08F WHERE term='everything'"
        res = run_sql(query)
        self.assertEqual(0, len(res))

    def test_compare_non_stopwords_occurrences_in_original_and_test_tables_word_theory(self):
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

    def test_compare_non_stopwords_occurrences_in_original_and_test_tables_word_on(self):
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


    def test_check_occurrences_after_latex_removal_word_u1(self):
        """Tests how many times experssion 'u(1)' occures"""

        word = "u(1)"
        query = "SELECT hitlist FROM test_idxWORD%02dF WHERE term='%s'" % (get_index_id_from_index_name('abstract'), word)
        res = run_sql(query)
        iset = "iset_change"
        if res:
            iset = intbitset(res[0][0])
        self.assertEqual(3, len(iset))

    def test_check_exact_occurrences_after_latex_removal_word_theta(self):
        """Tests where experssion 'theta' occures"""

        word = "theta"
        query = "SELECT hitlist FROM test_idxWORD%02dF WHERE term='%s'" % (get_index_id_from_index_name('abstract'), word)
        res = run_sql(query)
        ilist = []
        if res:
            iset = intbitset(res[0][0])
            ilist = iset.tolist()
        self.assertEqual([12], ilist)

    def test_compare_occurrences_after_and_before_latex_removal_math_expression(self):
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

    def test_check_occurrences_latex_expression_with_u1(self):
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


    def test_check_occurrences_after_html_removal_tag_p(self):
        """Tests if expression 'water-hog</p>' is not indexed after html markup removal"""

        word = 'water-hog</p>'
        query = "SELECT hitlist FROM test_idxWORD%02dF WHERE term='%s'" % (get_index_id_from_index_name('abstract'), word)
        res = run_sql(query)
        ilist = []
        if res:
            iset = intbitset(res[0][0])
            ilist = iset.tolist()
        self.assertEqual(0, len(ilist))


    def test_check_occurrences_after_and_before_html_removal_word_style(self):
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


class BibIndexYearIndexTest(unittest.TestCase):
    """
        Checks year index. Tests are diffrent than those inside WebSearch module because
        they only test content and reindexation and not the search itself.
    """

    test_counter = 0
    reindexed = False

    @classmethod
    def setUp(self):
        """reindexation to new table"""
        if not self.reindexed:
            reindex_word_tables_into_testtables('year')
            self.reindexed = True


    @classmethod
    def tearDown(self):
        """cleaning up"""
        self.test_counter += 1
        if self.test_counter == 3:
            remove_reindexed_word_testtables('year')


    def test_occurrences_in_year_index_1973(self):
        """checks content of year index for year 1973"""
        word = '1973'
        query = "SELECT hitlist FROM test_idxWORD%02dF WHERE term='%s'" % (get_index_id_from_index_name('year'), word)
        res = run_sql(query)
        ilist = []
        if res:
            iset = intbitset(res[0][0])
            ilist = iset.tolist()
        self.assertEqual([34], ilist)


    def test_occurrences_in_year_index_2001(self):
        """checks content of year index for year 2001"""
        word = '2001'
        query = "SELECT hitlist FROM test_idxWORD%02dF WHERE term='%s'" % (get_index_id_from_index_name('year'), word)
        res = run_sql(query)
        ilist = []
        if res:
            iset = intbitset(res[0][0])
            ilist = iset.tolist()
        self.assertEqual([2, 11, 12, 15], ilist)


    def test_comparison_for_number_of_items(self):
        """checks the reindexation of year index"""
        query_test = "SELECT count(*) FROM test_idxWORD%02dF" % get_index_id_from_index_name('year')
        query_orig = "SELECT count(*) FROM idxWORD%02dF" % get_index_id_from_index_name('year')
        num_orig = 0
        num_test = 1
        res = run_sql(query_test)
        if res:
            num_test = res[0][0]
        res = run_sql(query_orig)
        if res:
            num_orig = res[0][0]
        self.assertEqual(num_orig, num_test)



class BibIndexAuthorCountIndexTest(unittest.TestCase):
    """
       Checks author count index. Tests are diffrent than those inside WebSearch module because
       they only test content and reindexation and not the search itself.
    """

    test_counter = 0
    reindexed = False

    @classmethod
    def setUp(self):
        """reindexation to new table"""
        if not self.reindexed:
            reindex_word_tables_into_testtables('authorcount')
            self.reindexed = True

    @classmethod
    def tearDown(self):
        """cleaning up"""
        self.test_counter += 1
        if self.test_counter == 2:
            remove_reindexed_word_testtables('authorcount')


    def test_occurrences_in_authorcount_index(self):
        """checks content of authorcount index for papers with 4 authors"""
        word = '4'
        query = "SELECT hitlist FROM test_idxWORD%02dF WHERE term='%s'" % (get_index_id_from_index_name('authorcount'), word)
        res = run_sql(query)
        ilist = []
        if res:
            iset = intbitset(res[0][0])
            ilist = iset.tolist()
        self.assertEqual([51, 54, 59, 66, 92, 96], ilist)


    def test_comparison_for_number_of_items(self):
        """checks the reindexation of authorcount index"""
        query_test = "SELECT count(*) FROM test_idxWORD%02dF" % get_index_id_from_index_name('authorcount')
        query_orig = "SELECT count(*) FROM idxWORD%02dF" % get_index_id_from_index_name('authorcount')
        num_orig = 0
        num_test = 1
        res = run_sql(query_test)
        if res:
            num_test = res[0][0]
        res = run_sql(query_orig)
        if res:
            num_orig = res[0][0]
        self.assertEqual(num_orig, num_test)


class BibIndexItemCountIndexTest(unittest.TestCase):
    """
       Checks item count index. Checks a number of copies of books for records
       as well as occurrences of particular number of copies in test data.
    """

    def test_occurrences_in_itemcount_index_two_copies(self):
        """checks content of itemcount index for records with two copies of a book"""
        word = '2'
        query = "SELECT hitlist FROM idxWORD%02dF WHERE term='%s'" % (get_index_id_from_index_name('itemcount'), word)
        res = run_sql(query)
        ilist = []
        if res:
            iset = intbitset(res[0][0])
            ilist = iset.tolist()
        self.assertEqual([31, 34], ilist)

    def test_records_for_number_of_copies_record1(self):
        """checks content of itemcount index for record: 1"""
        query = "SELECT termlist FROM idxWORD%02dR WHERE id_bibrec=1" \
                 % get_index_id_from_index_name('itemcount')
        res = run_sql(query)
        self.assertEqual(deserialize_via_marshal(res[0][0]),['0'])

    def test_records_for_number_of_copies_record30(self):
        """checks content of itemcount index for record: 30"""
        query = "SELECT termlist FROM idxWORD%02dR WHERE id_bibrec=30" \
                 % get_index_id_from_index_name('itemcount')
        res = run_sql(query)
        self.assertEqual(deserialize_via_marshal(res[0][0]),['1'])

    def test_records_for_number_of_copies_record32(self):
        """checks content of itemcount index for record: 32"""
        query = "SELECT termlist FROM idxWORD%02dR WHERE id_bibrec=32" \
                 % get_index_id_from_index_name('itemcount')
        res = run_sql(query)
        self.assertEqual(deserialize_via_marshal(res[0][0]),['3'])


class BibIndexFiletypeIndexTest(unittest.TestCase):
    """
       Checks filetype index. Tests are diffrent than those inside WebSearch module because
       they only test content and indexation and not the search itself.
    """

    def test_occurances_of_tif_filetype(self):
        """tests which records has file with 'tif' extension"""
        query = "SELECT hitlist FROM idxWORD%02dF where term='tif'" \
                % get_index_id_from_index_name('filetype')
        res = run_sql(query)
        value = []
        if res:
            iset = intbitset(res[0][0])
            value = iset.tolist()
        self.assertEqual(sorted(value), [66, 71])

    def test_filetypes_of_records(self):
        """tests files extensions of record 1 and 77"""
        query1 = "SELECT termlist FROM idxWORD%02dR WHERE id_bibrec=1" \
                 % get_index_id_from_index_name('filetype')
        query2 = "SELECT termlist FROM idxWORD%02dR WHERE id_bibrec=77" \
                 % get_index_id_from_index_name('filetype')
        res1 = run_sql(query1)
        res2 = run_sql(query2)
        set1 = deserialize_via_marshal(res1[0][0])
        set2 = deserialize_via_marshal(res2[0][0])
        self.assertEqual(set1, ['gif', 'jpg'])
        self.assertEqual(set2, ['pdf', 'ps.gz'])


class BibIndexJournalIndexTest(unittest.TestCase):
    """
        Checks journal index. Tests are diffrent than those inside WebSearch module because
        they only test content and reindexation and not the search itself.
    """
    test_counter = 0
    reindexed = False

    @classmethod
    def setUp(self):
        """reindexation to new table"""
        if not self.reindexed:
            reindex_word_tables_into_testtables('journal')
            self.reindexed = True

    @classmethod
    def tearDown(self):
        """cleaning up"""
        self.test_counter += 1
        if self.test_counter == 2:
            remove_reindexed_word_testtables('journal')



    def test_occurrences_in_journal_index(self):
        """checks content of journal index for phrase: 'prog. theor. phys.' """
        word = 'prog. theor. phys.'
        query = "SELECT hitlist FROM test_idxWORD%02dF WHERE term='%s'" % (get_index_id_from_index_name('journal'), word)
        res = run_sql(query)
        ilist = []
        if res:
            iset = intbitset(res[0][0])
            ilist = iset.tolist()
        self.assertEqual([86], ilist)


    def test_comparison_for_number_of_items(self):
        """checks the reindexation of journal index"""
        query_test = "SELECT count(*) FROM test_idxWORD%02dF" % get_index_id_from_index_name('journal')
        query_orig = "SELECT count(*) FROM idxWORD%02dF" % get_index_id_from_index_name('journal')
        num_orig = 0
        num_test = 1
        res = run_sql(query_test)
        if res:
            num_test = res[0][0]
        res = run_sql(query_orig)
        if res:
            num_orig = res[0][0]
        self.assertEqual(num_orig, num_test)


class BibIndexCJKTokenizerTitleIndexTest(unittest.TestCase):
    """
       Checks CJK tokenization on title index.
    """
    test_counter = 0
    reindexed = False

    @classmethod
    def setUp(self):
        """reindexation to new table"""
        if not self.reindexed:
            reindex_word_tables_into_testtables('title', tokenizer = 'BibIndexCJKTokenizer')
            self.reindexed = True

    @classmethod
    def tearDown(self):
        """cleaning up"""
        self.test_counter += 1
        if self.test_counter == 2:
            remove_reindexed_word_testtables('title')
            reverse_changes = prepare_for_index_update(get_index_id_from_index_name('title'), tokenizer = 'BibIndexDefaultTokenizer')
            run_sql(reverse_changes)


    def test_splliting_and_indexing_CJK_characters_forward_table(self):
        """CJK Tokenizer - searching for a CJK term in title index, forward table"""
        query = "SELECT * from test_idxWORD%02dF where term='\xe6\x95\xac'" % get_index_id_from_index_name('title')
        res = run_sql(query)
        iset = []
        if res:
            iset = intbitset(res[0][2])
            iset = iset.tolist()
        self.assertEqual(iset, [104])

    def test_splliting_and_indexing_CJK_characters_reversed_table(self):
        """CJK Tokenizer - comparing terms for record with chinese poetry in title index, reverse table"""
        query = "SELECT * from test_idxWORD%02dR where id_bibrec='104'" % get_index_id_from_index_name('title')
        res = run_sql(query)
        iset = []
        if res:
            iset = deserialize_via_marshal(res[0][1])
        self.assertEqual(iset, ['\xe6\x95\xac', '\xe7\x8d\xa8', '\xe4\xba\xad', '\xe5\x9d\x90'])


class BibIndexAuthorityRecordTest(unittest.TestCase):
    """Test if BibIndex correctly knows when to update the index for a
    bibliographic record if it is dependent upon an authority record changed
    within the given date range"""

    def test_authority_record_recently_updated(self):
        """bibindex - reindexing after recently changed authority record"""

        authRecID = 118
        bibRecID = 9
        index_name = 'author'
        table = "idxWORD%02dF" % get_index_id_from_index_name(index_name)
        reindex_for_type_with_bibsched(index_name)
        run_sql("UPDATE bibrec SET modification_date = now() WHERE id = %s", (authRecID,))
        # run bibindex again
        task_id = reindex_for_type_with_bibsched(index_name)

        filename = os.path.join(CFG_LOGDIR, 'bibsched_task_' + str(task_id) + '.log')
        _file = open(filename)
        text = _file.read() # small file
        _file.close()
        self.assertTrue(text.find(CFG_BIBAUTHORITY_BIBINDEX_UPDATE_MESSAGE) >= 0)
        self.assertTrue(text.find(CFG_BIBINDEX_ADDING_RECORDS_STARTED_STR % (table, bibRecID, bibRecID)) >= 0)

    def test_authority_record_enriched_index(self):
        """bibindex - test whether reverse index for bibliographic record
        contains words from referenced authority records"""
        bibRecID = 9
        authority_string = 'jonathan'
        index_name = 'author'
        table = "idxWORD%02dR" % get_index_id_from_index_name(index_name)

        reindex_for_type_with_bibsched(index_name)
        self.assertTrue(
            authority_string in deserialize_via_marshal(
                run_sql("SELECT termlist FROM %s WHERE id_bibrec = %s" % (table, bibRecID))[0][0]
            )
        )

    def test_indexing_of_deleted_authority_record(self):
        """bibindex - no info for indexing from deleted authority record"""
        recID = 119 # deleted record
        control_nos = get_control_nos_from_recID(recID)
        info = get_index_strings_by_control_no(control_nos[0])
        self.assertEqual([], info)

    def test_authority_record_get_values_by_bibrecID_from_tag(self):
        """bibindex - find authors in authority records for given bibrecID"""
        tags = ['100__a']
        bibRecID = 9
        values = []
        for tag in tags:
            authority_tag = tag[0:3] + "__0"
            control_nos = get_fieldvalues(bibRecID, authority_tag)
            for control_no in control_nos:
                new_strings = get_index_strings_by_control_no(control_no)
                values.extend(new_strings)
        self.assertTrue('Ellis, Jonathan Richard' in values)


TEST_SUITE = make_test_suite(BibIndexRemoveStopwordsTest,
                             BibIndexRemoveLatexTest,
                             BibIndexRemoveHtmlTest,
                             BibIndexYearIndexTest,
                             BibIndexAuthorCountIndexTest,
                             BibIndexItemCountIndexTest,
                             BibIndexFiletypeIndexTest,
                             BibIndexJournalIndexTest,
                             BibIndexCJKTokenizerTitleIndexTest,
                             BibIndexAuthorityRecordTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)
