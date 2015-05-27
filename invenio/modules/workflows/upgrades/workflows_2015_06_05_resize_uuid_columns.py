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

"""Upgrade recipe."""

from invenio.ext.sqlalchemy import db
from invenio.modules.upgrader.api import op

depends_on = [u'workflows_2014_08_12_initial']


def info():
    """Info message."""
    return "Resize uuid columns on workflows tables."


def do_upgrade():
    """Implement your upgrades here."""
    with op.batch_alter_table("bwlWORKFLOW") as batch_op:
        batch_op.alter_column(
            column_name='uuid',
            type_=db.UUID(), nullable=False
        )
    with op.batch_alter_table("bwlOBJECT") as batch_op:
        batch_op.alter_column(
            column_name='id_workflow',
            type_=db.UUID(), nullable=True
        )
    with op.batch_alter_table("bwlWORKFLOWLOGGING") as batch_op:
        batch_op.alter_column(
            column_name='id_object',
            type_=db.UUID(), nullable=False
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
