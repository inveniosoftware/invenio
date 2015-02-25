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

"""communityFEATURED table addition."""

from invenio.ext.sqlalchemy import db
from invenio.modules.upgrader.api import op

depends_on = [u'communities_2014_03_07_ranker']


def info():
    """Short description of upgrade displayed to end-user."""
    return "communityFEATURED table addition"


def do_upgrade():
    """Implement your upgrades here."""
    op.create_table('communityFEATURED',
                    db.Column('id', db.Integer(), nullable=False),
                    db.Column('id_community', db.String(length=100),
                              nullable=False),
                    db.Column('start_date', db.DateTime(), nullable=False),
                    db.ForeignKeyConstraint(['id_community'],
                                            ['community.id'], ),
                    db.PrimaryKeyConstraint('id'),
                    mysql_charset='utf8',
                    mysql_engine='MyISAM'
                    )


def estimate():
    """Estimate the time needed to apply upgrades."""
    return 1
