# -*- coding: utf-8 -*-
#
# $Id: bfe_CERN_plots.py,v 1.3 2009/03/17 10:55:15 jerome Exp $
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
"""BibFormat element - Display image of the plot if we are in selected plots collection
"""
__revision__ = "$Id: bfe_CERN_plots.py,v 1.3 2009/03/17 10:55:15 jerome Exp $"

from invenio.legacy.bibdocfile.api import BibRecDocs


def format_element(bfo):
    """
    Display image of the thumbnail plot if we are in selected plots collections
    """
    ## To achieve this, we take the Thumb file associated with this document

    bibarchive = BibRecDocs(bfo.recID)

    img_files = []

    for doc in bibarchive.list_bibdocs():
        for _file in doc.list_latest_files():
            if _file.get_type() == "Plot":
                caption_text = _file.get_description()[5:]
                index = int(_file.get_description()[:5])
                img_location = _file.get_url()

                if img_location == "":
                    continue

                img = '<img src="%s" width="100px"/>' % \
                      (img_location)
                img_files.append((index, img_location)) # FIXME: was link here

            if _file.get_type() == "Thumb":
                img_location = _file.get_url()
                img = '<img src="%s" width="100px"/>' % \
                      (img_location)
                return '<div align="left">' + img  + '</div>'

    # then we use the default: the last plot with an image
    img_files = sorted(img_files, key=lambda x: x[0])
    if img_files:
        return '<div align="left">' + img_files[-1][1] + '</div>'
    else:
        return ''

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
