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
from sqlalchemy.dialects import mysql
from invenio.modules.upgrader.api import op

depends_on = []


def info():
    return "Add required tables for workflows module."


def do_upgrade():
    """Implement your upgrades here."""
    if not op.has_table('bwlWORKFLOW'):
        op.create_table(
            'bwlWORKFLOW',
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('created', sa.DateTime(), nullable=False),
            sa.Column('modified', sa.DateTime(), nullable=False),
            sa.Column('id_user', mysql.INTEGER(), nullable=False),
            sa.Column('_extra_data', sa.LargeBinary(), nullable=False),
            sa.Column('status', mysql.INTEGER(), nullable=False),
            sa.Column(
                'current_object', mysql.INTEGER(), nullable=False),
            sa.Column(
                'counter_initial', mysql.INTEGER(), nullable=False),
            sa.Column(
                'counter_halted', mysql.INTEGER(), nullable=False),
            sa.Column(
                'counter_error', mysql.INTEGER(), nullable=False),
            sa.Column(
                'counter_finished', mysql.INTEGER(), nullable=False),
            sa.Column(
                'module_name', sa.String(length=64), nullable=False),
            sa.PrimaryKeyConstraint('uuid'),
            mysql_charset='utf8',
            mysql_engine='MyISAM'
        )
    else:
        warnings.warn("*** Creation of 'bwlWORKFLOW' table skipped! ***")

    if not op.has_table('bwlOBJECT'):
        op.create_table(
            'bwlOBJECT',
            sa.Column('id', mysql.INTEGER(), nullable=False),
            sa.Column('_data', sa.LargeBinary(), nullable=False),
            sa.Column('_extra_data', sa.LargeBinary(), nullable=False),
            sa.Column(
                'id_workflow', sa.String(length=36), nullable=True),
            sa.Column(
                'version', mysql.INTEGER(display_width=3), nullable=False),
            sa.Column('id_parent', mysql.INTEGER(), nullable=True),
            sa.Column('created', sa.DateTime(), nullable=False),
            sa.Column('modified', sa.DateTime(), nullable=False),
            sa.Column('status', sa.String(length=255), nullable=False),
            sa.Column(
                'data_type', sa.String(length=150), nullable=True),
            sa.Column('uri', sa.String(length=500), nullable=True),
            sa.Column('id_user', mysql.INTEGER(), nullable=False),
            sa.ForeignKeyConstraint(['id_parent'], ['bwlOBJECT.id'], ),
            sa.ForeignKeyConstraint(
                ['id_workflow'], ['bwlWORKFLOW.uuid'], ),
            sa.PrimaryKeyConstraint('id'),
            mysql_charset='utf8',
            mysql_engine='MyISAM'
        )
    else:
        warnings.warn("*** Creation of 'bwlOBJECT' table skipped! ***")

    if not op.has_table('bwlWORKFLOWLOGGING'):
        op.create_table(
            'bwlWORKFLOWLOGGING',
            sa.Column('id', mysql.INTEGER(), nullable=False),
            sa.Column(
                'id_object', sa.String(length=255), nullable=False),
            sa.Column('log_type', mysql.INTEGER(), nullable=False),
            sa.Column('created', sa.DateTime(), nullable=True),
            sa.Column('message', sa.TEXT(), nullable=False),
            sa.ForeignKeyConstraint(
                ['id_object'], ['bwlWORKFLOW.uuid'], ),
            sa.PrimaryKeyConstraint('id'),
            mysql_charset='utf8',
            mysql_engine='MyISAM'
        )
    else:
        warnings.warn("*** Creation of 'bwlWORKFLOWLOGGING' table skipped! ***")

    if not op.has_table('bwlOBJECTLOGGING'):
        op.create_table(
            'bwlOBJECTLOGGING',
            sa.Column('id', mysql.INTEGER(), nullable=False),
            sa.Column('id_object', mysql.INTEGER(
                display_width=255), nullable=False),
            sa.Column('log_type', mysql.INTEGER(), nullable=False),
            sa.Column('created', sa.DateTime(), nullable=True),
            sa.Column('message', sa.TEXT(), nullable=False),
            sa.ForeignKeyConstraint(['id_object'], ['bwlOBJECT.id'], ),
            sa.PrimaryKeyConstraint('id'),
            mysql_charset='utf8',
            mysql_engine='MyISAM'
        )
    else:
        warnings.warn("*** Creation of 'bwlOBJECTLOGGING' table skipped! ***")


def estimate():
    """Estimate running time of upgrade in seconds (optional)."""
    return 1


def pre_upgrade():
    """Run pre-upgrade checks (optional)."""
    tables = ["bwlWORKFLOW", "bwlOBJECT", "bwlWORKFLOWLOGGING", "bwlOBJECTLOGGING"]
    for table in tables:
        if op.has_table(table):
            warnings.warn(
                "*** Table {0} already exists! *** "
                "This upgrade will *NOT* create the new table.".format(table)
            )


def post_upgrade():
    """Run post-upgrade checks (optional)."""
    pass
