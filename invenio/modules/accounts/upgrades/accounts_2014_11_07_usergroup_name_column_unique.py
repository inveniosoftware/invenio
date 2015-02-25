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

"""Upgrade Usergroup table."""

from invenio.legacy.dbquery import run_sql
from invenio.modules.upgrader.api import op
from sqlalchemy.exc import OperationalError

depends_on = ['invenio_release_1_1_0']


def info():
    """Upgrade Usergroup table."""
    return "Upgrade Usergroup table"


def do_upgrade():
    """Implement your upgrades here."""
    try:
        op.drop_index('ix_usergroup_name', table_name='usergroup')
    except OperationalError:
        pass
    try:
        op.drop_index('name', table_name='usergroup')
    except OperationalError:
        pass
    op.create_index(op.f('ix_usergroup_name'), 'usergroup', ['name'],
                    unique=True)


def estimate():
    """Estimate running time of upgrade in seconds (optional)."""
    return 1


def pre_upgrade():
    """Run pre-upgrade checks (optional)."""
    result = run_sql("""
        SELECT name, count(name) as count
        FROM usergroup
        GROUP BY name HAVING count > 1;
    """)
    if len(result) > 0:
        raise RuntimeError("Integrity problem in the table Usergroup",
                           "Duplicate Usergroup name")


def post_upgrade():
    """Run post-upgrade checks (optional)."""
