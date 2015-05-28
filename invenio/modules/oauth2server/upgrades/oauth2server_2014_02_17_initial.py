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

"""Upgrade recipe."""

import warnings

from invenio.ext.sqlalchemy import db
from invenio.modules.upgrader.api import op

from sqlalchemy_utils.types import URLType


depends_on = []


def info():
    """Info."""
    return "Tables for oauth2server"


def do_upgrade():
    """Implement your upgrades here."""
    if not op.has_table('oauth2CLIENT'):
        op.create_table(
            'oauth2CLIENT',
            db.Column('name', db.String(length=40), nullable=True),
            db.Column('description', db.Text(), nullable=True),
            db.Column('website', URLType(), nullable=True),
            db.Column('user_id', db.Integer(15, unsigned=True), nullable=True),
            db.Column('client_id', db.String(length=255), nullable=False),
            db.Column('client_secret', db.String(length=255), nullable=False),
            db.Column('is_confidential', db.Boolean(), nullable=True),
            db.Column('is_internal', db.Boolean(), nullable=True),
            db.Column('_redirect_uris', db.Text(), nullable=True),
            db.Column('_default_scopes', db.Text(), nullable=True),
            db.ForeignKeyConstraint(['user_id'], ['user.id'], ),
            db.PrimaryKeyConstraint('client_id'),
            mysql_charset='utf8',
            mysql_engine='MyISAM'
        )
    else:
        warnings.warn("*** Creation of table 'oauth2CLIENT' skipped!")

    if not op.has_table('oauth2TOKEN'):
        op.create_table(
            'oauth2TOKEN',
            db.Column('id', db.Integer(15, unsigned=True), autoincrement=True,
                      nullable=False),
            db.Column('client_id', db.String(length=40), nullable=False),
            db.Column('user_id', db.Integer(15, unsigned=True), nullable=True),
            db.Column('token_type', db.String(length=255), nullable=True),
            db.Column('access_token', db.String(length=255), nullable=True),
            db.Column('refresh_token', db.String(length=255), nullable=True),
            db.Column('expires', db.DateTime(), nullable=True),
            db.Column('_scopes', db.Text(), nullable=True),
            db.Column('is_personal', db.Boolean(), nullable=True),
            db.Column('is_internal', db.Boolean(), nullable=True),
            db.ForeignKeyConstraint(
                ['client_id'], ['oauth2CLIENT.client_id'],),
            db.ForeignKeyConstraint(['user_id'], ['user.id'], ),
            db.PrimaryKeyConstraint('id'),
            db.UniqueConstraint('access_token'),
            db.UniqueConstraint('refresh_token'),
            mysql_charset='utf8',
            mysql_engine='MyISAM'
        )
    else:
        warnings.warn("*** Creation of table 'oauth2TOKEN' skipped!")

    # # Following create index causes problems
    # op.create_index(
    #     'ix_oauth2CLIENT_client_secret', 'oauth2CLIENT', ['client_secret'],
    #     unique=True
    # )


def estimate():
    """Estimate."""
    return 1
