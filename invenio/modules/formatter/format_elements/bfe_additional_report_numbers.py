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
"""BibFormat element - Prints additional report numbers
"""

__revision__ = "$Id$"

from invenio.modules.formatter.format_elements.bfe_report_numbers import \
     build_report_number_link

def format_element(bfo, limit, separator=" ", link='yes'):
    """
    Prints the additional report numbers of the record

    @param separator: the separator between report numbers.
    @param limit: the max number of report numbers to display
    @param link: if 'yes', display report number with corresponding link when possible
    """
    numbers = bfo.fields("088__a")

    if limit.isdigit() and int(limit) <= len(numbers):
        numbers = numbers[:int(limit)]

    return separator.join([build_report_number_link(report_number,
                                                    link == 'yes') \
                           for report_number in numbers])

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
