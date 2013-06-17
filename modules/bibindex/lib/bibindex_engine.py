# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013 CERN.
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

"""
BibIndex indexing engine implementation.  See bibindex executable for entry point.
"""

__revision__ = "$Id$"

import re
import sys
import time
import fnmatch


from invenio.config import CFG_SOLR_URL
from invenio.bibindex_engine_config import CFG_MAX_MYSQL_THREADS, \
     CFG_MYSQL_THREAD_TIMEOUT, \
     CFG_CHECK_MYSQL_THREADS, \
     CFG_BIBINDEX_COLUMN_VALUE_SEPARATOR, \
     CFG_BIBINDEX_INDEX_TABLE_TYPE, \
     CFG_BIBINDEX_ADDING_RECORDS_STARTED_STR
from invenio.bibauthority_config import \
     CFG_BIBAUTHORITY_CONTROLLED_FIELDS_BIBLIOGRAPHIC, \
     CFG_BIBAUTHORITY_RECORD_CONTROL_NUMBER_FIELD, \
     CFG_BIBAUTHORITY_BIBINDEX_UPDATE_MESSAGE
from invenio.bibauthority_engine import get_index_strings_by_control_no,\
     get_control_nos_from_recID
from invenio.bibindexadminlib import get_idx_remove_html_markup, \
                                     get_idx_remove_latex_markup, \
                                     get_idx_remove_stopwords
from invenio.bibdocfile import BibRecDocs
from invenio.search_engine import perform_request_search, \
     get_index_stemming_language, \
     get_synonym_terms, \
     search_pattern, \
     search_unit_in_bibrec
from invenio.dbquery import run_sql, DatabaseError, serialize_via_marshal, \
     deserialize_via_marshal, wash_table_column_name
from invenio.bibindex_engine_washer import wash_index_term
from invenio.bibtask import task_init, write_message, get_datetime, \
    task_set_option, task_get_option, task_get_task_param, \
    task_update_progress, task_sleep_now_if_required
from invenio.intbitset import intbitset
from invenio.errorlib import register_exception
from invenio.bibrankadminlib import get_def_name
from invenio.solrutils_bibindex_indexer import solr_commit
from invenio.bibindex_tokenizers.BibIndexJournalTokenizer import \
    CFG_JOURNAL_TAG, \
    CFG_JOURNAL_PUBINFO_STANDARD_FORM, \
    CFG_JOURNAL_PUBINFO_STANDARD_FORM_REGEXP_CHECK
from invenio.bibindex_engine_utils import get_all_index_names_and_column_values, \
    load_tokenizers
from invenio.search_engine_utils import get_fieldvalues



if sys.hexversion < 0x2040000:
    # pylint: disable=W0622
    from sets import Set as set
    # pylint: enable=W0622


## precompile some often-used regexp for speed reasons:
re_subfields = re.compile('\$\$\w')
re_datetime_shift = re.compile("([-\+]{0,1})([\d]+)([dhms])")


nb_char_in_line = 50  # for verbose pretty printing
chunksize = 1000 # default size of chunks that the records will be treated by
base_process_size = 4500 # process base size
_last_word_table = None


_TOKENIZERS = load_tokenizers()


def list_union(list1, list2):
    "Returns union of the two lists."
    union_dict = {}
    for e in list1:
        union_dict[e] = 1
    for e in list2:
        union_dict[e] = 1
    return union_dict.keys()

def list_unique(_list):
    """Returns a _list with duplicates removed."""
    _dict = {}
    for e in _list:
        _dict[e] = 1
    return _dict.keys()

## safety function for killing slow DB threads:
def kill_sleepy_mysql_threads(max_threads=CFG_MAX_MYSQL_THREADS, thread_timeout=CFG_MYSQL_THREAD_TIMEOUT):
    """Check the number of DB threads and if there are more than
       MAX_THREADS of them, lill all threads that are in a sleeping
       state for more than THREAD_TIMEOUT seconds.  (This is useful
       for working around the the max_connection problem that appears
       during indexation in some not-yet-understood cases.)  If some
       threads are to be killed, write info into the log file.
    """
    res = run_sql("SHOW FULL PROCESSLIST")
    if len(res) > max_threads:
        for row in res:
            r_id, dummy, dummy, dummy, r_command, r_time, dummy, dummy = row
            if r_command == "Sleep" and int(r_time) > thread_timeout:
                run_sql("KILL %s", (r_id,))
                write_message("WARNING: too many DB threads, killing thread %s" % r_id, verbose=1)
    return

def get_associated_subfield_value(recID, tag, value, associated_subfield_code):
    """Return list of ASSOCIATED_SUBFIELD_CODE, if exists, for record
    RECID and TAG of value VALUE.  Used by fulltext indexer only.
    Note: TAG must be 6 characters long (tag+ind1+ind2+sfcode),
    otherwise en empty string is returned.
    FIXME: what if many tag values have the same value but different
    associated_subfield_code?  Better use bibrecord library for this.
    """
    out = ""
    if len(tag) != 6:
        return out
    bibXXx = "bib" + tag[0] + tag[1] + "x"
    bibrec_bibXXx = "bibrec_" + bibXXx
    query = """SELECT bb.field_number, b.tag, b.value FROM %s AS b, %s AS bb
               WHERE bb.id_bibrec=%%s AND bb.id_bibxxx=b.id AND tag LIKE
               %%s%%""" % (bibXXx, bibrec_bibXXx)
    res = run_sql(query, (recID, tag[:-1]))
    field_number = -1
    for row in res:
        if row[1] == tag and row[2] == value:
            field_number = row[0]
    if field_number > 0:
        for row in res:
            if row[0] == field_number and row[1] == tag[:-1] + associated_subfield_code:
                out = row[2]
                break
    return out

def get_field_tags(field):
    """Returns a list of MARC tags for the field code 'field'.
       Returns empty list in case of error.
       Example: field='author', output=['100__%','700__%']."""
    out = []
    query = """SELECT t.value FROM tag AS t, field_tag AS ft, field AS f
                WHERE f.code=%s AND ft.id_field=f.id AND t.id=ft.id_tag
                ORDER BY ft.score DESC"""
    res = run_sql(query, (field,))
    return [row[0] for row in res]


def get_author_canonical_ids_for_recid(recID):
    """
    Return list of author canonical IDs (e.g. `J.Ellis.1') for the
    given record.  Done by consulting BibAuthorID module.
    """
    from invenio.bibauthorid_dbinterface import get_persons_from_recids
    lwords = []
    res = get_persons_from_recids([recID])
    if res is None:
        ## BibAuthorID is not enabled
        return lwords
    else:
        dpersons, dpersoninfos = res
    for aid in dpersoninfos.keys():
        author_canonical_id = dpersoninfos[aid].get('canonical_id', '')
        if author_canonical_id:
            lwords.append(author_canonical_id)
    return lwords


def swap_temporary_reindex_tables(index_id, reindex_prefix="tmp_"):
    """Atomically swap reindexed temporary table with the original one.
    Delete the now-old one."""
    write_message("Putting new tmp index tables for id %s into production" % index_id)
    run_sql(
        "RENAME TABLE " +
        "idxWORD%02dR TO old_idxWORD%02dR," % (index_id, index_id) +
        "%sidxWORD%02dR TO idxWORD%02dR," % (reindex_prefix, index_id, index_id) +
        "idxWORD%02dF TO old_idxWORD%02dF," % (index_id, index_id) +
        "%sidxWORD%02dF TO idxWORD%02dF," % (reindex_prefix, index_id, index_id) +
        "idxPAIR%02dR TO old_idxPAIR%02dR," % (index_id, index_id) +
        "%sidxPAIR%02dR TO idxPAIR%02dR," % (reindex_prefix, index_id, index_id) +
        "idxPAIR%02dF TO old_idxPAIR%02dF," % (index_id, index_id) +
        "%sidxPAIR%02dF TO idxPAIR%02dF," % (reindex_prefix, index_id, index_id) +
        "idxPHRASE%02dR TO old_idxPHRASE%02dR," % (index_id, index_id) +
        "%sidxPHRASE%02dR TO idxPHRASE%02dR," % (reindex_prefix, index_id, index_id) +
        "idxPHRASE%02dF TO old_idxPHRASE%02dF," % (index_id, index_id) +
        "%sidxPHRASE%02dF TO idxPHRASE%02dF;" % (reindex_prefix, index_id, index_id)
    )
    write_message("Dropping old index tables for id %s" % index_id)
    run_sql("DROP TABLE old_idxWORD%02dR, old_idxWORD%02dF, old_idxPAIR%02dR, old_idxPAIR%02dF, old_idxPHRASE%02dR, old_idxPHRASE%02dF" % (index_id, index_id, index_id, index_id, index_id, index_id)) # kwalitee: disable=sql

