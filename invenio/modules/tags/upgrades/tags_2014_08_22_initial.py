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
    return "Creation of wtgTAG and wtgTAG_bibrec tables."


def do_upgrade():
    """Implement your upgrades here."""
    if not op.has_table("wtgTAG"):
        op.create_table(
            'wtgTAG',
            sa.Column('id', mysql.INTEGER(display_width=15), nullable=False),
            sa.Column('name', sa.String(length=255), server_default='', nullable=False, index=True),
            sa.Column('id_user', mysql.INTEGER(display_width=15), server_default='0', nullable=True),
            sa.Column('user_access_rights', mysql.INTEGER(display_width=2), nullable=False),
            sa.Column('id_usergroup', mysql.INTEGER(display_width=15), server_default='0', nullable=True),
            sa.Column('group_access_rights', mysql.INTEGER(display_width=2), nullable=False),
            sa.Column('public_access_rights', mysql.INTEGER(display_width=2), nullable=False),
            sa.Column('show_in_description', sa.Boolean(), nullable=False),
            sa.ForeignKeyConstraint(['id_user'], ['user.id'], ),
            sa.ForeignKeyConstraint(['id_usergroup'], ['usergroup.id'], ),
            sa.PrimaryKeyConstraint('id'),
            mysql_charset='utf8',
            mysql_engine='MyISAM'
        )
    else:
        warnings.warn("*** Creation of 'wtgTAG' table skipped! ***")

    if not op.has_table("wtgTAG_bibrec"):
        op.create_table(
            'wtgTAG_bibrec',
            sa.Column('id_tag', mysql.INTEGER(display_width=15), nullable=False),
            sa.Column('id_bibrec', mysql.INTEGER(display_width=15), nullable=False),
            sa.Column('annotation', sa.Text(convert_unicode=True), nullable=True),
            sa.Column('date_added', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['id_bibrec'], ['bibrec.id'], ),
            sa.ForeignKeyConstraint(['id_tag'], ['wtgTAG.id'], ),
            sa.PrimaryKeyConstraint('id_tag', 'id_bibrec'),
            mysql_charset='utf8',
            mysql_engine='MyISAM'
        )
    else:
        warnings.warn("*** Creation of 'wtgTAG_bibrec' table skipped! ***")


def estimate():
    """Estimate running time of upgrade in seconds (optional)."""
    return 1


def pre_upgrade():
    """Run pre-upgrade checks (optional)."""
    tables = ["wtgTAG", "wtgTAG_bibrec"]
    for table in tables:
        if op.has_table(table):
            warnings.warn(
                "*** Table {0} already exists! *** "
                "This upgrade will *NOT* create the new table.".format(table)
            )


def post_upgrade():
    """Run post-upgrade checks (optional)."""
    pass
