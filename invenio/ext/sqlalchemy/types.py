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
    invenio.ext.sqlalchemy.types
    ----------------------------

    Implements various custom column types.
"""
import json
import uuid

from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.types import TypeDecorator, TEXT, LargeBinary, CHAR
from sqlalchemy.dialects.postgresql import UUID

from invenio.utils.serializers import ZlibMarshal, ZlibPickle


@MutableDict.as_mutable
class JSONEncodedTextDict(TypeDecorator):
    """
    Represents an immutable structure as a json-encoded string.

    @see: http://docs.sqlalchemy.org/en/latest/core/types.html
    """

    impl = TEXT

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class MarshalBinary(TypeDecorator):

    impl = LargeBinary

    def __init__(self, default_value, force_type=None, *args, **kwargs):
        super(MarshalBinary, self).__init__(*args, **kwargs)
        self.default_value = default_value
        self.force_type = force_type if force_type is not None else lambda x: x

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = ZlibMarshal.dumps(self.force_type(value))
            return value
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            try:
                value = ZlibMarshal.loads(value)
            except:
                value = None
        return value if value is not None else \
            (self.default_value() if callable(self.default_value) else
             self.default_value)


class PickleBinary(TypeDecorator):

    impl = LargeBinary

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = ZlibPickle.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = ZlibPickle.loads(value)
        return value


#@compiles(sqlalchemy.types.LargeBinary, "postgresql")
#def compile_binary_postgresql(type_, compiler, **kw):
#    return "BYTEA"

#@compiles(sqlalchemy.types.LargeBinary, "mysql")
#def compile_binary_postgresql(type_, compiler, **kw):
#    return "BYTEA"
#


class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses Postgresql's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.

    """
    impl = CHAR

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value)
            else:
                # hexstring
                return "%.32x" % value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            return uuid.UUID(value)
