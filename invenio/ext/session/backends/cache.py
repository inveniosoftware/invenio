# -*- coding: utf-8 -*-

## This file is part of Invenio.
## Copyright (C) 2011, 2012, 2013 CERN.
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
    invenio.ext.session.backends.cache
    ----------------------------------

    Configuration:

    - SESSION_BACKEND_CACHE = 'invenio.ext.cache:cache'
    - SESSION_BACKEND_CACHE_PREFIX = 'session::'
    - SESSION_BACKEND_CACHE_TIMEOUT = 3600
"""

from flask import current_app
from flask.helpers import locked_cached_property
from werkzeug.utils import import_string

from ..storage import SessionStorage


class Storage(SessionStorage):
    """
    Implements session cache storage.
    """

    @locked_cached_property
    def cache(self):
        """Returns cache storage."""
        return import_string(current_app.config.get(
            'SESSION_BACKEND_CACHE', 'invenio.ext.cache:cache'))

    @locked_cached_property
    def key(self):
        """Returns cache key prefix."""
        return current_app.config.get('SESSION_BACKEND_CACHE_PREFIX',
                                      'session::')

    @locked_cached_property
    def timeout(self):
        """Return cache engine timeout."""
        return current_app.config.get('SESSION_BACKEND_CACHE_TIMEOUT', 3600)

    def set(self, name, value, timeout=None):
        timeout = timeout if timeout is not None else self.timeout
        self.cache.set(self.key+name, value, timeout=timeout)

    def get(self, name):
        return self.cache.get(self.key+name)

    def delete(self, name):
        self.cache.delete(self.key+name)
