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

"""Modifies column `tag.value`."""

from invenio.legacy.dbquery import run_sql

depends_on = ['invenio_2012_11_15_hstRECORD_marcxml_longblob']


def info():
    """Return upgrade recipe information."""
    return "Modifies column tag.value"


def do_upgrade():
    """Carry out the upgrade."""
    create_statement = run_sql('SHOW CREATE TABLE tag')[0][1]
    if 'affected_fields' not in create_statement:
        run_sql("ALTER TABLE tag MODIFY COLUMN value VARCHAR(6) default ''")


def estimate():
    """Estimate running time of upgrade in seconds (optional)."""
    return 1


def pre_upgrade():
    """Pre-upgrade checks."""
    pass


def post_upgrade():
    """Post-upgrade checks."""
    pass
