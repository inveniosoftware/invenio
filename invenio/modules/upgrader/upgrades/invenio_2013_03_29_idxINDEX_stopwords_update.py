# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013 CERN.
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

from __future__ import print_function


from invenio.legacy.dbquery import run_sql

depends_on = ['invenio_2013_03_28_idxINDEX_tokenizer']

def info():
    return "Updates column remove_stopwords of idxINDEX table with path to default 'stopwords' file if necessary"


def do_upgrade():
    #different stopwords file for every index:
    #need to update default stopwords path for every index
    from invenio.config import CFG_BIBINDEX_REMOVE_STOPWORDS
    if CFG_BIBINDEX_REMOVE_STOPWORDS:
        if CFG_BIBINDEX_REMOVE_STOPWORDS == 1:
            run_sql("UPDATE idxINDEX SET remove_stopwords='stopwords.kb'")


def estimate():
    return 1

def pre_upgrade():
    pass

def post_upgrade():
    print('NOTE: please double check your new index stopword settings in BibIndex Admin Interface.')