def init_temporary_reindex_tables(index_id, reindex_prefix="tmp_"):
    """Create reindexing temporary tables."""
    write_message("Creating new tmp index tables for id %s" % index_id)
    run_sql("""DROP TABLE IF EXISTS %sidxWORD%02dF""" % (wash_table_column_name(reindex_prefix), index_id)) # kwalitee: disable=sql
    run_sql("""CREATE TABLE %sidxWORD%02dF (
                        id mediumint(9) unsigned NOT NULL auto_increment,
                        term varchar(50) default NULL,
                        hitlist longblob,
                        PRIMARY KEY  (id),
                        UNIQUE KEY term (term)
                        ) ENGINE=MyISAM""" % (reindex_prefix, index_id))

    run_sql("""DROP TABLE IF EXISTS %sidxWORD%02dR""" % (wash_table_column_name(reindex_prefix), index_id)) # kwalitee: disable=sql
    run_sql("""CREATE TABLE %sidxWORD%02dR (
                        id_bibrec mediumint(9) unsigned NOT NULL,
                        termlist longblob,
                        type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
                        PRIMARY KEY (id_bibrec,type)
                        ) ENGINE=MyISAM""" % (reindex_prefix, index_id))

    run_sql("""DROP TABLE IF EXISTS %sidxPAIR%02dF""" % (wash_table_column_name(reindex_prefix), index_id)) # kwalitee: disable=sql
    run_sql("""CREATE TABLE %sidxPAIR%02dF (
                        id mediumint(9) unsigned NOT NULL auto_increment,
                        term varchar(100) default NULL,
                        hitlist longblob,
                        PRIMARY KEY  (id),
                        UNIQUE KEY term (term)
                        ) ENGINE=MyISAM""" % (reindex_prefix, index_id))

    run_sql("""DROP TABLE IF EXISTS %sidxPAIR%02dR""" % (wash_table_column_name(reindex_prefix), index_id)) # kwalitee: disable=sql
    run_sql("""CREATE TABLE %sidxPAIR%02dR (
                        id_bibrec mediumint(9) unsigned NOT NULL,
                        termlist longblob,
                        type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
                        PRIMARY KEY (id_bibrec,type)
                        ) ENGINE=MyISAM""" % (reindex_prefix, index_id))

    run_sql("""DROP TABLE IF EXISTS %sidxPHRASE%02dF""" % (wash_table_column_name(reindex_prefix), index_id)) # kwalitee: disable=sql
    run_sql("""CREATE TABLE %sidxPHRASE%02dF (
                        id mediumint(9) unsigned NOT NULL auto_increment,
                        term text default NULL,
                        hitlist longblob,
                        PRIMARY KEY  (id),
                        KEY term (term(50))
                        ) ENGINE=MyISAM""" % (reindex_prefix, index_id))

    run_sql("""DROP TABLE IF EXISTS %sidxPHRASE%02dR""" % (wash_table_column_name(reindex_prefix), index_id)) # kwalitee: disable=sql
    run_sql("""CREATE TABLE %sidxPHRASE%02dR (
                        id_bibrec mediumint(9) unsigned NOT NULL default '0',
                        termlist longblob,
                        type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
                        PRIMARY KEY  (id_bibrec,type)
                        ) ENGINE=MyISAM""" % (reindex_prefix, index_id))
    run_sql("UPDATE idxINDEX SET last_updated='0000-00-00 00:00:00' WHERE id=%s", (index_id,))


def remove_subfields(s):
    "Removes subfields from string, e.g. 'foo $$c bar' becomes 'foo bar'."
    return re_subfields.sub(' ', s)

def get_index_id_from_index_name(index_name):
    """Returns the words/phrase index id for INDEXNAME.
       Returns empty string in case there is no words table for this index.
       Example: field='author', output=4."""
    out = 0
    query = """SELECT w.id FROM idxINDEX AS w
                WHERE w.name=%s LIMIT 1"""
    res = run_sql(query, (index_name,), 1)
    if res:
        out = res[0][0]
    return out

def get_index_name_from_index_id(index_id):
    """Returns the words/phrase index name for INDEXID.
       Returns '' in case there is no words table for this indexid.
       Example: field=9, output='fulltext'."""
    res = run_sql("SELECT name FROM idxINDEX WHERE id=%s", (index_id,))
    if res:
        return res[0][0]
    return ''

def get_index_tags(indexname):
    """Returns the list of tags that are indexed inside INDEXNAME.
       Returns empty list in case there are no tags indexed in this index.
       Note: uses get_field_tags() defined before.
       Example: field='author', output=['100__%', '700__%']."""
    out = []
    query = """SELECT f.code FROM idxINDEX AS w, idxINDEX_field AS wf,
    field AS f WHERE w.name=%s AND w.id=wf.id_idxINDEX
    AND f.id=wf.id_field"""
    res = run_sql(query, (indexname,))
    for row in res:
        out.extend(get_field_tags(row[0]))
    return out

def get_all_indexes():
    """Returns the list of the names of all defined words indexes.
       Returns empty list in case there are no tags indexed in this index.
       Example: output=['global', 'author']."""
    out = []
    query = """SELECT name FROM idxINDEX"""
    res = run_sql(query)
    for row in res:
        out.append(row[0])
    return out


def get_all_synonym_knowledge_bases():
    """Returns a dictionary of name key and knowledge base name and match type tuple value
        information of all defined words indexes that have knowledge base information.
        Returns empty dictionary in case there are no tags indexed.
        Example: output['global'] = ('INDEX-SYNONYM-TITLE', 'exact'), output['title'] = ('INDEX-SYNONYM-TITLE', 'exact')."""
    res = get_all_index_names_and_column_values("synonym_kbrs")
    out = {}
    for row in res:
        kb_data = row[1]
        # ignore empty strings
        if len(kb_data):
            out[row[0]] = tuple(kb_data.split(CFG_BIBINDEX_COLUMN_VALUE_SEPARATOR))
    return out


def get_index_remove_stopwords(index_id):
    """Returns value of a remove_stopword field from idxINDEX database table
       if it's not 'No'. If it's 'No' returns False.
       Just for consistency with WordTable.
       @param index_id: id of the index
    """
    result = get_idx_remove_stopwords(index_id)
    if isinstance(result, tuple):
        return False
    if result == 'No' or result == '':
        return False
    return result


def get_index_remove_html_markup(index_id):
    """ Gets remove_html_markup parameter from database ('Yes' or 'No') and
        changes it  to True, False.
        Just for consistency with WordTable."""
    result = get_idx_remove_html_markup(index_id)
    if result == 'Yes':
        return True
    return False


def get_index_remove_latex_markup(index_id):
    """ Gets remove_latex_markup parameter from database ('Yes' or 'No') and
        changes it  to True, False.
        Just for consistency with WordTable."""
    result = get_idx_remove_latex_markup(index_id)
    if result == 'Yes':
        return True
    return False


def get_index_tokenizer(index_id):
    """Returns value of a tokenizer field from idxINDEX database table
       @param index_id: id of the index
    """
    query = "SELECT tokenizer FROM idxINDEX WHERE id=%s" % index_id
    out = None
    try:
        res = run_sql(query)
        if res:
            out = _TOKENIZERS[res[0][0]]
    except DatabaseError:
        write_message("Exception caught for SQL statement: %s; column tokenizer might not exist" % query, sys.stderr)
    except KeyError:
        write_message("Exception caught: there is no such tokenizer")
        out = None
    return out


def split_ranges(parse_string):
    """Parse a string a return the list or ranges."""
    recIDs = []
    ranges = parse_string.split(",")
    for arange in ranges:
        tmp_recIDs = arange.split("-")

        if len(tmp_recIDs) == 1:
            recIDs.append([int(tmp_recIDs[0]), int(tmp_recIDs[0])])
        else:
            if int(tmp_recIDs[0]) > int(tmp_recIDs[1]): # sanity check
                tmp = tmp_recIDs[0]
                tmp_recIDs[0] = tmp_recIDs[1]
                tmp_recIDs[1] = tmp
            recIDs.append([int(tmp_recIDs[0]), int(tmp_recIDs[1])])
    return recIDs

