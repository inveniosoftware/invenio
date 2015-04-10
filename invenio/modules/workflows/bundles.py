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

"""Workflows bundles."""

from __future__ import unicode_literals

from invenio.base.bundles import invenio as _i, jquery as _j
from invenio.ext.assets import Bundle, CleanCSSFilter, RequireJSFilter


js = Bundle(
    'js/workflows/init.js',
    filters=RequireJSFilter(exclude=[_j, _i]),
    output='workflows.js',
    weight=50,
    bower={
        "bootstrap-tagsinput": "git://github.com/inspirehep/bootstrap-tagsinput.git#master",
        "datatables": "latest",
        "datatables-plugins": "latest",
        "datatables-tabletools": "latest",
        "prism": "gh-pages",
        "flight": "latest"
    }
)

css = Bundle(
    'vendors/prism/themes/prism.css',
    'vendors/bootstrap-tagsinput/src/bootstrap-tagsinput.css',
    'vendors/datatables/media/css/jquery.dataTables.css',
    'vendors/datatables-plugins/integration/bootstrap/3/dataTables.bootstrap.css',
    'vendors/datatables-tabletools/css/dataTables.tableTools.css',
    'css/workflows/workflows.css',
    filters=CleanCSSFilter(),
    output='workflows.css',
    weight=30,
    bower={
        "bootstrap-tagsinput": "git://github.com/inspirehep/bootstrap-tagsinput.git#master",
        "datatables": "latest",
        "datatables-plugins": "latest",
        "datatables-tabletools": "latest",
        "prism": "gh-pages"
    }
)
