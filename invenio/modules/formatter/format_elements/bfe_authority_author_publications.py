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
"""BibFormat element - Prints the control number of an Authority Record.
"""

from invenio.config import CFG_SITE_URL, CFG_SITE_NAME

from invenio.legacy.bibauthority.config import \
    CFG_BIBAUTHORITY_AUTHORITY_COLLECTION_NAME, \
    CFG_BIBAUTHORITY_RECORD_CONTROL_NUMBER_FIELD, \
    CFG_BIBAUTHORITY_RECORD_AUTHOR_CONTROL_NUMBER_FIELDS
from invenio.legacy.bibauthority.engine import \
    get_low_level_recIDs_from_control_no, \
    get_dependent_records_for_control_no

from invenio.legacy.search_engine import get_fieldvalues

CFG_BIBAUTHORITY_PUBLICATION_VIEW_LIMIT = 10
__revision__ = "$Id$"

def format_element(bfo):
    """ Prints the control number of an author authority record in HTML.
    By default prints brief version.

    @param brief: whether the 'brief' rather than the 'detailed' format
    @type brief: 'yes' or 'no'
    """

    from invenio.messages import gettext_set_language
    _ = gettext_set_language(bfo.lang)    # load the right message language


    control_nos = [d['a'] for d in bfo.fields('035__') if d['a']]
    previous_recIDs = []
    parameters = []
    count = None
    publications_formatted = []
    ## for every control number that this author has, find all the connected records for each one
    for control_no in control_nos:
        for ctrl_number_field_numbers in CFG_BIBAUTHORITY_RECORD_AUTHOR_CONTROL_NUMBER_FIELDS:
            parameters.append(ctrl_number_field_numbers + ":" + control_no.replace(" ",""))
        recIDs = [x for x in get_dependent_records_for_control_no(control_no) if x not in previous_recIDs]
        count = len(recIDs)
        count_string = str(count) + " dependent records"
        from urllib import quote
        # if we have dependent records, provide a link to them
        if count:
            prefix_pattern = "<a href='" + CFG_SITE_URL + "%s" + "'>"
            postfix = "</a>"
            url_str = ''
            # print as many of the author's publications as the CFG_BIBAUTHORITY_PUBLICATION_VIEW_LIMIT allows
            for i in range(count if count<CFG_BIBAUTHORITY_PUBLICATION_VIEW_LIMIT else CFG_BIBAUTHORITY_PUBLICATION_VIEW_LIMIT):
                    title = get_fieldvalues(recIDs[i],"245__a")
                    if title:
                        url_str = "/record/"+ str(recIDs[i])
                        prefix = prefix_pattern % url_str
                        publications_formatted.append(prefix + title[0] + postfix)

    title = "<strong>" + _("Publication(s)") + "</strong>"
    if publications_formatted:
        content = "<ul><li>" + "</li><li> ".join(publications_formatted) + "</li></ul>"
    else:
        content = "<strong style='color:red'>Missing !</strong>"

    p_val = quote(" or ".join(parameters))
        # include "&c=" parameter for bibliographic records
        # and one "&c=" parameter for authority records
    url_str = \
    "/search" + \
    "?p=" + p_val + \
    "&c=" + quote(CFG_SITE_NAME) + \
    "&c=" + CFG_BIBAUTHORITY_AUTHORITY_COLLECTION_NAME + \
    "&sc=1" + \
    "&ln=" + bfo.lang
    prefix = prefix_pattern % url_str
    content += prefix + "See all " + str(count) + " publications..." + postfix

    return "<p>" + title + ": " + content + "</p>"

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
