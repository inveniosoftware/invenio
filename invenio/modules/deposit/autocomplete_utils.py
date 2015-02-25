# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014 CERN.
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

"""Utility functions for field autocomplete feature."""

from invenio.utils.sherpa_romeo import SherpaRomeoSearch
from invenio.utils.orcid import OrcidSearch


def kb_autocomplete(name, mapper=None):
    """Create an autocomplete function from knowledge base.

    :param name: Name of knowledge base
    :param mapper: Function that will map an knowledge base entry to
                   autocomplete entry.
    """
    def inner(dummy_form, dummy_field, term, limit=50):
        from invenio.modules.knowledge.api import get_kb_mappings
        result = get_kb_mappings(name, '', term, limit=limit)[:limit]
        return map(mapper, result) if mapper is not None else result
    return inner


def kb_dynamic_autocomplete(name, mapper=None):
    """Create an autocomplete function from dynamic knowledge base.

    :param name: Name of knowledge base
    :param mapper: Function that will map an knowledge base entry to
                   autocomplete entry.
    """
    def inner(dummy_form, dummy_field, term, limit=50):
        from invenio.modules.knowledge.api import get_kbd_values
        result = get_kbd_values(name, searchwith=term)[:limit]
        return map(mapper, result) if mapper is not None else result
    return inner


def sherpa_romeo_publishers(dummy_form, dummy_field, term, limit=50):
    """Autocomplete publishers from SHERPA/RoMEO service."""
    if term:
        sherpa_romeo = SherpaRomeoSearch()
        publishers = sherpa_romeo.search_publisher(term)
        if publishers is None:
            return []
        return map(lambda x: {'value': x}, publishers[:limit])
    return []


def sherpa_romeo_journals(dummy_form, dummy_field, term, limit=50):
    """Search SHERPA/RoMEO for journal name."""
    if term:
        # SherpaRomeoSearch doesnt' like unicode
        if isinstance(term, unicode):
            term = term.encode('utf8')
        s = SherpaRomeoSearch()
        journals = s.search_journal(term)
        if journals is not None:
            return map(lambda x: {'value': x}, journals[:limit])
    return []


def orcid_authors(dummy_form, dummy_field, term, limit=50):
    """Autocomplete authors from ORCID service."""
    if term:
        orcid = OrcidSearch()
        orcid.search_authors(term)
        return orcid.get_authors_names()
    return []
