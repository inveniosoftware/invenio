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
"""BibFormat element - Prints creation date
"""
__revision__ = "$Id$"

import datetime

from invenio.modules.records.recordext.functions.get_creation_date import \
    get_creation_date


def format_element(bfo, format='%Y-%m-%d', date_format='%Y-%m-%d'):
    '''
    Get the record creation date.
    <b>Note:</b> parameter <code>format</code> is deprecated

    @param date_format: The date format in MySQL syntax
    '''
    recID = bfo.recID
    creation_date = get_creation_date(recID) or datetime.now()

    # Let's be gentle and backward compatible while "format" is here:
    if date_format == '%Y-%m-%d' and format != '%Y-%m-%d':
        date_format = format
    return datetime.strptime(creation_date, date_format)
