# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2015 CERN.
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
"""BibFormat element - Prints document imprint
"""
__revision__ = "$Id$"

from invenio.utils.date import strftime, strptime

def format_element(bfo, place_label, publisher_label, date_label,
           separator=', ', date_format=""):
    """
    Print imprint (Order: Name of publisher, place of publication and date of publication).
    Parameter <code>date_format</code> allows to specify the string representation of the output.
    The format string has the same behaviour as the strftime() function::
        <pre>Eg: 1982-09-24 07:32:00
             "%d %B %Y"   -> 24 September 1982
             "%I:%M"      -> 07:32
        </pre>
    @param separator: a separator between the elements of imprint
    @param place_label: a label to print before the publication place value
    @param publisher_label: a label to print before the publisher name
    @param date_label: a a label to print before the publication date
    @param date_format: date format
    @see: place.py, publisher.py, date.py, reprints.py, pagination.py
    """

    place = bfo.field('260__a')
    publisher = bfo.field('260__b')
    date = bfo.field('260__c')

    out = ""

    if publisher != "sine nomine":
        out += publisher_label + ' ' + publisher + separator

    if place != "sine loco":
        out += place_label + ' ' + place + separator

    if len(date) > 0:
        if date_format != '':
            try:
                date_time = strptime(date, "%Y-%m-%d")
                out += date_label + " " + strftime(date_format, date_time)
            except ValueError:
                out += date_label + ' ' + date
        else:
            out += date_label + ' ' + date

    return out
