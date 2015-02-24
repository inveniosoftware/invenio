# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2014 CERN.
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

from __future__ import print_function

from invenio.dbquery import run_sql

depends_on = ['invenio_release_1_1_0']


def info():
    return "Update collection tree definition to match next structure"


def do_upgrade():
    """Change the score to the opposite order."""
    def change_collections_score(id_dad, collection_list):
        for i, col in enumerate(collection_list):
            run_sql("UPDATE collection_collection "
                    "SET score=%s "
                    "WHERE id_son=%s AND id_dad=%s",
                    (i, col[0], id_dad))
            son_collections = run_sql(
                "SELECT cc.id_son "
                "FROM collection_collection as cc, collection as c "
                "WHERE cc.id_dad=%s and cc.id_son=c.id "
                "ORDER BY cc.score DESC, c.name ASC",
                (col[0], ))
            change_collections_score(col[0], son_collections)

    main_collections = run_sql(
        "SELECT cc.id_son "
        "FROM collection_collection as cc, collection as c "
        "WHERE cc.id_dad=1 and cc.id_son=c.id "
        "ORDER BY cc.score DESC, c.name ASC")
    change_collections_score(1, main_collections)


def estimate():
    return 1


def post_upgrade():
    print(
        'Running webcoll is highly recommended to update the collection tree.')
