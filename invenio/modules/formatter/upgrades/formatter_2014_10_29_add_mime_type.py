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
from invenio.ext.sqlalchemy import db
from invenio.modules.upgrader.api import op
from invenio.legacy.dbquery import run_sql

depends_on = [u'formatter_2014_08_01_recjson']


def info():
    return "Adds a mime_type column to format table"


def do_upgrade():
    """Implement your upgrades here."""
    op.add_column('format', db.Column('mime_type',
                  db.String(length=255), unique=True, nullable=True))
    mime_type_dict = dict(
        xm='application/marcxml+xml',
        hm='application/marc',
        recjson='application/json',
        hx='application/x-bibtex',
        xn='application/x-nlm',
    )
    query = "UPDATE format SET mime_type=%s WHERE code=%s"
    for code, mime in mime_type_dict.items():
        params = (mime, code)
        try:
            run_sql(query, params)
        except Exception as e:
            warnings.warn("Failed to execute query {0}: {1}".format(query, e))


def estimate():
    """Estimate running time of upgrade in seconds (optional)."""
    return 1


def pre_upgrade():
    """Run pre-upgrade checks (optional)."""
    # Example of raising errors:
    # raise RuntimeError("Description of error 1", "Description of error 2")


def post_upgrade():
    """Run post-upgrade checks (optional)."""
    # Example of issuing warnings:
    # warnings.warn("A continuable error occurred")
