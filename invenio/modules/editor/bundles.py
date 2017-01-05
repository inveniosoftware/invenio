# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

"""Editor bundles."""

from invenio.ext.assets import Bundle

js = Bundle(
    "vendors/jquery-ui/jquery-ui.js",
    "js/editor/refextract.js",
    "js/editor/display.js",
    "js/editor/engine.js",
    "js/editor/keys.js",
    "js/editor/menu.js",
    "js/editor/holdingpen.js",
    "js/editor/marcxml.js",
    "js/editor/clipboard.js",
    output="editor.js",
    filters="uglifyjs",
    weight=51,
    bower={
        "jquery-ui": "~1.11",
        # from jquery.js
        #"jquery":
        #"bootstrap":
        #"json2":
        #"jquery.jeditable":
        #"jquery.hotkeys"
    }
)

styles = Bundle(
    "css/editor/base.css",
    "vendors/jquery-ui/themes/redmond/jquery-ui.css",
    output="editor.css",
    filters="cleancss",
    weight=51
)
