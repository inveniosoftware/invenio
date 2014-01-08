# -*- coding: utf-8 -*-
#
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
    invenio.ext.sqlalchemy.utils
    ----------------------------

    Implements various utilities.
"""

import sqlalchemy
import base64
from intbitset import intbitset
from sqlalchemy.orm import class_mapper, properties


def get_model_type(ModelBase):
    """Returns extended model type."""

    def getRelationships(self):
        """Returns table relations."""
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
        """Converts model to dictionary."""

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
        """Updates instance from dictionary."""
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
        """Returns an iterable that supports .next()
            so we can do dict(sa_instance)

        """
        return self.todict()

    ModelBase.todict = todict
    ModelBase.fromdict = fromdict
    ModelBase.__iter__ = __iter__
    ModelBase.__table_args__ = {}

    return ModelBase
