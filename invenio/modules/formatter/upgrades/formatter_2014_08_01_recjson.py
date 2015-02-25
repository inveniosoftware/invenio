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

"""Formatter upgrade."""

import warnings
from sqlalchemy import *
from invenio.legacy.dbquery import run_sql


depends_on = ['invenio_2014_08_12_format_code_varchar20']


def info():
    """Upgrader info."""
    return "Recjson Format"


def do_upgrade():
    """Perform upgrade."""
    _run_sql_ignore("INSERT INTO format (name, code, description, content_type, visibility) VALUES ('Recjson Format', 'recjson', 'Recjson format.', 'application/json', 0);")


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


def _run_sql_ignore(query, *args, **kwargs):
    """Execute SQL query but ignore any errors."""
    try:
        run_sql(query, *args, **kwargs)
    except Exception as e:
        warnings.warn("Failed to execute query %s: %s" % (query, unicode(e)))
