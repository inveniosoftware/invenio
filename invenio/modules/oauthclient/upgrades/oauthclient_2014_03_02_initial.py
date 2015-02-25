# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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
from sqlalchemy import *
from invenio.ext.sqlalchemy import db
from invenio.modules.upgrader.api import op

depends_on = []


def info():
    return "Initial creation of tables"


def do_upgrade():
    """ Implement your upgrades here  """
    if not op.has_table('remoteACCOUNT'):
        op.create_table(
            'remoteACCOUNT',
            db.Column('id', db.Integer(display_width=15), nullable=False),
            db.Column('user_id', db.Integer(display_width=15), nullable=False),
            db.Column('client_id', db.String(length=255), nullable=False),
            db.Column('extra_data', db.JSON, nullable=True),
            db.ForeignKeyConstraint(['user_id'], ['user.id'], ),
            db.PrimaryKeyConstraint('id'),
            db.UniqueConstraint('user_id', 'client_id'),
            mysql_charset='utf8',
            mysql_engine='MyISAM'
        )
    else:
        warnings.warn("*** Creation of table 'remoteACCOUNT table skipped!'")

    if not op.has_table('remoteTOKEN'):
        op.create_table(
            'remoteTOKEN',
            db.Column('id_remote_account', db.Integer(display_width=15),
                    nullable=False),
            db.Column('token_type', db.String(length=40), nullable=False),
            db.Column('access_token', db.Text(), nullable=False),
            db.Column('secret', db.Text(), nullable=False),
            db.ForeignKeyConstraint(['id_remote_account'],
                                    ['remoteACCOUNT.id'], ),
            db.PrimaryKeyConstraint('id_remote_account', 'token_type'),
            mysql_charset='utf8',
            mysql_engine='MyISAM'
        )
    else:
        warnings.warn("*** Creation of table 'remoteTOKEN' skipped!'")


def estimate():
    return 1
