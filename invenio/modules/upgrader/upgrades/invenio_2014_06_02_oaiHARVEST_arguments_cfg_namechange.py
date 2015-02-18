# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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

from invenio.legacy.dbquery import run_sql
from invenio.utils.serializers import deserialize_via_marshal, \
    serialize_via_marshal

depends_on = ['invenio_release_1_1_0']


def info():
    """info."""
    return "Change of oaiHARVEST.arguments c_cfg-file to c_stylesheet"


def do_upgrade():
    """do upgrade."""
    rows_to_change = run_sql(
        "SELECT id, arguments FROM oaiHARVEST", with_dict=True)
    # Move away from old columns
    for row in rows_to_change:
        if row['arguments']:
            arguments = deserialize_via_marshal(row['arguments'])
            if "c_cfg-file" in arguments:
                arguments['c_stylesheet'] = arguments['c_cfg-file']
                del arguments['c_cfg-file']
                run_sql("UPDATE oaiHARVEST set arguments=%s WHERE id=%s",
                        (serialize_via_marshal(arguments), row['id']))


def estimate():
    """Estimate running time of upgrade in seconds (optional)."""
    count_rows = run_sql("SELECT COUNT(*) FROM oaiHARVEST")[0][0]
    return count_rows / 20


def pre_upgrade():
    """pre upgade."""
    pass


def post_upgrade():
    """post upgrade."""
    pass
