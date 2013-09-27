# -*- coding: utf-8 -*-
## This file is part of Invenio.
## Copyright (C) 2012, 2013 CERN.
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
"""
    invenio.ext.assets
    ------------------

    This module provides additional extensions and functions for
    `flask.ext.assets` module.
"""

import os
from flask import current_app
from flask.ext.assets import Environment, Bundle
from .extensions import CollectionExtension


def setup_app(app):
    """Initializes Assets extension."""

    # Let's create assets environment.
    assets = Environment(app)
    assets.debug = 'assets-debug' in app.config.get('CFG_DEVEL_TOOLS', [])
    assets.directory = app.config.get('CFG_WEBDIR', '')

    def _jinja2_new_bundle(tag, collection, name=None):
        if not assets.debug:
            files = [f for f in collection if os.path.isfile(
                     os.path.join(assets.directory, f))]
            if len(files) != len(collection):
                ## Turn on debuging to generate 404 request on missing files.
                assets.debug = True
                current_app.logger.error('Missing files: ' + ','.join(
                    set(collection) - set(files)))

        if len(collection):
            return Bundle(output="%s/%s-%s.%s" %
                          (tag, 'invenio' if name is None else name,
                           hash('|'.join(collection)), tag), *collection)

    app.jinja_env.extend(new_bundle=_jinja2_new_bundle,
                         default_bundle_name='90-invenio')
    app.jinja_env.add_extension(CollectionExtension)

    return app
