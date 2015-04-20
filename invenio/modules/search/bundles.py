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

"""Search bundles."""

from __future__ import unicode_literals

from invenio.base.bundles import invenio as _i, jquery as _j
from invenio.ext.assets import Bundle, RequireJSFilter

js = Bundle(
    'js/search/init.js',
    filters=RequireJSFilter(exclude=[_j, _i]),
    output="search.js",
    weight=50
)

styles = Bundle(
    'css/search/collection.css',
    'css/search/search.css',
    'css/search/searchbar.css',
    filters="cleancss",
    output="search.css",
    weight=60
)

adminjs = Bundle(
    'js/admin/search/init.js',
    filters=RequireJSFilter(exclude=[_j, _i]),
    output="admin/search.js",
    weight=50,
    bower={
        "jquery-ui": "~1.11",
    }
)
