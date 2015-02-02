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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Upgrade for explicitly hiding the 'holdings' tab for all collections\
 except 'Books' without an existing rule"""

from invenio.legacy.dbquery import run_sql

depends_on = ['invenio_release_1_1_0']


def info():
    """Upgrade recipe information."""
    return "Updates the collectiondetailedrecordpagetabs to hide 'holdings' for every collection \
            except 'Books' without an existing rule."


def do_upgrade():
    """Upgrade recipe procedure."""
    # Show holdings for the 'Books' collection unless there's an existing rule
    run_sql("""
    INSERT IGNORE INTO collectiondetailedrecordpagetabs (id_collection, tabs)
    SELECT id, "files;references;keywords;plots;hepdata;holdings;comments;linkbacks;citations;usage;metadata"
    FROM collection WHERE name = 'Books'
    """)

    # Insert the rest of the rules
    run_sql("""
    INSERT IGNORE INTO collectiondetailedrecordpagetabs (id_collection, tabs)
    SELECT id, "files;references;keywords;plots;hepdata;comments;linkbacks;citations;usage;metadata"
    FROM collection
    """)


def estimate():
    """Upgrade recipe time estimate."""
    return 1
