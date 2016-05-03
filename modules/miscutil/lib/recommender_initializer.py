# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
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

"""Initializes the Redis connection."""

from invenio.config import CFG_RECOMMENDER_REDIS


_RECOMMENDATION_REDIS = None


def get_redis_connection():
    """
    Stores a persistent Redis connection.

    @return: Redis connection object.
    """
    global _RECOMMENDATION_REDIS

    if CFG_RECOMMENDER_REDIS == "":
        # Recommender is not configured.
        return None

    if _RECOMMENDATION_REDIS is None:
        import redis
        _RECOMMENDATION_REDIS = redis.StrictRedis(host=CFG_RECOMMENDER_REDIS,
                                                  port=6379,
                                                  db=0)
    return _RECOMMENDATION_REDIS
