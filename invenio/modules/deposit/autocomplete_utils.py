# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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

from invenio.sherpa_romeo import SherpaRomeoSearch
from invenio.orcid import OrcidSearch


def kb_autocomplete(name, mapper=None):
    """
    Create a autocomplete function from knowledge base

    @param name: Name of knowledge base
    @param mapper: Function that will map an knowledge base entry to
                   autocomplete entry.
    """
    def inner(dummy_form, dummy_field, term, limit=50):
        from invenio.bibknowledge import get_kb_mappings
        result = get_kb_mappings(name, '', term)[:limit]
        return map(mapper, result) if mapper is not None else result
    return inner


def sherpa_romeo_publishers(dummy_form, term, limit=50):
    if term:
        sherpa_romeo = SherpaRomeoSearch()
        publishers = sherpa_romeo.search_publisher(term)
        if publishers is None:
            return []
        return publishers
    return []


def sherpa_romeo_journals(dummy_form, term, limit=50):
    """
    Search SHERPA/RoMEO for journal name
    """
    if term:
        # SherpaRomeoSearch doesnt' like unicode
        if isinstance(term, unicode):
            term = term.encode('utf8')
        s = SherpaRomeoSearch()
        journals = s.search_journal(term)
        if journals is not None:
            return journals[:limit]
    return []


def orcid_authors(dummy_form, term, limit=50):
    if term:
        orcid = OrcidSearch()
        orcid.search_authors(term)
        return orcid.get_authors_names()
    return []
