# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2014, 2015 CERN.
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

"""BibFormat element to print a link to BibEdit."""

from invenio.base.i18n import gettext_set_language
from invenio.config import CFG_BASE_URL, CFG_SITE_RECORD
from invenio.legacy.bibedit.utils import user_can_edit_record_collection
from invenio.utils.url import create_html_link


def format_element(bfo, style, html_class='', link_label=None):
    """Print a link to BibEdit, if authorization is granted.

    :param style: the CSS style to be applied to the link.
    :param html_class: the class attribute to be applied to the link.
    :param link_label: Localized link label. Default: "Edit This Record"
                       (or its translated variant).
    """
    _ = gettext_set_language(bfo.lang)

    out = ""

    user_info = bfo.user_info
    if user_can_edit_record_collection(user_info, bfo.recID):
        linkattrd = {}
        if style != '':
            linkattrd['style'] = style
        if html_class != '':
            linkattrd['class'] = html_class
        out += create_html_link(
            CFG_BASE_URL +
            '/%s/edit/?ln=%s#state=edit&recid=%s' % (CFG_SITE_RECORD, bfo.lang,
                                                     str(bfo.recID)),
            {},
            link_label=link_label or _('Edit This Record'),
            linkattrd=linkattrd)

    return out


def escape_values(bfo):
    """Check if output of this element should be escaped."""
    return 0