def get_word_tables(tables):
    """ Given a list of table names it return a list of tuples
    (index_id, index_name, index_tags).
    If tables is empty it returns the whole list."""
    wordTables = []
    if tables:
        indexes = tables.split(",")
        for index in indexes:
            index_id = get_index_id_from_index_name(index)
            if index_id:
                wordTables.append((index_id, index, get_index_tags(index)))
            else:
                write_message("Error: There is no %s words table." % index, sys.stderr)
    else:
        for index in get_all_indexes():
            index_id = get_index_id_from_index_name(index)
            wordTables.append((index_id, index, get_index_tags(index)))
    return wordTables

def get_date_range(var):
    "Returns the two dates contained as a low,high tuple"
    limits = var.split(",")
    if len(limits) == 1:
        low = get_datetime(limits[0])
        return low, None
    if len(limits) == 2:
        low = get_datetime(limits[0])
        high = get_datetime(limits[1])
        return low, high
    return None, None

def create_range_list(res):
    """Creates a range list from a recID select query result contained
    in res. The result is expected to have ascending numerical order."""
    if not res:
        return []
    row = res[0]
    if not row:
        return []
    else:
        range_list = [[row, row]]
    for row in res[1:]:
        row_id = row
        if row_id == range_list[-1][1] + 1:
            range_list[-1][1] = row_id
        else:
            range_list.append([row_id, row_id])
    return range_list

def beautify_range_list(range_list):
    """Returns a non overlapping, maximal range list"""
    ret_list = []
    for new in range_list:
        found = 0
        for old in ret_list:
            if new[0] <= old[0] <= new[1] + 1 or new[0] - 1 <= old[1] <= new[1]:
                old[0] = min(old[0], new[0])
                old[1] = max(old[1], new[1])
                found = 1
                break

        if not found:
            ret_list.append(new)

    return ret_list

def truncate_index_table(index_name):
    """Properly truncate the given index."""
    index_id = get_index_id_from_index_name(index_name)
    if index_id:
        write_message('Truncating %s index table in order to reindex.' % index_name, verbose=2)
        run_sql("UPDATE idxINDEX SET last_updated='0000-00-00 00:00:00' WHERE id=%s", (index_id,))
        run_sql("TRUNCATE idxWORD%02dF" % index_id) # kwalitee: disable=sql
        run_sql("TRUNCATE idxWORD%02dR" % index_id) # kwalitee: disable=sql
        run_sql("TRUNCATE idxPHRASE%02dF" % index_id) # kwalitee: disable=sql
        run_sql("TRUNCATE idxPHRASE%02dR" % index_id) # kwalitee: disable=sql

def update_index_last_updated(index_id, starting_time=None):
    """Update last_updated column of the index table in the database.
    Puts starting time there so that if the task was interrupted for record download,
    the records will be reindexed next time."""
    if starting_time is None:
        return None
    write_message("updating last_updated to %s..." % starting_time, verbose=9)
    return run_sql("UPDATE idxINDEX SET last_updated=%s WHERE id=%s",
                    (starting_time, index_id,))

def get_percentage_completed(num_done, num_total):
    """ Return a string containing the approx. percentage completed """
    percentage_remaining = 100.0 * float(num_done) / float(num_total)
    if percentage_remaining:
        percentage_display = "(%.1f%%)" % (percentage_remaining,)
    else:
        percentage_display = ""
    return percentage_display

#def update_text_extraction_date(first_recid, last_recid):
    #"""for all the bibdoc connected to the specified recid, set
    #the text_extraction_date to the task_starting_time."""
    #run_sql("UPDATE bibdoc JOIN bibrec_bibdoc ON id=id_bibdoc SET text_extraction_date=%s WHERE id_bibrec BETWEEN %s AND %s", (task_get_task_param('task_starting_time'), first_recid, last_recid))

