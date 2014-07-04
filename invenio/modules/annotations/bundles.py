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

"""Annotations bundles."""


from invenio.ext.assets import Bundle

from invenio.modules.previewer.bundles import pdfjs as _pdfjs
from invenio.modules.comments.bundles import (js as _commentsjs,
                                              css as _commentscss)


_pdfjs.contents += ("js/annotations/pdf_notes_helpers.js",)

_commentsjs.contents += ("js/annotations/notes_popover.js",)
_commentscss.contents += ("css/annotations/annotations.css",)


js = Bundle(
    "plupload/moxie.js",
    "plupload/plupload.dev.js",
    "js/annotations/annotations.js",
    "js/annotations/plupload_helper.js",
    filters="uglifyjs",
    output="gen/annotations.js",
    name="30-annotations.js",
    bower={
        "plupload": "latest"
    }
)
