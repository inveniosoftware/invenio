# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013 CERN.
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
Invenio utilities to settings manipulation.
"""
from werkzeug.utils import cached_property

from invenio.ext.sqlalchemy import db
from invenio.modules.accounts.models import User
from invenio.ext.login import current_user, login_user, logout_user


class Storage(object):
    """
    Generic storage engine for settings.

    It allows to load and store key-value data only for specified keys.
    """
    _keys = []
    _data = {}

    def __init__(self, keys):
        """
        @param keys: allowed keys in the storage.
        """
        self._keys = keys

    def load(self, default=None):
        """
        Loads values from storage system.

        @return: Filtered dictionary and for non-existing keys returns `default`
        """
        return dict((k, self._data.get(k, default)) for k in self._keys)

    def store(self, data):
        """
        Stores data in storage system.

        @param data: Stores data provided by the form
        @type data: dict
        """
        self._data.update(
            [(k, v) for (k, v) in data.items() if k in self._keys])

    def save(self):
        """
        Implement this method for persistent storage system.
        """
        pass


class UserSettingsStorage(Storage):
    """
    Storage engine using User settings object for data persistency.
    """
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

        self._user.settings = None
        db.session.commit()

        self._user.settings = data
        db.session.commit()

        current_user.reload()

    def store(self, data):
        self._data = {}
        super(UserSettingsStorage, self).store(data)


def UserSettingsAttributeStorage(attr):
    """
    Class factory for 2nd level user settings.
    """
    return lambda self, key: UserSettingsStorage(key, attr)


def ModelSettingsStorageBuilder(query_builder):
    """
    Class factory for database model storage system.

    @param query_builder: callable that returns valid SQLAlchemy model instance.
    """
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
    """
    Settings object designed for user account page with widgets.
    """
    keys = [] ## list of valid setting keys
    storage_builder = Storage ## storage builder factory method
    form_builder = None ## form builder factory method

    def __init__(self):
        ## initializes storage system
        self.storage = self.storage_builder(self.keys)

    @cached_property
    def name(self):
        return self.__class__.__name__

    def load(self):
        """
        Loads data from storage system.
        """
        return self.storage.load()

    def store(self, data):
        """
        Stores data in storage system.
        """
        self.storage.store(data)

    def save(self):
        """
        Commit data in persistent storage system.
        """
        self.storage.save()

    def build_form(self):
        if not self.form_builder:
            return None

        data = self.load()
        form = self.form_builder()

        for key in self.keys:
            if data.get(key) is not None:
                form[key].data = data[key]

        return form