class WordTable:
    "A class to hold the words table."

    def __init__(self, index_name, index_id, fields_to_index, table_name_pattern, wordtable_type, tag_to_tokenizer_map, wash_index_terms=50, is_fulltext_index=False):
        """Creates words table instance.
        @param index_name: the index name
        @param index_id: the index integer identificator
        @param fields_to_index: a list of fields to index
        @param table_name_pattern: i.e. idxWORD%02dF or idxPHRASE%02dF
        @parm wordtable_type: type of the wordtable: Words, Pairs, Phrases
        @param tag_to_tokenizer_map: a mapping to specify particular tokenizer to
            extract words from particular metdata (such as 8564_u)
        @param wash_index_terms: do we wash index terms, and if yes (when >0),
            how many characters do we keep in the index terms; see
            max_char_length parameter of wash_index_term()
        """
        self.index_name = index_name
        self.index_id = index_id
        self.tablename = table_name_pattern % index_id
        self.humanname = get_def_name('%s' % (str(index_id),), "idxINDEX")[0][1]
        self.recIDs_in_mem = []
        self.fields_to_index = fields_to_index
        self.value = {}
        self.stemming_language = get_index_stemming_language(index_id)
        self.remove_stopwords = get_index_remove_stopwords(index_id)
        self.remove_html_markup = get_index_remove_html_markup(index_id)
        self.remove_latex_markup = get_index_remove_latex_markup(index_id)
        self.tokenizer = get_index_tokenizer(index_id)(self.stemming_language,
                                                       self.remove_stopwords,
                                                       self.remove_html_markup,
                                                       self.remove_latex_markup)
        self.default_tokenizer_function = self.tokenizer.get_tokenizing_function(wordtable_type)
        self.is_fulltext_index = is_fulltext_index
        self.wash_index_terms = wash_index_terms

        # tagToTokenizer mapping. It offers an indirection level necessary for
        # indexing fulltext.
        self.tag_to_words_fnc_map = {}
        for k in tag_to_tokenizer_map.keys():
            special_tokenizer_for_tag = _TOKENIZERS[tag_to_tokenizer_map[k]](self.stemming_language,
                                                                             self.remove_stopwords,
                                                                             self.remove_html_markup,
                                                                             self.remove_latex_markup)
            special_tokenizer_function = special_tokenizer_for_tag.get_tokenizing_function(wordtable_type)
            self.tag_to_words_fnc_map[k] = special_tokenizer_function

        if self.stemming_language and self.tablename.startswith('idxWORD'):
            write_message('%s has stemming enabled, language %s' % (self.tablename, self.stemming_language))

    def get_field(self, recID, tag):
        """Returns list of values of the MARC-21 'tag' fields for the
           record 'recID'."""

        out = []
        bibXXx = "bib" + tag[0] + tag[1] + "x"
        bibrec_bibXXx = "bibrec_" + bibXXx
        query = """SELECT value FROM %s AS b, %s AS bb
                WHERE bb.id_bibrec=%%s AND bb.id_bibxxx=b.id
                AND tag LIKE %%s""" % (bibXXx, bibrec_bibXXx)
        res = run_sql(query, (recID, tag))
        for row in res:
            out.append(row[0])
        return out

    def clean(self):
        "Cleans the words table."
        self.value = {}

    def put_into_db(self, mode="normal"):
        """Updates the current words table in the corresponding DB
           idxFOO table.  Mode 'normal' means normal execution,
           mode 'emergency' means words index reverting to old state.
           """
        write_message("%s %s wordtable flush started" % (self.tablename, mode))
        write_message('...updating %d words into %s started' % \
                (len(self.value), self.tablename))
        task_update_progress("(%s:%s) flushed %d/%d words" % (self.tablename, self.humanname, 0, len(self.value)))

        self.recIDs_in_mem = beautify_range_list(self.recIDs_in_mem)

        if mode == "normal":
            for group in self.recIDs_in_mem:
                query = """UPDATE %sR SET type='TEMPORARY' WHERE id_bibrec
                BETWEEN %%s AND %%s AND type='CURRENT'""" % self.tablename[:-1]
                write_message(query % (group[0], group[1]), verbose=9)
                run_sql(query, (group[0], group[1]))

        nb_words_total = len(self.value)
        nb_words_report = int(nb_words_total / 10.0)
        nb_words_done = 0
        for word in self.value.keys():
            self.put_word_into_db(word)
            nb_words_done += 1
            if nb_words_report != 0 and ((nb_words_done % nb_words_report) == 0):
                write_message('......processed %d/%d words' % (nb_words_done, nb_words_total))
                percentage_display = get_percentage_completed(nb_words_done, nb_words_total)
                task_update_progress("(%s:%s) flushed %d/%d words %s" % (self.tablename, self.humanname, nb_words_done, nb_words_total, percentage_display))
        write_message('...updating %d words into %s ended' % \
                      (nb_words_total, self.tablename))

        write_message('...updating reverse table %sR started' % self.tablename[:-1])
        if mode == "normal":
            for group in self.recIDs_in_mem:
                query = """UPDATE %sR SET type='CURRENT' WHERE id_bibrec
                BETWEEN %%s AND %%s AND type='FUTURE'""" % self.tablename[:-1]
                write_message(query % (group[0], group[1]), verbose=9)
                run_sql(query, (group[0], group[1]))
                query = """DELETE FROM %sR WHERE id_bibrec
                BETWEEN %%s AND %%s AND type='TEMPORARY'""" % self.tablename[:-1]
                write_message(query % (group[0], group[1]), verbose=9)
                run_sql(query, (group[0], group[1]))
                #if self.is_fulltext_index:
                    #update_text_extraction_date(group[0], group[1])
            write_message('End of updating wordTable into %s' % self.tablename, verbose=9)
        elif mode == "emergency":
            for group in self.recIDs_in_mem:
                query = """UPDATE %sR SET type='CURRENT' WHERE id_bibrec
                BETWEEN %%s AND %%s AND type='TEMPORARY'""" % self.tablename[:-1]
                write_message(query % (group[0], group[1]), verbose=9)
                run_sql(query, (group[0], group[1]))
                query = """DELETE FROM %sR WHERE id_bibrec
                BETWEEN %%s AND %%s AND type='FUTURE'""" % self.tablename[:-1]
                write_message(query % (group[0], group[1]), verbose=9)
                run_sql(query, (group[0], group[1]))
            write_message('End of emergency flushing wordTable into %s' % self.tablename, verbose=9)
        write_message('...updating reverse table %sR ended' % self.tablename[:-1])

        self.clean()
        self.recIDs_in_mem = []
        write_message("%s %s wordtable flush ended" % (self.tablename, mode))
        task_update_progress("(%s:%s) flush ended" % (self.tablename, self.humanname))

    def load_old_recIDs(self, word):
        """Load existing hitlist for the word from the database index files."""
        query = "SELECT hitlist FROM %s WHERE term=%%s" % self.tablename
        res = run_sql(query, (word,))
        if res:
            return intbitset(res[0][0])
        else:
            return None

    def merge_with_old_recIDs(self, word, set):
        """Merge the system numbers stored in memory (hash of recIDs with value +1 or -1
        according to whether to add/delete them) with those stored in the database index
        and received in set universe of recIDs for the given word.

        Return False in case no change was done to SET, return True in case SET
        was changed.
        """
        oldset = intbitset(set)
        set.update_with_signs(self.value[word])
        return set != oldset

    def put_word_into_db(self, word):
        """Flush a single word to the database and delete it from memory"""

        set = self.load_old_recIDs(word)
        if set is not None: # merge the word recIDs found in memory:
            if not self.merge_with_old_recIDs(word, set):
                # nothing to update:
                write_message("......... unchanged hitlist for ``%s''" % word, verbose=9)
                pass
            else:
                # yes there were some new words:
                write_message("......... updating hitlist for ``%s''" % word, verbose=9)
                run_sql("UPDATE %s SET hitlist=%%s WHERE term=%%s" % wash_table_column_name(self.tablename), (set.fastdump(), word)) # kwalitee: disable=sql

        else: # the word is new, will create new set:
            write_message("......... inserting hitlist for ``%s''" % word, verbose=9)
            set = intbitset(self.value[word].keys())
            try:
                run_sql("INSERT INTO %s (term, hitlist) VALUES (%%s, %%s)" % wash_table_column_name(self.tablename), (word, set.fastdump())) # kwalitee: disable=sql
            except Exception, e:
                ## We send this exception to the admin only when is not
                ## already reparing the problem.
                register_exception(prefix="Error when putting the term '%s' into db (hitlist=%s): %s\n" % (repr(word), set, e), alert_admin=(task_get_option('cmd') != 'repair'))

        if not set: # never store empty words
            run_sql("DELETE FROM %s WHERE term=%%s" % wash_table_column_name(self.tablename), (word,)) # kwalitee: disable=sql

        del self.value[word]

    def display(self):
        "Displays the word table."
        keys = self.value.keys()
        keys.sort()
        for k in keys:
            write_message("%s: %s" % (k, self.value[k]))

    def count(self):
        "Returns the number of words in the table."
        return len(self.value)

    def info(self):
        "Prints some information on the words table."
        write_message("The words table contains %d words." % self.count())

    def lookup_words(self, word=""):
        "Lookup word from the words table."

        if not word:
            done = 0
            while not done:
                try:
                    word = raw_input("Enter word: ")
                    done = 1
                except (EOFError, KeyboardInterrupt):
                    return

        if self.value.has_key(word):
            write_message("The word '%s' is found %d times." \
                % (word, len(self.value[word])))
        else:
            write_message("The word '%s' does not exist in the word file."\
                              % word)

    def add_recIDs(self, recIDs, opt_flush):
        """Fetches records which id in the recIDs range list and adds
        them to the wordTable.  The recIDs range list is of the form:
        [[i1_low,i1_high],[i2_low,i2_high], ..., [iN_low,iN_high]].
        """
        global chunksize, _last_word_table
        flush_count = 0
        records_done = 0
        records_to_go = 0

        for arange in recIDs:
            records_to_go = records_to_go + arange[1] - arange[0] + 1

        time_started = time.time() # will measure profile time
        for arange in recIDs:
            i_low = arange[0]
            chunksize_count = 0
            while i_low <= arange[1]:
                task_sleep_now_if_required()
                # calculate chunk group of recIDs and treat it:
                i_high = min(i_low + opt_flush - flush_count - 1, arange[1])
                i_high = min(i_low + chunksize - chunksize_count - 1, i_high)

                try:
                    self.chk_recID_range(i_low, i_high)
                except StandardError:
                    if self.index_name == 'fulltext' and CFG_SOLR_URL:
                        solr_commit()
                    raise

                write_message(CFG_BIBINDEX_ADDING_RECORDS_STARTED_STR % \
                        (self.tablename, i_low, i_high))
                if CFG_CHECK_MYSQL_THREADS:
                    kill_sleepy_mysql_threads()
                percentage_display = get_percentage_completed(records_done, records_to_go)
                task_update_progress("(%s:%s) adding recs %d-%d %s" % (self.tablename, self.humanname, i_low, i_high, percentage_display))
                self.del_recID_range(i_low, i_high)
                just_processed = self.add_recID_range(i_low, i_high)
                flush_count = flush_count + i_high - i_low + 1
                chunksize_count = chunksize_count + i_high - i_low + 1
                records_done = records_done + just_processed
                write_message(CFG_BIBINDEX_ADDING_RECORDS_STARTED_STR % \
                        (self.tablename, i_low, i_high))

                if chunksize_count >= chunksize:
                    chunksize_count = 0
                # flush if necessary:
                if flush_count >= opt_flush:
                    self.put_into_db()
                    self.clean()
                    if self.index_name == 'fulltext' and CFG_SOLR_URL:
                        solr_commit()
                    write_message("%s backing up" % (self.tablename))
                    flush_count = 0
                    self.log_progress(time_started, records_done, records_to_go)
                # iterate:
                i_low = i_high + 1
        if flush_count > 0:
            self.put_into_db()
            if self.index_name == 'fulltext' and CFG_SOLR_URL:
                solr_commit()
            self.log_progress(time_started, records_done, records_to_go)

    def add_recIDs_by_date(self, dates, opt_flush):
        """Add records that were modified between DATES[0] and DATES[1].
           If DATES is not set, then add records that were modified since
           the last update of the index.
        """
        if not dates:
            table_id = self.tablename[-3:-1]
            query = """SELECT last_updated FROM idxINDEX WHERE id=%s"""
            res = run_sql(query, (table_id,))
            if not res:
                return
            if not res[0][0]:
                dates = ("0000-00-00", None)
            else:
                dates = (res[0][0], None)
        if dates[1] is None:
            res = intbitset(run_sql("""SELECT b.id FROM bibrec AS b
                              WHERE b.modification_date >= %s""",
                          (dates[0],)))
            if self.is_fulltext_index:
                res |= intbitset(run_sql("""SELECT id_bibrec FROM bibrec_bibdoc JOIN bibdoc ON id_bibdoc=id WHERE text_extraction_date <= modification_date AND modification_date >= %s AND status<>'DELETED'""", (dates[0],)))
        elif dates[0] is None:
            res = intbitset(run_sql("""SELECT b.id FROM bibrec AS b
                              WHERE b.modification_date <= %s""",
                          (dates[1],)))
            if self.is_fulltext_index:
                res |= intbitset(run_sql("""SELECT id_bibrec FROM bibrec_bibdoc JOIN bibdoc ON id_bibdoc=id WHERE text_extraction_date <= modification_date AND modification_date <= %s AND status<>'DELETED'""", (dates[1],)))
        else:
            res = intbitset(run_sql("""SELECT b.id FROM bibrec AS b
                              WHERE b.modification_date >= %s AND
                                    b.modification_date <= %s""",
                          (dates[0], dates[1])))
            if self.is_fulltext_index:
                res |= intbitset(run_sql("""SELECT id_bibrec FROM bibrec_bibdoc JOIN bibdoc ON id_bibdoc=id WHERE text_extraction_date <= modification_date AND modification_date >= %s AND modification_date <= %s AND status<>'DELETED'""", (dates[0], dates[1],)))
        alist = create_range_list(list(res))
        if not alist:
            write_message("No new records added. %s is up to date" % self.tablename)
        else:
            self.add_recIDs(alist, opt_flush)
        # special case of author indexes where we need to re-index
        # those records that were affected by changed BibAuthorID
        # attributions:
        if self.index_name in ('author', 'firstauthor', 'exactauthor', 'exactfirstauthor'):
            from invenio.bibauthorid_personid_maintenance import get_recids_affected_since
            # dates[1] is ignored, since BibAuthorID API does not offer upper limit search
            alist = create_range_list(get_recids_affected_since(dates[0]))
            if not alist:
                write_message("No new records added by author canonical IDs. %s is up to date" % self.tablename)
            else:
                self.add_recIDs(alist, opt_flush)
        # special case of authority controlled indexes where we need to re-index
        # those records that were affected by changed Authority Records:
        res = intbitset()
        for tag in self.fields_to_index:
            pattern = tag.replace('%', '*')
            matches = fnmatch.filter(CFG_BIBAUTHORITY_CONTROLLED_FIELDS_BIBLIOGRAPHIC.keys(), pattern)
            if not len(matches):
                continue
            for tag_match in matches:
                # get the type of authority record associated with this field
                auth_type = CFG_BIBAUTHORITY_CONTROLLED_FIELDS_BIBLIOGRAPHIC.get(tag_match)
                # find updated authority records of this type
                # dates[1] is ignored, needs dates[0] to find res
                auth_recIDs = search_pattern(p='980__a:' + auth_type) \
                    & search_unit_in_bibrec(str(dates[0]), 'now()', type='m')
                # now find dependent bibliographic records
                for auth_recID in auth_recIDs:
                    # get the fix authority identifier of this authority record
                    control_nos = get_control_nos_from_recID(auth_recID)
                    # there may be multiple control number entries! (the '035' field is repeatable!)
                    for control_no in control_nos:
                        # get the bibrec IDs that refer to AUTHORITY_ID in TAG
                        tag_0 = tag_match[:5] + '0' # possibly do the same for '4' subfields ?
                        fieldvalue = '"' + control_no + '"'
                        res |= search_pattern(p=tag_0 + ':' + fieldvalue)
        authority_list = create_range_list(list(res))
        if not authority_list:
            write_message("No new authority records added. %s is up to date" % self.tablename)
        else:
            write_message(CFG_BIBAUTHORITY_BIBINDEX_UPDATE_MESSAGE)
            self.add_recIDs(authority_list, opt_flush)

    def add_recID_range(self, recID1, recID2):
        """Add records from RECID1 to RECID2."""
        wlist = {}
        self.recIDs_in_mem.append([recID1, recID2])
        # special case of author indexes where we also add author
        # canonical IDs:
        if self.index_name in ('author', 'firstauthor', 'exactauthor', 'exactfirstauthor'):
            for recID in range(recID1, recID2 + 1):
                if not wlist.has_key(recID):
                    wlist[recID] = []
                wlist[recID] = list_union(get_author_canonical_ids_for_recid(recID),
                                          wlist[recID])
        # case of special indexes:
        if self.index_name in ('authorcount', 'journal'):
            for tag in self.fields_to_index:
                get_words_function = self.tag_to_words_fnc_map.get(tag, self.default_tokenizer_function)
                for recID in range(recID1, recID2 + 1):
                    new_words = get_words_function(recID)
                    if not wlist.has_key(recID):
                        wlist[recID] = []
                    wlist[recID] = list_union(new_words, wlist[recID])
        else:
            # usual tag-by-tag indexing:
            for tag in self.fields_to_index:
                get_words_function = self.tag_to_words_fnc_map.get(tag, self.default_tokenizer_function)
                bibXXx = "bib" + tag[0] + tag[1] + "x"
                bibrec_bibXXx = "bibrec_" + bibXXx
                query = """SELECT bb.id_bibrec,b.value FROM %s AS b, %s AS bb
                        WHERE bb.id_bibrec BETWEEN %%s AND %%s
                        AND bb.id_bibxxx=b.id AND tag LIKE %%s""" % (bibXXx, bibrec_bibXXx)
                res = run_sql(query, (recID1, recID2, tag))
                if tag == '8564_u':
                    ## FIXME: Quick hack to be sure that hidden files are
                    ## actually indexed.
                    res = set(res)
                    for recid in xrange(int(recID1), int(recID2) + 1):
                        for bibdocfile in BibRecDocs(recid).list_latest_files():
                            res.add((recid, bibdocfile.get_url()))
                for row in sorted(res):
                    recID, phrase = row
                    if not wlist.has_key(recID):
                        wlist[recID] = []
                    new_words = get_words_function(phrase)
                    wlist[recID] = list_union(new_words, wlist[recID])

                #authority records
                pattern = tag.replace('%', '*')
                matches = fnmatch.filter(CFG_BIBAUTHORITY_CONTROLLED_FIELDS_BIBLIOGRAPHIC.keys(), pattern)
                if not len(matches):
                    continue
                for tag_match in matches:
                    authority_tag = tag_match[0:3] + "__0"
                    for recID in xrange(int(recID1), int(recID2) + 1):
                        control_nos = get_fieldvalues(recID, authority_tag)
                        for control_no in control_nos:
                            new_strings = get_index_strings_by_control_no(control_no)
                            for string_value in new_strings:
                                new_words = get_words_function(string_value)
                                wlist[recID] = list_union(new_words, wlist[recID])

        # lookup index-time synonyms:
        synonym_kbrs = get_all_synonym_knowledge_bases()
        if synonym_kbrs.has_key(self.index_name):
            if len(wlist) == 0: return 0
            recIDs = wlist.keys()
            for recID in recIDs:
                for word in wlist[recID]:
                    word_synonyms = get_synonym_terms(word,
                                                      synonym_kbrs[self.index_name][0],
                                                      synonym_kbrs[self.index_name][1],
                                                      use_memoise=True)

                    if word_synonyms:
                        wlist[recID] = list_union(word_synonyms, wlist[recID])

        # were there some words for these recIDs found?
        if len(wlist) == 0: return 0
        recIDs = wlist.keys()
        for recID in recIDs:
            # was this record marked as deleted?
            if "DELETED" in self.get_field(recID, "980__c"):
                wlist[recID] = []
                write_message("... record %d was declared deleted, removing its word list" % recID, verbose=9)
            write_message("... record %d, termlist: %s" % (recID, wlist[recID]), verbose=9)

        # put words into reverse index table with FUTURE status:
        for recID in recIDs:
            run_sql("INSERT INTO %sR (id_bibrec,termlist,type) VALUES (%%s,%%s,'FUTURE')" % wash_table_column_name(self.tablename[:-1]), (recID, serialize_via_marshal(wlist[recID]))) # kwalitee: disable=sql
            # ... and, for new records, enter the CURRENT status as empty:
            try:
                run_sql("INSERT INTO %sR (id_bibrec,termlist,type) VALUES (%%s,%%s,'CURRENT')" % wash_table_column_name(self.tablename[:-1]), (recID, serialize_via_marshal([]))) # kwalitee: disable=sql
            except DatabaseError:
                # okay, it's an already existing record, no problem
                pass

        # put words into memory word list:
        put = self.put
        for recID in recIDs:
            for w in wlist[recID]:
                put(recID, w, 1)

        return len(recIDs)

    def log_progress(self, start, done, todo):
        """Calculate progress and store it.
        start: start time,
        done: records processed,
        todo: total number of records"""
        time_elapsed = time.time() - start
        # consistency check
        if time_elapsed == 0 or done > todo:
            return

        time_recs_per_min = done / (time_elapsed / 60.0)
        write_message("%d records took %.1f seconds to complete.(%1.f recs/min)"\
                % (done, time_elapsed, time_recs_per_min))

        if time_recs_per_min:
            write_message("Estimated runtime: %.1f minutes" % \
                    ((todo - done) / time_recs_per_min))

    def put(self, recID, word, sign):
        """Adds/deletes a word to the word list."""
        try:
            if self.wash_index_terms:
                word = wash_index_term(word, self.wash_index_terms)
            if self.value.has_key(word):
                # the word 'word' exist already: update sign
                self.value[word][recID] = sign
            else:
                self.value[word] = {recID: sign}
        except:
            write_message("Error: Cannot put word %s with sign %d for recID %s." % (word, sign, recID))

    def del_recIDs(self, recIDs):
        """Fetches records which id in the recIDs range list and adds
        them to the wordTable.  The recIDs range list is of the form:
        [[i1_low,i1_high],[i2_low,i2_high], ..., [iN_low,iN_high]].
        """
        count = 0
        for arange in recIDs:
            task_sleep_now_if_required()
            self.del_recID_range(arange[0], arange[1])
            count = count + arange[1] - arange[0]
        self.put_into_db()
        if self.index_name == 'fulltext' and CFG_SOLR_URL:
            solr_commit()

    def del_recID_range(self, low, high):
        """Deletes records with 'recID' system number between low
           and high from memory words index table."""
        write_message("%s fetching existing words for records #%d-#%d started" % \
                (self.tablename, low, high), verbose=3)
        self.recIDs_in_mem.append([low, high])
        query = """SELECT id_bibrec,termlist FROM %sR as bb WHERE bb.id_bibrec
        BETWEEN %%s AND %%s""" % (self.tablename[:-1])
        recID_rows = run_sql(query, (low, high))
        for recID_row in recID_rows:
            recID = recID_row[0]
            wlist = deserialize_via_marshal(recID_row[1])
            for word in wlist:
                self.put(recID, word, -1)
        write_message("%s fetching existing words for records #%d-#%d ended" % \
                (self.tablename, low, high), verbose=3)

    def report_on_table_consistency(self):
        """Check reverse words index tables (e.g. idxWORD01R) for
        interesting states such as 'TEMPORARY' state.
        Prints small report (no of words, no of bad words).
        """
        # find number of words:
        query = """SELECT COUNT(*) FROM %s""" % (self.tablename)
        res = run_sql(query, None, 1)
        if res:
            nb_words = res[0][0]
        else:
            nb_words = 0

        # find number of records:
        query = """SELECT COUNT(DISTINCT(id_bibrec)) FROM %sR""" % (self.tablename[:-1])
        res = run_sql(query, None, 1)
        if res:
            nb_records = res[0][0]
        else:
            nb_records = 0

        # report stats:
        write_message("%s contains %d words from %d records" % (self.tablename, nb_words, nb_records))

        # find possible bad states in reverse tables:
        query = """SELECT COUNT(DISTINCT(id_bibrec)) FROM %sR WHERE type <> 'CURRENT'""" % (self.tablename[:-1])
        res = run_sql(query)
        if res:
            nb_bad_records = res[0][0]
        else:
            nb_bad_records = 999999999
        if nb_bad_records:
            write_message("EMERGENCY: %s needs to repair %d of %d index records" % \
                (self.tablename, nb_bad_records, nb_records))
        else:
            write_message("%s is in consistent state" % (self.tablename))

        return nb_bad_records

    def repair(self, opt_flush):
        """Repair the whole table"""
        # find possible bad states in reverse tables:
        query = """SELECT COUNT(DISTINCT(id_bibrec)) FROM %sR WHERE type <> 'CURRENT'""" % (self.tablename[:-1])
        res = run_sql(query, None, 1)
        if res:
            nb_bad_records = res[0][0]
        else:
            nb_bad_records = 0

        if nb_bad_records == 0:
            return

        query = """SELECT id_bibrec FROM %sR WHERE type <> 'CURRENT'""" \
                % (self.tablename[:-1])
        res = intbitset(run_sql(query))
        recIDs = create_range_list(list(res))

        flush_count = 0
        records_done = 0
        records_to_go = 0

        for arange in recIDs:
            records_to_go = records_to_go + arange[1] - arange[0] + 1

        time_started = time.time() # will measure profile time
        for arange in recIDs:

            i_low = arange[0]
            chunksize_count = 0
            while i_low <= arange[1]:
                task_sleep_now_if_required()
                # calculate chunk group of recIDs and treat it:
                i_high = min(i_low + opt_flush - flush_count - 1, arange[1])
                i_high = min(i_low + chunksize - chunksize_count - 1, i_high)

                self.fix_recID_range(i_low, i_high)

                flush_count = flush_count + i_high - i_low + 1
                chunksize_count = chunksize_count + i_high - i_low + 1
                records_done = records_done + i_high - i_low + 1
                if chunksize_count >= chunksize:
                    chunksize_count = 0
                # flush if necessary:
                if flush_count >= opt_flush:
                    self.put_into_db("emergency")
                    self.clean()
                    flush_count = 0
                    self.log_progress(time_started, records_done, records_to_go)
                # iterate:
                i_low = i_high + 1
        if flush_count > 0:
            self.put_into_db("emergency")
            self.log_progress(time_started, records_done, records_to_go)
        write_message("%s inconsistencies repaired." % self.tablename)

    def chk_recID_range(self, low, high):
        """Check if the reverse index table is in proper state"""
        ## check db
        query = """SELECT COUNT(*) FROM %sR WHERE type <> 'CURRENT'
        AND id_bibrec BETWEEN %%s AND %%s""" % self.tablename[:-1]
        res = run_sql(query, (low, high), 1)
        if res[0][0] == 0:
            write_message("%s for %d-%d is in consistent state" % (self.tablename, low, high))
            return # okay, words table is consistent

        ## inconsistency detected!
        write_message("EMERGENCY: %s inconsistencies detected..." % self.tablename)
        error_message = "Errors found. You should check consistency of the " \
                "%s - %sR tables.\nRunning 'bibindex --repair' is " \
                "recommended." % (self.tablename, self.tablename[:-1])
        write_message("EMERGENCY: " + error_message, stream=sys.stderr)
        raise StandardError(error_message)

    def fix_recID_range(self, low, high):
        """Try to fix reverse index database consistency (e.g. table idxWORD01R) in the low,high doc-id range.

        Possible states for a recID follow:
        CUR TMP FUT: very bad things have happened: warn!
        CUR TMP    : very bad things have happened: warn!
        CUR     FUT: delete FUT (crash before flushing)
        CUR        : database is ok
            TMP FUT: add TMP to memory and del FUT from memory
                     flush (revert to old state)
            TMP    : very bad things have happened: warn!
                FUT: very bad things have happended: warn!
        """

        state = {}
        query = "SELECT id_bibrec,type FROM %sR WHERE id_bibrec BETWEEN %%s AND %%s"\
                % self.tablename[:-1]
        res = run_sql(query, (low, high))
        for row in res:
            if not state.has_key(row[0]):
                state[row[0]] = []
            state[row[0]].append(row[1])

        ok = 1 # will hold info on whether we will be able to repair
        for recID in state.keys():
            if not 'TEMPORARY' in state[recID]:
                if 'FUTURE' in state[recID]:
                    if 'CURRENT' not in state[recID]:
                        write_message("EMERGENCY: Index record %d is in inconsistent state. Can't repair it." % recID)
                        ok = 0
                    else:
                        write_message("EMERGENCY: Inconsistency in index record %d detected" % recID)
                        query = """DELETE FROM %sR
                        WHERE id_bibrec=%%s""" % self.tablename[:-1]
                        run_sql(query, (recID,))
                        write_message("EMERGENCY: Inconsistency in record %d repaired." % recID)

            else:
                if 'FUTURE' in state[recID] and not 'CURRENT' in state[recID]:
                    self.recIDs_in_mem.append([recID, recID])

                    # Get the words file
                    query = """SELECT type,termlist FROM %sR
                    WHERE id_bibrec=%%s""" % self.tablename[:-1]
                    write_message(query, verbose=9)
                    res = run_sql(query, (recID,))
                    for row in res:
                        wlist = deserialize_via_marshal(row[1])
                        write_message("Words are %s " % wlist, verbose=9)
                        if row[0] == 'TEMPORARY':
                            sign = 1
                        else:
                            sign = -1
                        for word in wlist:
                            self.put(recID, word, sign)

                else:
                    write_message("EMERGENCY: %s for %d is in inconsistent "
                            "state. Couldn't repair it." % (self.tablename,
                                recID), stream=sys.stderr)
                    ok = 0

        if not ok:
            error_message = "Unrepairable errors found. You should check " \
                    "consistency of the %s - %sR tables. Deleting affected " \
                    "TEMPORARY and FUTURE entries from these tables is " \
                    "recommended; see the BibIndex Admin Guide." % \
                    (self.tablename, self.tablename[:-1])
            write_message("EMERGENCY: " + error_message, stream=sys.stderr)
            raise StandardError(error_message)

