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

from invenio.ext.sqlalchemy import db
from invenio.modules.upgrader.api import op
from sqlalchemy.dialects import mysql

depends_on = []


def info():
    return "Short description of upgrade displayed to end-user"


def do_upgrade():
    """ Implement your upgrades here  """
    op.create_table(
        'pages',
        db.Column('id', mysql.INTEGER(display_width=15), nullable=False),
        db.Column('url', db.String(length=100), nullable=False),
        db.Column('title', db.String(length=200), nullable=True),
        db.Column('content', db.TEXT(length=4294967294), nullable=True),
        db.Column('template_name', db.String(length=70), nullable=True),
        db.Column('created', db.DateTime(), nullable=False),
        db.Column('last_modified', db.DateTime(), nullable=False),
        db.PrimaryKeyConstraint('id'),
        db.UniqueConstraint('url'),
        mysql_charset='utf8',
        mysql_engine='MyISAM'
    )


def estimate():
    """  Estimate running time of upgrade in seconds (optional). """
    return 1


def pre_upgrade():
    """  Run pre-upgrade checks (optional). """
    # Example of raising errors:
    # raise RuntimeError("Description of error 1", "Description of error 2")


def post_upgrade():
    """  Run post-upgrade checks (optional). """
    # Example of issuing warnings:
    # warnings.warn("A continuable error occurred")
