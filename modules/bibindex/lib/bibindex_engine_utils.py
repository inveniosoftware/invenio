# -*- coding:utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2010, 2011, 2012, 2013, 2014 CERN.
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

"""bibindex_engine_utils: here are some useful regular experssions for tokenizers
   and several helper functions.
"""


import re
import sys
import os

from invenio.dbquery import run_sql, \
    DatabaseError
from invenio.bibtask import write_message
from invenio.search_engine_utils import get_fieldvalues
from invenio.config import \
    CFG_BIBINDEX_CHARS_PUNCTUATION, \
    CFG_BIBINDEX_CHARS_ALPHANUMERIC_SEPARATORS
from invenio.pluginutils import PluginContainer
from invenio.bibindex_engine_config import CFG_BIBINDEX_TOKENIZERS_PATH, \
    CFG_BIBINDEX_COLUMN_VALUE_SEPARATOR

from invenio.memoiseutils import Memoise

latex_formula_re = re.compile(r'\$.*?\$|\\\[.*?\\\]')
phrase_delimiter_re = re.compile(r'[\.:;\?\!]')
space_cleaner_re = re.compile(r'\s+')
re_block_punctuation_begin = re.compile(
    r"^" + CFG_BIBINDEX_CHARS_PUNCTUATION + "+")
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
    return PluginContainer(os.path.join(CFG_BIBINDEX_TOKENIZERS_PATH, 'BibIndex*.py'))


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
        write_message("Exception caught for SQL statement: %s; column %s might not exist" %
                      (query, column_name), sys.stderr)
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
            out[row[0]] = tuple(
                kb_data.split(CFG_BIBINDEX_COLUMN_VALUE_SEPARATOR))
    return out


def get_index_remove_stopwords(index_id):
    """Returns value of a remove_stopword field from idxINDEX database table
       if it's not 'No'. If it's 'No' returns False.
       Just for consistency with WordTable.
       @param index_id: id of the index
    """
    try:
        result = run_sql(
            "SELECT remove_stopwords FROM idxINDEX WHERE ID=%s", (index_id, ))[0][0]
    except:
        return False
    if result == 'No' or result == '':
        return False
    return result


def get_index_remove_html_markup(index_id):
    """ Gets remove_html_markup parameter from database ('Yes' or 'No') and
        changes it  to True, False.
        Just for consistency with WordTable."""
    try:
        result = run_sql(
            "SELECT remove_html_markup FROM idxINDEX WHERE ID=%s", (index_id, ))[0][0]
    except:
        return False
    if result == 'Yes':
        return True
    return False


def get_index_remove_latex_markup(index_id):
    """ Gets remove_latex_markup parameter from database ('Yes' or 'No') and
        changes it  to True, False.
        Just for consistency with WordTable."""
    try:
        result = run_sql(
            "SELECT remove_latex_markup FROM idxINDEX WHERE ID=%s", (index_id, ))[0][0]
    except:
        return False
    if result == 'Yes':
        return True
    return False


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
        if str(e).find("Unknown table") > -1:
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


def filter_for_virtual_indexes(index_list):
    """
        Function removes all non-virtual indexes
        from given list of indexes.
        @param index_list: list of index names
    """
    try:
        virtual = zip(*get_all_virtual_indexes())[1]
        selected = set(virtual) & set(index_list)
        return list(selected)
    except IndexError:
        return []
    return []


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


def get_field_tags(field, tagtype="marc"):
    """Returns a list of tags for the field code 'field'. Works
       for both MARC and nonMARC tags.
       Returns empty list in case of error.
       Example: field='author', output=['100__%','700__%'].
       @param tagtype: can be: "marc" or "nonmarc", default value
            is "marc" for backward compatibility
    """
    query = """SELECT t.%s FROM tag AS t,
                                field_tag AS ft,
                                field AS f
                WHERE f.code=%%s AND
                ft.id_field=f.id AND
                t.id=ft.id_tag
                ORDER BY ft.score DESC"""
    if tagtype == "marc":
        query = query % "value"
        res = run_sql(query, (field,))
        return [row[0] for row in res]
    else:
        query = query % "recjson_value"
        res = run_sql(query, (field,))
        values = []
        for row in res:
            values.extend(row[0].split(","))
        return values


