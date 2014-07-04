# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
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

"""Previewer bundles."""


from invenio.ext.assets import Bundle

pdfjs = Bundle(
    "js/previewer/pdf_viewer.js",
    filters="uglifyjs",
    output="gen/previewer/pdf.js",
    name="20-previewer-pdf.js"
)

pdfcss = Bundle(
    "css/previewer/pdf_viewer.css",
    filters="cleancss",
    output="gen/previewer/pdf.css",
    name="20-previewer-pdf.css"
)
