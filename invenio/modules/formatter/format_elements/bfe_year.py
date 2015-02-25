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
"""BibFormat element - Prints the publication year
"""
__revision__ = "$Id$"

import re

def format_element(bfo):
    """
    Prints the publication year.
    @see: pagination.py, publisher.py, reprints.py, imprint.py, place.py
    """
    for date_field in ['773__y', '260__c', '269__c', '909C4y', '925__a']:
        date = bfo.field(date_field)
        match_obj = re.search('\d\d\d\d', date)
        if match_obj is not None:
            return match_obj.group()
