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

import warnings
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from invenio.modules.upgrader.api import op
from sqlalchemy.exc import OperationalError

depends_on = ['formatter_2014_08_01_recjson']


def info():
    return "Adds new column 'kind' to bibfmt and allows null for format.last_updated."


def do_upgrade():
    """Implement your upgrades here."""
    try:
        op.add_column(
            'bibfmt',
            sa.Column(
                'kind',
                sa.String(length=10),
                server_default='',
                nullable=False
            )
        )
    except OperationalError:
        warnings.warn("*** Problem adding column bibfmt.kind. Does it already exist? ***")

    op.alter_column(
        'format',
        'last_updated',
        existing_type=mysql.DATETIME(),
        nullable=True,
        existing_server_default='0000-00-00 00:00:00'
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
