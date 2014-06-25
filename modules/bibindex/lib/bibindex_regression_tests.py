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

from invenio.testutils import InvenioTestCase
import os
import re
from datetime import timedelta
from time import sleep

from invenio.bibindex_engine import WordTable, \
    VirtualIndexTable, \
    get_word_tables, \
    find_affected_records_for_index, \
    get_recIDs_by_date_authority, \
    get_recIDs_by_date_bibliographic, \
    create_range_list, \
    beautify_range_list, \
    get_last_updated_all_indexes, \
    re_prefix
from invenio.bibindex_engine_utils import get_index_id_from_index_name, \
    get_index_tags, \
    get_all_indexes, \
    make_prefix, \
    get_marc_tag_indexes, \
    get_nonmarc_tag_indexes, \
    get_all_indexes
from invenio.bibindex_engine_config import \
    CFG_BIBINDEX_ADDING_RECORDS_STARTED_STR, \
    CFG_BIBINDEX_INDEX_TABLE_TYPE, \
    CFG_BIBINDEX_UPDATE_MESSAGE
from invenio.bibtask import task_low_level_submission
from invenio.config import CFG_BINDIR, CFG_LOGDIR
from invenio.testutils import make_test_suite, run_test_suite, nottest
from invenio.dbquery import run_sql, deserialize_via_marshal
from invenio.intbitset import intbitset
from invenio.search_engine import get_record
from invenio.search_engine_utils import get_fieldvalues
from invenio.bibauthority_engine import get_index_strings_by_control_no, \
    get_control_nos_from_recID
from invenio.bibindex_engine_utils import run_sql_drop_silently

from invenio.bibupload import bibupload, xml_marc_to_records
from invenio.bibupload_regression_tests import wipe_out_record_from_all_tables
from invenio.bibrecord import record_get_field_value
from invenio.bibsort_engine import get_max_recid
from invenio.bibtask import task_log_path

from invenio.dbquery import get_table_update_time
from invenio.search_engine import get_index_stemming_language as gis

def reindex_for_type_with_bibsched(index_name, force_all=False, *other_options):
    """Runs bibindex for the specified index and returns the task_id.
       @param index_name: name of the index to reindex
       @param force_all: if it's True function will reindex all records
       not just affected ones
    """
    program = os.path.join(CFG_BINDIR, 'bibindex')
    args = ['bibindex', 'bibindex_regression_tests', '-w', index_name, '-u', 'admin']
    args.extend(other_options)
    if force_all:
        args.append("--force")
    task_id = task_low_level_submission(*args)
    COMMAND = "%s %s > /dev/null 2> /dev/null" % (program, str(task_id))
    os.system(COMMAND)
    return task_id


def prepare_for_index_update(index_id, parameters={}):
    """ Prepares SQL query for an update of an index in the idxINDEX table.
        Takes into account remove_stopwords, remove_html_markup, remove_latex_markup,
        tokenizer and last_updated as parameters to change.
        remove_html_markup and remove_latex_markup accepts these values:
                                        '' to leave it unchanged
                                        'Yes' to change it to 'Yes'
                                        'No' to change it to 'No'.
        For remove_stopwords instead of 'Yes' one must give the name of the file (for example: 'stopwords.kb')
        from CFG_ETCDIR/bibrank/ directory pointing at stopwords knowledge base.
        For tokenizer please specify the name of the tokenizer.
        For last_updated provide a date in format: '2013-01-31 00:00:00'
        @param index_id: id of the index to change
        @param parameters: dict with names of parameters and their new values
    """
    if len(parameters) == 0:
        return ''

    parameter_set = False
    query_update = "UPDATE idxINDEX SET "
    for key in parameters:
        if parameters[key] is not None:
            query_update += parameter_set and ", " or ""
            query_update += "%s='%s'" % (key, parameters[key])
            parameter_set = True
    query_update += " WHERE id=%s" % index_id
    return query_update


@nottest
def reindex_word_tables_into_testtables(index_name, recids = None, prefix = 'test_', parameters={}, turn_off_virtual_indexes=True):
    """Function for setting up a test enviroment. Reindexes an index with a given name to a
       new temporary table with a given prefix. During the reindexing it changes some parameters
       of chosen index. It's useful for conducting tests concerning the reindexing process.
       Reindexes only idxWORDxxx tables.
       @param index_name: name of the index we want to reindex
       @param recids: None means reindexing all records, set ids of the records to update only part of them
       @param prefix: prefix for the new tabels, empty prefix means indexing original tables
       @param parameters: dict with parameters and their new values; for more specific
       description take a look at  'prepare_for_index_update' function.
       @param turn_off_virtual_indexes: if True only specific index will be reindexed
       without connected virtual indexes
    """
    index_id = get_index_id_from_index_name(index_name)
    query_update = prepare_for_index_update(index_id, parameters)
    last_updated = run_sql("""SELECT last_updated FROM idxINDEX WHERE id=%s""" % index_id)[0][0]

    test_tablename = "%sidxWORD%02d" % (prefix, index_id)
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

    if not prefix == "":
        run_sql_drop_silently(query_drop_forward_index_table)
        run_sql_drop_silently(query_drop_reversed_index_table)
        run_sql(query_create_forward_index_table)
        run_sql(query_create_reversed_index_table)
    if query_update:
        run_sql(query_update)

    wordTable = WordTable(index_name=index_name,
                          table_prefix=prefix,
                          table_type = CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"],
                          wash_index_terms=50)
    if turn_off_virtual_indexes:
        wordTable.turn_off_virtual_indexes()
    if recids:
        wordTable.add_recIDs(recids, 10000)
    else:
        recIDs_for_index = find_affected_records_for_index([index_name],
                                                 [[1, get_max_recid()]],
                                                                   True)
        bib_recIDs = get_recIDs_by_date_bibliographic([], index_name)
        auth_recIDs = get_recIDs_by_date_authority([], index_name)
        final_recIDs = bib_recIDs | auth_recIDs
        final_recIDs = set(final_recIDs) & set(recIDs_for_index[index_name])
        final_recIDs = beautify_range_list(create_range_list(list(final_recIDs)))
        wordTable.add_recIDs(final_recIDs, 10000)
    return last_updated


@nottest
def remove_reindexed_word_testtables(index_name, prefix = 'test_'):
    """
        Removes <<prefix>>idxWORDxxx tables created during tests.
        @param index_name: name of the index
        @param prefix: prefix for the tables
    """
    index_id = get_index_id_from_index_name(index_name)
    test_tablename = "%sidxWORD%02d" % (prefix, index_id)
    query_drop_forward_index_table = """DROP TABLE IF EXISTS %sF""" % test_tablename
    query_drop_reversed_index_table = """DROP TABLE IF EXISTS %sR""" % test_tablename
    run_sql(query_drop_forward_index_table)
    run_sql(query_drop_reversed_index_table)


def is_part_of(container, content):
    """checks if content is a part of container"""
    ctr = set(container)
    cont = set(content)
    return cont.issubset(ctr)


class BibIndexRemoveStopwordsTest(InvenioTestCase):
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
            self.last_updated = reindex_word_tables_into_testtables(
                'title',
                parameters = {'remove_stopwords':'stopwords.kb',
                              'last_updated':'0000-00-00 00:00:00'})
            self.reindexed = True

    @classmethod
    def tearDown(self):
        """cleaning up"""
        self.test_counter += 1
        if self.test_counter == 4:
            remove_reindexed_word_testtables('title')
            reverse_changes = prepare_for_index_update(
                get_index_id_from_index_name('title'),
                parameters = {'remove_stopwords':'No',
                              'last_updated':self.last_updated})
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


