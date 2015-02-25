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

"""Initial upgrade script from Invenio v1.x to v2.0."""

import sqlalchemy as sa
import warnings
from invenio.modules.upgrader.api import op
from sqlalchemy.exc import OperationalError
from invenio.legacy.dbquery import run_sql

depends_on = []


def info():
    return "Add workflows column and drop frequency."


def do_upgrade():
    """Implement your upgrades here."""
    try:
        op.add_column(
            'oaiHARVEST',
            sa.Column(
                'workflows',
                sa.String(length=255),
                server_default='',
                nullable=False
            )
        )

    except OperationalError:
        op.alter_column(
            'oaiHARVEST',
            'workflows',
            existing_type=sa.String(length=255),
            nullable=False,
            server_default=''
        )

    # Set default workflow with backwards compatibility for those who have none.
    all_data_objects = run_sql("SELECT id, workflows FROM oaiHARVEST")
    for object_id, workflows in all_data_objects:
        if not workflows:
            run_sql("UPDATE oaiHARVEST set workflows=%s WHERE id=%s",
                    ("oaiharvest_harvest_repositories", str(object_id)))

    try:
        op.drop_column('oaiHARVEST', 'frequency')
    except OperationalError as err:
        warnings.warn(
            "*** Error removing 'oaiHARVEST.frequency' column: {0} ***".format(
                str(err)
            )
        )


def estimate():
    """Estimate running time of upgrade in seconds (optional)."""
    return 1


def pre_upgrade():
    """Run pre-upgrade checks (optional)."""
    pass


def post_upgrade():
    """Run post-upgrade checks (optional)."""
    pass
