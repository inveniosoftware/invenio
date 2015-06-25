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

"""Replace zero value for id_accARGUMENT with NULL."""

from invenio.legacy.dbquery import run_sql


depends_on = [u'access_2015_05_06_accROLE_accACTION_accARGUMENT_id']


def info():
    """Info message."""
    return __doc__


def do_upgrade():
    """Implement your upgrades here."""
    run_sql("""
        UPDATE "accROLE_accACTION_accARGUMENT"
        SET "id_accARGUMENT" = NULL
        WHERE "id_accARGUMENT" = 0
    """)


def estimate():
    """Estimate running time of upgrade in seconds (optional)."""
    total = run_sql("""
        SELECT count(*) FROM "accROLE_accACTION_accARGUMENT"
        WHERE "id_accARGUMENT" = 0
    """)
    return total[0][0] // 1000 + 1


def pre_upgrade():
    """Run pre-upgrade checks (optional)."""
    pass


def post_upgrade():
    """Run post-upgrade checks (optional)."""
    pass
