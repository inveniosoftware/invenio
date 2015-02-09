# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2015 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Upgrade recipe for altering community column connected with logo."""

from invenio.ext.sqlalchemy import db
from invenio.modules.upgrader.api import op


depends_on = [u'communities_2014_10_17_featured_communities']


def info():
    """Upgrade description."""
    return "Alter community column connected with logo."


def do_upgrade():
    """Upgrade implementation."""
    op.alter_column(
        table_name="community",
        column_name="has_logo",
        new_column_name="logo_ext",
        type_=db.String(length=5),
        )


def estimate():
    """Estimate running time of upgrade in seconds."""
    return 1
