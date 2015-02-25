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

"""Upgrade knwKBRVAL table."""

import sqlalchemy as sa
import warnings

from invenio.legacy.dbquery import run_sql
from invenio.modules.upgrader.api import op

depends_on = ['invenio_release_1_1_0']


def info():
    """Upgrade knwKBRVAL table."""
    return "Upgrade knwKBRVAL table"


def do_upgrade():
    """Implement your upgrades here."""
    op.drop_column('knwKBRVAL', 'id')
    op.create_primary_key('pkey', 'knwKBRVAL', ['m_key', 'id_knwKB'])
    op.alter_column('knwKBRVAL', 'm_key',
                    existing_type=sa.String(length=255),
                    type_=sa.String(length=255),
                    existing_server_default='',
                    server_default=None,
                    existing_nullable=False,
                    nullable=False)


def estimate():
    """Estimate running time of upgrade in seconds (optional)."""
    return 1


def pre_upgrade():
    """Run pre-upgrade checks (optional)."""
    result = run_sql("""
        SELECT m_key, count(m_key) as count
        FROM knwKBRVAL
        GROUP BY m_key, id_knwKB HAVING count > 1;
    """)
    if len(result) > 0:
        raise RuntimeError("Integrity problem in the table knwKBRVAL",
                           "Duplicate pairs m_key/id_knwKB")


def post_upgrade():
    """Run post-upgrade checks (optional)."""
    warnings.warn(
        "NOTE: If you are running Invenio 1 and Invenio 2 on top "
        "of the same database, please use only Invenio 2 knowledge "
        "base administration interface from now on, in order to "
        "ensure data consistency.")
    pass