class BibIndexRemoveLatexTest(InvenioTestCase):
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
            self.last_updated = reindex_word_tables_into_testtables(
                'abstract',
                parameters = {'remove_latex_markup':'Yes',
                              'last_updated':'0000-00-00 00:00:00'})
            self.reindexed = True

    @classmethod
    def tearDown(self):
        """cleaning up"""
        self.test_counter += 1
        if self.test_counter == 4:
            remove_reindexed_word_testtables('abstract')
            reverse_changes = prepare_for_index_update(
                get_index_id_from_index_name('abstract'),
                parameters = {'remove_latex_markup':'No',
                              'last_updated':self.last_updated})
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


class BibIndexRemoveHtmlTest(InvenioTestCase):
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
            self.last_updated = reindex_word_tables_into_testtables(
                'abstract',
                parameters = {'remove_html_markup':'Yes',
                              'last_updated':'0000-00-00 00:00:00'})
            self.reindexed = True

    @classmethod
    def tearDown(self):
        """cleaning up"""
        self.test_counter += 1
        if self.test_counter == 2:
            remove_reindexed_word_testtables('abstract')
            reverse_changes = prepare_for_index_update(
                get_index_id_from_index_name('abstract'),
                parameters = {'remove_html_markup':'No',
                              'last_updated':self.last_updated})
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


class BibIndexYearIndexTest(InvenioTestCase):
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
            self.last_updated = reindex_word_tables_into_testtables(
                'year',
                parameters = {'last_updated':'0000-00-00 00:00:00'})
            self.reindexed = True


    @classmethod
    def tearDown(self):
        """cleaning up"""
        self.test_counter += 1
        if self.test_counter == 3:
            remove_reindexed_word_testtables('year')
            reverse_changes = prepare_for_index_update(
                get_index_id_from_index_name('year'),
                parameters = {'last_updated':self.last_updated})
            run_sql(reverse_changes)


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



class BibIndexAuthorCountIndexTest(InvenioTestCase):
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
            self.last_updated = reindex_word_tables_into_testtables(
                'authorcount',
                parameters = {'last_updated':'0000-00-00 00:00:00'})
            self.reindexed = True

    @classmethod
    def tearDown(self):
        """cleaning up"""
        self.test_counter += 1
        if self.test_counter == 2:
            remove_reindexed_word_testtables('authorcount')
            reverse_changes = prepare_for_index_update(
                get_index_id_from_index_name('authorcount'),
                parameters = {'last_updated':self.last_updated})
            run_sql(reverse_changes)


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


class BibIndexItemCountIndexTest(InvenioTestCase):
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


class BibIndexFiletypeIndexTest(InvenioTestCase):
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


class BibIndexDOIIndexTest(InvenioTestCase):
    """
       Checks DOI index.
    """

    def test_doi_values_record_127(self):
        """bibindex - tests if record 127 has proper values in DOI index"""
        query = "SELECT termlist FROM idxWORD%02dR where id_bibrec=127" \
                % get_index_id_from_index_name('doi')
        res = run_sql(query)
        self.assertEqual(deserialize_via_marshal(res[0][0]), ['10.1063/1.2737136'])

    def test_doi_values_record_130(self):
        """bibindex - tests if record 130 doesn't have any values indexed"""
        query = "SELECT termlist FROM idxWORD%02dR where id_bibrec=130" \
                % get_index_id_from_index_name('doi')
        res = run_sql(query)
        self.assertEqual(deserialize_via_marshal(res[0][0]), [])

    def test_doi_values_like_63(self):
        """bibindex - tests how many values like ".*63.*" were indexed"""
        query = """SELECT count(*) FROM idxWORD%02dF where term LIKE '%%63%%' """ \
                % get_index_id_from_index_name('doi')
        res = run_sql(query)
        self.assertEqual(res[0][0], 2)

    def test_records_for_doi_value(self):
        """bibindex - tests records for '0255-5476' value"""
        query = """SELECT hitlist FROM idxWORD%02dF where term='0255-5476' """ \
                % get_index_id_from_index_name('doi')
        res = run_sql(query)
        self.assertEqual(res, tuple())

    def test_if_909C4_is_indexed(self):
        """bibindex - checks if values from 909C4 are indexed"""
        query = """SELECT id_bibrec,termlist FROM idxWORD%02dR """ \
                % get_index_id_from_index_name('doi')
        res = run_sql(query)
        self.assertTrue(96 in [id_bibrec for id_bibrec,terms in res if deserialize_via_marshal(terms)])


class BibIndexJournalIndexTest(InvenioTestCase):
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
            self.last_updated = reindex_word_tables_into_testtables(
                'journal',
                parameters = {'last_updated':'0000-00-00 00:00:00'})
            self.reindexed = True

    @classmethod
    def tearDown(self):
        """cleaning up"""
        self.test_counter += 1
        if self.test_counter == 2:
            remove_reindexed_word_testtables('journal')
            reverse_changes = prepare_for_index_update(
                get_index_id_from_index_name('journal'),
                parameters = {'last_updated':self.last_updated})
            run_sql(reverse_changes)


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


class BibIndexCJKTokenizerTitleIndexTest(InvenioTestCase):
    """
       Checks CJK tokenization on title index.
    """
    test_counter = 0
    reindexed = False

    @classmethod
    def setUp(self):
        """reindexation to new table"""
        if not self.reindexed:
            self.last_updated = reindex_word_tables_into_testtables(
                'title',
                parameters = {'tokenizer':'BibIndexCJKTokenizer',
                              'last_updated':'0000-00-00 00:00:00'})
            self.reindexed = True

    @classmethod
    def tearDown(self):
        """cleaning up"""
        self.test_counter += 1
        if self.test_counter == 2:
            remove_reindexed_word_testtables('title')
            reverse_changes = prepare_for_index_update(
                get_index_id_from_index_name('title'),
                parameters = {'tokenizer':'BibIndexDefaultTokenizer',
                              'last_updated':self.last_updated})
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


class BibIndexAuthorityRecordTest(InvenioTestCase):
    """Test if BibIndex correctly knows when to update the index for a
    bibliographic record if it is dependent upon an authority record changed
    within the given date range"""

    def test_authority_record_recently_updated(self):
        """bibindex - reindexing after recently changed authority record"""

        authRecID = 118
        index_name = 'author'
        table = "idxWORD%02dF" % get_index_id_from_index_name(index_name)
        reindex_for_type_with_bibsched(index_name)
        run_sql("UPDATE bibrec SET modification_date = now() WHERE id = %s", (authRecID,))
        # run bibindex again
        task_id = reindex_for_type_with_bibsched(index_name, force_all=True)
        filename = task_log_path(task_id, 'log')
        _file = open(filename)
        text = _file.read() # small file
        _file.close()
        self.assertTrue(text.find(CFG_BIBINDEX_UPDATE_MESSAGE) >= 0)
        adding_records_text = CFG_BIBINDEX_ADDING_RECORDS_STARTED_STR[:CFG_BIBINDEX_ADDING_RECORDS_STARTED_STR.find("#")] % table
        self.assertTrue(text.find(adding_records_text) >= 0)

    def test_authority_record_enriched_index(self):
        """bibindex - test whether reverse index for bibliographic record
        contains words from referenced authority records"""
        bibRecID = 9
        authority_string = 'jonathan'
        index_name = 'author'
        table = "idxWORD%02dR" % get_index_id_from_index_name(index_name)

        reindex_for_type_with_bibsched(index_name, force_all=True)
        self.assertTrue(
            authority_string in deserialize_via_marshal(
                run_sql("SELECT termlist FROM %s WHERE id_bibrec = %s" % (table, bibRecID))[0][0]
            )
        )

    def test_subject_authority_record_content(self):
        """bibindex - test content of auth. record"""
        bibRecID = 125
        t1 = 'colorature'
        t2 = 'embellishment'
        table = "idxWORD%02dR" % get_index_id_from_index_name("authoritysubject")
        res = deserialize_via_marshal(run_sql("""SELECT termlist
                                                 FROM %s WHERE id_bibrec=%s
                                              """ % (table, bibRecID))[0][0])
        self.assertTrue(t1 in res)
        self.assertTrue(t2 in res)

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