def main():
    """Main that construct all the bibtask."""
    task_init(authorization_action='runbibindex',
            authorization_msg="BibIndex Task Submission",
            description="""Examples:
\t%s -a -i 234-250,293,300-500 -u admin@localhost
\t%s -a -w author,fulltext -M 8192 -v3
            \t%s -d -m +4d -A on --flush=10000\n""" % ((sys.argv[0],) * 3), help_specific_usage=""" Indexing options:
  -a, --add\t\tadd or update words for selected records
  -d, --del\t\tdelete words for selected records
  -i, --id=low[-high]\t\tselect according to doc recID
  -m, --modified=from[,to]\tselect according to modification date
  -c, --collection=c1[,c2]\tselect according to collection
  -R, --reindex\treindex the selected indexes from scratch

 Repairing options:
  -k, --check\t\tcheck consistency for all records in the table(s)
  -r, --repair\t\ttry to repair all records in the table(s)

 Specific options:
  -w, --windex=w1[,w2]\tword/phrase indexes to consider (all)
  -M, --maxmem=XXX\tmaximum memory usage in kB (no limit)
  -f, --flush=NNN\t\tfull consistent table flush after NNN records (10000)
""",
            version=__revision__,
            specific_params=("adi:m:c:w:krRM:f:", [
                "add",
                "del",
                "id=",
                "modified=",
                "collection=",
                "windex=",
                "check",
                "repair",
                "reindex",
                "maxmem=",
                "flush=",
            ]),
            task_stop_helper_fnc=task_stop_table_close_fnc,
            task_submit_elaborate_specific_parameter_fnc=task_submit_elaborate_specific_parameter,
            task_run_fnc=task_run_core,
            task_submit_check_options_fnc=task_submit_check_options)

