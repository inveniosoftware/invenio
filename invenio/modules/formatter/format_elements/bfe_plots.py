# -*- coding: utf-8 -*-
#
# $Id: bfe_CERN_plots.py,v 1.3 2009/03/17 10:55:15 jerome Exp $
#
# This file is part of Invenio.
# Copyright (C) 2010, 2011, 2013, 2014 CERN.
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
"""BibFormat element - Display image of the plot if we are in selected plots collection
"""

from invenio.legacy.bibdocfile.api import BibRecDocs
from invenio.utils.url import create_html_link
from invenio.config import CFG_SITE_RECORD
from invenio.base.i18n import gettext_set_language

try:
    from invenio.config import CFG_BASE_URL
except ImportError:
    from invenio.config import CFG_SITE_URL
    CFG_BASE_URL = CFG_SITE_URL


def format_element(bfo, width="", caption="yes", max_plots="3"):
    """
    Display image of the plot if we are in selected plots collections

    To achieve this, we take the pngs associated with this document

    @param width: the width of the returned image (Eg: '100px')
    @param caption: display the captions or not?
    @param max_plots: the maximum number of plots to display (-1 is all plots)
    """
    _ = gettext_set_language(bfo.lang)

    img_files = []
    try:
        max_plots = int(max_plots)
    except ValueError:
        # Someone tried to squeeze in something non-numerical. Hah!
        max_plots = 3

    link = ""
    bibarchive = BibRecDocs(bfo.recID)

    if width != "":
        width = 'width="%s"' % width

    for doc in bibarchive.list_bibdocs(doctype="Plot"):
        for _file in doc.list_latest_files():
            if _file.subformat == "context":
                # Ignore context files
                continue

            caption_text = _file.get_description()[5:]
            index = int(_file.get_description()[:5])
            img_location = _file.get_url()

            img = '<img style="vertical-align:middle;" src="%s" title="%s" %s/>' % \
                  (img_location, caption_text, width)

            plotlink = create_html_link(urlbase='%s/%s/%s/plots#%d' %
                                        (CFG_BASE_URL,
                                         CFG_SITE_RECORD,
                                         bfo.recID,
                                         index),
                                        urlargd={},
                                        link_label=img)

            img_files.append((index, plotlink))

    img_files = sorted(img_files, key=lambda x: x[0])
    if max_plots > 0:
        img_files = img_files[:max_plots]

    if len(img_files) >= max_plots:
        link = "<a href='/%s/%s/plots'>%s</a>" % \
               (CFG_SITE_RECORD, bfo.recID, _("Show more plots"))

    for index in range(len(img_files)):
        img_files[index] = img_files[index][1]

    if len(img_files) == 0:
        return ''

    return '<div style="overflow-x:auto;display:inline;width:100%;">' +\
           " ".join(img_files) + ' ' + link + '</div>'


def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
