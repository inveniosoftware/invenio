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

"""Implement an in-memory engine for *JSONAlchemy*."""

import six

from invenio.modules.jsonalchemy.storage import Storage


class MemoryStorage(Storage):

    """Implement in-memory storage engine."""

    def __init__(self, **kwargs):
        """See also :meth:`~invenio.modules.jsonalchemy.storage.Storage.__init__`."""
        self._database = kwargs.get('database', dict())

    def save_one(self, data, id=None):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.save_one`."""
        if id is not None:
            data['_id'] = id
        id = data['_id']
        self._database[id] = data
        return data

    def save_many(self, jsons, ids=None):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.save_many`."""
        return map(lambda k: self.save_one(*k), zip(jsons, ids))

    def update_one(self, data, id=None):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.update_one`."""
        if id is not None:
            data['_id'] = id
        id = data['_id']

        return self._database[id].update(data)

    def update_many(self, jsons, ids=None):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.update_many`."""
        return map(lambda k: self.update_one(*k), zip(jsons, ids))

    def get_one(self, id):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.get_one`."""
        return self._database[id]

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
                test_v = item.get(k)
                if test_v is None and v is not None:
                    return False
                elif test_v != v:
                    return False
            return True
        return filter(_find, self._database.values())

    def create(self):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.create`."""
        if self._database is None:
            self._database = dict()
        assert len(self._database.keys()) == 0

    def drop(self):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.create`."""
        del self._database
