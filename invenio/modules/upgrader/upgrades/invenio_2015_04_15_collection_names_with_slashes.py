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

"""Check collection table and warn user about collection names with slashes."""

from invenio.legacy.dbquery import run_sql

depends_on = ['invenio_release_1_2_0']


def info():
    """Return upgrade recipe information."""
    return "Warns user about collection names with slashes."


def do_upgrade():
    """Carry out the upgrade."""
    res = run_sql("SELECT name FROM collection WHERE name LIKE '%/%'")
    for row in res:
        print "WARNING: Collection '%s' contains forward slashes" \
            " which is not recommended." % row[0]
        print "WARNING: You may safely continue, but we recommend" \
            " changing this collection name to avoid slashes."


def estimate():
    """Estimate running time of upgrade in seconds (optional)."""
    return 1


def pre_upgrade():
    """Pre-upgrade checks."""
    pass  # because slashes would still work


def post_upgrade():
    """Post-upgrade checks."""
    pass
