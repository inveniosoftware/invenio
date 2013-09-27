# -*- coding: utf-8 -*-

## This file is part of Invenio.
## Copyright (C) 2011, 2012, 2013 CERN.
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
    invenio.ext.session.backends.sqlalchemy
    ---------------------------------------

    Configuration:

    - SESSION_BACKEND_SQLALCHEMY = 'invenio.ext.sqlalchemy:db'
    - SESSION_BACKEND_SQLALCHEMY_MODEL = 'invenio.ext.session.model:Session'
    - SESSION_BACKEND_SQLALCHEMY_GETTER = 'get_session'
    - SESSION_BACKEND_SQLALCHEMY_SETTER = 'set_session'
    - SESSION_BACKEND_SQLALCHEMY_VALUE = 'session_object'
"""

from flask import current_app
from flask.helpers import locked_cached_property
from werkzeug import import_string

from ..storage import SessionStorage


class Storage(SessionStorage):
    """
    Implements database backend for SQLAlchemy model storage.
    """

    def __init__(self, *args, **kwargs):
        if not self.db.engine.dialect.has_table(self.db.engine,
                                                self.model.__tablename__):
            self.model.__table__.create(bind=self.db.engine)
            self.db.commit()

    @locked_cached_property
    def db(self):
        """Returns SQLAlchemy database object."""
        return import_string(current_app.config.get(
            'SESSION_BACKEND_SQLALCHEMY', 'invenio.ext.sqlalchemy:db'))

    @locked_cached_property
    def model(self):
        """Returns SQLAlchemy model."""
        return import_string(current_app.config.get(
            'SESSION_BACKEND_SQLALCHEMY_MODEL',
            'invenio.ext.session.model:Session'))

    @locked_cached_property
    def getter(self):
        return getattr(self.model, current_app.config.get(
            'SESSION_BACKEND_SQLALCHEMY_GETTER', 'get_session'
            ))

    @locked_cached_property
    def setter(self):
        return getattr(self.model, current_app.config.get(
            'SESSION_BACKEND_SQLALCHEMY_SETTER', 'set_session'
            ))

    @locked_cached_property
    def value(self):
        return current_app.config.get('SESSION_BACKEND_SQLALCHEMY_VALUE',
                                      'session_object')

    def set(self, name, value, timeout=None):
        s = self.setter(name, value, timeout=timeout)
        self.db.session.merge(s)
        self.db.session.commit()

        session_expiry = datetime.utcnow() + timeout
        s = Session()
        s.uid = current_user.get_id()
        s.session_key = name
        s.session_object = value
        s.session_expiry = session_expiry
        #FIXME REPLACE OR UPDATE
        db.session.merge(s)
        db.session.commit()

    def get(self, name):
        return getattr(self.getter(name), self.value)
        s = Session.query.filter(db.and_(
            Session.session_key == name,
            Session.session_expiry >= db.func.current_timestamp())).one()
        return s.session_object

    def delete(self, name):
        self.getter(name).delete()
        self.db.session.commit()
