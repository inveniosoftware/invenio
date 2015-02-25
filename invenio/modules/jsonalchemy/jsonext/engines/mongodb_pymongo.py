# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014 CERN.
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

"""MongoDB Storage engine implementation."""

import pymongo
from itertools import imap

from invenio.modules.jsonalchemy.storage import Storage


class MongoDBStorage(Storage):

    """Storage engine for MongoDB using the driver pymongo."""

    def __init__(self, model, **kwards):
        """See also :meth:`~invenio.modules.jsonalchemy.storage.Storage.__init__`."""
        self.model = model
        host = kwards.get('host', 'localhost')
        port = kwards.get('port', 27017)
        database = kwards.get('database', 'invenio')
        self.__connection = pymongo.MongoClient(host=host, port=port)
        self.__database = self.__connection[database]
        self.__collection = self.__database[model]

    def save_one(self, json, id=None):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.save_one`."""
        if id is not None:
            json['_id'] = id
        return self.__collection.insert(json)

    def save_many(self, jsons, ids=None):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.save_many`."""
        if ids is not None:
            def add_id(t):
                t[0]['_id'] = t[1]
                return t[0]
            jsons = imap(add_id, zip(jsons, ids))

        return self.__collection.insert(jsons, continue_on_error=True)

    def update_one(self, json, id=None):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.update_one`."""
        # FIXME: what if we get only the fields that have change
        if id is not None:
            json['_id'] = id

        return self.__collection.save(json)

    def update_many(self, jsons, ids=None):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.update_many`."""
        if ids is not None:
            def add_id(t):
                t[0]['_id'] = t[1]
                return t[0]
            jsons = imap(add_id, zip(jsons, ids))

        return map(self.__collection.save, jsons)

    def get_one(self, id):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.get_one`."""
        return self.__collection.find_one(id)

    def get_many(self, ids):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.get_many`."""
        return self.__collection.find({'_id': {'$in': ids}})

    def get_field_values(self, ids, field, repetitive_values=True, count=False,
                         include_id=False, split_by=0):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.get_field_values`."""
        raise NotImplementedError()

    def get_fields_values(self, ids, fields, repetitive_values=True, count=False,
                          include_id=False, split_by=0):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.get_fields_values`."""
        raise NotImplementedError()

    def search(self, query):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.search`."""
        return self.__collection.find(query)

    def create(self):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.create`."""
        assert self.__collection.count() == 0

    def drop(self):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.create`."""
        self.__collection.drop()
