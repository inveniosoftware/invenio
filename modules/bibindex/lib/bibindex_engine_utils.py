# -*- coding:utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2010, 2011, 2012 CERN.
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

from invenio.dbquery import run_sql, DatabaseError
from invenio.bibtask import write_message
from invenio.search_engine_utils import get_fieldvalues
from invenio.config import \
     CFG_BIBINDEX_CHARS_PUNCTUATION, \
     CFG_BIBINDEX_CHARS_ALPHANUMERIC_SEPARATORS
from invenio.pluginutils import PluginContainer
from invenio.bibindex_engine_config import CFG_BIBINDEX_TOKENIZERS_PATH


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
