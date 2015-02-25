# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2013, 2014 CERN.
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

"""SQLAlchemy backend for session.

Configuration variables for SQLAlchemy backend.

=================================== ===========================================
`SESSION_BACKEND_SQLALCHEMY`        Configured *Flask-SQLAlchemy* object.
                                    **Default:** ``invenio.ext.sqlalchemy:db``
`SESSION_BACKEND_SQLALCHEMY_MODEL`  SQLAlchemy ORM model. **Default:**
                                    ``invenio.ext.session.model:Session'``
`SESSION_BACKEND_SQLALCHEMY_GETTER` Name of method on model to retrieve session
                                    data. **Default:** ``get_session``
`SESSION_BACKEND_SQLALCHEMY_SETTER` Name of method on medel to set session
                                    data. **Default:** ``set_session``
`SESSION_BACKEND_SQLALCHEMY_VALUE`  Name of model attribute where to store
                                    session data. **Default:**
                                    ``session_object``
=================================== ===========================================
"""

from flask import current_app
from flask.helpers import locked_cached_property
from werkzeug import import_string

from ..storage import SessionStorage


class Storage(SessionStorage):

    """Implement database backend for SQLAlchemy model storage."""

    def __init__(self, *args, **kwargs):
        """Initialize database backend and create table if necessary."""
        if not self.db.engine.dialect.has_table(self.db.engine,
                                                self.model.__tablename__):
            self.model.__table__.create(bind=self.db.engine)
            self.db.session.commit()

    @locked_cached_property
    def db(self):
        """Return SQLAlchemy database object."""
        return import_string(current_app.config.get(
            'SESSION_BACKEND_SQLALCHEMY', 'invenio.ext.sqlalchemy:db'))

    @locked_cached_property
    def model(self):
        """Return SQLAlchemy model."""
        return import_string(current_app.config.get(
            'SESSION_BACKEND_SQLALCHEMY_MODEL',
            'invenio.ext.session.model:Session'))()

    @locked_cached_property
    def getter(self):
        """Return method to get session value."""
        return getattr(self.model, current_app.config.get(
            'SESSION_BACKEND_SQLALCHEMY_GETTER', 'get_session'
        ))

    @locked_cached_property
    def setter(self):
        """Return method to set session value."""
        return getattr(self.model, current_app.config.get(
            'SESSION_BACKEND_SQLALCHEMY_SETTER', 'set_session'
        ))

    @locked_cached_property
    def value(self):
        """Return model property for storing session value."""
        return current_app.config.get('SESSION_BACKEND_SQLALCHEMY_VALUE',
                                      'session_object')

    def set(self, name, value, timeout=None):
        """Store value in database table."""
        s = self.setter(name, value, timeout=timeout)
        self.db.session.merge(s)
        self.db.session.commit()

    def get(self, name):
        """Return value from database table."""
        return getattr(self.getter(name), self.value)

    def delete(self, name):
        """Delete key from database table."""
        self.getter(name).delete()
        self.db.session.commit()