def insert_record_one_and_second_revision():
    """Inserts test record no. 1 and a second revision for that record"""

    rev1 = """<record>
              <controlfield tag="001">123456789</controlfield>
              <controlfield tag="005">20110101000000.0</controlfield>
              <datafield tag ="100" ind1=" " ind2=" ">
                <subfield code="a">Close, John</subfield>
                <subfield code="u">DESY</subfield>
              </datafield>
              <datafield tag="245" ind1=" " ind2=" ">
                <subfield code="a">Particles world</subfield>
              </datafield>
            </record>"""
    rev1_final = rev1.replace('<controlfield tag="001">123456789</controlfield>','')
    rev1_final = rev1_final.replace('<controlfield tag="005">20110101000000.0</controlfield>','')

    rev2 = rev1.replace('<subfield code="a">Close, John</subfield>', '<subfield code="a">Dawkins, Richard</subfield>')
    rev2 = rev2.replace('Particles world', 'Particles universe')

    rec1 = xml_marc_to_records(rev1_final)
    res = bibupload(rec1[0], opt_mode='insert')
    _id = res[1]
    rec = get_record(_id)
    _rev = record_get_field_value(rec, '005', '', '')

    #need to index for the first time
    indexes = get_all_indexes(virtual=False)
    for index_name in indexes:
        wordTable = WordTable(index_name=index_name,
                              table_type = CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"],
                              wash_index_terms=50)
        wordTable.add_recIDs([[_id, _id]], 10000)

    #upload the second revision, but don't index
    rev2_final = rev2.replace('123456789', str(_id))
    rev2_final = rev2_final.replace('20110101000000.0', _rev)
    rec2 = xml_marc_to_records(rev2_final)
    res = bibupload(rec2[0], opt_mode='correct')

    return _id


def insert_record_two_and_second_revision():
    """Inserts test record no. 2 and a revision for that record"""

    rev1 = """<record>
              <controlfield tag="001">123456789</controlfield>
              <controlfield tag="005">20110101000000.0</controlfield>
              <datafield tag ="100" ind1=" " ind2=" ">
                <subfield code="a">Locke, John</subfield>
                <subfield code="u">UNITRA</subfield>
              </datafield>
              <datafield tag="245" ind1=" " ind2=" ">
                <subfield code="a">Collision course</subfield>
              </datafield>
            </record>"""
    rev1_final = rev1.replace('<controlfield tag="001">123456789</controlfield>','')
    rev1_final = rev1_final.replace('<controlfield tag="005">20110101000000.0</controlfield>','')

    rev2 = rev1.replace('Collision course', 'Course of collision')

    rec1 = xml_marc_to_records(rev1_final)
    res = bibupload(rec1[0], opt_mode='insert')
    id_bibrec = res[1]
    rec = get_record(id_bibrec)
    _rev = record_get_field_value(rec, '005', '', '')

    #need to index for the first time
    indexes = get_all_indexes(virtual=False)
    for index_name in indexes:
        wordTable = WordTable(index_name=index_name,
                              table_type = CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"],
                              wash_index_terms=50)
        wordTable.add_recIDs([[id_bibrec, id_bibrec]], 10000)

    #upload the second revision, but don't index
    rev2_final = rev2.replace('123456789', str(id_bibrec))
    rev2_final = rev2_final.replace('20110101000000.0', _rev)
    rec2 = xml_marc_to_records(rev2_final)
    res = bibupload(rec2[0], opt_mode='correct')

    return id_bibrec


def create_index_tables(index_id):
    query_create = """CREATE TABLE IF NOT EXISTS idxWORD%02dF (
                      id mediumint(9) unsigned NOT NULL auto_increment,
                      term varchar(50) default NULL,
                      hitlist longblob,
                      PRIMARY KEY  (id),
                      UNIQUE KEY term (term)
                    ) ENGINE=MyISAM"""

    query_create_r = """CREATE TABLE IF NOT EXISTS idxWORD%02dR (
                        id_bibrec mediumint(9) unsigned NOT NULL,
                        termlist longblob,
                        type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
                        PRIMARY KEY (id_bibrec,type)
                      ) ENGINE=MyISAM"""

    query_create_q = """CREATE TABLE IF NOT EXISTS idxWORD%02dQ (
                        id mediumint(10) unsigned NOT NULL auto_increment,
                        runtime datetime NOT NULL default '0000-00-00 00:00:00',
                        id_bibrec_low mediumint(9) unsigned NOT NULL,
                        id_bibrec_high mediumint(9) unsigned NOT NULL,
                        index_name varchar(50) NOT NULL default '',
                        mode varchar(50) NOT NULL default 'update',
                        PRIMARY KEY (id),
                        INDEX (index_name),
                        INDEX (runtime)
                     ) ENGINE=MyISAM;"""

    run_sql(query_create % index_id)
    run_sql(query_create_r % index_id)
    run_sql(query_create_q % index_id)


def drop_index_tables(index_id):
    query_drop = """DROP TABLE IF EXISTS idxWORD%02d%s"""
    run_sql(query_drop % (index_id, "F"))
    run_sql(query_drop % (index_id, "R"))
    run_sql(query_drop % (index_id, "Q"))


def create_virtual_index(index_id, dependent_indexes):
    """creates new virtual index and binds it to specific dependent indexes"""
    index_name = 'testindex'
    query = """INSERT INTO idxINDEX (id, name, tokenizer) VALUES (%s, '%s', 'BibIndexDefaultTokenizer')"""
    run_sql(query % (index_id, index_name))
    query = """INSERT INTO idxINDEX_idxINDEX VALUES (%s, %s)"""
    for index in dependent_indexes:
        run_sql(query % (index_id, get_index_id_from_index_name(index)))
    create_index_tables(index_id)
    return index_name


def remove_virtual_index(index_id):
    """removes tables and other traces after virtual index"""
    drop_index_tables(index_id)
    query = """DELETE FROM idxINDEX WHERE id=%s""" % index_id
    run_sql(query)
    query = """DELETE FROM idxINDEX_idxINDEX WHERE id_virtual=%s"""
    run_sql(query % index_id)


class BibIndexFindingAffectedIndexes(InvenioTestCase):
    """
    Checks if function 'find_affected_records_for_index'
    works correctly.
    """

    counter = 0
    indexes = ['global', 'fulltext', 'caption', 'journal', 'miscellaneous', 'reportnumber', 'year']

    @classmethod
    def setUp(self):
        if self.counter == 0:
            self.last_updated = dict(get_last_updated_all_indexes())
            res = run_sql("SELECT job_date FROM hstRECORD WHERE id_bibrec=10 AND affected_fields<>''")
            self.hst_date = res[0][0]
            date_to_set = self.hst_date - timedelta(seconds=1)
            for index in self.indexes:
                run_sql("""UPDATE idxINDEX SET last_updated=%s
                           WHERE name=%s""", (str(date_to_set), index))

    @classmethod
    def tearDown(self):
        self.counter += 1
        if self.counter >= 8:
            for index in self.indexes:
                run_sql("""UPDATE idxINDEX SET last_updated=%s
                           WHERE name=%s""", (self.last_updated[index], index))

    def test_find_proper_indexes(self):
        """bibindex - checks if affected indexes are found correctly"""
        records_for_indexes = find_affected_records_for_index(get_all_indexes(virtual=False),
                                                              [[1,20]])
        self.assertEqual(sorted(['miscellaneous', 'fulltext', 'caption', 'journal', 'reportnumber', 'year']),
                         sorted(records_for_indexes.keys()))

    def test_find_proper_recrods_for_miscellaneous_index(self):
        """bibindex - checks if affected recids are found correctly for miscellaneous index"""
        records_for_indexes = find_affected_records_for_index(get_all_indexes(virtual=False),
                                                              [[1,20]])
        self.assertEqual(records_for_indexes['miscellaneous'], [10,12])

    def test_find_proper_records_for_year_index(self):
        """bibindex - checks if affected recids are found correctly for year index"""
        records_for_indexes = find_affected_records_for_index(get_all_indexes(virtual=False),
                                                              [[1,20]])
        self.assertEqual(records_for_indexes['year'], [10,12])

    def test_find_proper_records_for_caption_index(self):
        """bibindex - checks if affected recids are found correctly for caption index"""
        records_for_indexes = find_affected_records_for_index(get_all_indexes(virtual=False),
                                                              [[1,100]])
        self.assertEqual(records_for_indexes['caption'], [10,12, 55, 98])

    def test_find_proper_records_for_journal_index(self):
        """bibindex - checks if affected recids are found correctly for journal index"""
        records_for_indexes = find_affected_records_for_index(get_all_indexes(virtual=False),
                                                              [[1,100]])
        self.assertEqual(records_for_indexes['journal'], [10])

    def test_find_proper_records_specified_only_year(self):
        """bibindex - checks if affected recids are found correctly for year index if we specify only year index as input"""
        records_for_indexes = find_affected_records_for_index(["year"], [[1, 100]])
        self.assertEqual(records_for_indexes["year"], [10, 12, 55])

    def test_find_proper_records_force_all(self):
        """bibindex - checks if all recids will be assigned to all specified indexes"""
        records_for_indexes = find_affected_records_for_index(["year", "title"], [[10, 15]], True)
        self.assertEqual(records_for_indexes["year"], records_for_indexes["title"])
        self.assertEqual(records_for_indexes["year"], [10, 11, 12, 13, 14, 15])

    def test_find_proper_records_nothing_for_title_index(self):
        """bibindex - checks if nothing was found for title index in range of records: 1 - 20"""
        records_for_indexes = find_affected_records_for_index(["title"], [[1, 20]])
        self.assertRaises(KeyError, lambda :records_for_indexes["title"])




