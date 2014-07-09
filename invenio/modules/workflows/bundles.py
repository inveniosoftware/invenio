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

_jquery.contents += ('js/bootstrap-tagsinput.min.js',)

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
    'js/prism.js',
    'js/prettify.min.js',
    filters="uglifyjs",
    output='vendors.js',
    weight=40
)

vendors_css = Bundle(
    'css/prism.css',
    'css/prettify.css',
    filters="cleancss",
    output='vendors.css',
    weight=40
)

dataTables_css = Bundle(
    'css/dataTables.colVis.css',
    'css/dataTables.bootstrap.css',
    'css/bootstrap-tagsinput.css',
    filters="cleancss",
    output='dataTables.css',
    weight=30
)

dataTables_js = Bundle(
    'js/jquery.dataTables.min.js',
    'js/dataTables.colVis.js',
    'js/dataTables.bootstrap.js',
    filters="uglifyjs",
    output='dataTables.js',
    weight=30
)