def task_submit_check_options():
    """Check for options compatibility."""
    if task_get_option("reindex"):
        if task_get_option("cmd") != "add" or task_get_option('id') or task_get_option('collection'):
            print >> sys.stderr, "ERROR: You can use --reindex only when adding modified record."
            return False
    return True

def task_submit_elaborate_specific_parameter(key, value, opts, args):
    """ Given the string key it checks it's meaning, eventually using the
    value. Usually it fills some key in the options dict.
    It must return True if it has elaborated the key, False, if it doesn't
    know that key.
    eg:
    if key in ['-n', '--number']:
        self.options['number'] = value
        return True
    return False
    """
    if key in ("-a", "--add"):
        task_set_option("cmd", "add")
        if ("-x", "") in opts or ("--del", "") in opts:
            raise StandardError("Can not have --add and --del at the same time!")
    elif key in ("-k", "--check"):
        task_set_option("cmd", "check")
    elif key in ("-r", "--repair"):
        task_set_option("cmd", "repair")
    elif key in ("-d", "--del"):
        task_set_option("cmd", "del")
    elif key in ("-i", "--id"):
        task_set_option('id', task_get_option('id') + split_ranges(value))
    elif key in ("-m", "--modified"):
        task_set_option("modified", get_date_range(value))
    elif key in ("-c", "--collection"):
        task_set_option("collection", value)
    elif key in ("-R", "--reindex"):
        task_set_option("reindex", True)
    elif key in ("-w", "--windex"):
        task_set_option("windex", value)
    elif key in ("-M", "--maxmem"):
        task_set_option("maxmem", int(value))
        if task_get_option("maxmem") < base_process_size + 1000:
            raise StandardError("Memory usage should be higher than %d kB" % \
                (base_process_size + 1000))
    elif key in ("-f", "--flush"):
        task_set_option("flush", int(value))
    else:
        return False
    return True

