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

"""Fix 'recjson_value' for 'collection identifier' tag."""

import warnings

from invenio.ext.sqlalchemy import db

depends_on = []


def info():
    """Info message."""
    return __doc__


def do_upgrade():
    """Implement your upgrades here."""
    name = 'collection identifier'
    value = ''
    recjson_value = '_collections'

    tag = list(db.engine.execute(
        """SELECT value, recjson_value FROM tag WHERE name=%s""", (name, )
    ))

    if not tag:
        raise RuntimeError("Missing 'collection identifier' tag.")
    elif not (tag[0][0] == value and tag[0][1] == recjson_value):
        db.engine.execute(
            """UPDATE tag SET value=%s, recjson_value=%s """
            """WHERE name=%s""", (value, recjson_value, name))
    else:
        warnings.warn("Good, 'collection identifier' tag did not require "
                      "an upgrade.")


def estimate():
    """Estimate running time of upgrade in seconds (optional)."""
    return 1


def pre_upgrade():
    """Run pre-upgrade checks (optional)."""
    tag = list(db.engine.execute(
        """SELECT value, recjson_value FROM tag WHERE name=%s""",
        ('collection identifier', )
    ))
    if not tag:
        raise RuntimeError("Missing 'collection identifier' tag.")


def post_upgrade():
    """Run post-upgrade checks (optional)."""
    # Example of issuing warnings:
    # warnings.warn("A continuable error occurred")
