# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2010, 2011 CERN.
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
Invenio utilities to settings manipulation.
"""

from invenio.sqlalchemyutils import db
from invenio.websession_model import User
from invenio.webuser_flask import current_user, login_user, logout_user

class Storage(object):

    _keys = []
    _data = {}

    def __init__(self, keys):
        self._keys = keys

    def load(self):
        return dict((k, self._data.get(k, None)) for k in self._keys)

    def store(self, data):
        self._data.update(map(
            lambda (k,v): (k, v[0] if len(v) == 1 else v),
            filter(
                lambda (k,v): k in self._keys,
                data.lists()
            )))

    def save(self):
        pass


class UserSettingsStorage(Storage):

    def __init__(self, keys, attr=None):
        self._keys = keys
        self._user = User.query.get(current_user.get_id())
        self._attr = attr
        if self._attr is None:
            self._data = dict(self._user.settings)
        else:
            self._data = dict(self._user.settings.get(self._attr, {}))

    def save(self):
        data = dict(self._user.settings)
        if self._attr is None:
            data.update(self.load())
        else:
            values = data.get(self._attr, {})
            values.update(self.load())
            data[self._attr] = values

        self._user.settings = data
        db.session.merge(self._user)
        db.session.commit()


def UserSettingsAttributeStorage(attr):
    return lambda self, key: UserSettingsStorage(key, attr)

def ModelSettingsStorageBuilder(query_builder):

    class ModelSettingsStorage(Storage):

        def __init__(self, keys):
            self._keys = keys
            self._model = query_builder()
            self._data = dict(self._model)

        def save(self):
            for (k,v) in self.load().items():
                setattr(self._model, k, v)
            db.session.merge(self._model)
            db.session.commit()

    return ModelSettingsStorage


class Settings(object):

    keys = []
    storage_builder = Storage
    form_builder = None

    def __init__(self):
        self.storage = self.storage_builder(self.keys)

    def load(self):
        return self.storage.load()

    def store(self, data):
        self.storage.store(data)

    def save(self):
        self.storage.save()


