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
"""BibFormat element - Prints reference to documents citing this one
"""
__revision__ = "$Id$"

import cgi

def format_element(bfo, separator='; '):
    """
    Prints a list of records citing this record

    @param separator: a separator between citations
    """
    from urllib import quote
    from invenio.config import CFG_BASE_URL

    primary_report_numbers = bfo.fields('037__a')
    additional_report_numbers = bfo.fields('088__a')

    primary_citations = ['<a href="' + CFG_BASE_URL + \
                         '/search?f=reference&amp;p=' + quote(report_number) + \
                         '&amp;ln='+ bfo.lang +'">' + \
                         cgi.escape(report_number) + '</a>' \
                         for report_number in primary_report_numbers]

    additional_citations = ['<a href="' + CFG_BASE_URL + \
                            '/search?f=reference&amp;p=' + quote(report_number)+ \
                            '&amp;ln='+ bfo.lang + '">' + \
                            cgi.escape(report_number) + '</a>' \
                            for report_number in additional_report_numbers]

    citations = primary_citations
    citations.extend(additional_citations)

    return separator.join(citations)

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
