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
import sqlalchemy.orm
import base64
import json
from sqlalchemy.orm import class_mapper, \
                           properties
from sqlalchemy.ext.hybrid import hybrid_property
from invenio.intbitset import intbitset
from sqlalchemy.types import TypeDecorator, TEXT


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

# Global variables
from invenio.dbquery import CFG_DATABASE_HOST, CFG_DATABASE_PORT,\
    CFG_DATABASE_NAME, CFG_DATABASE_USER, CFG_DATABASE_PASS

# TODO Add to invenio.config
CFG_DATABASE_TYPE = 'mysql'

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import ColumnClause, FunctionElement

class AsBINARY(FunctionElement):
    name = 'AsBINARY'

@compiles(AsBINARY)
def compile(element, compiler, **kw):
    return "BINARY %s" % compiler.process(element.clauses)


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

#@compiles(sqlalchemy.types.LargeBinary, "postgresql")
#def compile_binary_postgresql(type_, compiler, **kw):
#    return "BYTEA"

#@compiles(sqlalchemy.types.LargeBinary, "mysql")
#def compile_binary_postgresql(type_, compiler, **kw):
#    return "BYTEA"

def _include_sqlalchemy(obj, engine=None):
    if engine is None:
        engine = CFG_DATABASE_TYPE
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
    setattr(obj, 'TinyText', engine_types.TINYTEXT)
    setattr(obj, 'hybrid_property', hybrid_property)
    setattr(obj, 'Double', engine_types.DOUBLE)
    setattr(obj, 'Integer', engine_types.INTEGER)
    setattr(obj, 'SmallInteger', engine_types.SMALLINT)
    setattr(obj, 'MediumInteger', engine_types.MEDIUMINT)
    setattr(obj, 'BigInteger', engine_types.BIGINT)
    setattr(obj, 'TinyInteger', engine_types.TINYINT)
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
            kwargs['native_enum'] = engine == 'mysql' #False
            return f(*args, **kwargs)
        return decorated

    obj.Enum.__init__ = default_enum(obj.Enum.__init__)

    obj.AsBINARY = AsBINARY

def _model_plugin_builder(plugin_name, plugin_code):
    return plugin_code

def load_all_model_files(db=None):
    """Load all SQLAlchemy database models."""
    import os
    import invenio
    from invenio.config import CFG_PYLIBDIR
    from invenio.pluginutils import PluginContainer
    models = os.path.join(CFG_PYLIBDIR, 'invenio', '*_model.py')
    return PluginContainer(models,
        plugin_builder=_model_plugin_builder).values()

from sqlalchemy.ext.hybrid import Comparator

class PasswordComparator(Comparator):
    def __eq__(self, other):
        return self.__clause_element__() == self.hash(other)

    def hash(self, password):
        if db.engine.name != 'mysql':
            import hashlib
            return hashlib.md5(password).digest()
        email = self.__clause_element__().table.columns.email
        return db.func.aes_encrypt(email, password)

try:
    from flask.ext.sqlalchemy import SQLAlchemy
except:
    from flaskext.sqlalchemy import SQLAlchemy

from sqlalchemy.engine.url import URL

from sqlalchemy import event
from sqlalchemy.pool import Pool

def autocommit_on_checkin(dbapi_con, con_record):
    """Calls autocommit on raw mysql connection for fixing bug in MySQL 5.5"""
    dbapi_con.autocommit(True)

## Possibly register globally.
#event.listen(Pool, 'checkin', autocommit_on_checkin)

class InvenioDB(SQLAlchemy):
    """Invenio database object."""

    PasswordComparator = PasswordComparator

    def init_invenio(self, engine=None):
        #               connect_args={'use_unicode':False, 'charset':'utf8'})
        #self.session = scoped_session(sessionmaker(autocommit=False,
        #                                 autoflush=False,
        #                                 bind=self.engine))

        self.Model.todict = todict
        self.Model.fromdict = fromdict
        self.Model.__iter__ = iterfunc
        #if engine == 'mysql':
        self.Model.__table_args__ = {
            'keep_existing':    True,
            'extend_existing':  False,
            'mysql_engine':     'MyISAM',
            'mysql_charset':    'utf8'
            }

        _include_sqlalchemy(self, engine=engine)

    def init_cfg(self, app):
        app.debug = True
        app.config['SQLALCHEMY_DATABASE_URI'] = URL(
            CFG_DATABASE_TYPE,
            username = CFG_DATABASE_USER,
            password = CFG_DATABASE_PASS,
            host = CFG_DATABASE_HOST,
            database = CFG_DATABASE_NAME,
            port = CFG_DATABASE_PORT,
            )

    def __getattr__(self, name):
        # This is only called when the normal mechanism fails, so in practice
        # should never be called.
        # It is only provided to satisfy pylint that it is okay not to
        # raise E1101 errors in the client code.
        # :see http://stackoverflow.com/a/3515234/780928
        raise AttributeError("%r instance has no attribute %r" % (self, name))

    def schemadiff(self, excludeTables=None):
        from migrate.versioning import schemadiff
        for m in load_all_model_files():
            exec("from %s import *"%(m.__name__))
        return schemadiff.getDiffOfModelAgainstDatabase(self.metadata,
            self.engine, excludeTables=excludeTables)

    def apply_driver_hacks(self, app, info, options):
        """
        This method is called before engine creation.
        """
        # Don't forget to apply hacks defined on parent object.
        super(InvenioDB, self).apply_driver_hacks(app, info, options)
        if info.drivername == 'mysql':
            options.setdefault('execution_options', {'autocommit': True })
            event.listen(Pool, 'checkin', autocommit_on_checkin)


db = InvenioDB()
# FIXME add __init__ method for db.
_include_sqlalchemy(db, engine=None)
