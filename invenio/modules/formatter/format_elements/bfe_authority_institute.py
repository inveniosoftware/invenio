# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2013, 2015 CERN.
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
"""BibFormat element - Prints institute data from an Authority Record.
"""

__revision__ = "$Id$"

from invenio.config import CFG_SITE_URL
from invenio.legacy.bibauthority.config import \
    CFG_BIBAUTHORITY_RECORD_CONTROL_NUMBER_FIELD, \
    CFG_BIBAUTHORITY_AUTHORITY_COLLECTION_NAME

from invenio.legacy.bibauthority.engine import \
    get_control_nos_from_recID, \
    guess_main_name_from_authority_recID
from invenio.legacy.search_engine import \
    perform_request_search, \
    get_record

def format_element(bfo, main_name='yes', detail='no'):
    """ Prints the data of an institute authority record in HTML. By default prints
    brief version.

    @param detail: whether the 'detailed' rather than the 'brief' format
    @type detail: 'yes' or 'no'
    """
    from invenio.base.i18n import gettext_set_language
    _ = gettext_set_language(bfo.lang)    # load the right message language

    # return value
    out = ""
    # brief
    main_dicts = bfo.fields('110%%')
    if len(main_dicts) and main_name=='yes':
        main = main_dicts[0].get('a') or ""
        ##out += "<p style='margin-top:0px;margin-bottom:0px>" + "<strong>" + _("Main %s name") % _("institute") + "</strong>" + ": " + main + "</p>"
        out += "<a href='" +"/record/"+ str(bfo.recID) +"?ln=" + bfo.lang + "' >" + main + "</a>"
    # detail
    if detail.lower() == "yes":
        sees = [see_dict['a'] for see_dict in bfo.fields('410%%') if 'a' in see_dict]
        sees = filter(None, sees) # fastest way to remove empty ""s
        if len(sees):
            out += "<p>" + "<strong>" + _("Variant(s)") + "</strong>" + ": " + ", ".join(sees) + "</p>"
        see_also_dicts = bfo.fields('510%%')
        cc_val = CFG_BIBAUTHORITY_AUTHORITY_COLLECTION_NAME
        c_val = "Institutes"
        record_url_pattern = "/record/" + "%s"
        search_url_pattern = "/search?" + \
            "cc=" + "%s" + \
            "&c=" + "%s" + \
            "&p=" + "%s" + \
            "&sc=" + "%s"
        link_pattern = "<a href='" + CFG_SITE_URL + '%s' + "'>" + '%s' + "</a>"
        # populate the first 3 lists
        parent_htmls, predecessor_htmls, successor_htmls = \
            get_main_htmls(see_also_dicts, cc_val, c_val, record_url_pattern,
                           search_url_pattern, link_pattern)
        # populate the list of children
        child_htmls = \
            get_child_htmls(bfo.recID, cc_val, c_val, record_url_pattern,
                            link_pattern)
        # put it all together
        if len(parent_htmls):
            out += "<p>" + "<strong>" + _("Parent") + "</strong>" + ": " + ", ".join(parent_htmls) + "</p>"
        if len(child_htmls):
            out += "<p>" + "<strong>" + _("Children") + "</strong>" + ": " + ", ".join(child_htmls) + "</p>"
        if len(predecessor_htmls):
            out += "<p>" + "<strong>" + _("Predecessor") + "</strong>" + ": " + ", ".join(predecessor_htmls) + "</p>"
        if len(successor_htmls):
            out += "<p>" + "<strong>" + _("Successor") + "</strong>" + ": " + ", ".join(successor_htmls) + "</p>"
    # return
    return out

def get_main_htmls(see_also_dicts, cc_val, c_val, record_url_pattern,
                   search_url_pattern, link_pattern):
    """parent_htmls, predecessor_htmls, successor_htmls can all be deduced
    directly from the metadata of the record"""
    # reusable vars
    f_val = CFG_BIBAUTHORITY_RECORD_CONTROL_NUMBER_FIELD
    sc_val = "1"
    parent_htmls = []
    predecessor_htmls = []
    successor_htmls = []

    # start processing
    for see_also_dict in see_also_dicts:
        if 'w' in see_also_dict:
            # $w contains 'a' for predecessor, 'b' for successor, etc.
            w_subfield = see_also_dict.get('w')
            # $4 contains control_no of linked authority record
            _4_subfield = see_also_dict.get('4')
            # $a contains the name of the linked institute
            out_string = see_also_dict.get('a') or _4_subfield
            # if we have something to display
            if out_string:
                url = ''
                # if we have a control number
                if _4_subfield:
                    p_val = _4_subfield
#                    if CFG_BIBAUTHORITY_PREFIX_SEP in _4_subfield:
#                        unused, p_val = _4_subfield.split(CFG_BIBAUTHORITY_PREFIX_SEP);
                    recIDs = perform_request_search(cc=cc_val,
                                                    c=c_val,
                                                    p=p_val,
                                                    f=f_val)
                    if len(recIDs) == 1:
                        url = record_url_pattern % (recIDs[0])
                    elif len(recIDs) > 1:
                        p_val = "recid:" + \
                            " or recid:".join([str(r) for r in recIDs])
                        url = search_url_pattern % (cc_val,
                                                      c_val,
                                                      p_val,
                                                      sc_val)
                # if we found one or multiple records for the control_no,
                # make the out_string a clickable url towards those records
                if url:
                    out_string = link_pattern % (url, out_string)
                # add the out_string to the appropriate list
                if w_subfield == 't':
                    parent_htmls.append(out_string)
                elif w_subfield == 'a':
                    predecessor_htmls.append(out_string)
                elif w_subfield == 'b':
                    successor_htmls.append(out_string)
    # return
    return parent_htmls, predecessor_htmls, successor_htmls

def get_child_htmls(this_recID, cc_val, c_val, record_url_pattern,
                    link_pattern):
    """children aren'r referenced by parents, so we need special treatment to find
    them"""
    control_nos = get_control_nos_from_recID(this_recID)
    for control_no in control_nos:
        url = ''
        p_val = '510%4:"' + control_no + '" and 510%w:t'
        # find a first, fuzzy result set
        # narrowing down on a few possible recIDs
        recIDs = perform_request_search(cc=cc_val,
                                        c=c_val,
                                        p=p_val)
        # now filter to find the ones where the subfield conditions of p_val
        # are both true within the exact same field
        sf_req = [('w', 't'), ('4', control_no)]
        recIDs = filter(lambda x:
                            match_all_subfields_for_tag(x, '510', sf_req),
                        recIDs)
        # proceed with assembling the html link
        child_htmls = []
        for recID in recIDs:
            url = record_url_pattern % str(recID)
            display = guess_main_name_from_authority_recID(recID) or str(recID)
            out_html = link_pattern % (url, display)
            child_htmls.append(out_html)
        return child_htmls

def match_all_subfields_for_tag(recID, field_tag, subfields_required=[]):
    """
    Tests whether the record with recID has at least one field with 'field_tag'
    where all of the required subfields in subfields_required match a subfield
    in the given field both in code and value

    @param recID: record ID
    @type recID: int

    @param field_tag: a 3 digit code for the field tag code
    @type field_tag: string

    @param subfields_required: a list of subfield code/value tuples
    @type subfields_required: list of tuples of strings.
        same format as in get_record():
            e.g. [('w', 't'),
                  ('4', 'XYZ123')]

    @return: boolean
    """
    rec = get_record(recID)
    for field in rec[field_tag]:
        subfields_present = field[0]
        intersection = set(subfields_present) & set(subfields_required)
        if set(subfields_required) == intersection:
            return True
    return False

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
