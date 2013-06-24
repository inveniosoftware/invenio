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

import sqlalchemy
import base64
import json
from sqlalchemy import event
from sqlalchemy.pool import Pool
from sqlalchemy.ext.hybrid import hybrid_property, Comparator
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import class_mapper, properties
from sqlalchemy.types import TypeDecorator, TEXT, LargeBinary
from sqlalchemy.sql.expression import FunctionElement
from invenio.importutils import autodiscover_modules
from invenio.intbitset import intbitset
from invenio.errorlib import register_exception
from invenio.dbquery import serialize_via_marshal, deserialize_via_marshal
from invenio.hashutils import md5

try:
    from flask.ext.sqlalchemy import SQLAlchemy
except:
    from flaskext.sqlalchemy import SQLAlchemy


def autodiscover_models():
    """Makes sure that all tables are loaded in `db.metadata.tables`."""
    return autodiscover_modules(['invenio'], related_name_re=".+_model\.py")


def getRelationships(self):
    retval = list()
    mapper = class_mapper(self)
    actualNameToSynonym = dict()
    relationships = set()

    for prop in mapper.iterate_properties:
        if isinstance(prop, properties.SynonymProperty):
            actualNameToSynonym[prop.name] = prop.key
            # dictionary <_userName, userName, userGroup, _userGroup>

        elif isinstance(prop, properties.RelationshipProperty):
            relationships.add(prop.key)
            #set with _userGroup, and rest of relationships

    for relationship in relationships:
        retval.append(actualNameToSynonym[relationship])

    return retval


def todict(self):
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
    """
    """
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


def iterfunc(self):
    """Returns an iterable that supports .next()
        so we can do dict(sa_instance)

    """
    return self.todict()


class AsBINARY(FunctionElement):
    name = 'AsBINARY'


@compiles(AsBINARY)
def compile(element, compiler, **kw):
    return "BINARY %s" % compiler.process(element.clauses)


