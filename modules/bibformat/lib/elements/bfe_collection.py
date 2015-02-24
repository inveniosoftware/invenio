# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2012 CERN.
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
"""BibFormat element - Prints collection identifier
"""

__revision__ = "$Id$"

def format_element(bfo, kb):
    """
    Prints the collection identifier.
    Translate using given knowledge base.

    @param kb: a knowledge base use to translate the collection identifier
    """

    collection_identifiers = bfo.fields("980__a")

    for collection_identifier in collection_identifiers:
        translated_collection_identifier = bfo.kb(kb, collection_identifier)
        if translated_collection_identifier:
            return translated_collection_identifier

    return ''
