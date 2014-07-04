# -*- coding: utf-8 -*-
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
    output="gen/invenio.js",
    filters="requirejs",
    name="90-invenio.js"
)

styles = Bundle(
    "css/token-input.css",
    "css/token-input-facebook.css",
    "less/base.less",
    "css/tags/popover.css",
    output="gen/invenio.css",
    depends=[
        "less/base.less",
        "less/base/**/*.less"
    ],
    extra={
        "rel": "stylesheet/less"
    },
    filters="less,cleancss",
    name="50-invenio.css"
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

    output="gen/jquery.js",
    filters="uglifyjs",
    name="10-jquery.js",
    bower={
        "jquery": "2.1.0",
        "bootstrap": "3.2.0",
        "hogan": "3.0.0",
        "jquery.jeditable": "http://invenio-software.org/download/jquery/v1.5/js/jquery.jeditable.mini.js",
        "jquery.tokeninput": "*"
    }
)

# jQuery UI
jqueryui = Bundle(
    "js/jqueryui/jquery-ui.js",
    filters="uglifyjs",
    output="gen/jquery-ui.js",
    name="11-jquery-ui.js",
    bower={
        "jqueryui": "1.11.0",
    }
)

# if ASSETS_DEBUG and not LESS_RUN_IN_DEBUG
lessjs = Bundle(
    "js/less.js",
    output="gen/less.js",
    filters="uglifyjs",
    name="00-less.js",
    bower={
        "less": "1.7.0"
    }
)

# if ASSETS_DEBUG and not REQUIRESJS_RUN_IN_DEBUG
requirejs = Bundle(
    "js/require.js",
    "js/settings.js",
    output="gen/require.js",
    filters="uglifyjs",
    name="00-require.js",
    bower={
        "requirejs": "latest"
    }
)
# else
almondjs = Bundle(
    "js/almond.js",
    "js/settings.js",
    output="gen/almond.js",
    filters="uglifyjs",
    name="00-require.almond.js",
    bower={
        "almond": "latest"
    }
)
