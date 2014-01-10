# -*- coding:utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2010, 2011, 2012, 2013 CERN.
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

"""bibindex.engine_utils: here are some useful regular experssions for tokenizers
   and several helper functions.
"""


import re
import sys

from invenio.legacy.dbquery import run_sql, \
    DatabaseError
from invenio.legacy.bibsched.bibtask import write_message
from invenio.legacy.bibrecord import get_fieldvalues
from invenio.config import \
     CFG_BIBINDEX_CHARS_PUNCTUATION, \
     CFG_BIBINDEX_CHARS_ALPHANUMERIC_SEPARATORS


latex_formula_re = re.compile(r'\$.*?\$|\\\[.*?\\\]')
phrase_delimiter_re = re.compile(r'[\.:;\?\!]')
space_cleaner_re = re.compile(r'\s+')
re_block_punctuation_begin = re.compile(r"^" + CFG_BIBINDEX_CHARS_PUNCTUATION + "+")
re_block_punctuation_end = re.compile(CFG_BIBINDEX_CHARS_PUNCTUATION + "+$")
re_punctuation = re.compile(CFG_BIBINDEX_CHARS_PUNCTUATION)
re_separators = re.compile(CFG_BIBINDEX_CHARS_ALPHANUMERIC_SEPARATORS)
re_arxiv = re.compile(r'^arxiv:\d\d\d\d\.\d\d\d\d')

re_pattern_fuzzy_author_trigger = re.compile(r'[\s\,\.]')
# FIXME: re_pattern_fuzzy_author_trigger could be removed and an
# BibAuthorID API function could be called instead after we
# double-check that there are no circular imports.


def load_tokenizers():
    """
    Load all the bibindex tokenizers and returns it.
    """
    from invenio.modules.indexer.registry import tokenizers
    return dict((module.__name__.split('.')[-1],
        getattr(module, module.__name__.split('.')[-1], ''))
        for module in tokenizers)


def get_all_index_names_and_column_values(column_name):
    """Returns a list of tuples of name and another column of all defined words indexes.
       Returns empty list in case there are no tags indexed in this index or in case
       the column name does not exist.
       Example: output=[('global', something), ('title', something)]."""
    out = []
    query = """SELECT name, %s FROM idxINDEX""" % column_name
    try:
        res = run_sql(query)
        for row in res:
            out.append((row[0], row[1]))
    except DatabaseError:
        write_message("Exception caught for SQL statement: %s; column %s might not exist" % (query, column_name), sys.stderr)
    return out



def author_name_requires_phrase_search(p):
    """
    Detect whether author query pattern p requires phrase search.
    Notably, look for presence of spaces and commas.
    """
    if re_pattern_fuzzy_author_trigger.search(p):
        return True
    return False


def get_field_count(recID, tags):
    """
    Return number of field instances having TAGS in record RECID.

    @param recID: record ID
    @type recID: int
    @param tags: list of tags to count, e.g. ['100__a', '700__a']
    @type tags: list
    @return: number of tags present in record
    @rtype: int
    @note: Works internally via getting field values, which may not be
           very efficient.  Could use counts only, or else retrieve stored
           recstruct format of the record and walk through it.
    """
    out = 0
    for tag in tags:
        out += len(get_fieldvalues(recID, tag))
    return out


def run_sql_drop_silently(query):
    """
        SQL DROP statement with IF EXISTS part generates
        warning if table does not exist. To mute the warning
        we can remove IF EXISTS and catch SQL exception telling
        us that table does not exist.
    """
    try:
        query = query.replace(" IF EXISTS", "")
        run_sql(query)
    except Exception, e:
        if  str(e).find("Unknown table") > -1:
            pass
        else:
            raise e


def get_idx_indexer(name):
    """Returns the indexer field value"""
    try:
        return run_sql("SELECT indexer FROM idxINDEX WHERE NAME=%s", (name, ))[0][0]
    except StandardError, e:
        return (0, e)


def get_all_indexes(virtual=True, with_ids=False):
    """Returns the list of the names of all defined words indexes.
       Returns empty list in case there are no tags indexed in this index.
       @param virtual: if True function will return also virtual indexes
       @param with_ids: if True function will return also IDs of found indexes
       Example: output=['global', 'author']."""
    out = []
    if virtual:
        query = """SELECT %s name FROM idxINDEX"""
        query = query % (with_ids and "id," or "")
    else:
        query = """SELECT %s w.name FROM idxINDEX AS w
                   WHERE w.id NOT IN (SELECT DISTINCT id_virtual FROM idxINDEX_idxINDEX)"""
        query = query % (with_ids and "w.id," or "")
    res = run_sql(query)
    if with_ids:
        out = [row for row in res]
    else:
        out = [row[0] for row in res]
    return out


