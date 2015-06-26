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

"""Change id column from VARBINARY to String."""

from invenio.ext.sqlalchemy import db
from invenio.modules.upgrader.api import op

depends_on = [u'accounts_2015_03_06_passlib']


def info():
    """Info message."""
    return __doc__


def do_upgrade():
    """Implement your upgrades here."""
    with op.batch_alter_table("UserEXT") as batch_op:
        batch_op.alter_column(
            column_name='id',
            type_=db.String(255), nullable=False
        )


def estimate():
    """Estimate running time of upgrade in seconds (optional)."""
    pass


def pre_upgrade():
    """Run pre-upgrade checks (optional)."""
    pass


def post_upgrade():
    """Run post-upgrade checks (optional)."""
    pass
