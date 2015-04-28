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
from sqlalchemy.dialects import mysql

from invenio.ext.sqlalchemy import db
from invenio.modules.upgrader.api import op

depends_on = [u'accounts_2015_03_06_passlib',
              u'accounts_2015_01_14_add_name_columns']


def info():
    return "Default value for family/given names."


def do_upgrade():
    """Implement your upgrades here."""
    m = db.MetaData(bind=db.engine)
    m.reflect()
    u = m.tables['user']

    conn = db.engine.connect()
    conn.execute(u.update().where(u.c.family_name == None).values(
        family_name=''))
    conn.execute(u.update().where(u.c.given_names == None).values(
        given_names=''))

    op.alter_column('user', 'family_name',
                    existing_type=mysql.VARCHAR(length=255),
                    nullable=False,
                    server_default='')
    op.alter_column('user', 'given_names',
                    existing_type=mysql.VARCHAR(length=255),
                    nullable=False,
                    server_default='')


def estimate():
    """Estimate running time of upgrade in seconds (optional)."""
    return 1
