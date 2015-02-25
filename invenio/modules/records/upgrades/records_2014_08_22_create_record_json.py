# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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
import sqlalchemy as sa
from invenio.ext.sqlalchemy import db
from invenio.modules.upgrader.api import op


depends_on = ['records_2014_04_14_json_type_fix']


def info():
    return "Create table record_json."


def do_upgrade():
    """Implement your upgrades here."""
    if not op.has_table("record_json"):
        op.create_table(
            'record_json',
            sa.Column('id', db.MediumInteger(8, unsigned=True), nullable=False),
            sa.Column('json', db.JSON, nullable=False),
            sa.ForeignKeyConstraint(['id'], ['bibrec.id'], ),
            sa.PrimaryKeyConstraint('id'),
            mysql_charset='utf8',
            mysql_engine='MyISAM'
        )
    else:
        warnings.warn("*** Creation of 'record_json' table skipped! ***")


def estimate():
    """Estimate running time of upgrade in seconds (optional)."""
    return 1


def pre_upgrade():
    """Run pre-upgrade checks (optional)."""
    table = "record_json"
    if op.has_table(table):
        warnings.warn(
            "*** Table {0} already exists! *** "
            "This upgrade will *NOT* create the new table.".format(table)
        )


def post_upgrade():
    """Run post-upgrade checks (optional)."""
    pass
