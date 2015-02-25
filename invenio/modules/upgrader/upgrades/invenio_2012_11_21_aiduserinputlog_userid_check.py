# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012 CERN.
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

from invenio.legacy.dbquery import run_sql

depends_on = ['invenio_release_1_1_0']

def info():
    return "Check existence of aidUSERINPUTLOG.userid column"

def do_upgrade():
    """
    Developers upgrading their existing master installations will likely be issued
    with many warnings from invenio_release_1_1_0 upgrade, due to being inbetween
    1.0 and 1.1 on the upgrade path. Most warnings can safely be ignored except for
    one related to aidUSERINPUTLOG. This upgrade implements an extra check of this
    table to ensure that it is in a consistent state.
    """
    fields = [x[0] for x in run_sql("SHOW FIELDS FROM aidUSERINPUTLOG")]
    indexes = [x[2] for x in run_sql("SHOW INDEXES FROM aidUSERINPUTLOG")]

    if 'userid' not in fields:
        run_sql("ALTER TABLE aidUSERINPUTLOG ADD COLUMN userid int AFTER timestamp;")
    if 'userid-b' not in indexes:
        run_sql("ALTER TABLE aidUSERINPUTLOG ADD KEY `userid-b` (userid)")

