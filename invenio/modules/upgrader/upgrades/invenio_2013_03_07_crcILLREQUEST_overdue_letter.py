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
    return "New crcILLREQUEST overdue letter columns"

def do_upgrade():
    stmt = run_sql('SHOW CREATE TABLE crcILLREQUEST')[0][1]
    if '`overdue_letter_number` int(3)' not in stmt:
        run_sql("ALTER TABLE crcILLREQUEST ADD COLUMN overdue_letter_number int(3) unsigned NOT NULL default '0'")
    if '`overdue_letter_date` datetime' not in stmt:
        run_sql("ALTER TABLE crcILLREQUEST ADD COLUMN overdue_letter_date datetime NOT NULL default '0000-00-00 00:00:00'")
 

def estimate():
    return 1

def pre_upgrade():
    pass

def post_upgrade():
    pass