def task_stop_table_close_fnc():
    """ Close tables to STOP. """
    global _last_word_table
    if _last_word_table:
        _last_word_table.put_into_db()

def task_run_core():
    """Runs the task by fetching arguments from the BibSched task queue.  This is
    what BibSched will be invoking via daemon call.
    The task prints Fibonacci numbers for up to NUM on the stdout, and some
    messages on stderr.
    Return 1 in case of success and 0 in case of failure."""
    global _last_word_table

    if task_get_option("cmd") == "check":
        wordTables = get_word_tables(task_get_option("windex"))
        for index_id, index_name, index_tags in wordTables:
            wordTable = WordTable(index_name=index_name,
                                  index_id=index_id,
                                  fields_to_index=index_tags,
                                  table_name_pattern='idxWORD%02dF',
                                  wordtable_type=CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"],
                                  tag_to_tokenizer_map={'8564_u': "BibIndexFulltextTokenizer"},
                                  wash_index_terms=50)
            _last_word_table = wordTable
            wordTable.report_on_table_consistency()
            task_sleep_now_if_required(can_stop_too=True)


            wordTable = WordTable(index_name=index_name,
                                  index_id=index_id,
                                  fields_to_index=index_tags,
                                  table_name_pattern='idxPAIR%02dF',
                                  wordtable_type=CFG_BIBINDEX_INDEX_TABLE_TYPE["Pairs"],
                                  tag_to_tokenizer_map={'8564_u': "BibIndexEmptyTokenizer"},
                                  wash_index_terms=100)
            _last_word_table = wordTable
            wordTable.report_on_table_consistency()
            task_sleep_now_if_required(can_stop_too=True)


            wordTable = WordTable(index_name=index_name,
                                  index_id=index_id,
                                  fields_to_index=index_tags,
                                  table_name_pattern='idxPHRASE%02dF',
                                  wordtable_type=CFG_BIBINDEX_INDEX_TABLE_TYPE["Phrases"],
                                  tag_to_tokenizer_map={'8564_u': "BibIndexEmptyTokenizer"},
                                  wash_index_terms=0)
            _last_word_table = wordTable
            wordTable.report_on_table_consistency()
            task_sleep_now_if_required(can_stop_too=True)
        _last_word_table = None
        return True

    # Let's work on single words!
    wordTables = get_word_tables(task_get_option("windex"))
    for index_id, index_name, index_tags in wordTables:
        is_fulltext_index = index_name == 'fulltext'
        reindex_prefix = ""
        if task_get_option("reindex"):
            reindex_prefix = "tmp_"
            init_temporary_reindex_tables(index_id, reindex_prefix)

        wordTable = WordTable(index_name=index_name,
                              index_id=index_id,
                              fields_to_index=index_tags,
                              table_name_pattern=reindex_prefix + 'idxWORD%02dF',
                              wordtable_type=CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"],
                              tag_to_tokenizer_map={'8564_u': "BibIndexFulltextTokenizer"},
                              is_fulltext_index=is_fulltext_index,
                              wash_index_terms=50)
        _last_word_table = wordTable
        wordTable.report_on_table_consistency()
        try:
            if task_get_option("cmd") == "del":
                if task_get_option("id"):
                    wordTable.del_recIDs(task_get_option("id"))
                    task_sleep_now_if_required(can_stop_too=True)
                elif task_get_option("collection"):
                    l_of_colls = task_get_option("collection").split(",")
                    recIDs = perform_request_search(c=l_of_colls)
                    recIDs_range = []
                    for recID in recIDs:
                        recIDs_range.append([recID, recID])
                    wordTable.del_recIDs(recIDs_range)
                    task_sleep_now_if_required(can_stop_too=True)
                else:
                    error_message = "Missing IDs of records to delete from " \
                            "index %s." % wordTable.tablename
                    write_message(error_message, stream=sys.stderr)
                    raise StandardError(error_message)
            elif task_get_option("cmd") == "add":
                if task_get_option("id"):
                    wordTable.add_recIDs(task_get_option("id"), task_get_option("flush"))
                    task_sleep_now_if_required(can_stop_too=True)
                elif task_get_option("collection"):
                    l_of_colls = task_get_option("collection").split(",")
                    recIDs = perform_request_search(c=l_of_colls)
                    recIDs_range = []
                    for recID in recIDs:
                        recIDs_range.append([recID, recID])
                    wordTable.add_recIDs(recIDs_range, task_get_option("flush"))
                    task_sleep_now_if_required(can_stop_too=True)
                else:
                    wordTable.add_recIDs_by_date(task_get_option("modified"), task_get_option("flush"))
                    ## here we used to update last_updated info, if run via automatic mode;
                    ## but do not update here anymore, since idxPHRASE will be acted upon later
                    task_sleep_now_if_required(can_stop_too=True)
            elif task_get_option("cmd") == "repair":
                wordTable.repair(task_get_option("flush"))
                task_sleep_now_if_required(can_stop_too=True)
            else:
                error_message = "Invalid command found processing %s" % \
                    wordTable.tablename
                write_message(error_message, stream=sys.stderr)
                raise StandardError(error_message)
        except StandardError, e:
            write_message("Exception caught: %s" % e, sys.stderr)
            register_exception(alert_admin=True)
            if _last_word_table:
                _last_word_table.put_into_db()
            raise

        wordTable.report_on_table_consistency()
        task_sleep_now_if_required(can_stop_too=True)

        # Let's work on pairs now
        wordTable = WordTable(index_name=index_name,
                              index_id=index_id,
                              fields_to_index=index_tags,
                              table_name_pattern=reindex_prefix + 'idxPAIR%02dF',
                              wordtable_type=CFG_BIBINDEX_INDEX_TABLE_TYPE["Pairs"],
                              tag_to_tokenizer_map={'8564_u': "BibIndexEmptyTokenizer"},
                              wash_index_terms=100)
        _last_word_table = wordTable
        wordTable.report_on_table_consistency()
        try:
            if task_get_option("cmd") == "del":
                if task_get_option("id"):
                    wordTable.del_recIDs(task_get_option("id"))
                    task_sleep_now_if_required(can_stop_too=True)
                elif task_get_option("collection"):
                    l_of_colls = task_get_option("collection").split(",")
                    recIDs = perform_request_search(c=l_of_colls)
                    recIDs_range = []
                    for recID in recIDs:
                        recIDs_range.append([recID, recID])
                    wordTable.del_recIDs(recIDs_range)
                    task_sleep_now_if_required(can_stop_too=True)
                else:
                    error_message = "Missing IDs of records to delete from " \
                            "index %s." % wordTable.tablename
                    write_message(error_message, stream=sys.stderr)
                    raise StandardError(error_message)
            elif task_get_option("cmd") == "add":
                if task_get_option("id"):
                    wordTable.add_recIDs(task_get_option("id"), task_get_option("flush"))
                    task_sleep_now_if_required(can_stop_too=True)
                elif task_get_option("collection"):
                    l_of_colls = task_get_option("collection").split(",")
                    recIDs = perform_request_search(c=l_of_colls)
                    recIDs_range = []
                    for recID in recIDs:
                        recIDs_range.append([recID, recID])
                    wordTable.add_recIDs(recIDs_range, task_get_option("flush"))
                    task_sleep_now_if_required(can_stop_too=True)
                else:
                    wordTable.add_recIDs_by_date(task_get_option("modified"), task_get_option("flush"))
                    # let us update last_updated timestamp info, if run via automatic mode:
                    task_sleep_now_if_required(can_stop_too=True)
            elif task_get_option("cmd") == "repair":
                wordTable.repair(task_get_option("flush"))
                task_sleep_now_if_required(can_stop_too=True)
            else:
                error_message = "Invalid command found processing %s" % \
                        wordTable.tablename
                write_message(error_message, stream=sys.stderr)
                raise StandardError(error_message)
        except StandardError, e:
            write_message("Exception caught: %s" % e, sys.stderr)
            register_exception()
            if _last_word_table:
                _last_word_table.put_into_db()
            raise

        wordTable.report_on_table_consistency()
        task_sleep_now_if_required(can_stop_too=True)

        # Let's work on phrases now
        wordTable = WordTable(index_name=index_name,
                              index_id=index_id,
                              fields_to_index=index_tags,
                              table_name_pattern=reindex_prefix + 'idxPHRASE%02dF',
                              wordtable_type=CFG_BIBINDEX_INDEX_TABLE_TYPE["Phrases"],
                              tag_to_tokenizer_map={'8564_u': "BibIndexEmptyTokenizer"},
                              wash_index_terms=0)
        _last_word_table = wordTable
        wordTable.report_on_table_consistency()
        try:
            if task_get_option("cmd") == "del":
                if task_get_option("id"):
                    wordTable.del_recIDs(task_get_option("id"))
                    task_sleep_now_if_required(can_stop_too=True)
                elif task_get_option("collection"):
                    l_of_colls = task_get_option("collection").split(",")
                    recIDs = perform_request_search(c=l_of_colls)
                    recIDs_range = []
                    for recID in recIDs:
                        recIDs_range.append([recID, recID])
                    wordTable.del_recIDs(recIDs_range)
                    task_sleep_now_if_required(can_stop_too=True)
                else:
                    error_message = "Missing IDs of records to delete from " \
                            "index %s." % wordTable.tablename
                    write_message(error_message, stream=sys.stderr)
                    raise StandardError(error_message)
            elif task_get_option("cmd") == "add":
                if task_get_option("id"):
                    wordTable.add_recIDs(task_get_option("id"), task_get_option("flush"))
                    task_sleep_now_if_required(can_stop_too=True)
                elif task_get_option("collection"):
                    l_of_colls = task_get_option("collection").split(",")
                    recIDs = perform_request_search(c=l_of_colls)
                    recIDs_range = []
                    for recID in recIDs:
                        recIDs_range.append([recID, recID])
                    wordTable.add_recIDs(recIDs_range, task_get_option("flush"))
                    task_sleep_now_if_required(can_stop_too=True)
                else:
                    wordTable.add_recIDs_by_date(task_get_option("modified"), task_get_option("flush"))
                    # let us update last_updated timestamp info, if run via automatic mode:
                    update_index_last_updated(index_id, task_get_task_param('task_starting_time'))
                    task_sleep_now_if_required(can_stop_too=True)
            elif task_get_option("cmd") == "repair":
                wordTable.repair(task_get_option("flush"))
                task_sleep_now_if_required(can_stop_too=True)
            else:
                error_message = "Invalid command found processing %s" % \
                        wordTable.tablename
                write_message(error_message, stream=sys.stderr)
                raise StandardError(error_message)
        except StandardError, e:
            write_message("Exception caught: %s" % e, sys.stderr)
            register_exception()
            if _last_word_table:
                _last_word_table.put_into_db()
            raise

        wordTable.report_on_table_consistency()
        task_sleep_now_if_required(can_stop_too=True)

        if task_get_option("reindex"):
            swap_temporary_reindex_tables(index_id, reindex_prefix)
            update_index_last_updated(index_id, task_get_task_param('task_starting_time'))
        task_sleep_now_if_required(can_stop_too=True)

    _last_word_table = None
    return True


### okay, here we go:
if __name__ == '__main__':
    main()