from sqlalchemy.ext.mutable import MutableDict
@MutableDict.as_mutable
class JSONEncodedTextDict(TypeDecorator):
    """
    Represents an immutable structure as a json-encoded string.

    @see: http://docs.sqlalchemy.org/en/latest/core/types.html#marshal-json-strings
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
            value = serialize_via_marshal(self.force_type(value))
            return value
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            try:
                value = deserialize_via_marshal(value)
            except:
                value = None
        return value if value is not None else \
            (self.default_value() if callable(self.default_value) else
             self.default_value)


#@compiles(sqlalchemy.types.LargeBinary, "postgresql")
#def compile_binary_postgresql(type_, compiler, **kw):
#    return "BYTEA"

#@compiles(sqlalchemy.types.LargeBinary, "mysql")
#def compile_binary_postgresql(type_, compiler, **kw):
#    return "BYTEA"


def _include_sqlalchemy(obj, engine=None):
    #for module in sqlalchemy, sqlalchemy.orm:
    #    for key in module.__all__:
    #        if not hasattr(obj, key):
    #            setattr(obj, key,
    #                    getattr(module, key))

    if engine == 'mysql':
        from sqlalchemy.dialects import mysql as engine_types
    else:
        from sqlalchemy import types as engine_types

    setattr(obj, 'JSON', JSONEncodedTextDict)
    setattr(obj, 'Char', engine_types.CHAR)
    try:
        setattr(obj, 'TinyText', engine_types.TINYTEXT)
    except:
        setattr(obj, 'TinyText', engine_types.TEXT)
    setattr(obj, 'hybrid_property', hybrid_property)
    try:
        setattr(obj, 'Double', engine_types.DOUBLE)
    except:
        setattr(obj, 'Double', engine_types.FLOAT)
    setattr(obj, 'Integer', engine_types.INTEGER)
    setattr(obj, 'SmallInteger', engine_types.SMALLINT)
    try:
        setattr(obj, 'MediumInteger', engine_types.MEDIUMINT)
    except:
        setattr(obj, 'MediumInteger', engine_types.INT)
    setattr(obj, 'BigInteger', engine_types.BIGINT)
    try:
        setattr(obj, 'TinyInteger', engine_types.TINYINT)
    except:
        setattr(obj, 'TinyInteger', engine_types.INT)
    setattr(obj, 'Binary', sqlalchemy.types.LargeBinary)
    setattr(obj, 'iBinary', sqlalchemy.types.LargeBinary)
    setattr(obj, 'iLargeBinary', sqlalchemy.types.LargeBinary)
    setattr(obj, 'iMediumBinary', sqlalchemy.types.LargeBinary)

    if engine == 'mysql':
        import invenio.sqlalchemyutils_mysql
    #    module = invenio.sqlalchemyutils_mysql
    #    for key in module.__dict__:
    #        setattr(obj, key,
    #                getattr(module, key))

    def default_enum(f):
        def decorated(*args, **kwargs):
            kwargs['native_enum'] = engine == 'mysql'  # False
            return f(*args, **kwargs)
        return decorated

    obj.Enum.__init__ = default_enum(obj.Enum.__init__)
    obj.AsBINARY = AsBINARY
    obj.MarshalBinary = MarshalBinary

    ## Overwrite :meth:`MutableDick.update` to detect changes.
    from sqlalchemy.ext.mutable import MutableDict

    def update_mutable_dict(self, *args, **kwargs):
        super(MutableDict, self).update(*args, **kwargs)
        self.changed()

    MutableDict.update = update_mutable_dict
    obj.MutableDict = MutableDict


class PasswordComparator(Comparator):
    def __eq__(self, other):
        return self.__clause_element__() == self.hash(other)

    def hash(self, password):
        if db.engine.name != 'mysql':
            return md5(password).digest()
        email = self.__clause_element__().table.columns.email
        return db.func.aes_encrypt(email, password)


def autocommit_on_checkin(dbapi_con, con_record):
    """Calls autocommit on raw mysql connection for fixing bug in MySQL 5.5"""
    try:
        dbapi_con.autocommit(True)
    except:
        register_exception()

## Possibly register globally.
#event.listen(Pool, 'checkin', autocommit_on_checkin)


class InvenioDB(SQLAlchemy):
    """Invenio database object."""

    PasswordComparator = PasswordComparator

    def init_app(self, app):
        super(InvenioDB, self).init_app(app)
        engine = app.config.get('CFG_DATABASE_TYPE', 'mysql')
        self.Model.todict = todict
        self.Model.fromdict = fromdict
        self.Model.__iter__ = iterfunc
        self.Model.__table_args__ = {}
        if engine == 'mysql':
            self.Model.__table_args__ = {'keep_existing':    True,
                                         'extend_existing':  False,
                                         'mysql_engine':     'MyISAM',
                                         'mysql_charset':    'utf8'}

        _include_sqlalchemy(self, engine=engine)

    def __getattr__(self, name):
        # This is only called when the normal mechanism fails, so in practice
        # should never be called.
        # It is only provided to satisfy pylint that it is okay not to
        # raise E1101 errors in the client code.
        # :see http://stackoverflow.com/a/3515234/780928
        raise AttributeError("%r instance has no attribute %r" % (self, name))

    def schemadiff(self, excludeTables=None):
        from migrate.versioning import schemadiff
        return schemadiff.getDiffOfModelAgainstDatabase(self.metadata,
                                                        self.engine,
                                                        excludeTables=excludeTables)

    def apply_driver_hacks(self, app, info, options):
        """
        This method is called before engine creation.
        """
        # Don't forget to apply hacks defined on parent object.
        super(InvenioDB, self).apply_driver_hacks(app, info, options)
        if info.drivername == 'mysql':
            options.setdefault('execution_options', {'autocommit': True,
                                                     'use_unicode': False  # , 'charset': 'utf8'
                                                     })
            event.listen(Pool, 'checkin', autocommit_on_checkin)


db = InvenioDB()
