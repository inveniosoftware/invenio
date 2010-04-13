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

import cgi
from invenio.bibdocfile import BibRecDocs, get_subformat_from_format

def format(bfo, separator=" ", style='', print_links='yes'):
    """
    Lists the photos of a record. Display the icon version, linked to
    its original version.

    This element works for photos appended to a record as BibDoc
    files, for which a preview icon has been generated. If there are
    several formats for one photo, use the first one found.

    @param separator: separator between each photo
    @param print_links: if 'yes', print links to the original photo
    @param style: style attributes of the images. Eg: "width:50px;border:none"
    """

    photos = []
    bibarchive = BibRecDocs(bfo.recID)
    for doc in bibarchive.list_bibdocs():
        found_url = ''
        found_icon = ''
        for docfile in doc.list_latest_files():
            if docfile.is_icon():
                if not found_icon:
                    found_icon = docfile.get_url()
            else:
                if not found_url:
                    found_url = docfile.get_url()

        if found_icon:
            name = doc.get_docname()
            img = '<img src="%s" alt="%s" style="%s">' % (cgi.escape(found_icon, True), cgi.escape(name, True), cgi.escape(style, True))
            if print_links.lower() == 'yes':
                img = '<a href="%s">%s</a>' % (cgi.escape(found_url, True), img)
            photos.append(img)

    return separator.join(photos)

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
