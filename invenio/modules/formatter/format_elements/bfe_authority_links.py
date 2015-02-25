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
    CFG_BIBAUTHORITY_RECORD_AUTHOR_CONTROL_NUMBER_FIELDS
from invenio.legacy.bibauthority.engine import \
    get_low_level_recIDs_from_control_no, \
    get_dependent_records_for_control_no

from invenio.utils.viaf import get_wikipedia_link,get_wiki_link_from_record

__revision__ = "$Id$"

def format_element(bfo):
    """ Prints the control number of an author authority record in HTML.
    By default prints brief version.

    @param brief: whether the 'brief' rather than the 'detailed' format
    @type brief: 'yes' or 'no'
    """

    from invenio.messages import gettext_set_language
    _ = gettext_set_language(bfo.lang)    # load the right message language

    control_nos = [d['a'] for d in bfo.fields('035__') if d['a'] is not None]
    control_nos = filter(None, control_nos) # fastest way to remove empty ""s

    style = "style='width:auto;height:20px;margin-right:10px'"
    links_formatted = []
    for control_no in control_nos:
        from urllib import quote
        image_pattern = "<a href='%(external_article)s'><img class='author_usefull_link' src='/img/%(image)s'/>%(text)s</a>"

        if (control_no.find("|(VIAF)") != -1):
            viaf_id = control_no.split("|(VIAF)")[1]
            link_to_wikipedia = get_wiki_link_from_record(bfo)
            if not link_to_wikipedia:
                link_to_wikipedia = get_wikipedia_link(viaf_id)
            ## Wikipedia link with wiki icon
            if link_to_wikipedia:
                image_element = image_pattern % { "text": "Wikipedia link", "image": "wikipedia.png", "external_article": link_to_wikipedia}
                links_formatted.append(image_element)
            ## VIAF link
            image_element = image_pattern \
                    % { "text" : "VIAF cluster link","image": "viaf.png", "external_article": str("http://viaf.org/viaf/"+viaf_id) }
            links_formatted.append(image_element)
            ## Library of congress link
        if (control_no.find("|(DLC)") != -1):
            dlc_id = control_no.split("|(DLC)")[1].replace(" ","")
            link_to_lccn = "http://lccn.loc.gov/"+ dlc_id
            image_element = image_pattern % { "text": "Library of Congress link", "image": "library_of_congress.png", "external_article" : link_to_lccn }
            links_formatted.append(image_element)





    if links_formatted:
        title = "<strong>" + _("Useful links") + "</strong>"
        if links_formatted:
            content = "<ul><li>" + "</li><li> ".join(links_formatted) + "</li></ul>"
        else:
            content = "<strong style='color:red'>Missing !</strong>"

        return "<p>" + title + ": " + content + "</p>"
    else:
        return None
def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
