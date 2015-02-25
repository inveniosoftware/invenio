# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2010, 2011 CERN.
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
"""BibFormat element - Prints publcation information and link to ejournal
"""
__revision__ = "$Id$"

from urllib import quote
import cgi

def format_element(bfo):
    """
    Displays inline publication information with html link to ejournal
    (when available).
    """


    out = ''

    publication_info = bfo.field('909C4')
    if publication_info == "":
        return ""

    journal_source = publication_info.get('p')
    journal = bfo.kb('ejournals', journal_source)
    volume = publication_info.get('v')
    year = publication_info.get('y')
    number = publication_info.get('n')
    pages = publication_info.get('c')
    doi = publication_info.get('a')

    if journal is not None:
        journal = cgi.escape(journal)
    if volume is not None:
        volume = cgi.escape(volume)
    if year is not None:
        year = cgi.escape(year)
    if number is not None:
        number = cgi.escape(number)
    if pages is not None:
        pages = cgi.escape(pages)
    if doi is not None:
        doi = cgi.escape(doi)

    if journal != '' and volume is not None:

        out += '<a href="https://cds.cern.ch/ejournals.py?publication='
        out += quote(journal_source)
        out += '&amp;volume=' + volume
        out += '&amp;year=' + year
        out += '&amp;page='
        page = pages.split('-')# get first page from range
        if len(page) > 0:
            out += page[0]
        out += '">%(journal)s :%(volume)s %(year)s %(page)s</a>' % {'journal': journal,
                                                                    'volume': volume,
                                                                    'year': year,
                                                                    'page': pages}
    else:
        out += journal_source + ': '
        if volume is not None:
            out +=  volume
        if year is not None:
            out += ' (' + year + ') '
        if number is not None:
            out += 'no. ' + number + ', '
        if pages is not None:
            out += 'pp. ' + pages

    return out

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0