def get_marc_tag_indexes(tag, virtual=True):
    """Returns indexes names and ids corresponding to the given tag
       @param tag: MARC tag in one of the forms:
            'xx%', 'xxx', 'xxx__a', 'xxx__%'
       @param virtual: if True function will also return virtual indexes"""
    tag2 = tag[0:2] + "%"  # for tags in the form: 10%
    tag3 = tag[:-1] + "%"  # for tags in the form: 100__%
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
        tag3 = tag + "%"  # for all tags which start from 'tag'
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
    return ()


def get_nonmarc_tag_indexes(nonmarc_tag, virtual=True):
    """Returns index names and ids corresponding to the given nonmarc tag
       (nonmarc tag can be also called 'bibfield field').
       If param 'virtual' is set to True function will also return
       virtual indexes"""
    query = """SELECT DISTINCT w.id, w.name FROM idxINDEX AS w,
                                                 idxINDEX_field AS wf,
                                                 field_tag AS ft,
                                                 tag as t
               WHERE (t.recjson_value LIKE %s OR
                      t.recjson_value LIKE %s OR
                      t.recjson_value LIKE %s OR
                      t.recjson_value=%s) AND
                     t.id=ft.id_tag AND
                     ft.id_field=wf.id_field AND
                     wf.id_idxINDEX=w.id"""

    at_the_begining = nonmarc_tag + ',%%'
    in_the_middle = '%%,' + nonmarc_tag + ',%%'
    at_the_end = '%%,' + nonmarc_tag

    res = run_sql(
        query, (at_the_begining, in_the_middle, at_the_end, nonmarc_tag))
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
    return ()


def get_index_tags(indexname, virtual=True, tagtype="marc"):
    """Returns the list of tags that are indexed inside INDEXNAME.
       Returns empty list in case there are no tags indexed in this index.
       Note: uses get_field_tags() defined before.
       Example: field='author', output=['100__%', '700__%'].
       @param tagtype: can be: "marc" or "nonmarc", default value
            is "marc" for backward compatibility
    """
    out = []
    query = """SELECT f.code FROM idxINDEX AS w,
                                  idxINDEX_field AS wf,
                                  field AS f
               WHERE w.name=%s AND
                     w.id=wf.id_idxINDEX AND
                     f.id=wf.id_field"""
    res = run_sql(query, (indexname,))
    for row in res:
        out.extend(get_field_tags(row[0], tagtype))
    if not out and virtual:
        index_id = get_index_id_from_index_name(indexname)
        try:
            dependent_indexes = map(
                str, zip(*get_virtual_index_building_blocks(index_id))[0])
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
            tags |= set(get_field_tags(row[0], tagtype))
        out = list(tags)
    out = [tag for tag in out if tag]
    return out


def get_field_indexes(field):
    """Returns indexes names and ids corresponding to the given field"""
    if recognize_marc_tag(field):
        # field is actually a tag
        return get_marc_tag_indexes(field, virtual=False)
    else:
        return get_nonmarc_tag_indexes(field, virtual=False)


get_field_indexes_memoised = Memoise(get_field_indexes)


def get_last_updated(index_name):
    """Returns min modification date for 'indexes':
       min(last_updated)
       @param indexes: list of indexes
    """
    query = """SELECT last_updated FROM idxINDEX WHERE name = %s"""
    res = run_sql(query, (index_name,))
    return res[0][0]


def get_min_last_updated(indexes):
    """Returns min modification date for 'indexes':
       min(last_updated)
       @param indexes: list of indexes
    """
    query = """SELECT min(last_updated) FROM idxINDEX WHERE name IN ("""
    query += "%s,"*len(indexes)
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


