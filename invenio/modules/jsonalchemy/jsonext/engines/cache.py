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

"""Wrapper for *Flask-Cache* as engine for *JSONAlchemy*."""

import six

from invenio.ext.cache import cache
from invenio.modules.jsonalchemy.storage import Storage


class CacheStorage(Storage):

    """Implement storage engine for Flask-Cache useful for testing."""

    def __init__(self, **kwargs):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.__init__`."""
        self._prefix = kwargs.get('model', '')

    def _set(self, data):
        self._keys = self._keys | set([data['_id']])
        cache.set(self._prefix + data['_id'], data, timeout=99999)

    def _get(self, id):
        value = cache.get(self._prefix + id)
        if value is None:
            raise KeyError()
        return value

    @property
    def _keys(self):
        return cache.get(self._prefix + '::keys') or set()

    @_keys.setter
    def _keys(self, value):
        cache.set(self._prefix + '::keys', value)

    def save_one(self, data, id=None):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.save_one`."""
        if id is not None:
            data['_id'] = id
        self._set(data)
        return data

    def save_many(self, jsons, ids=None):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.save_many`."""
        return map(lambda k: self.save_one(*k), zip(jsons, ids))

    def update_one(self, data, id=None):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.update_one`."""
        if id is not None:
            data['_id'] = id
        id = data['_id']
        old_data = self._get(id)
        old_data.update(data)
        self._set(old_data)
        return old_data

    def update_many(self, jsons, ids=None):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.update_many`."""
        return map(lambda k: self.update_one(*k), zip(jsons, ids))

    def get_one(self, id):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.get_one`."""
        return self._get(id)

    def get_many(self, ids):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.get_many`."""
        return map(self.get_one, ids)

    def get_field_values(self, ids, field, repetitive_values=True, count=False,
                         include_recid=False, split_by=0):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.get_field_values`."""
        raise NotImplementedError()

    def get_fields_values(self, ids, fields, repetitive_values=True,
                          count=False, include_recid=False, split_by=0):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.get_fields_values`."""
        raise NotImplementedError()

    def search(self, query):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.search`."""
        def _find(item):
            for k, v in six.iteritems(query):
                if item is None:
                    return False
                test_v = item.get(k)
                if test_v is None and v is not None:
                    return False
                elif test_v != v:
                    return False
            return True
        return filter(_find, map(self._get, self._keys))

    def create(self):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.create`."""
        assert len(self._keys) == 0

    def drop(self):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.create`."""
        while self._keys:
            cache.delete(self._prefix + self._keys.pop())
