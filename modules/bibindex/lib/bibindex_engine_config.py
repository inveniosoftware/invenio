# -*- coding: utf-8 -*-
##
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

"""
BibIndex indexing engine configuration parameters.
"""

__revision__ = \
    "$Id$"

import os
# configuration parameters read from the general config file:
from invenio.config import CFG_VERSION, CFG_PYLIBDIR
# version number:
BIBINDEX_ENGINE_VERSION = "Invenio/%s bibindex/%s" % (CFG_VERSION, CFG_VERSION)

# safety parameters concerning DB thread-multiplication problem:
CFG_CHECK_MYSQL_THREADS = 0  # to check or not to check the problem?
CFG_MAX_MYSQL_THREADS = 50  # how many threads (connections) we
                           # consider as still safe
CFG_MYSQL_THREAD_TIMEOUT = 20  # we'll kill threads that were sleeping
                              # for more than X seconds

CFG_BIBINDEX_SYNONYM_MATCH_TYPE = {'None': '-None-',
                                   'exact': 'exact',
                                   'leading_to_comma': 'leading_to_comma',
                                   'leading_to_number': 'leading_to_number'}

CFG_BIBINDEX_COLUMN_VALUE_SEPARATOR = ","

CFG_BIBINDEX_INDEX_TABLE_TYPE = {'Words': 'WORD',
                                 'Pairs': 'PAIR',
                                 'Phrases': 'PHRASE'}

CFG_BIBINDEX_WASH_INDEX_TERMS = {'Words': 50,
                                 'Pairs': 100,
                                 'Phrases': 0}

CFG_BIBINDEX_TOKENIZERS_PATH = os.path.join(
    CFG_PYLIBDIR, 'invenio', 'bibindex_tokenizers')

CFG_BIBINDEX_ADDING_RECORDS_STARTED_STR = "%s adding records #%d-#%d started"

CFG_BIBINDEX_OPTIONS_ERROR_MESSAGE = "There is an error in the command line options."

CFG_BIBINDEX_UPDATE_MESSAGE = "Searching for records which should be reindexed..."

CFG_BIBINDEX_UPDATE_MODE = {'Update': 'update',
                            'Insert': 'insert',
                            'Remove': 'remove'}

CFG_BIBINDEX_TOKENIZER_TYPE = {"string": "string",
                               "multifield": "multifield",
                               "recjson": "recjson",
                               "unknown": "unknown"}

CFG_BIBINDEX_SPECIAL_TAGS = {'8564_u': {'Words': 'BibIndexFulltextTokenizer',
                                        'Pairs': 'BibIndexEmptyTokenizer',
                                        'Phrases': 'BibIndexEmptyTokenizer'}}