def get_all_virtual_indexes():
    """ Returns all defined 'virtual' indexes. """
    query = """SELECT DISTINCT v.id_virtual, w.name FROM idxINDEX_idxINDEX AS v,
                                                         idxINDEX AS w
               WHERE v.id_virtual=w.id"""
    res = run_sql(query)
    return res


def get_index_virtual_indexes(index_id):
    """Returns 'virtual' indexes that should be indexed together with
       given index."""
    query = """SELECT v.id_virtual, w.name  FROM idxINDEX_idxINDEX AS v,
                                                 idxINDEX AS w
               WHERE v.id_virtual=w.id AND
                     v.id_normal=%s"""
    res = run_sql(query, (index_id,))
    return res


def is_index_virtual(index_id):
    """Checks if index is virtual"""
    query = """SELECT id_virtual FROM idxINDEX_idxINDEX
               WHERE id_virtual=%s"""
    res = run_sql(query, (index_id,))
    if res:
        return True
    return False


def get_virtual_index_building_blocks(index_id):
    """Returns indexes that made up virtual index of given index_id.
       If index_id is an id of normal index (not virtual) returns
       empty tuple.
       """
    query = """SELECT v.id_normal, w.name FROM idxINDEX_idxINDEX AS v,
                                               idxINDEX AS w
               WHERE v.id_normal=w.id AND
                     v.id_virtual=%s"""
    res = run_sql(query, (index_id,))
    return res


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


def get_tag_indexes(tag, virtual=True):
    """Returns indexes names and ids corresponding to the given tag
       @param tag: MARC tag in one of the forms:
            'xx%', 'xxx', 'xxx__a', 'xxx__%'
       @param virtual: if True function will also return virtual indexes"""
    tag2 = tag[0:2] + "%" #for tags in the form: 10%
    tag3 = tag[:-1] + "%" #for tags in the form: 100__%
    query = """SELECT DISTINCT w.id,w.name FROM idxINDEX AS w,
                                                idxINDEX_field AS wf,
                                                field_tag AS ft,
                                                tag as t
               WHERE (t.value=%%s OR
                      t.value=%%s OR
                      %s) AND
                     t.id=ft.id_tag AND
                     ft.id_field=wf.id_field AND
                     wf.id_idxINDEX=w.id"""
    if tag[-1] == "%":
        missing_piece = "t.value LIKE %s"
    elif tag[-1] != "%" and len(tag) == 3:
        missing_piece = "t.value LIKE %s"
        tag3 = tag + "%" #for all tags which start from 'tag'
    else:
        missing_piece = "t.value=%s"
    query = query % missing_piece
    res = run_sql(query, (tag, tag2, tag3))
    if res:
        if virtual:
            response = list(res)
            index_ids = map(str, zip(*res)[0])
            query = """SELECT DISTINCT v.id_virtual,w.name FROM idxINDEX_idxINDEX AS v,
                                                                idxINDEX as w
                       WHERE v.id_virtual=w.id AND
                             v.id_normal IN ("""
            query = query + ", ".join(index_ids) + ")"
            response.extend(run_sql(query))
            return tuple(response)
        return res
    return None


def get_index_tags(indexname, virtual=True):
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
    if not out and virtual:
        index_id = get_index_id_from_index_name(indexname)
        try:
            dependent_indexes = map(str, zip(*get_virtual_index_building_blocks(index_id))[0])
        except IndexError:
            return out
        tags = set()
        query = """SELECT DISTINCT f.code FROM idxINDEX AS w, idxINDEX_field AS wf, field AS f
                   WHERE w.id=wf.id_idxINDEX AND
                         f.id=wf.id_field AND
                         w.id IN ("""
        query = query + ", ".join(dependent_indexes) + ")"
        res = run_sql(query)
        for row in res:
            tags |= set(get_field_tags(row[0]))
        return list(tags)
    return out


def get_min_last_updated(indexes):
    """Returns min modification date for 'indexes':
       min(last_updated)
       @param indexes: list of indexes
    """
    query= """SELECT min(last_updated) FROM idxINDEX WHERE name IN ("""
    for index in indexes:
        query += "%s,"
    query = query[:-1] + ")"
    res = run_sql(query, tuple(indexes))
    return res


def remove_inexistent_indexes(indexes, leave_virtual=False):
    """Removes indexes that don't exist from the given list of indexes.
       @param indexes: list of indexes
       @param leave_virtual: should we leave virtual indexes in the list?
    """
    correct_indexes = get_all_indexes(leave_virtual)
    cleaned = []
    for index in indexes:
        if index in correct_indexes:
            cleaned.append(index)
    return cleaned
