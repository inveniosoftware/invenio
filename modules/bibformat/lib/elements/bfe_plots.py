# -*- coding: utf-8 -*-
##
## $Id: bfe_CERN_plots.py,v 1.3 2009/03/17 10:55:15 jerome Exp $
##
## This file is part of Invenio.
## Copyright (C) 2010, 2011 CERN.
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
"""BibFormat element - Display image of the plot if we are in selected plots collection
"""
__revision__ = "$Id: bfe_CERN_plots.py,v 1.3 2009/03/17 10:55:15 jerome Exp $"

from invenio.bibdocfile import BibRecDocs
from invenio.urlutils import create_html_link
from invenio.config import CFG_BASE_URL, CFG_SITE_RECORD

def format_element(bfo, width="", caption="yes", max="-1"):
    """
    Display image of the plot if we are in selected plots collections

    @param width: the width of the returned image (Eg: '100px')
    @param caption: display the captions or not?
    @param max: the maximum number of plots to display (-1 is all plots)
    """
    ## To achieve this, we take the pngs associated with this document

    img_files = []
    max = int(max)

    bibarchive = BibRecDocs(bfo.recID)

    if width != "":
        width = 'width="%s"' % width

    for doc in bibarchive.list_bibdocs():
        for _file in doc.list_latest_files():
            if _file.get_type() == "Plot":

                try:
                    caption_text = _file.get_description()[5:]
                    index = int(_file.get_description()[:5])
                    img_location = _file.get_url()
                except:
                    # FIXME: we have hit probably a plot context file,
                    # so ignore this document; but it would be safer
                    # to check subformat type, so that we don't mask
                    # other eventual errors here.
                    continue

                img = '<img src="%s" title="%s" %s/>' % \
                      (img_location, caption_text, width)

                link = create_html_link(urlbase='%s/%s/%s/plots#%d' %
                                                (CFG_BASE_URL, CFG_SITE_RECORD, bfo.recID,\
                                                 index),
                                        urlargd={},
                                        link_label=img)

                img_files.append((index, link))

    img_files = sorted(img_files, key=lambda x: x[0])
    if max > 0:
        img_files = img_files[:max]

    for index in range(len(img_files)):
        img_files[index] = img_files[index][1]

    if len(img_files) == 0:
        return ''

    return '<div style="overflow-x:scroll;width=100%;white-space:nowrap">' +\
           " ".join(img_files) + '</div>'

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
