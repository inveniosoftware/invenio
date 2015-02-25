# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2010, 2011, 2014 CERN.
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
"""BibFormat element - Prints a link to BibDocFile
"""
__revision__ = "$Id$"

from invenio.utils.url import create_html_link
from invenio.base.i18n import gettext_set_language
from invenio.config import CFG_BASE_URL, CFG_SITE_RECORD
from invenio.modules.access.engine import acc_authorize_action

def format_element(bfo, style):
    """
    Prints a link to simple file management interface (BibDocFile), if
    authorization is granted.

    @param style: the CSS style to be applied to the link.
    """
    _ = gettext_set_language(bfo.lang)

    out = ""

    user_info = bfo.user_info
    (auth_code, auth_message) = acc_authorize_action(user_info,
                                                     'runbibdocfile')
    if auth_code == 0:
        linkattrd = {}
        if style != '':
            linkattrd['style'] = style

        out += create_html_link(CFG_BASE_URL + '/%s/managedocfiles' % CFG_SITE_RECORD,
                                urlargd={'ln': bfo.lang,
                                         'recid': str(bfo.recID)},
                                link_label=_("Manage Files of This Record"),
                                linkattrd=linkattrd)
    return out

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
