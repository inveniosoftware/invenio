#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This file is part of Invenio.
# Copyright (C) 2009, 2010, 2011 CERN.
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
"""
WebJournal Element - display article title
"""
def format_element(bfo):
    """
    Display article title
    """
    # Retrieve context (journal, issue and category) from URI
    ln = bfo.lang

    if ln == "fr":
        title = bfo.fields('246_1a', escape=1)
        if len(title) == 0:
            title = bfo.fields('245__a', escape=1)
    else:
        title = bfo.fields('245__a', escape=1)
        if not title:
            title = bfo.fields('246_1a', escape=1)

    return ' '.join(title)

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
