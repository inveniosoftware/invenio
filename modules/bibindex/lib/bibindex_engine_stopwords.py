## This file is part of Invenio.
## Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011, 2014 CERN.
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

"""BibIndex engine stopwords facility."""

__revision__ = "$Id$"

from invenio.config import CFG_BIBRANK_PATH_TO_STOPWORDS_FILE, \
    CFG_ETCDIR
from invenio.bibindex_engine_utils import get_all_index_names_and_column_values


def create_stopwords(filename=CFG_BIBRANK_PATH_TO_STOPWORDS_FILE):
    """Create stopword dictionary out of FILENAME."""
    try:
        file_descriptor = open(filename, 'r')
    except IOError:
        return {}
    lines = file_descriptor.readlines()
    file_descriptor.close()
    stopdict = {}
    for line in lines:
        stopdict[line.rstrip()] = 1
    return stopdict


def map_stopwords_paths_to_stopwords_kb():
    """
        Maps paths to stopwords file to stopwords dicts.
        It ensures that given stopwords dict is mapped only once.
        Here is an example of an entry:
        "/opt/invenio/etc/bibrank/stopwords.kb" : {... ,'of':1, ... }
        It will always map the default stopwords knowledge base given by
        CFG_BIBRANK_PATH_TO_STOPWORDS_FILE. It is useful for bibrank module.
    """
    stopwords_kb_map = {}
    stopwords_kb_map[CFG_BIBRANK_PATH_TO_STOPWORDS_FILE] = create_stopwords()
    index_stopwords = get_all_index_names_and_column_values("remove_stopwords")
    for _, stopwords in index_stopwords:
        if stopwords and stopwords != 'No':
            stopwords_path = CFG_ETCDIR + "/bibrank/" + stopwords
            if not stopwords_kb_map.has_key(stopwords_path):
                stopwords_kb_map[
                    stopwords_path] = create_stopwords(stopwords_path)
    return stopwords_kb_map


stopwords_kb = map_stopwords_paths_to_stopwords_kb()


def is_stopword(word, stopwords_path=CFG_BIBRANK_PATH_TO_STOPWORDS_FILE):
    """Return true if WORD is found among stopwords for given index, false otherwise.
       It searches in the default stopwords knowledge base if stopwords_path is not specified
       which is useful for bibrank module. If one wants to search in diffrent stopwords knowledge base
       he must specify the path to stopwords file.
       @param word: word we want to check if it's stopword or not
       @param index: path to stopwords knowledge base we want to search in
    """
    # note: input word is assumed to be in lowercase
    if stopwords_kb.has_key(stopwords_path):
        if stopwords_kb[stopwords_path].has_key(word):
            return True
    return False
