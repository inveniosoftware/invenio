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

"""Cited by excluding self-cites search unit."""

from intbitset import intbitset


def search_unit(query, f, m, wl=None):
    """Search for records in citation index excluding self-cites."""
    from invenio.legacy.search_engine import search_pattern
    from invenio.legacy.bibrank.citation_searcher import get_refers_to_list
    from invenio.legacy.bibrank.selfcites_searcher import (
        get_self_refers_to_list
    )

    if query:
        if isinstance(query, intbitset):
            ahitset = query
        else:
            ahitset = search_pattern(p=query)
        citees = intbitset()
        references = get_refers_to_list(ahitset)
        selfreferences = get_self_refers_to_list(ahitset)
        for refs, selfrefs in zip(references, selfreferences):
            # refs is in the form [(citer, citees), ...]
            citees += refs[1] - selfrefs[1]
        return citees
    else:
        return intbitset([])
