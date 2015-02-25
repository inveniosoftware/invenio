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

from invenio.legacy.dbquery import run_sql

depends_on = ['invenio_2013_09_25_virtual_indexes']

def info():
    return "Small compatibility change in idxINDEX table"

def do_upgrade():
    res = run_sql("SELECT DISTINCT(id_virtual) FROM idxINDEX_idxINDEX")
    for row in res:
        run_sql("UPDATE idxINDEX SET indexer='virtual' WHERE id=%s", (row[0],))

def estimate():
    return 1

def pre_upgrade():
    pass

def post_upgrade():
    pass
