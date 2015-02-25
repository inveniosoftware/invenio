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
import zlib
from invenio.legacy.dbquery import run_sql

depends_on = ['invenio_release_1_1_0']

def info():
    return "Change bibHOLDINGPEN.changeset_xml storage to longblob"

def do_upgrade():
    create_statement = run_sql('SHOW CREATE TABLE bibHOLDINGPEN')[0][1]
    if '`changeset_xml` longblob' not in create_statement:
        # First do a backup of the table
        run_sql("""CREATE TABLE IF NOT EXISTS bibHOLDINGPEN_backup SELECT * FROM bibHOLDINGPEN""")
        # And alter it
        run_sql("ALTER TABLE bibHOLDINGPEN CHANGE changeset_xml changeset_xml longblob NOT NULL")

        # Compress all the record xml content
        for row in run_sql("""SELECT * FROM bibHOLDINGPEN"""):
            try:
                record_xml = row[2]
                zlib.decompress(record_xml)
            except zlib.error:
                run_sql("UPDATE bibHOLDINGPEN SET changeset_xml=%s WHERE changeset_id=%s", (zlib.compress(record_xml), row[0]))

        warnings.warn("A backup table bibHOLDINGPEN_backup was created in the process. It can be deleted now.")

def estimate():
    """  Estimate running time of upgrade in seconds (optional). """
    count_rows = run_sql("SELECT COUNT(*) FROM bibHOLDINGPEN")[0][0]
    return count_rows / 20

def pre_upgrade():
    """Check for potentially invalid revisions"""
    res = run_sql("""SELECT DISTINCT(changeset_id) FROM bibHOLDINGPEN
                     WHERE LENGTH(changeset_xml) =  %s""", [2**16-1])
    if res:
        warnings.warn("""You have %s holding pen entries with potentially corrupt data!
                         You can find the rows affected with the sql command:
                         SELECT DISTINCT(changeset_id) FROM bibHOLDINGPEN
                         WHERE LENGTH(changeset_xml) =  65535""" % len(res))

        from invenio.utils.text import wait_for_user
        try:
            wait_for_user("\nThis upgrade will delete all the corrupted entries. A backup table bibHOLDINGPEN_backup will be created.\n")
        except SystemExit:
            raise RuntimeError("Upgrade aborted by user.")

        for r in res:
            run_sql("""DELETE FROM bibHOLDINGPEN WHERE changeset_id=%s""" % r[0])

def post_upgrade():
    pass
