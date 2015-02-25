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

"""SQLAlchemy storage engine implementation."""

import six

from flask.helpers import locked_cached_property
from werkzeug import import_string

from invenio.modules.jsonalchemy.storage import Storage


class SQLAlchemyStorage(Storage):

    """Implement database backend for SQLAlchemy model storage."""

    # FIXME: This storage engine should use transactions!

    def __init__(self, model, **kwards):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.__init__`."""
        self.__db = kwards.get('sqlalchemy_backend',
                               'invenio.ext.sqlalchemy:db')
        self.__model = model

    @locked_cached_property
    def db(self):
        """Return SQLAlchemy database object."""
        if isinstance(self.__db, six.string_types):
            self.__db = import_string(self.__db)
        if not self.__db.engine.dialect.has_table(self.__db.engine,
                                                  self.model.__tablename__):
            self.model.__table__.create(bind=self.__db.engine)
            self.__db.session.commit()
        return self.__db

    @locked_cached_property
    def model(self):
        """Return SQLAchemy model."""
        if isinstance(self.__model, six.string_types):
            return import_string(self.__model)
        return self.__model

    def save_one(self, json, id=None):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.save_one`."""
        if id is None:
            id = json['_id']

        self.db.session.add(self.model(id=id, json=json))
        self.db.session.commit()

    def save_many(self, jsons, ids=None):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.save_many`."""
        if ids is None:
            ids = map(lambda j: j['_id'], jsons)
        self.db.session.add_all([self.model(id=id, json=json)
                                 for id, json in zip(ids, jsons)])
        self.db.session.commit()

    def update_one(self, json, id=None):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.update_one`."""
        #FIXME: what if we get only the fields that have change
        if id is None:
            id = json['_id']

        self.db.session.merge(self.model(id=id, json=json))
        self.db.session.commit()

    def update_many(self, jsons, ids=None):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.update_many`."""
        #FIXME: what if we get only the fields that have change
        if ids is None:
            ids = map(lambda j: j['_id'], jsons)

        for id, json in zip(ids, jsons):
            self.db.session.merge(self.model(id=id, json=json))
        self.db.session.commit()

    def get_one(self, id):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.get_one`."""
        return self.db.session.query(self.model.json)\
            .filter_by(id=id).one().json

    def get_many(self, ids):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.get_many`."""
        for json in self.db.session.query(self.model.json)\
                .filter(self.model.id.in_(ids))\
                .all():
            yield json[0]

    def get_field_values(self, recids, field, repetitive_values=True, count=False,
                         include_recid=False, split_by=0):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.get_field_values`."""
        #TODO
        raise NotImplementedError()

    def get_fields_values(self, recids, fields, repetitive_values=True, count=False,
                          include_recid=False, split_by=0):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.get_fields_values`."""
        #TODO
        raise NotImplementedError()

    def search(self, query):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.search`."""
        raise NotImplementedError()

    def create(self):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.create`."""
        if self.db.engine.dialect.has_table(
                self.db.engine.connect(),
                self.model.__tablename__):
            assert self.model.query.count() == 0
        else:
            self.model.__table__.create(bind=self.db.engine)

    def drop(self):
        """See :meth:`~invenio.modules.jsonalchemy.storage.Storage.create`."""
        self.model.__table__.drop(bind=self.db.engine)