def get_records_range_for_index(index_id):
    """
        Get records range for given index.
    """
    try:
        query = """SELECT min(id_bibrec), max(id_bibrec) FROM idxWORD%02dR""" % index_id
        resp = run_sql(query)
        if resp:
            return resp[0]
        return None
    except Exception:
        return None


def make_prefix(index_name):
    """
        Creates a prefix for specific index which is added
        to every word from this index stored in reversed table
        of corresponding virtual index.
        @param index_name: name of the dependent index we want to create prefix for
    """
    return "__" + index_name + "__"


class UnknownTokenizer(Exception):
    pass


def list_union(list1, list2):
    "Returns union of the two lists."
    union_dict = {}
    for e in list1:
        union_dict[e] = 1
    for e in list2:
        union_dict[e] = 1
    return union_dict.keys()


def get_index_fields(index_id):
    """Returns fields that are connected to index specified by
       index_id.
    """
    query = """SELECT f.id, f.name FROM field as f,
                                        idxINDEX as w,
                                        idxINDEX_field as wf
               WHERE f.id=wf.id_field AND
                     wf.id_idxINDEX=w.id AND
                     w.id=%s
            """
    index_fields = run_sql(query, (index_id, ))
    return index_fields


def recognize_marc_tag(tag):
    """Checks if tag is a MARC tag or not"""
    tag_len = len(tag)
    if 3 <= tag_len <= 6 and tag[0:3].isdigit():
        return True
    if tag_len == 3 and tag[0:2].isdigit() and tag[2] == '%':
        return True
    return False


def _is_collection(subfield):
    """Checks if a type is a collection;
       get_values_recursively internal function."""
    return hasattr(subfield, '__iter__')


def _get_values(subfield):
    """Returns values of a subfield suitable for later tokenizing;
       get_values_recursively internal function."""
    if type(subfield) == dict:
        return subfield.values()
    else:
        return subfield


def get_values_recursively(subfield, phrases):
    """Finds all values suitable for later tokenizing in
       field/subfield of bibfield record.
       @param subfield: name of the field/subfield
       @param phrases: container for phrases (for example empty list)

       FIXME: move this function to bibfield!
       As soon as possible. Note that journal tokenizer
       also needs to be changed.
    """
    if _is_collection(subfield):
        for s in _get_values(subfield):
            get_values_recursively(s, phrases)
    elif subfield is not None:
        phrases.append(str(subfield))


def get_author_canonical_ids_for_recid(recID):
    """
    Return list of author canonical IDs (e.g. `J.Ellis.1') for the
    given record.  Done by consulting BibAuthorID module.
    """
    return [word[0] for word in run_sql("""SELECT data FROM aidPERSONIDDATA
        JOIN aidPERSONIDPAPERS USING (personid) WHERE bibrec=%s AND
        tag='canonical_name' AND flag>-2""", (recID, ))]


def create_range_list(int_list):
    """Converts an ordered list of integers to a range list.
    If the input list is not ordered, the resulting range list can be
    unordered and non maximal.

    @param int_list: an **ordered** list of positive integers (not zero)
    @return: an ordered, maximal, non overlapping list of ranges [start, end]
        edge inclusive
    """
    if not int_list:
        return []
    row = int_list[0]
    if not row:
        return []
    else:
        range_list = [[row, row]]
    for row in int_list[1:]:
        row_id = row
        if row_id == range_list[-1][1] + 1:
            range_list[-1][1] = row_id
        else:
            range_list.append([row_id, row_id])
    return range_list


def unroll_range_list(range_list):
    """Converts a **non overlapping** range list to a list of integers.

    @param range_list: unordered list of non overlapping ranges [start, end],
        edge inclusive. e.g. [[1,3], [123, 125], [20, 22]]
    @return: unordered list of unique integers
    """
    int_list = []
    for single_range in range_list:
        int_list.extend(range(single_range[0], single_range[1] + 1))
    return int_list
