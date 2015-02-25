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

depends_on = ['invenio_2012_10_29_idxINDEX_new_indexer_column']


def info():
    return "Introduces new column for idxINDEX table: synonym_kbrs"


def do_upgrade():
    #first step: change tables
    stmt = run_sql('SHOW CREATE TABLE idxINDEX')[0][1]
    if '`synonym_kbrs` varchar(255)' not in stmt:
        run_sql("ALTER TABLE idxINDEX ADD COLUMN synonym_kbrs varchar(255) NOT NULL default '' AFTER indexer")
    #second step: fill tables
    run_sql("UPDATE idxINDEX SET synonym_kbrs='INDEX-SYNONYM-TITLE,exact' WHERE name IN ('global','title')")
    #third step: check invenio.conf
    from invenio.config import CFG_BIBINDEX_SYNONYM_KBRS
    if CFG_BIBINDEX_SYNONYM_KBRS:
        for index in CFG_BIBINDEX_SYNONYM_KBRS:
            synonym = ",".join(CFG_BIBINDEX_SYNONYM_KBRS[index])
            query = "UPDATE idxINDEX SET synonym_kbrs='%s' WHERE name=%s" % (synonym, index)
            run_sql(query)

def estimate():
    return 1

def pre_upgrade():
    pass

def post_upgrade():
    print('NOTE: please double check your new index synonym settings in BibIndex Admin Interface.')
