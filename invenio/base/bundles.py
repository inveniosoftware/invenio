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

"""Base bundles.

.. note:: `bootstrap.js` bundle must be loaded after jQuery UI to avoid conflicts.
    You can use `noConflict()` if you need to access functions
    of jQuery UI covered by `bootstrap.js`.
"""

import mimetypes

from invenio.ext.assets import Bundle


mimetypes.add_type("text/css", ".less")


invenio = Bundle(
    "js/invenio.js",
    output="invenio.js",
    filters="requirejs",
    weight=90
)

styles = Bundle(
    "vendors/jquery-tokeninput/styles/token-input.css",
    "vendors/jquery-tokeninput/styles/token-input-facebook.css",
    "vendors/jqueryui-timepicker-addon/dist/jquery-ui-timepicker-addon.css",
    "vendors/typeahead.js-bootstrap3.less/typeahead.css",
    "less/base.less",
    output="invenio.css",
    depends=[
        "less/base.less",
        "less/base/**/*.less"
    ],
    filters="less,cleancss",
    weight=50,
    bower={
        "bootstrap": "3.2.0",
        "font-awesome": "4.1.0",
        "typeahead.js-bootstrap3.less": "0.2.3",
        "jqueryui-timepicker-addon": "latest"
    }
)

# FIXME
#if config.CFG_WEBSTYLE_TEMPLATE_SKIN != "default":
#    styles.contents.append("css/" + config.CFG_WEBSTYLE_TEMPLATE_SKIN + ".css")

jquery = Bundle(
    "vendors/jquery/dist/jquery.js",
    "vendors/jquery.jeditable/index.js",
    "vendors/jquery-tokeninput/src/jquery.tokeninput.js",
    "vendors/jquery.caret/dist/jquery.caret-1.5.2.js",
    "vendors/typeahead.js/dist/typeahead.bundle.js",
    "vendors/hogan/web/builds/3.0.2/hogan-3.0.2.js",
    "js/translate.js",
    "js/init.js",
    output="jquery.js",
    filters="requirejs",
    weight=10,
    bower={
        # The dependencies marked as *orphan* are not part of any bundles
        # and loaded manually using the script tag. Usually from legacy pages.
        "flot": "latest",  # orphan
        "jquery": "~1.11",
        "jquery.caret": "https://github.com/acdvorak/jquery.caret.git",
        "jquery-form": "latest",  # orphan
        "jquery.hotkeys": "https://github.com/jeresig/"  # orphan
                          "jquery.hotkeys.git",
        "jquery.jeditable": "http://invenio-software.org/download/jquery/"
                            "v1.5/js/jquery.jeditable.mini.js",
        "jquery-migrate": "latest",  # orphan
        "jquery-multifile": "svn+http://jquery-multifile-plugin.googlecode.com"
                            "/svn/",  # orphan
        "jquery-tablesorter": "http://invenio-software.org/download/jquery/"
                              "jquery.tablesorter.20111208.zip",  # orphan
        "jquery-tokeninput": "latest",
        "jquery.treeview": "latest",  # orphan, to be replaced by jqTree
        "json2": "latest",  # orphan
        "hogan": "~3",
        "MathJax": "~2.4",  # orphan
        "swfobject": "latest",  # orphan
        "typeahead.js": "latest",
        "uploadify": "latest"  # orphan
    }
)

# jQuery UI
jqueryui = Bundle(
    "js/jquery-ui.js",
    filters="requirejs",
    output="jquery-ui.js",
    weight=11,
    bower={
        "jquery-ui": "~1.11.0",
        #"jqueryui-timepicker-addon": "latest" is set by styles already
    }
)

# must be loaded after jQuery UI to avoid conflicts
# use noConflict() from bootstrap.js to get the functions of jQuery UI covered
# by bootstrap.js
bootstrap = Bundle(
    "vendors/bootstrap/dist/js/bootstrap.js",
    "js/bootstrap-select.js",
    output="bootstrap.js",
    filters="uglifyjs",
    weight=jqueryui.weight + 1,
    bower={
        #"bootstrap": "*", is set by invenio.css already.
    }
)

# less.js is only used when the following configuration is set:
#
#  - ASSETS_DEBUG is True
#  - LESS_RUN_IN_DEBUG is False
#
lessjs = Bundle(
    "vendors/less/dist/less-1.7.0.js",
    output="less.js",
    filters="uglifyjs",
    weight=0,
    bower={
        "less": "latest"
    }
)

# require.js is only used when:
#
#  - ASSETS_DEBUG is True
#  - REQUIREJS_RUN_IN_DEBUG is not False
requirejs = Bundle(
    "vendors/requirejs/require.js",
    "js/settings.js",
    output="require.js",
    filters="uglifyjs",
    weight=0,
    bower={
        "requirejs": "latest",
        "requirejs-hogan-plugin": "latest"
    }
)

# almond.js is only used when:
#
#  - ASSETS_DEBUG is False
#  - or REQUIREJS_RUN_IN_DEBUG is True
almondjs = Bundle(
    "vendors/almond/almond.js",
    "js/settings.js",
    output="almond.js",
    filters="uglifyjs",
    weight=0,
    bower={
        "almond": "latest"
    }
)
