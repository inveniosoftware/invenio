# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2013, 2014 CERN.
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

"""Flask-Cache backend for session.

Configuration variables for Flask-Cache backend.

=============================== ===============================================
`SESSION_BACKEND_CACHE`         Configured *Flask-Cache* object.
                                **Default:** ``invenio.ext.cache:cache``
`SESSION_BACKEND_CACHE_PREFIX`  Prefix for keys stored in cache.
                                **Default:** ``session::``
`SESSION_BACKEND_CACHE_TIMEOUT` Default cache timeout. **Default:** ``3600``
=============================== ===============================================
"""

from datetime import timedelta
from flask import current_app
from flask.helpers import locked_cached_property
from werkzeug.utils import import_string

from ..storage import SessionStorage


class Storage(SessionStorage):

    """Implement session cache storage."""

    @locked_cached_property
    def cache(self):
        """Return cache storage."""
        return import_string(current_app.config.get(
            'SESSION_BACKEND_CACHE', 'invenio.ext.cache:cache'))

    @locked_cached_property
    def key(self):
        """Return cache key prefix."""
        return current_app.config.get('SESSION_BACKEND_CACHE_PREFIX',
                                      'session::')

    @locked_cached_property
    def timeout(self):
        """Return cache engine timeout."""
        return current_app.config.get('SESSION_BACKEND_CACHE_TIMEOUT', 3600)

    def set(self, name, value, timeout=None):
        """Store value in cache."""
        timeout = timeout if timeout is not None else self.timeout
        # Convert datetime.timedeltas to seconds.
        if isinstance(timeout, timedelta):
            timeout = timeout.seconds + timeout.days * 24 * 3600
        self.cache.set(self.key + name, value, timeout=timeout)

    def get(self, name):
        """Return value from cache."""
        return self.cache.get(self.key + name)

    def delete(self, name):
        """Delete key from cache."""
        self.cache.delete(self.key + name)
