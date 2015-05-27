# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
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

"""Invenio to obelix-client connector."""

from invenio.config import CFG_OBELIX_HOST, CFG_OBELIX_PREFIX
from invenio.errorlib import register_exception


_OBELIX = None


class ObelixNotExist(object):
    """Empty Object, that accept everything without error."""

    def __getattr__(self, name):
        """Return always None."""
        return lambda *args, **keyargs: None


def get_obelix():
    """Create or get a Obelix instance."""
    global _OBELIX

    recommendation_prefix = "recommendations::"

    if CFG_OBELIX_HOST == "":
        # Obelix is not used, so ignore all calls without error.
        return ObelixNotExist()
    if _OBELIX is None:
        try:
            import json
            import redis
            from obelix_client import Obelix
            from obelix_client.storage import RedisStorage
            from obelix_client.queue import RedisQueue

            obelix_redis = redis.StrictRedis(host=CFG_OBELIX_HOST,
                                             port=6379,
                                             db=0)

            obelix_cache = RedisStorage(obelix_redis, prefix=CFG_OBELIX_PREFIX,
                                        encoder=json)

            recommendation_storage = RedisStorage(obelix_redis,
                                                  prefix=CFG_OBELIX_PREFIX +
                                                  recommendation_prefix,
                                                  encoder=json)

            obelix_queue = RedisQueue(obelix_redis, prefix=CFG_OBELIX_PREFIX,
                                      encoder=json)

            _OBELIX = Obelix(obelix_cache, recommendation_storage,
                             obelix_queue)
        except Exception:
            register_exception(alert_admin=True)
            _OBELIX = None

    return _OBELIX

obelix = get_obelix()


def clean_user_info(user_info):
    """Remove all unwanted information."""
    return {'uid': user_info.get('uid'),
            'referer': user_info.get('referer'),
            'uri': user_info.get('uri'),
            'group': user_info.get('group'),
            '': user_info.get(''),
            }
