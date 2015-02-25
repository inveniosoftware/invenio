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

"""Add full name columns to User table."""

from invenio.ext.sqlalchemy import db
from invenio.modules.upgrader.api import op

depends_on = [u'accounts_2014_11_07_usergroup_name_column_unique']


def info():
    """Upgrade description."""
    return __doc__


def do_upgrade():
    """Implement your upgrades here."""
    op.add_column('user', db.Column('family_name',
                  db.String(length=255), nullable=True))
    op.add_column('user', db.Column('given_names',
                  db.String(length=255), nullable=True))


def estimate():
    """Estimate running time of upgrade in seconds (optional)."""
    return 1