class BibIndexIndexingAffectedIndexes(InvenioTestCase):

    started = False
    records = []
    counter = 0

    @classmethod
    def setUp(self):
        self.counter += 1
        if not self.started:
            self.records.append(insert_record_one_and_second_revision())
            self.records.append(insert_record_two_and_second_revision())
            records_for_indexes = find_affected_records_for_index(get_all_indexes(virtual=False),
                                                                  [self.records])
            for index_name in records_for_indexes.keys():
                wordTable = WordTable(index_name=index_name,
                                      table_type = CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"],
                                      wash_index_terms=50)
                wordTable.add_recIDs([self.records], 10000)
            vit = VirtualIndexTable('global',
                                    CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"])
            vit.run_update()
            self.started = True

    @classmethod
    def tearDown(self):
        if self.counter == 3:
            for rec in self.records:
                wipe_out_record_from_all_tables(rec)
            indexes = get_all_indexes(virtual=False)
            for index_name in indexes:
                wordTable = WordTable(index_name=index_name,
                                      table_type = CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"],
                                      wash_index_terms=50)
                wordTable.del_recIDs([self.records])
            vit = VirtualIndexTable('global',
                                    CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"])
            vit.run_update()


    def test_proper_content_in_title_index(self):
        """bibindex - checks reindexation of title index for test records.."""
        index_id = get_index_id_from_index_name('title')
        query = """SELECT termlist FROM idxWORD%02dR WHERE id_bibrec IN (""" % (index_id,)
        query = query + ", ".join(map(str, self.records)) + ")"
        resp = run_sql(query)
        affiliation_rec1 = deserialize_via_marshal(resp[0][0])
        affiliation_rec2 = deserialize_via_marshal(resp[1][0])
        self.assertEqual(['univers', 'particl'], affiliation_rec1)
        self.assertEqual(['of', 'cours', 'collis'], affiliation_rec2)


    def test_proper_content_in_author_index(self):
        """bibindex - checks reindexation of author index for test records.."""
        index_id = get_index_id_from_index_name('author')
        query = """SELECT termlist FROM idxWORD%02dR WHERE id_bibrec IN (""" % (index_id,)
        query = query + ", ".join(map(str, self.records)) + ")"
        resp = run_sql(query)
        author_rec1 = deserialize_via_marshal(resp[0][0])
        author_rec2 = deserialize_via_marshal(resp[1][0])
        self.assertEqual(['dawkins', 'richard', ], author_rec1)
        self.assertEqual(['john', 'locke'], author_rec2)


    def test_proper_content_in_global_index(self):
        """bibindex - checks reindexation of global index for test records.."""
        index_id = get_index_id_from_index_name('global')
        query = """SELECT termlist FROM idxWORD%02dR WHERE id_bibrec IN (""" % (index_id,)
        query = query + ", ".join(map(str, self.records)) + ")"
        resp = run_sql(query)
        global_rec1 = deserialize_via_marshal(resp[0][0])
        global_rec2 = deserialize_via_marshal(resp[1][0])
        misc_prefix = make_prefix("miscellaneous")
        title_prefix = make_prefix("title")
        self.assertEqual(True, misc_prefix + 'dawkin' in global_rec1)
        self.assertEqual(False, misc_prefix + 'close' in global_rec1)
        self.assertEqual(True, title_prefix + 'univers' in global_rec1)
        self.assertEqual(True, misc_prefix + 'john' in global_rec2)
        self.assertEqual(False, misc_prefix + 'john' in global_rec1)


class BibIndexFindingIndexesForTags(InvenioTestCase):
    """ Tests function 'get_marc_tag_indexes' """

    def test_fulltext_tag_virtual_indexes_on(self):
        """bibindex - checks if 'get_marc_tag_indexes' for tag 8564_u will find only 'fulltext' index"""
        self.assertEqual(('fulltext',), zip(*get_marc_tag_indexes('8564_u'))[1])

    def test_title_tag_virtual_indexes_on(self):
        """bibindex - checks if 'get_marc_tag_indexes' for tag 245__% will find also 'global' index"""
        self.assertEqual(('title', 'exacttitle', 'global'), zip(*get_marc_tag_indexes('245__%'))[1])

    def test_title_tag_virtual_indexes_off(self):
        """bibindex - checks if 'get_marc_tag_indexes' for tag 245__% wont find 'global' index (with virtual=False)"""
        self.assertEqual(('title', 'exacttitle'), zip(*get_marc_tag_indexes('245__%', virtual=False))[1])

    def test_author_tag_virtual_indexes_on(self):
        """bibindex - checks 'get_marc_tag_indexes' for tag '100'"""
        self.assertEqual(('author', 'affiliation', 'exactauthor', 'firstauthor',
                          'exactfirstauthor', 'authorcount', 'authorityauthor',
                          'miscellaneous', 'global'),
                         zip(*get_marc_tag_indexes('100'))[1])

    def test_author_exact_tag_virtual_indexes_off(self):
        """bibindex - checks 'get_marc_tag_indexes' for tag '100__a'"""
        self.assertEqual(('author', 'exactauthor', 'firstauthor',
                          'exactfirstauthor', 'authorcount',
                          'authorityauthor', 'miscellaneous'),
                         zip(*get_marc_tag_indexes('100__a', virtual=False))[1])

    def test_wide_tag_virtual_indexes_off(self):
        """bibindex - checks 'get_marc_tag_indexes' for tag like '86%'"""
        self.assertEqual(('miscellaneous',), zip(*get_marc_tag_indexes('86%', virtual=False))[1])

    def test_909_tags_in_misc_index(self):
        """bibindex - checks connection between misc index and tags: 909C1%, 909C4%"""
        self.assertEqual(('miscellaneous',), zip(*get_marc_tag_indexes('909C1%', virtual=False))[1])
        self.assertEqual('miscellaneous' in zip(*get_marc_tag_indexes('909C4%', virtual=False))[1], False)

    def test_year_tag_virtual_indexes_on(self):
        """bibindex - checks 'get_marc_tag_indexes' for tag 909C0y"""
        self.assertEqual(('year', 'global'), zip(*get_marc_tag_indexes('909C0y'))[1])

    def test_wide_tag_authority_index_virtual_indexes_off(self):
        """bibindex - checks 'get_marc_tag_indexes' for tag like '15%'"""
        self.assertEqual(('authoritysubject', 'miscellaneous'), zip(*get_marc_tag_indexes('15%',virtual=False))[1])

    def test_nonmarc_tag_title_additional_virtual_indexes_on(self):
        """bibindex - checks 'get_nonmarc_tag_indexes' for tag 'title_additional'"""
        self.assertEqual(('title', 'exacttitle', 'global'),
                         zip(*get_nonmarc_tag_indexes('title_additional'))[1])

    def test_nonmarc_tag_isbn_virtual_indexes_off(self):
        """bibindex - checks 'get_nonmarc_tag_indexes' for tag 'isbn'"""
        self.assertEqual(('miscellaneous', ),
                        zip(*get_nonmarc_tag_indexes('isbn', virtual=False))[1])

    def test_nonmarc_tag_report_number_virtual_indexes_on(self):
        """bibindex - checks 'get_nonmarc_tag_indexes' for tag 'report_number.report_number'"""
        self.assertEqual(('reportnumber', 'global' ),
                        zip(*get_nonmarc_tag_indexes('report_number.report_number'))[1])

    def test_nonmarc_tag_that_doesnt_exist(self):
        """bibindex - checks 'get_nonmarc_tag_indexes' for MARC tag"""
        self.assertEqual(tuple(),
                         get_nonmarc_tag_indexes('8564_u'))


class BibIndexFindingTagsForIndexes(InvenioTestCase):
    """ Tests function 'get_index_tags' """


    def test_tags_for_author_index(self):
        """bibindex - checks if 'get_index_tags' finds proper marc tag values for 'author' index """
        self.assertEqual(get_index_tags('author'), ['100__a', '700__a'])

    def test_tags_for_global_index_virtual_indexes_off(self):
        """bibindex - checks if 'get_index_tags' finds proper marc tag values for 'global' index """
        self.assertEqual(get_index_tags('global', virtual=False),[])

    def test_tags_for_global_index_virtual_indexes_on(self):
        """bibindex - checks if 'get_index_tags' finds proper marc tag values for 'global' index """
        tags = get_index_tags('global')
        self.assertEqual('86%' in tags, True)
        self.assertEqual('100__a' in tags, True)
        self.assertEqual('245__%' in tags, True)

    def test_tags_for_authority_author(self):
        """bibindex - checks if 'get_index_tags' finds marc tag values for authority author"""
        tags = get_index_tags('authorityauthor')
        self.assertEqual(tags, ['100__a', '500__a', '400__a'])

    def test_nonmarc_tag_values_for_title(self):
        """bibindex - checks if 'get_index_tags' finds proper nonmarc/recjson tag values for title index"""
        tags = get_index_tags('title', tagtype='nonmarc')
        self.assertEqual(tags , ['title', 'title_additional'])

    def test_nonmarc_tag_values_for_authorcount(self):
        """bibindex - checks if 'get_index_tags' finds proper nonmarc/recjson tag values for authorcount index"""
        tags = get_index_tags('authorcount', tagtype='nonmarc')
        self.assertEqual(tags, ['authors[0].full_name', 'contributor.full_name'])

    def test_nonmarc_tag_values_for_keyword(self):
        """bibindex - checks if 'get_index_tags' finds proper nonmarc/recjson tag values for keyword index"""
        tags = get_index_tags('keyword', tagtype='nonmarc')
        self.assertEqual(tags, ['keywords.term'])

    def test_nonmarc_tag_values_for_year(self):
        """bibindex - checks if 'get_index_tags' finds proper nonmarc/recjson tag values for year index"""
        tags = get_index_tags('year', tagtype='nonmarc')
        self.assertEqual(tags, ['year'])

    def test_nonmarc_tag_values_for_misc_inside_global(self):
        """bibindex - checks if nonmarc/recjson tag values from misc index are also inside global index"""
        tags_misc = get_index_tags('miscellaneous', tagtype='nonmarc')
        tags_global = get_index_tags('global', tagtype='nonmarc')
        self.assertEqual(is_part_of(tags_global, tags_misc), True)

    def test_nonmarc_tag_values_for_title_inside_global(self):
        """bibindex - checks if nonmarc/recjson tag values from title index are also inside global index"""
        tags_title = get_index_tags('title', tagtype='nonmarc')
        tags_global = get_index_tags('global', tagtype='nonmarc')
        self.assertEqual(is_part_of(tags_global, tags_title), True)


class BibIndexGlobalIndexContentTest(InvenioTestCase):
    """ Tests if virtual global index is correctly indexed"""

    def test_title_index_compatibility_reversed_table(self):
        """bibindex - checks if the same words are in title and global index, reversed table"""
        global_id = get_index_id_from_index_name('global')
        title_id = get_index_id_from_index_name('title')
        prefix = make_prefix("title")
        for rec in range(1, 4):
            query = """SELECT termlist FROM idxWORD%02dR WHERE id_bibrec=%s""" % (title_id, rec)
            res = run_sql(query)
            termlist_title = deserialize_via_marshal(res[0][0])
            termlist_title = [prefix + item for item in termlist_title]
            query = """SELECT termlist FROM idxWORD%02dR WHERE id_bibrec=%s""" % (global_id, rec)
            glob = run_sql(query)
            termlist_global = deserialize_via_marshal(glob[0][0])
            self.assertEqual(is_part_of(termlist_global, termlist_title), True)

    def test_abstract_index_compatibility_reversed_table(self):
        """bibindex - checks if the same words are in abstract and global index, reversed table"""
        global_id = get_index_id_from_index_name('global')
        abstract_id = get_index_id_from_index_name('abstract')
        prefix = make_prefix("abstract")
        for rec in range(6, 9):
            query = """SELECT termlist FROM idxWORD%02dR WHERE id_bibrec=%s""" % (abstract_id, rec)
            res = run_sql(query)
            termlist_abstract = deserialize_via_marshal(res[0][0])
            termlist_abstract = [prefix + item for item in termlist_abstract]
            query = """SELECT termlist FROM idxWORD%02dR WHERE id_bibrec=%s""" % (global_id, rec)
            glob = run_sql(query)
            termlist_global = deserialize_via_marshal(glob[0][0])
            self.assertEqual(is_part_of(termlist_global, termlist_abstract), True)

    def test_misc_index_compatibility_reversed_table(self):
        """bibindex - checks if the same words are in misc and global index, reversed table"""
        global_id = get_index_id_from_index_name('global')
        misc_id = get_index_id_from_index_name('miscellaneous')
        prefix = make_prefix("miscellaneous")
        for rec in range(10, 14):
            query = """SELECT termlist FROM idxWORD%02dR WHERE id_bibrec=%s""" % (misc_id, rec)
            res = run_sql(query)
            termlist_misc = deserialize_via_marshal(res[0][0])
            termlist_misc = [prefix + item for item in termlist_misc]
            query = """SELECT termlist FROM idxWORD%02dR WHERE id_bibrec=%s""" % (global_id, rec)
            glob = run_sql(query)
            termlist_global = deserialize_via_marshal(glob[0][0])
            self.assertEqual(is_part_of(termlist_global, termlist_misc), True)

    def test_journal_index_compatibility_forward_table(self):
        """bibindex - checks if the same words are in journal and global index, forward table"""
        global_id = get_index_id_from_index_name('global')
        journal_id = get_index_id_from_index_name('journal')
        query = """SELECT term FROM idxWORD%02dF""" % journal_id
        res = zip(*run_sql(query))[0]
        query = """SELECT term FROM idxWORD%02dF""" % global_id
        glob = zip(*run_sql(query))[0]
        self.assertEqual(is_part_of(glob, res), True)

    def test_keyword_index_compatibility_forward_table(self):
        """bibindex - checks if the same pairs are in keyword and global index, forward table"""
        global_id = get_index_id_from_index_name('global')
        keyword_id = get_index_id_from_index_name('keyword')
        query = """SELECT term FROM idxPAIR%02dF""" % keyword_id
        res = zip(*run_sql(query))[0]
        query = """SELECT term FROM idxPAIR%02dF""" % global_id
        glob = zip(*run_sql(query))[0]
        self.assertEqual(is_part_of(glob, res), True)

    def test_affiliation_index_compatibility_forward_table(self):
        """bibindex - checks if the same phrases are in affiliation and global index, forward table"""
        global_id = get_index_id_from_index_name('global')
        affiliation_id = get_index_id_from_index_name('affiliation')
        query = """SELECT term FROM idxPHRASE%02dF""" % affiliation_id
        res = zip(*run_sql(query))[0]
        query = """SELECT term FROM idxPHRASE%02dF""" % global_id
        glob = zip(*run_sql(query))[0]
        self.assertEqual(is_part_of(glob, res), True)


class BibIndexVirtualIndexAlsoChangesTest(InvenioTestCase):
    """ Tests if virtual index changes after changes in dependent index"""

    counter = 0
    indexes = ["title"]
    _id = 39
    new_index_name = ""

    @classmethod
    def prepare_virtual_index(self):
        """creates new virtual index and binds it to specific normal index"""
        self.new_index_name = create_virtual_index(self._id, self.indexes)
        for index_name in self.indexes:
            wordTable = WordTable(index_name=index_name,
                                  table_type=CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"],
                                  wash_index_terms=50)
            wordTable.add_recIDs([[1, 10]], 1000)
        vit = VirtualIndexTable(self.new_index_name,
                                CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"])
        vit.run_update()
        vit = VirtualIndexTable('global',
                                CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"])
        vit.run_update()

    @classmethod
    def reindex_virtual_index(self, special_tokenizer=False):
        """reindexes virtual and dependent indexes with different tokenizer"""
        def tokenize_for_words(phrase):
            return phrase.split(" ")

        for index_name in self.indexes:
            wordTable = WordTable(index_name=index_name,
                                  table_type=CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"],
                                  wash_index_terms=50)
            if special_tokenizer == True:
                wordTable.tokenizer.tokenize_for_words = tokenize_for_words
            wordTable.add_recIDs([[1, 10]], 1000)
        vit = VirtualIndexTable(self.new_index_name,
                                CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"])
        vit.run_update()
        vit = VirtualIndexTable('global',
                                CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"])
        vit.run_update()


    @classmethod
    def setUp(self):
        self.counter += 1
        if self.counter == 1:
            self.prepare_virtual_index()
        elif self.counter == 2:
            self.reindex_virtual_index(special_tokenizer=True)

    @classmethod
    def tearDown(self):
        if self.counter == 3:
            self.reindex_virtual_index()
        elif self.counter == 4:
            remove_virtual_index(self._id)

    def test_virtual_index_1_has_10_records(self):
        """bibindex - checks if virtual index was filled with only ten records from title index"""
        query = "SELECT count(*) FROM idxWORD%02dR" % self._id
        self.assertEqual(10, run_sql(query)[0][0])

    def test_virtual_index_2_correct_content_record_1(self):
        """bibindex - after reindexing with different tokenizer virtual index also changes - record 1"""
        query = "SELECT termlist FROM idxWORD%02dR WHERE id_bibrec=%s" % (self._id, 1)
        prefix = make_prefix("title")
        self.assertEqual(prefix + 'Higgs' in deserialize_via_marshal(run_sql(query)[0][0]), True)

    def test_virtual_index_3_correct_content_record_3(self):
        """bibindex - after reindexing with different tokenizer virtual index also changes - record 3"""
        query = "SELECT termlist FROM idxWORD%02dR WHERE id_bibrec=%s" % (self._id, 3)
        prefix = make_prefix("title")
        self.assertEqual([prefix + item for item in ('Conference', 'Biology', 'Molecular', 'European')],
                         deserialize_via_marshal(run_sql(query)[0][0]))

    def test_virtual_index_4_cleaned_up(self):
        """bibindex - after reindexing with normal title tokenizer everything is back to normal"""
        #this is version of test for installation with PyStemmer package
        #without this package word 'biology' is stemmed differently
        query = "SELECT termlist FROM idxWORD%02dR WHERE id_bibrec=%s" % (self._id, 3)
        prefix = make_prefix("title")
        self.assertEqual([prefix + item for item in ('biolog', 'molecular', 'confer', 'european')],
                         deserialize_via_marshal(run_sql(query)[0][0]))


class BibIndexVirtualIndexRemovalTest(InvenioTestCase):

    counter = 0
    indexes = ["authorcount", "journal", "year"]
    _id = 40
    new_index_name = ""

    @classmethod
    def setUp(self):
        self.counter += 1
        if self.counter == 1:
            self.new_index_name = create_virtual_index(self._id, self.indexes)
            wtabs = get_word_tables(self.indexes)
            for index_id, index_name, index_tags in wtabs:
                wordTable = WordTable(index_name=index_name,
                                    fields_to_index=index_tags,
                                    table_type=CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"],
                                    wash_index_terms=50)
                wordTable.add_recIDs([[1, 113]], 1000)
            vit = VirtualIndexTable(self.new_index_name,
                                    CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"])
            vit.run_update()
            #removal part
            vit.remove_dependent_index("authorcount")


    @classmethod
    def tearDown(self):
        remove_virtual_index(self._id)


    def test_authorcount_removal_number_of_items(self):
        """bibindex - checks virtual index after authorcount index removal - number of items"""
        query = """SELECT count(*) FROM idxWORD%02dF"""
        res = run_sql(query % self._id)
        self.assertEqual(220, res[0][0])

    def test_authorcount_removal_common_terms_intact(self):
        """bibindex - checks virtual index after authorcount index removal - common terms"""
        query = """SELECT term FROM idxWORD%02dF WHERE term IN ('10', '2', '4', '7')"""
        res = run_sql(query % self._id)
        self.assertEqual(4, len(res))

    def test_authorcount_removal_no_315_term(self):
        """bibindex - checks virtual index after authorcount index removal - no '315' term in virtual index"""
        query = """SELECT term FROM idxWORD%02dF WHERE term='315'"""
        res = run_sql(query % self._id)
        self.assertEqual(0, len(res))

    def test_authorcount_removal_term_10_hitlist(self):
        """bibindex - checks virtual index after authorcount index removal - hitlist for '10' term"""
        query = """SELECT hitlist FROM idxWORD%02dF WHERE term='10'"""
        res = run_sql(query % self._id)
        self.assertEqual([80, 92], intbitset(res[0][0]).tolist())

    def test_authorcount_removal_term_1985_hitlist(self):
        """bibindex - checks virtual index after authorcount index removal - hitlist for '1985' term"""
        query = """SELECT hitlist FROM idxWORD%02dF WHERE term='1985'"""
        res = run_sql(query % self._id)
        self.assertEqual([16, 18], intbitset(res[0][0]).tolist())

    def test_authorcount_removal_record_16_hitlist(self):
        """bibindex - checks virtual index after authorcount index removal - termlist for record 16"""
        query = """SELECT termlist FROM idxWORD%02dR WHERE id_bibrec=16"""
        res = run_sql(query % self._id)
        terms = deserialize_via_marshal(res[0][0])
        terms = [re.sub(re_prefix, '', term) for term in terms]
        self.assertEqual(['1985'], terms)

    def test_authorcount_removal_record_10_hitlist(self):
        """bibindex - checks virtual index after authorcount index removal - termlist for record 10"""
        query = """SELECT termlist FROM idxWORD%02dR WHERE id_bibrec=10"""
        res = run_sql(query % self._id)
        terms = deserialize_via_marshal(res[0][0])
        terms = [re.sub(re_prefix, '', term) for term in terms]
        self.assertEqual(sorted(['2002', 'Eur. Phys. J., C']), sorted(terms))

    def test_year_removal_number_of_items(self):
        """bibindex - checks virtual index after year removal - number of items"""
        #must be run after: tearDown
        vit = VirtualIndexTable(self.new_index_name,
                                CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"])
        vit.remove_dependent_index("year")
        query = """SELECT count(*) FROM idxWORD%02dF"""
        res = run_sql(query % self._id)
        self.assertEqual(197, res[0][0])

    def test_year_removal_record_18_hitlist(self):
        """bibindex - checks virtual index after year removal - termlist for record 18"""
        #must be run after: tearDown, test_year_removal_number_of_items
        query = """SELECT termlist FROM idxWORD%02dR WHERE id_bibrec=18"""
        res = run_sql(query % self._id)
        terms = deserialize_via_marshal(res[0][0])
        terms = [re.sub(re_prefix, '', term) for term in terms]
        self.assertEqual(sorted(['151', '1985', '1985', '357', '357-362',
                         'Phys. Lett., B',
                         'Phys. Lett., B 151',
                         'Phys. Lett., B 151 (1985) 357',
                         'Phys. Lett., B 151 (1985) 357-362']),
                         sorted(terms))

class BibIndexCLICallTest(InvenioTestCase):
    """Tests if calls to bibindex from CLI (bibsched deamon) are run correctly"""

    def test_correct_message_for_wrong_index_names(self):
        """bibindex - checks if correct message for wrong index appears"""
        index_name = "titlexrg"
        task_id = reindex_for_type_with_bibsched(index_name, force_all=True)
        filename = task_log_path(task_id, 'log')
        fl = open(filename)
        text = fl.read() # small file
        fl.close()
        self.assertTrue(text.find("Specified indexes can't be found.") >= 0)

    def test_correct_message_for_up_to_date_indexes(self):
        """bibindex - checks if correct message for index up to date appears"""
        index_name = "abstract"
        task_id = reindex_for_type_with_bibsched(index_name)
        filename = task_log_path(task_id, 'log')
        fl = open(filename)
        text = fl.read() # small file
        fl.close()
        self.assertTrue(text.find("Selected indexes/recIDs are up to date.") >= 0)


class BibIndexCommonWordsInVirtualIndexTest(InvenioTestCase):
    """Tests if WordTable indexes virtual index correctly in case when
       two or more dependent indexes have common words and we change
       only one of them
    """
    counter = 0
    index_name = 'title'
    prefix = make_prefix("title")

    @classmethod
    def setUp(self):
        self.counter += 1
        if self.counter == 3:
            index_id = get_index_id_from_index_name(self.index_name)
            # tests are too fast for DataCacher timestamp_verifier to notice the difference
            sleep(1)
            query = """UPDATE idxINDEX SET stemming_language='' WHERE id=8"""
            run_sql(query)

            wordTable = WordTable(index_name=self.index_name,
                                  table_type=CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"],
                                  wash_index_terms=50)
            wordTable.add_recIDs([[1, 9]], 1000)
            vit = VirtualIndexTable('global',
                                    CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"])
            vit.run_update()
            wordTable = WordTable(index_name=self.index_name,
                                  table_type=CFG_BIBINDEX_INDEX_TABLE_TYPE["Pairs"],
                                  wash_index_terms=50)
            wordTable.add_recIDs([[6, 9]], 1000)
            vit = VirtualIndexTable('global',
                                    CFG_BIBINDEX_INDEX_TABLE_TYPE["Pairs"])
            vit.run_update()

    def tearDown(self):
        if self.counter == 8:
            index_id = get_index_id_from_index_name(self.index_name)
            # tests are too fast for DataCacher timestamp_verifier to notice the difference
            sleep(1)
            query = """UPDATE idxINDEX SET stemming_language='en' WHERE id=8"""
            run_sql(query)

            wordTable = WordTable(index_name=self.index_name,
                                  table_type=CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"],
                                  wash_index_terms=50)
            wordTable.add_recIDs([[1, 9]], 1000)
            vit = VirtualIndexTable('global',
                                    CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"])
            vit.run_update()
            wordTable = WordTable(index_name=self.index_name,
                                  table_type=CFG_BIBINDEX_INDEX_TABLE_TYPE["Pairs"],
                                  wash_index_terms=50)
            wordTable.add_recIDs([[6, 9]], 1000)
            vit = VirtualIndexTable('global',
                                    CFG_BIBINDEX_INDEX_TABLE_TYPE["Pairs"])
            vit.run_update()

    def test_1_initial_state_of_record_1(self):
        """bibindex - checks if record 1 has proper initial state for word: experiment"""
        query = """SELECT termlist FROM idxWORD08R WHERE id_bibrec=1"""
        terms = deserialize_via_marshal(run_sql(query)[0][0])
        self.assertEqual(terms.count('experi'), 1)
        query = """SELECT termlist FROM idxWORD01R WHERE id_bibrec=1"""
        terms = deserialize_via_marshal(run_sql(query)[0][0])
        terms = [re.sub(re_prefix, '', term) for term in terms]
        self.assertEqual(terms.count('experi'), 2)
        self.assertEqual(terms.count('experiment'), 1)

    def test_2_initial_state_of_record_3(self):
        """bibindex - checks if record 3 has proper initial state for word: biology"""
        query = """SELECT termlist FROM idxWORD08R WHERE id_bibrec=3"""
        terms = deserialize_via_marshal(run_sql(query)[0][0])
        self.assertEqual(terms.count('biolog'), 1)
        self.assertEqual(terms.count('biology'), 0)
        query = """SELECT termlist FROM idxWORD01R WHERE id_bibrec=3"""
        terms = deserialize_via_marshal(run_sql(query)[0][0])
        terms = [re.sub(re_prefix, '', term) for term in terms]
        self.assertEqual(terms.count('biolog'), 2)

    def test_3_experiment_in_record_1(self):
        """bibindex - checks count of 'experiment' and 'experi' words in global virtual index"""
        query = """SELECT termlist FROM idxWORD01R WHERE id_bibrec=1"""
        terms = deserialize_via_marshal(run_sql(query)[0][0])
        terms = [re.sub(re_prefix, '', term) for term in terms]
        self.assertEqual(terms.count('experi'), 1)
        self.assertEqual(terms.count('experiment'), 2)

    def test_4_boson_in_record_1(self):
        """bibindex - checks count of 'boson' - it doesn't change"""
        query = """SELECT termlist FROM idxWORD01R WHERE id_bibrec=1"""
        terms = deserialize_via_marshal(run_sql(query)[0][0])
        terms = [re.sub(re_prefix, '', term) for term in terms]
        self.assertEqual(terms.count('boson'), 3)

    def test_5_biology_in_record_3(self):
        """bibindex - checks count of 'biology' word in record 3"""
        query = """SELECT termlist FROM idxWORD01R WHERE id_bibrec=3"""
        terms = deserialize_via_marshal(run_sql(query)[0][0])
        terms = [re.sub(re_prefix, '', term) for term in terms]
        self.assertEqual(terms.count('biology'), 2)
        self.assertEqual(terms.count('biolog'), 1)
        query = """SELECT termlist FROM idxWORD08R WHERE id_bibrec=3"""
        terms = deserialize_via_marshal(run_sql(query)[0][0])
        self.assertEqual(terms.count('biolog'), 0)

    def test_6_supersymmetry_in_record_9(self):
        """bibindex - checks count of 'supersymmetry' word in record 9"""
        query = """SELECT termlist FROM idxWORD01R WHERE id_bibrec=9"""
        terms = deserialize_via_marshal(run_sql(query)[0][0])
        terms = [re.sub(re_prefix, '', term) for term in terms]
        self.assertEqual(terms.count('supersymmetri'), 0)

    def test_7_biology_in_record_3_forward_table(self):
        """bibindex - checks if 'biolog' word is in forward table"""
        query = """SELECT term FROM idxWORD01F WHERE term='biolog'"""
        res = run_sql(query)
        self.assertEqual('biolog', res[0][0])

    def test_8_nobel_prizewinners_pair_in_record_6(self):
        """bibindex - checks if 'nobel prizewinners' is in virtual index"""
        query = """SELECT termlist FROM idxPAIR08R WHERE id_bibrec=6"""
        terms = deserialize_via_marshal(run_sql(query)[0][0])
        self.assertEqual('nobel prizewinners' in terms, True)
        query = """SELECT termlist FROM idxPAIR01R WHERE id_bibrec=6"""
        terms = deserialize_via_marshal(run_sql(query)[0][0])
        terms = [re.sub(re_prefix, '', term) for term in terms]
        self.assertEqual('nobel prizewinn' in terms, True)
        self.assertEqual('nobel prizewinners' in terms, True)


class BibIndexVirtualIndexQueueTableTest(InvenioTestCase):
    """Tests communication through Queue tables between virtual index and
       dependent indexes"""


    @classmethod
    def index_dependent_index(self, index_name, records_range, table_type):
        """indexes a dependent index for given record range"""
        index_id = get_index_id_from_index_name(index_name)
        wordTable = WordTable(index_name=index_name,
                              table_type=table_type,
                              wash_index_terms=50)
        wordTable.add_recIDs(records_range, 10000)

    @classmethod
    def run_update_for_virtual_index(self, table_type):
        """triggers an update in virtual 'global' index"""
        vit = VirtualIndexTable('global', table_type)
        vit.run_update()

    def test_1_correct_entry_in_queue_for_word_table(self):
        """bibindex - checks correct entry in queue table for words"""
        self.index_dependent_index('title', [[10,14]], CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"])
        query = "SELECT * FROM idxWORD01Q"
        res = run_sql(query)
        self.assertEqual((10, 14), (res[0][2], res[0][3]))
        self.run_update_for_virtual_index(CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"])

    def test_2_correct_entry_in_queue_for_pair_table(self):
        """bibindex - checks correct entry in queue table for pairs"""
        self.index_dependent_index('collection', [[1,5],[20,21]], CFG_BIBINDEX_INDEX_TABLE_TYPE["Pairs"])
        query = "SELECT * FROM idxPAIR01Q ORDER BY runtime,id DESC"
        res = run_sql(query)
        self.assertEqual(2, len(res))
        self.assertEqual((20, 21), (res[0][2], res[0][3]))
        self.assertEqual('update', res[0][5])
        self.run_update_for_virtual_index(CFG_BIBINDEX_INDEX_TABLE_TYPE["Pairs"])

    def test_3_correct_entry_in_queue_for_phrase_table(self):
        """bibindex - checks correct entry in queue table for phrases"""
        self.index_dependent_index('keyword', [[19,19]], CFG_BIBINDEX_INDEX_TABLE_TYPE["Phrases"])
        query = "SELECT * FROM idxPHRASE01Q"
        res = run_sql(query)
        self.assertEqual((19, 19), (res[0][2], res[0][3]))
        self.assertEqual('keyword', res[0][4])
        self.run_update_for_virtual_index(CFG_BIBINDEX_INDEX_TABLE_TYPE["Phrases"])

    def test_4_no_entries_in_queue_table(self):
        """bibindex - checks if virtual index removes entries from queue table after update"""
        query = "SELECT * FROM idxWORD01Q"
        res = run_sql(query)
        empty = tuple()
        self.assertEqual(empty, res)

    def test_5_remove_duplicates_in_queue_table(self):
        """bibindex - checks if duplicates are removed"""
        index_name = 'title'
        table_type = CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"]
        self.index_dependent_index(index_name, [[10,14]], table_type)
        self.index_dependent_index(index_name, [[20,23]], table_type)
        self.index_dependent_index(index_name, [[10,14]], table_type)
        query = """SELECT id_bibrec_low, id_bibrec_high, mode FROM idx%s01Q
                   WHERE index_name='%s' ORDER BY runtime ASC""" % (table_type, index_name)
        entries_before = run_sql(query)
        vit = VirtualIndexTable('global', table_type)
        entries_after = vit.remove_duplicates(entries_before)
        self.assertEqual(len(entries_before), 3)
        self.assertEqual(len(entries_after), 2)
        self.assertTrue(entries_before[1] == entries_after[1])
        self.run_update_for_virtual_index(table_type)


class BibIndexSpecialTagsTest(InvenioTestCase):

    def test_special_tags_for_title(self):
        """bibindex - special tags for title"""
        index_name = 'title'
        wt = WordTable(index_name, CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"])
        wt.tags = ['8564_u']
        wt.special_tags = wt._handle_special_tags()
        self.assertNotEqual(wt.default_tokenizer_function.__self__.__class__.__name__,
                            wt.special_tags['8564_u'].__self__.__class__.__name__)

    def test_special_tags_for_fulltext(self):
        """bibindex - special tags for fulltext"""
        index_name = 'fulltext'
        wt = WordTable(index_name, CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"])
        wt.fields_to_index = ['8564_u']
        wt.special_tags = wt._handle_special_tags()
        self.assertEqual(wt.default_tokenizer_function.__self__.__class__.__name__,
                            wt.special_tags['8564_u'].__self__.__class__.__name__)


class BibIndexFilenameIndexTest(InvenioTestCase):


    def test_common_filename_with_different_extensions(self):
        """bibindex - checks if file name '0105155' will occur only once"""
        index_id = get_index_id_from_index_name('filename')
        query = """SELECT termlist FROM idxWORD%02dR
                   WHERE id_bibrec=12""" % index_id
        res = run_sql(query)
        self.assertEqual(sorted(deserialize_via_marshal(res[0][0])),
                         sorted(['0105155', '0105155.pdf',
                                 '0105155.ps', '0105155.ps.gz']))

    def test_filename_with_extension_present(self):
        """bibindex - checks if file name with extension is found"""
        index_id = get_index_id_from_index_name('filename')
        query = """SELECT termlist FROM idxWORD%02dR
                   WHERE id_bibrec=92""" % index_id
        res = run_sql(query)
        self.assertTrue('0606096.pdf' in deserialize_via_marshal(res[0][0]))

    def test_incorrect_extension(self):
        """bibindex - checks if incorrect filename could not be found"""
        index_id = get_index_id_from_index_name('filename')
        query = """SELECT termlist FROM idxWORD%02dR
                   WHERE id_bibrec=12""" % index_id
        res = run_sql(query)
        self.assertFalse('0105155.gz' in deserialize_via_marshal(res[0][0]))

    def test_filename_in_forward_table(self):
        """bibindex - checks if words are present in forward table"""
        index_id = get_index_id_from_index_name('filename')
        query = """SELECT term FROM idxWORD%02dF
                   WHERE term LIKE '05011%%'""" % index_id
        res = run_sql(query)
        self.assertTrue(len(res) == 2)


TEST_SUITE = make_test_suite(BibIndexRemoveStopwordsTest,
                             BibIndexRemoveLatexTest,
                             BibIndexRemoveHtmlTest,
                             BibIndexYearIndexTest,
                             BibIndexAuthorCountIndexTest,
                             BibIndexItemCountIndexTest,
                             BibIndexFiletypeIndexTest,
                             BibIndexDOIIndexTest,
                             BibIndexJournalIndexTest,
                             BibIndexCJKTokenizerTitleIndexTest,
                             BibIndexAuthorityRecordTest,
                             BibIndexFindingAffectedIndexes,
                             BibIndexIndexingAffectedIndexes,
                             BibIndexFindingIndexesForTags,
                             BibIndexFindingTagsForIndexes,
                             BibIndexGlobalIndexContentTest,
                             BibIndexVirtualIndexAlsoChangesTest,
                             BibIndexVirtualIndexRemovalTest,
                             BibIndexCLICallTest,
                             BibIndexCommonWordsInVirtualIndexTest,
                             BibIndexVirtualIndexQueueTableTest,
                             BibIndexSpecialTagsTest,
                             BibIndexFilenameIndexTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)


