# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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

"""Multimedia utilities."""

import redis


def initialize_redis():
    """Initialize redis service.

    .. note::

        FIXME: Should be remove it and replaced with an invenio redis object.

    """
    from flask import current_app

    _redis_server = redis.Redis.from_url(
        current_app.config.get('CACHE_REDIS_URL', 'redis://localhost:6379')
    )
    return _redis_server
