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
"""BibFormat element - Prints publisher name
"""
__revision__ = "$Id$"

from invenio.config import CFG_SITE_URL

from invenio.legacy.bibauthority.engine import get_low_level_recIDs_from_control_no

def format_element(bfo):
    """
    Prints the publisher name

    @see: place.py, date.py, reprints.py, imprint.py, pagination.py
    """

    publisher = bfo.field('260__b')
    control_no = bfo.field('260__0')

    if publisher != "sine nomine":
        if control_no:
            recIDs = get_low_level_recIDs_from_control_no(control_no)
            if len(recIDs):
                publisher = '<a href="' + CFG_SITE_URL + '/record/' + \
                            str(recIDs[0]) + \
                            '?ln=' + bfo.lang + \
                            '">' + publisher + '</a>'
        return publisher


def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0

