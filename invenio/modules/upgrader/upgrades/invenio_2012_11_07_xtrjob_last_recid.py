# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012 CERN.
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

import warnings
from invenio.legacy.dbquery import run_sql
from invenio.utils.text import wait_for_user

depends_on = ['invenio_release_1_1_0']

def info():
    return "New xtrJOB.last_recid column"

def do_upgrade():
    create_statement = run_sql('SHOW CREATE TABLE xtrJOB')[0][1]
    if '`last_recid` mediumint(8)' not in create_statement:
        run_sql("ALTER TABLE xtrJOB ADD COLUMN last_recid mediumint(8) unsigned NOT NULL")

def estimate():
    return 1

def pre_upgrade():
    pass

def post_upgrade():
    pass
