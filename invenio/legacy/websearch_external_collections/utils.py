# -*- coding: utf-8 -*-

# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

"""Some misc function for the external collections search.
"""

__revision__ = "$Id$"

import sys

from six import iteritems

from invenio.legacy.dbquery import run_sql

def get_verbose_print(req, prefix, cur_verbosity_level):
    """Return a function used to print verbose message."""

    def vprint(verbosity_level, message):
        """Print a verbose message."""
        if cur_verbosity_level >= verbosity_level:
            req.write('<br /><span class="quicknote">' + prefix + message + '</span><br />')

    return vprint

def warning(message):
    """Issue a warning alert."""
    sys.stderr.write("WARNING: %(message)s\n" % locals())

# Collections function
collections_id = None

def collections_id_load(force_reload=False):
    """If needed, load the database for building the dictionary collection_name -> collection_id."""

    global collections_id

    if not (force_reload or collections_id is None):
        return

    collections_id = {}
    results = run_sql("SELECT id, name FROM collection;")
    for result in results:
        collection_id = result[0]
        name = result[1]

        collections_id[name] = collection_id

def get_collection_id(name):
    """Return the id of a collection named 'name'."""

    collections_id_load()

    if name in collections_id:
        return collections_id[name]
    else:
        return None

def get_collection_name_by_id(colid):
    """Return the name of collection with id 'id'."""

    collections_id_load()

    for (collection_name, collection_id) in iteritems(collections_id):
        if collection_id == colid:
            return collection_name
            break
    return None

def get_collection_descendants(id_dad):
    "Returns list of all descendants of the collection having for id id_dad."

    descendants = []
    results = run_sql("SELECT id_son FROM collection_collection WHERE id_dad=%s",
                      (id_dad,))
    for result in results:
        id_son = int(result[0])
        descendants.append(id_son)
        descendants += get_collection_descendants(id_son)

    return descendants

