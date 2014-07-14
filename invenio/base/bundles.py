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

"""Base bundles."""

from invenio.ext.assets import Bundle


invenio = Bundle(
    "js/invenio.js",
    output="invenio.js",
    filters="requirejs",
    weight=90
)

styles = Bundle(
    "css/token-input.css",
    "css/token-input-facebook.css",
    "css/typeahead.js-bootstrap.css",
    "less/base.less",
    "css/tags/popover.css",
    output="invenio.css",
    depends=[
        "less/base.less",
        "less/base/**/*.less"
    ],
    filters="less,cleancss",
    weight=50
)

# FIXME
#if config.CFG_WEBSTYLE_TEMPLATE_SKIN != "default":
#    styles.contents.append("css/" + config.CFG_WEBSTYLE_TEMPLATE_SKIN + ".css")

jquery = Bundle(
    "js/jquery.js",
    "js/jquery.jeditable.mini.js",
    "js/jquery.tokeninput.js",
    "js/jquery-caret.js",
    "js/typeahead.js",
    "js/bootstrap.js",
    "js/bootstrap-select.js",
    "js/hogan.js",
    "js/translate.js",
    output="jquery.js",
    filters="uglifyjs",
    weight=10,
    bower={
        "jquery": "2.1.0",
        "bootstrap": "3.2.0",
        "hogan": "3.0.0",
        "jquery.jeditable": "http://invenio-software.org/download/jquery/v1.5/js/jquery.jeditable.mini.js",
        "jquery-tokeninput": "*"
    }
)

# jQuery UI
jqueryui = Bundle(
    "js/jqueryui/jquery-ui.custom.js",
    "js/jquery-ui-timepicker-addon.js",
    filters="uglifyjs",
    output="jquery-ui.js",
    weight=11,
    bower={
        "jqueryui": "1.11.0",
        "jquery.ui.timepicker": "http://invenio-software.org/download/jquery/jquery-ui-timepicker-addon-1.0.3.js"
    }
)

# if ASSETS_DEBUG and not LESS_RUN_IN_DEBUG
lessjs = Bundle(
    "js/less.js",
    output="less.js",
    filters="uglifyjs",
    weight=0,
    bower={
        "less": "1.7.0"
    }
)

# if ASSETS_DEBUG and not REQUIRESJS_RUN_IN_DEBUG
requirejs = Bundle(
    "js/require.js",
    "js/settings.js",
    output="require.js",
    filters="uglifyjs",
    weight=0,
    bower={
        "requirejs": "latest"
    }
)
# else
almondjs = Bundle(
    "js/almond.js",
    "js/settings.js",
    output="almond.js",
    filters="uglifyjs",
    weight=0,
    bower={
        "almond": "latest"
    }
)
