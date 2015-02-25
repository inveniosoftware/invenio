# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2007, 2008, 2009, 2010, 2011 CERN.
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
"""BibFormat element - Prints report numbers
"""

__revision__ = ""

import cgi
from invenio.utils.url import create_html_link

def format_element(bfo, limit, separator=" ", extension=" etc.", link='yes', just_one='no'):
    """
    Prints the report numbers of the record (037__a and 088__a)

    @param separator: the separator between report numbers.
    @param limit: the max number of report numbers to print
    @param extension: a prefix printed when limit param is reached
    @param link: if 'yes', display report number with corresponding link when possible
    """
    numbers = bfo.fields("037__a")
    numbers.extend(bfo.fields("088__a"))

    # Only display the first one
    if just_one == 'yes':
        numbers = numbers[:1]

    if limit.isdigit():
        limit_as_int = int(limit)
        if limit_as_int <= len(numbers):
            return separator.join(numbers[:limit_as_int]) + extension

    return separator.join([build_report_number_link(report_number, \
                                                    link == 'yes') \
                           for report_number in numbers])

def build_report_number_link(report_number, link_p=True):
    """
    Build HTML link out of given report number when it make sense (or
    is possible) and/or escape report number.
    @param report_number: the report number to consider
    @param link_p: if True, build link, otherwise just escape
    """
    if link_p and report_number.lower().startswith('arxiv:'):
        return create_html_link('http://arxiv.org/abs/' + report_number,
                                urlargd={}, link_label=report_number)
    else:
        return cgi.escape(report_number)

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
