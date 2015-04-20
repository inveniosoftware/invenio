# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011, 2015 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""BibIndex engine stopwords facility."""

__revision__ = "$Id$"

from invenio.base.globals import cfg
from invenio.modules.ranker.registry import configuration
from invenio.legacy.bibindex.engine_utils import get_all_index_names_and_column_values
from invenio.utils.datastructures import LazyDict


def create_stopwords(filename=None):
    """Create stopword dictionary out of FILENAME."""
    filename = filename or cfg['CFG_BIBRANK_PATH_TO_STOPWORDS_FILE']
    stopdict  = {}
    with open(configuration[filename], 'r') as file_descriptor:
        lines = file_descriptor.readlines()
        file_descriptor.close()
        for line in lines:
            stopdict[line.rstrip()] = 1
    return stopdict


def map_stopwords_names_to_stopwords_kb():
    """
        Maps paths to stopwords filename to stopwords dicts.
        It ensures that given stopwords dict is mapped only once.
        Here is an example of an entry:
        "stopwords.kb" : {... ,'of':1, ... }
        It will always map the default stopwords knowledge base given by
        CFG_BIBRANK_PATH_TO_STOPWORDS_FILE. It is useful for bibrank module.
    """
    stopwords_kb_map = {}
    stopwords_kb_map[cfg['CFG_BIBRANK_PATH_TO_STOPWORDS_FILE']] = create_stopwords()
    index_stopwords = get_all_index_names_and_column_values("remove_stopwords")
    for index, stopwords in index_stopwords:
        if stopwords and stopwords != 'No':
            if stopwords not in stopwords_kb_map:
                stopwords_kb_map[stopwords] = create_stopwords(stopwords)
    return stopwords_kb_map


stopwords_kb = LazyDict(map_stopwords_names_to_stopwords_kb)

def is_stopword(word, stopwords=None):
    """Return true if WORD is found among stopwords for given index, false otherwise.
       It searches in the default stopwords knowledge base if stopwords_path is not specified
       which is useful for bibrank module. If one wants to search in diffrent stopwords knowledge base
       he must specify the path to stopwords file.
       :param word: word we want to check if it's stopword or not
       :param stopwords: name of stopwords knowledge base we want to search in
    """
    # note: input word is assumed to be in lowercase
    if stopwords in stopwords_kb:
        if word in stopwords_kb[stopwords]:
            return True
    return False
