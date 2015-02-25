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
"""BibFormat element - Prints the control number of an Authority Record.
"""

from invenio.config import CFG_SITE_URL, CFG_SITE_NAME

from invenio.legacy.bibauthority.config import \
    CFG_BIBAUTHORITY_AUTHORITY_COLLECTION_NAME, \
    CFG_BIBAUTHORITY_RECORD_CONTROL_NUMBER_FIELD, \
    CFG_BIBAUTHORITY_RECORD_AUTHOR_CONTROL_NUMBER_FIELDS as control_number_fields, \
    CFG_BIBAUTHORITY_AUTHORITY_COLLECTION_IDENTIFIER as authority_identifier
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

    control_nos = [d['a'] for d in bfo.fields('035__') if d.get('a')]
    control_nos.extend([d['a'] for d in bfo.fields('970__') if d.get('a')])

    authority_type = [d.get('a') for d in bfo.fields('980__') if d.get('a') and d.get('a')!=authority_identifier]
    if authority_type and type(authority_type) is list:
        authority_type = authority_type[0]

    related_control_number_fields = ['510','970']
    related_control_number_fields.extend(control_number_fields.get(authority_type,[]))
    control_nos_formatted = []
    for control_no in control_nos:
        recIDs = get_dependent_records_for_control_no(control_no)
        count = len(recIDs)
        count_string = str(count) + " dependent records"
        from urllib import quote
        # if we have dependent records, provide a link to them
        if count:
            prefix_pattern = "<a href='" + CFG_SITE_URL + "%s" + "'>"
            postfix = "</a>"
            url_str = ''
            # we have multiple dependent records
            if count > 1:
                # joining control_nos might be more helpful for the user
                # than joining recIDs... or maybe not...
                parameters = []
                for control_number_field in related_control_number_fields:
                    parameters.append(control_number_field + ":" + control_no )
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
                    "?p=" + CFG_BIBAUTHORITY_RECORD_CONTROL_NUMBER_FIELD + ":" + control_no + \
                    "&c=" + quote(CFG_SITE_NAME) + \
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
    if control_nos_formatted:
        content = "<ul><li>" + "</li><li> ".join(control_nos_formatted) + "</li></ul>"
    else:
        content = "<strong style='color:red'>Missing !</strong>"

    return "<p>" + title + ": " + content + "</p>"

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
