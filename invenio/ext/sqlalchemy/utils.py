# -*- coding: utf-8 -*-
#
## This file is part of Invenio.
## Copyright (C) 2011, 2012, 2013, 2014 CERN.
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

"""Implements various utility functions.

For example, session_manager used to handle commit/rollback:

    .. code-block:: python

        class SomeModel(db.Model):
            @session_manager
            def save(self):
                db.session.add(self)
"""

import sqlalchemy
import base64
from intbitset import intbitset
from sqlalchemy.orm import class_mapper, properties


def get_model_type(ModelBase):
    """Return extended model type."""
    def getRelationships(self):
        """Return table relations."""
        retval = list()
        mapper = class_mapper(self)
        synonyms = dict()
        relationships = set()

        for prop in mapper.iterate_properties:
            if isinstance(prop, properties.SynonymProperty):
                synonyms[prop.name] = prop.key
                # dictionary <_userName, userName, userGroup, _userGroup>

            elif isinstance(prop, properties.RelationshipProperty):
                relationships.add(prop.key)
                #set with _userGroup, and rest of relationships

        for relationship in relationships:
            retval.append(synonyms[relationship])

        return retval

    def todict(self):
        """Convert model to dictionary."""
        def convert_datetime(value):
            try:
                return value.strftime("%Y-%m-%d %H:%M:%S")
            except:
                return ''

        for c in self.__table__.columns:
            #NOTE   This hack is not needed if you redefine types.TypeDecorator for
            #       desired classes (Binary, LargeBinary, ...)

            value = getattr(self, c.name)
            if value is None:
                continue
            if isinstance(c.type, sqlalchemy.Binary):
                value = base64.encodestring(value)
            elif isinstance(c.type, sqlalchemy.DateTime):
                value = convert_datetime(value)
            elif isinstance(value, intbitset):
                value = value.tolist()
            yield(c.name, value)

    def fromdict(self, args):
        """Update instance from dictionary."""
        #NOTE Why not to do things simple ...
        self.__dict__.update(args)

        #for c in self.__table__.columns:
        #    name = str(c).split('.')[1]
        #    try:
        #        d = args[name]
        #    except:
        #        continue
        #
        #    setattr(self, c.name, d)

    def __iter__(self):
        """Return an iterable that supports .next() for dict(sa_instance)."""
        return self.todict()

    ModelBase.todict = todict
    ModelBase.fromdict = fromdict
    ModelBase.__iter__ = __iter__
    ModelBase.__table_args__ = {}

    return ModelBase


def session_manager(orig_func):
    """Decorator to wrap function with the session.

    Useful to add to models functions that is meant to
    commit itself to DB when called.

    .. code-block:: python

        class SomeModel(db.Model):
            @session_manager
            def save(self):
                db.session.add(self)

    Now the session manager will handle committing and
    rollbacks on errors and re-raise.

    :param orig_func: original function
    :type orig_func: callable

    :return: decorated function.
    """
    from invenio.ext.sqlalchemy import db

    def new_func(self, *a, **k):
        """Wrapper function to manage DB session."""
        try:
            resp = orig_func(self, *a, **k)
            db.session.commit()
            return resp
        except:
            db.session.rollback()
            raise

    return new_func
