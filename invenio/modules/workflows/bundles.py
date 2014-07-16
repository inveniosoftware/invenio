# -*- coding: utf-8 -*-
#
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

"""Workflows bundles."""

from invenio.ext.assets import Bundle
from invenio.base.bundles import jquery as _jquery


_jquery.contents.append('vendors/bootstrap-tagsinput/dist/'
                        'bootstrap-tagsinput.js')
_jquery.bower['bootstrap-tagsinput'] = "latest"

js = Bundle(
    'js/workflows/entry_details.js',
    'js/workflows/hp_details.js',
    'js/workflows/hp_maintable.js',
    'js/workflows/hp_selection.js',
    'js/workflows/hp_tags.js',
    'js/workflows/hp_utilities.js',
    'js/workflows/utilities.js',
    'js/workflows/workflows.js',
    filters="uglifyjs",
    output='workflows.js',
    weight=50
)

actions = Bundle(
    'js/workflows/actions/approval.js',
    filters="uglifyjs",
    output='actions.js',
    weight=50
)

vendors_js = Bundle(
    'vendors/prism/prism.js',
    'js/prettify.min.js',  # is https://code.google.com/p/google-code-prettify/
    filters="uglifyjs",
    output='vendors.js',
    weight=40,
    bower={
        "prism": "gh-pages"
    }
)

vendors_css = Bundle(
    'vendors/prism/themes/prism.css',
    'css/prettify.css',
    filters="cleancss",
    output='vendors.css',
    weight=40,
    bower={
        #"prism": "*"  # already present in vendors_js
    }
)

dataTables_css = Bundle(
    'css/dataTables.colVis.css',
    'css/dataTables.bootstrap.css',
    'vendors/bootstrap-tagsinput/dist/bootstrap-tagsinput.less',
    filters="less,cleancss",
    output='dataTables.css',
    weight=30,
    bower={
        #"bootstrap-tagsinput": "*"  # already present in _jquery
    }
)

dataTables_js = Bundle(
    'js/jquery.dataTables.min.js',
    'js/dataTables.colVis.js',
    'js/dataTables.bootstrap.js',
    filters="uglifyjs",
    output='dataTables.js',
    weight=30
)
