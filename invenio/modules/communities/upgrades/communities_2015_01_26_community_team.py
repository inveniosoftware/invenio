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

from sqlalchemy import *
from invenio.ext.sqlalchemy import db
from invenio.modules.upgrader.api import op
from sqlalchemy_utils.types.choice import ChoiceType

depends_on = [u'communities_2014_10_17_featured_communities']


def info():
    return "Short description of upgrade displayed to end-user"


def do_upgrade():
    """Upgrades here."""

    TEAM_RIGHTS = {
        'ADMIN': 'A',
        'WRITE': 'W',
        'READ': 'R'
    }

    op.create_table(
        'communityTEAM',
        db.Column('id_community', db.String(length=100), nullable=False),
        db.Column('id_usergroup', db.Integer(15, unsigned=True),
                  nullable=False),
        db.Column('team_rights', ChoiceType(
            map(lambda (k, v): (v, k), TEAM_RIGHTS.items()),
        ), nullable=False, server_default=TEAM_RIGHTS['READ']),
        db.ForeignKeyConstraint(['id_community'], [u'community.id'], ),
        db.ForeignKeyConstraint(['id_usergroup'], [u'usergroup.id'], ),
        db.PrimaryKeyConstraint('id_community', 'id_usergroup'),
        mysql_charset='utf8',
        mysql_engine='MyISAM'
    )


def estimate():
    """Estimate running time of upgrade in seconds (optional)."""
    return 1
