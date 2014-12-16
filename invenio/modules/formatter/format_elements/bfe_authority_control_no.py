# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
"""BibFormat element - Prints the control number of an Authority Record.
"""

from invenio.config import CFG_SITE_URL, CFG_SITE_NAME

from invenio.legacy.bibauthority.config import \
    CFG_BIBAUTHORITY_AUTHORITY_COLLECTION_NAME
from invenio.legacy.bibauthority.engine import \
    get_low_level_recIDs_from_control_no, \
    get_dependent_records_for_control_no

__revision__ = "$Id$"

def format_element(bfo):
    """ Prints the control number of an author authority record in HTML. 
    By default prints brief version.

    @param brief: whether the 'brief' rather than the 'detailed' format
    @type brief: 'yes' or 'no'
    """

    from invenio.base.i18n import gettext_set_language
    _ = gettext_set_language(bfo.lang)    # load the right message language

    control_nos = [d['a'] for d in bfo.fields('035__')]
    control_nos = filter(None, control_nos) # fastest way to remove empty ""s
        
    control_nos_formatted = []
    for control_no in control_nos:
#        recIDs = []
#        types = guess_authority_types(bfo.recID)
#        # control_no example: AUTHOR:(CERN)aaa0005"
#        control_nos = [(type + CFG_BIBAUTHORITY_PREFIX_SEP + control_no) for type in types]
#        for control_no in control_nos:
#            recIDs.extend(list(search_pattern(p='"' + control_no + '"')))
        recIDs = get_dependent_records_for_control_no(control_no)
        count = len(recIDs)
        count_string = str(count) + " dependent records"
        
        # if we have dependent records, provide a link to them
        if count:
            prefix_pattern = "<a href='" + CFG_SITE_URL + "%s" + "'>"
            postfix = "</a>"
            url_str = ''
            # we have multiple dependent records
            if count > 1:
                # joining control_nos might be more helpful for the user 
                # than joining recIDs... or maybe not...
#                p_val = '"' + '" or "'.join(control_nos) + '"' # more understandable for the user
                p_val = "recid:" + ' or recid:'.join([str(recID) for recID in recIDs]) # more efficient
                # include "&c=" parameter for bibliographic records 
                # and one "&c=" parameter for authority records
                url_str = \
                    "/search" + \
                    "?p=" + p_val + \
                    "&c=" + CFG_SITE_NAME + \
                    "&c=" + CFG_BIBAUTHORITY_AUTHORITY_COLLECTION_NAME + \
                    "&sc=1" + \
                    "&ln=" + bfo.lang
            # we have exactly one dependent record
            elif count == 1:
                url_str = "/record/" + str(recIDs[0])
            
            prefix = prefix_pattern % (url_str)
            count_string = prefix + count_string + postfix
        #assemble the html and append to list
        html_str = control_no + " (" + count_string + ")"
        
        # check if there are more than one authority record with the same
        # control number. If so, warn the user about this inconsistency. 
        # TODO: hide this warning from unauthorized users
        my_recIDs = get_low_level_recIDs_from_control_no(control_no)
        if len(my_recIDs) > 1:
            url_str = \
                    "/search" + \
                    "?p=" + "recid:" + 'or recid:'.join([str(_id) for _id in my_recIDs]) + \
                    "&c=" + CFG_SITE_NAME + \
                    "&c=" + CFG_BIBAUTHORITY_AUTHORITY_COLLECTION_NAME + \
                    "&sc=1" + \
                    "&ln=" + bfo.lang
            html_str += \
                ' <span style="color:red">' + \
                '(Warning, there is currently ' + \
                '<a href="' + url_str + '">more than one authority record</a> ' + \
                'with this Control Number)' + \
                '</span>'
        
        control_nos_formatted.append(html_str)
    
    title = "<strong>" + _("Control Number(s)") + "</strong>"
    content = ", ".join(control_nos_formatted) \
        or "<strong style='color:red'>Missing !</strong>"
    
    return "<p>" + title + ": " + content + "</p>"

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
