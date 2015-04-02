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

"""Cited search unit."""

from intbitset import intbitset


def search_unit(query, f, m, wl=None):
    """Search for records with given citation count.

    Query usually looks like '10->23'.
    """
    from invenio.modules.records.models import Record
    from invenio.legacy.bibrank.citation_searcher import (
        get_records_with_num_cites
    )
    numstr = '"{}"'.format(query)
    #this is sort of stupid but since we may need to
    #get the records that do _not_ have cites, we have to
    #know the ids of all records, too
    #but this is needed only if bsu_p is 0 or 0 or 0->0
    allrecs = intbitset()
    if query == 0 or query == "0" or \
       query.startswith("0->") or query.endswith("->0"):
        allrecs = Record.allids()
    return get_records_with_num_cites(numstr, allrecs)
