# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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
    invenio.core.record.backends.sqlalchemy
    ---------------------------------------

"""
from itertools import izip, imap

from flask import current_app
from flask.helpers import locked_cached_property
from werkzeug import import_string

from invenio.utils.jsonalchemy.storage import Storage


class SQLAlchemyStorage(Storage):
    """
    Implements database backend for SQLAlchemy model storage.
    """
    #FIXME: This storage engine should use transactions!

    def __init__(self, model, **kwards):
        """
        TBC
        See also :meth:`~invenio.utils.jsonalchemy.storage:Storage.__init__`
        """
        self.__db = kwards.get('sqlalchemy_backend', 'invenio.ext.sqlalchemy:db')
        self.__model = model
        if not self.db.engine.dialect.has_table(self.db.engine,
                self.model.__tablename__):
            self.model.__table__.create(bind=self.db.engine)
            self.db.session.commit()

    @locked_cached_property
    def db(self):
        """Returns SQLAlchemy database object."""
        if isinstance(self.__db, basestring):
            return import_string(self.__db)
        return self.__db

    @locked_cached_property
    def model(self):
        """Returns SQLAchemy model."""
        if isinstance(self.__model, basestring):
            return import_string(self.__model)
        return self.__model

    def save_one(self, json, id=None):
        """See :meth:`~invenio.utils.jsonalchemy.storage:Storage.save_one`"""
        if id is None:
            id = json_record['_id']

        self.db.session.add(self.model(id=id, json=json))
        self.db.session.commit()

    def save_many(self, jsons, ids=None):
        """See :meth:`~invenio.utils.jsonalchemy.storage:Storage.save_many`"""
        if ids is None:
            ids = imap(lambda j: j['_id'], jsons)
        self.db.session.add_all([self.model(id=id, json=json)
            for id, json in izip(ids, jsons)])
        self.db.session.commit()

    def update_one(self, json, id=None):
        """See :meth:`~invenio.utils.jsonalchemy.storage:Storage.update_one`"""
        #FIXME: what if we get only the fields that have change
        if id is None:
            id = json['id']

        self.db.session.merge(self.model(id=id, json=json))
        self.db.session.commit()

    def update_many(self, jsons, ids=None):
        """See :meth:`~invenio.utils.jsonalchemy.storage:Storage.update_many`"""
        #FIXME: what if we get only the fields that have change
        if ids is None:
            ids = imap(lambda j: j['_id'], jsons)

        for id, json in izip(ids, jsons):
            self.db.session.merge(self.model(id=id, json=json))
        self.db.session.commit()

    def get_one(self, id):
        """See :meth:`~invenio.utils.jsonalchemy.storage:Storage.get_one`"""
        return self.db.session.query(self.model.json)\
                .filter_by(id=id).one().json

    def get_many(self, ids):
        """See :meth:`~invenio.utils.jsonalchemy.storage:Storage.get_many`"""
        for json in self.db.session.query(self.model.json)\
                .filter(RecordMetadata.id.in_(ids))\
                .all():
            yield json[0]

    def get_field_values(recids, field, repetitive_values=True, count=False,
            include_recid=False, split_by=0):
        """See :meth:`~invenio.utils.jsonalchemy.storage:Storage.get_field_values`"""
        #TODO
        raise NotImplementedError()

    def get_fields_values(recids, fields, repetitive_values=True, count=False,
            include_recid=False, split_by=0):
        """See :meth:`~invenio.utils.jsonalchemy.storage:Storage.get_fields_values`"""
        #TODO
        raise NotImplementedError()
