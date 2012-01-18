# -*- coding: utf-8 -*-
#
## Author: Jiri Kuncar <jiri.kuncar@gmail.com> 
##
## This file is part of Invenio.
## Copyright (C) 2011, 2012 CERN.
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
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, class_mapper, \
        properties
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.serializer import loads, dumps
from sqlalchemy.orm.collections import column_mapped_collection, \
        attribute_mapped_collection, mapped_collection

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
    #def convert_datetime(value):
    #    return value.strftime("%Y-%m-%d %H:%M:%S")

    d = {}
    for c in self.__table__.columns:
        #NOTE   This hack is not needed if you redefine types.TypeDecorator for
        #       desired classes (Binary, LargeBinary, ...)
        ##if isinstance(c.type, sqlalchemy.Binary):
        ##    value = base64.encodestring(getattr(self, c.name))
        ###if isinstance(c.type, sqlalchemy.DateTime):
        ###    value = convert_datetime(getattr(self, c.name))
        ##else:
        value = getattr(self, c.name)
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
from invenio.config import CFG_DATABASE_HOST, CFG_DATABASE_PORT,\
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

def _include_sqlalchemy(obj):
    for module in sqlalchemy, sqlalchemy.orm:
        for key in module.__all__:
            if not hasattr(obj, key):
                setattr(obj, key,
                        getattr(module, key))

    if CFG_DATABASE_TYPE == 'mysql':
        import invenio.sqlalchemyutils_mysql
        module = invenio.sqlalchemyutils_mysql
        for key in module.__dict__:
            setattr(obj, key,
                    getattr(module, key))

    obj.AsBINARY = AsBINARY

def _model_plugin_builder(plugin_name, plugin_code):
    #print plugin_name
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

class InvenioDB(object):
    """Invenio database object."""
    def __init__(self, use_native_unicode=True,
                 session_extensions=None, session_options=None):
        self.use_native_unicode = use_native_unicode

        self.engine = create_engine('%(t)s://%(u)s:%(p)s@%(h)s/%(n)s' % \
                       {'t': CFG_DATABASE_TYPE,
                        'u': CFG_DATABASE_USER,
                        'p': CFG_DATABASE_PASS,
                        'h': CFG_DATABASE_HOST,
                        'n': CFG_DATABASE_NAME}, echo=True, encoding='utf-8',
                       connect_args={'use_unicode':False, 'charset':'utf8'})
        self.session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=self.engine))

        self.Model = declarative_base()
        self.Model.metadata.bind = self.engine
        self.Model.query = self.session.query_property()
        self.Model.todict = todict
        self.Model.fromdict = fromdict
        self.Model.__iter__ = iterfunc
        #self.Model.__table_args__ = {
        #        'extend_existing':True, 
        #        'mysql_engine':'MyISAM',
        #        'mysql_charset':'utf8'
        #        }

        _include_sqlalchemy(self)
        #self.Query = sqlalchemy.orm.Query

    @property
    def metadata(self):
        """Returns the metadata"""
        return self.Model.metadata

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


db = InvenioDB()



