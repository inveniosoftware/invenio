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
"""BibFormat element - Prints affiliation
"""
__revision__ = "$Id$"

import cgi
from invenio.config import \
    CFG_SITE_URL, CFG_SITE_NAME
from invenio.legacy.bibauthority.config import \
    CFG_BIBAUTHORITY_AUTHORITY_COLLECTION_NAME
    
from invenio.legacy.bibauthority.engine import \
    get_low_level_recIDs_from_control_no

def format_element(bfo):
    """
    HTML Affiliation display
    """
    affiliations = bfo.fields('909C1', repeatable_subfields_p=True)
    out = ""
    for affiliation_dict in affiliations:
        if 'u' in affiliation_dict:
            recIDs = []
            affiliation = affiliation_dict['u'][0]
            control_nos = affiliation_dict.get('0')
            for control_no in control_nos or []:
                recIDs.extend(get_low_level_recIDs_from_control_no(control_no))
            affiliation = cgi.escape(affiliation)
            if len(recIDs) == 1:
                affiliation = '<a href="' + CFG_SITE_URL + \
                              '/record/' + str(recIDs[0]) + \
                              '?ln=' + bfo.lang + \
                              '">' + affiliation + '</a>'
            elif len(recIDs) > 1:
                affiliation = '<a href="' + CFG_SITE_URL + \
                              '/search?' + \
                              'p=recid:' +  " or recid:".join([str(_id) for _id in recIDs]) + \
                              '&amp;c=' + CFG_SITE_NAME + \
                              '&amp;c=' + CFG_BIBAUTHORITY_AUTHORITY_COLLECTION_NAME + \
                              '&amp;ln=' + bfo.lang + \
                              '">' + affiliation + '</a>'

            out += affiliation + "       "

    if out:
        return "<br/>" + out


def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
