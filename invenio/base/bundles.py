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

"""Base bundles.

.. py:data:: invenio

    Invenio JavaScript scripts

.. py:data:: styles

    Stylesheets such as Twitter Bootstrap, Font-Awesome, Invenio, ...

.. py:data:: jquery

    JavaScript libraries such as jQuery, Type Ahead, Bootstrap, Hogan, ...

    .. note::
        ``bootstrap.js`` provides ``$.fn.button`` which will be overwritten by
        jQueryUI button when loaded globally. Use require.js to load only the
        jQueryUI modules of your needs.

        .. code-block:: javascript

            require(['jquery', 'ui/accordion'], function($) {
                $(function(){
                    $('#accordion').accordion()
                })
            })

.. py:data:: lessjs

    LessCSS JavaScript library that is used in debug mode to render the less
    stylesheets

.. py:data:: requirejs

    Require.js JavaScript library used in debug mode to load asynchronously the
    Javascript modules (defined using AMD).

.. py:data:: almondjs

    Require.js JavaScript library used in production mode. It cannot load
    asynchronously the module that must be bundles using ``r.js``.
"""

from __future__ import unicode_literals

import mimetypes

from invenio.ext.assets import Bundle, RequireJSFilter


mimetypes.add_type("text/css", ".less")


styles = Bundle(
    "vendors/jquery-tokeninput/styles/token-input.css",
    "vendors/jquery-tokeninput/styles/token-input-facebook.css",
    "vendors/typeahead.js-bootstrap3.less/typeahead.css",
    "less/base.less",
    "less/user-menu.less",
    "less/sticky-footer.less",
    "less/footer.less",
    output="invenio.css",
    depends=[
        "less/base.less",
        "less/base/**/*.less"
    ],
    filters="less,cleancss",
    weight=50,
    bower={
        "bootstrap": "3.3.4",
        "font-awesome": "4.1.0",
        "typeahead.js-bootstrap3.less": "0.2.3",
    }
)

jquery = Bundle(
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
        "jquery-multifile": "https://github.com/fyneworks/multifile",
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
        #"bootstrap": "*", is set by invenio.css already.
    }
)

invenio = Bundle(
    "js/invenio.js",
    output="invenio.js",
    filters=RequireJSFilter(exclude=[jquery]),
    weight=90
)

admin = Bundle(
    "js/admin.js",
    output="admin.js",
    filters=RequireJSFilter(exclude=[jquery]),
    weight=50
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
