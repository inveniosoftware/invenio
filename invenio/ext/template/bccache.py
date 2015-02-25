# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2014 CERN.
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
Configuration class for `jinja2.bccache`.

.. code-block:: python

    JINJA2_BCCACHE = False
    JINJA2_BCCACHE_SIZE = -1
    JINJA2_BCCACHE_AUTO_RELOAD = False
    JINJA2_BCCACHE_CLIENT = 'invenio.ext.cache:cache'
    JINJA2_BCCACHE_PREFIX = 'jinja2::bccache::'
    JINJA2_BCCACHE_TIMEOUT = None
    JINJA2_BCCACHE_IGNORE_CACHE_ERRORS = True

"""

from werkzeug.utils import import_string
from jinja2.bccache import MemcachedBytecodeCache


class BytecodeCacheWithConfig(MemcachedBytecodeCache):

    """A bytecode cache that uses application config for initialization."""

    def __init__(self, app):
        """Initialize `BytecodeCache` from application config."""
        client_string = app.config.get('JINJA2_BCCACHE_CLIENT',
                                       'invenio.ext.cache:cache')
        client = import_string(client_string)
        prefix = app.config.get('JINJA2_BCCACHE_PREFIX', 'jinja2::bccache::')
        timeout = app.config.get('JINJA2_BCCACHE_TIMEOUT', None)
        ignore_memcache_errors = app.config.get(
            'JINJA2_BCCACHE_IGNORE_CACHE_ERRORS', True)
        super(self.__class__, self).__init__(
            client, prefix=prefix, timeout=timeout,
            ignore_memcache_errors=ignore_memcache_errors)
