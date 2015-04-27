# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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

"""Annotations bundles."""

from __future__ import unicode_literals

from invenio.ext.assets import Bundle
from invenio.modules.comments.bundles import css as _commentscss, \
    js as _commentsjs
from invenio.modules.previewer.bundles import pdftk as _pdftk


_pdftk.contents += ("js/annotations/pdf_notes_helpers.js",)

_commentsjs.contents += ("js/annotations/notes_popover.js",)
_commentscss.contents += ("css/annotations/annotations.css",)

js = Bundle(
    "vendors/plupload/js/moxie.js",
    "vendors/plupload/js/plupload.dev.js",
    "js/annotations/annotations.js",
    "js/annotations/plupload_helper.js",
    filters="uglifyjs",
    output="annotations.js",
    weight=30,
    bower={
        "plupload": "latest"
    }
)
