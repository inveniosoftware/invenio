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

"""Bundles for Jasmine test runner."""

from invenio.ext.assets import Bundle

jasmine_js = Bundle(
    # es5-shim is needed by PhantomJS
    'vendors/es5-shim/es5-shim.js',
    'vendors/es5-shim/es5-sham.js',
    'vendors/jasmine/lib/jasmine-core/jasmine.js',
    'vendors/jasmine/lib/jasmine-core/jasmine-html.js',
    'js/jasmine/boot.js',
    'vendors/jquery/dist/jquery.js',
    'vendors/jasmine-jquery/lib/jasmine-jquery.js',
    'vendors/jasmine-flight/lib/jasmine-flight.js',
    'vendors/jasmine-ajax/lib/mock-ajax.js',
    output="jasmine.js",
    # Must be included prior to RequireJS
    weight=-1,
    bower={
        "es5-shim": "latest",
        "jasmine": "latest",
        "jasmine-jquery": "latest",
        "jasmine-flight": "latest",
        "jasmine-ajax": "latest",
    }
)

jasmine_styles = Bundle(
    'vendors/jasmine/lib/jasmine-core/jasmine.css',
    weight=-1,
    output='jasmine.css'
)
