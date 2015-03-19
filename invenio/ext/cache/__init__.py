# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2015 CERN.
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
"""
    invenio.ext.cache
    -----------------

    This module provides initialization and configuration for `flask_cache`
    module.
"""

from flask_cache import Cache
cache = Cache()

__all__ = ['cache', 'setup_app']


def setup_app(app):
    """Setup cache extension."""

    app.config.setdefault('CACHE_TYPE',
                          app.config.get('CFG_FLASK_CACHE_TYPE', 'redis'))
    # if CACHE_KEY_PREFIX is not specified then CFG_DATABASE_NAME:: is used.
    prefix = app.config.get('CFG_DATABASE_NAME', '')
    if prefix:
        prefix += '::'
    app.config.setdefault('CACHE_KEY_PREFIX', prefix)
    cache.init_app(app)
    return app
