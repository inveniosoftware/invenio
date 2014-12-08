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

"""Collection search unit."""

from intbitset import intbitset


def search_unit(query, f, m, wl=None):
    """Search for records in collection query.

    Example:

    .. code-block:: text

        collection:"BOOK"
        collection:"Books"
    """
    from invenio.legacy.search_engine import (
        get_collection_reclist, search_unit_in_bibwords
    )
    if len(query):
        ahitset = get_collection_reclist(query)
        if not ahitset:
            return search_unit_in_bibwords(query, 'collection', m, wl=wl)
        return ahitset
    else:
        return intbitset([])
