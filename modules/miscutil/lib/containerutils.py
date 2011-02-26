## This file is part of Invenio.
## Copyright (C) 2012 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
This module contains functions for basic containers (dict, list, str)
"""

def treasure_hunter(island, route):
    """
    Tries to find the treasure in the island. If it cannot find, returns home
    with just None.

    >>> island = {'a': 5, 'b': {'c': [1, 2, [{'f': [57]}], 4], 'd': 'test'}}
    >>> treasure_hunter(island, "bc")
    [1, 2, [{'f': [57]}], 4]
    >>> treasure_hunter(island, ['b', 'c'])
    [1, 2, [{'f': [57]}], 4]
    >>> treasure_hunter(island, ['b', 'c', 2, 0, 'f', 0])
    57
    >>> treasure_hunter(island, ['b', 'c', 2, 0, 'f', 'd'])
    None

    @param island: a container
    @type island: str|dict|list|(an indexable container)

    @param route: location of the data
    @type route: list|str

    @rtype: *
    """

    if not len(route):
        return island

    try:
        return treasure_hunter(island[route[0]], route[1:])
    except (TypeError, IndexError, KeyError):
        return None