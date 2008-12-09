# -*- coding: utf-8 -*-
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
"""BibFormat element - Print photos of the record (if bibdoc file)
"""
from invenio.bibdocfile import BibRecDocs

def format(bfo, separator=" ", style='', print_links='yes'):
    """
    Lists the photos of a record. Display the icon version, linked to
    its original version.

    This element works for photos appended to a record as BibDoc
    files, for which a preview icon has been generated. If there are
    several formats for one photo, use the first one found.

    @param separator separator between each photo
    @param print_links if 'yes', print links to the original photo
    @param style style attributes of the images. Eg: "width:50px;border:none"
    """

    photos = []
    bibarchive = BibRecDocs(bfo.recID)
    for doc in bibarchive.list_bibdocs():
        if doc.get_icon() is not None:
            original_url = doc.list_latest_files()[0].get_url()
            icon_url = doc.get_icon().list_latest_files()[0].get_url()
            name = doc.get_docname()
            img = '<img src="%s" alt="%s" style="%s">' % (icon_url, name, style)
            if print_links.lower() == 'yes':
                img = '<a href="%s">%s</a>' % (original_url, img)
            photos.append(img)

    return separator.join(photos)

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
