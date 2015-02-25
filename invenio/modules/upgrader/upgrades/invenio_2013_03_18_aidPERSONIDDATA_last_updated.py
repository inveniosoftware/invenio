# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013 CERN.
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
    return "Introduces aidPERSONIDDATA last_updated column and new table indexes"

def do_upgrade():
    column_exists = run_sql("SHOW COLUMNS FROM `aidPERSONIDDATA` LIKE 'last_updated'")
    if not column_exists:
        run_sql("""
                ALTER TABLE aidPERSONIDDATA
                ADD COLUMN last_updated TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL
                DEFAULT CURRENT_TIMESTAMP AFTER opt3,
                ADD INDEX `timestamp-b` (`last_updated`)
		""")

    indexes = [i[2] for i in run_sql('SHOW INDEX FROM aidPERSONIDPAPERS')]
    if 'personid-flag-b' not in indexes:
        run_sql("""
		ALTER TABLE aidPERSONIDPAPERS
		ADD INDEX `personid-flag-b` (`personid`, `flag`)
                """)

def estimate():
    return 1

