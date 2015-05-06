# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

"""Upgrade recipe."""

import warnings

from invenio.ext.sqlalchemy import db
from invenio.legacy.dbquery import run_sql
from invenio.modules.upgrader.api import op

from sqlalchemy.engine import reflection

depends_on = ['invenio_release_1_2_0']


def exists_id_column():
    """Check if id column already exists."""
    insp = reflection.Inspector.from_engine(db.engine)
    columns = insp.get_columns('accROLE_accACTION_accARGUMENT')

    return any([column['name'] == 'id' for column in columns])


def info():
    """Info."""
    return "Add new column id to accROLE_accACTION_accARGUMENT table."""


def do_upgrade():
    """Implement your upgrades here."""
    if exists_id_column():
        warnings.warn(
            """Upgrade skipped. """
            """Column 'id' already exists on accROLE_accACTION_accARGUMENT.""")
        return
    if op.impl.dialect.name != 'mysql':
        warnings.warn("""This upgrade supports only MySQL.""")
        return

    # table accROLE_accACTION_accARGUMENT

    # - drop primary key
    # - add "id" column int(15) unsigned
    # - set "id" as primary key, autoincrement
    # - column id_accROLE, id_accACTION, id_accARGUMENT, argumentlistid server
    #   default = None
    op.execute(
        """
        SET SESSION sql_mode = ANSI_QUOTES;
        ALTER TABLE "accROLE_accACTION_accARGUMENT"
        CHANGE COLUMN "id_accROLE" "id_accROLE" INT(15) UNSIGNED NULL ,
        CHANGE COLUMN "id_accACTION" "id_accACTION" INT(15) UNSIGNED NULL ,
        CHANGE COLUMN "id_accARGUMENT" "id_accARGUMENT" INT(15) NULL ,
        CHANGE COLUMN "argumentlistid" "argumentlistid" MEDIUMINT(8) NULL ,
        ADD COLUMN "id" INT(15) UNSIGNED NOT NULL AUTO_INCREMENT,
        DROP PRIMARY KEY,
        ADD PRIMARY KEY ("id");
        """)


def estimate():
    """Estimate running time of upgrade in seconds (optional)."""
    total = run_sql(
        """SELECT count(*) FROM "accROLE_accACTION_accARGUMENT" """)
    return int(float(int(total[0][0])) / 1000) + 1


def pre_upgrade():
    """Run pre-upgrade checks (optional)."""
    if exists_id_column():
        warnings.warn(
            """Column 'id' already exists on accROLE_accACTION_accARGUMENT.""")
    if op.impl.dialect.name != 'mysql':
        warnings.warn("""This upgrade supports only MySQL.""")


def post_upgrade():
    """Run post-upgrade checks (optional)."""
    pass
