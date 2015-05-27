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
# MERCHANTABILITY or FITNESS FOR A PARTIiULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import warnings
import sqlalchemy as sa

from invenio.ext.sqlalchemy import db
from invenio.modules.upgrader.api import op


depends_on = []


def info():
    return "Create table record_json_history."


def do_upgrade():
    """Create new table for the record history.

    To fill it up please use:
    `python scripts/history_record_migration_kit.py run`.
    """
    if not op.has_table("record_json_history"):
        op.create_table(
            'record_json_history',
            sa.Column(
                'id', db.MediumInteger(8, unsigned=True), nullable=False),
            sa.Column('revision', db.DateTime, nullable=False),
            sa.Column('json', db.JSON, nullable=False),
            sa.PrimaryKeyConstraint('id', 'revision'),
            mysql_charset='utf8',
            mysql_engine='MyISAM'
        )
    else:
        warnings.warn(
            "*** Creation of 'record_json_history' table skipped! ***")


def estimate():
    """Estimate running time of upgrade in seconds (optional)."""
    return 1


def pre_upgrade():
    """Run pre-upgrade checks (optional)."""
    table = "record_json_history"
    if op.has_table(table):
        warnings.warn(
            "*** Table {0} already exists! *** "
            "This upgrade will *NOT* create the new table.".format(table)
        )
    warnings.warn("Manually populate new history table  using "
                  "'python scripts/history_record_migration_kit.py run'.")
