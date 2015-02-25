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

"""This module contains functions for basic containers (dict, list, str)."""

import re


def get_substructure(data, path):
    """
    Tries to retrieve a sub-structure within some data. If the path does not
    match any sub-structure, returns None.

    >>> data = {'a': 5, 'b': {'c': [1, 2, [{'f': [57]}], 4], 'd': 'test'}}
    >>> get_substructure(island, "bc")
    [1, 2, [{'f': [57]}], 4]
    >>> get_substructure(island, ['b', 'c'])
    [1, 2, [{'f': [57]}], 4]
    >>> get_substructure(island, ['b', 'c', 2, 0, 'f', 0])
    57
    >>> get_substructure(island, ['b', 'c', 2, 0, 'f', 'd'])
    None

    @param data: a container
    @type data: str|dict|list|(an indexable container)

    @param path: location of the data
    @type path: list|str

    @rtype: *
    """

    if not len(path):
        return data

    try:
        return get_substructure(data[path[0]], path[1:])
    except (TypeError, IndexError, KeyError):
        return None
