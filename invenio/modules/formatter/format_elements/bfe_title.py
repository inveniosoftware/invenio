# -*- coding: utf-8 -*-
#
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
"""BibFormat element - Prints titles
"""
__revision__ = "$Id$"

import cgi

def format_element(bfo, separator=" ", highlight='no'):
    """
    Prints the titles of a record.

    @param separator: separator between the different titles
    @param highlight: highlights the words corresponding to search query if set to 'yes'
    """
    titles = []

    title = bfo.field('245__a')
    title_remainder = bfo.field('245__b')
    edition_statement = bfo.field('250__a')
    title_tome = bfo.field('245__n')
    title_part = bfo.field('245__p')

    if len(title) > 0:
        if title_remainder:
            title += ': ' + title_remainder
        if len(title_tome) > 0:
            title += ", " + title_tome
        if len(title_part) > 0:
            title += ": " + title_part
        titles.append( title )

    title = bfo.field('246__a')
    if len(title) > 0:
        titles.append( title )

    title = bfo.field('246__b')
    if len(title) > 0:
        titles.append( title )

    title = bfo.field('246_1a')
    if len(title) > 0:
        titles.append( title )

    if len(titles) > 0:
        #Display 'Conference' title only if other titles were not found
        title = bfo.field('111__a')
        if len(title) > 0:
            titles.append( title )

    titles = [cgi.escape(x) for x in titles]

    if highlight == 'yes':
        from invenio.modules.formatter import utils as bibformat_utils
        titles = [bibformat_utils.highlight(x, bfo.search_pattern) for x in titles]

    if len(edition_statement) > 0:
        return separator.join(titles) + "; " + edition_statement
    else:
        return separator.join(titles)

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0






