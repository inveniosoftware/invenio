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

"""
    invenio.ext.sqlalchemy
    ----------------------

    This module provides initialization and configuration for
    `flask.ext.sqlalchemy` module.
"""

from .expressions import AsBINARY
from .types import JSONEncodedTextDict, MarshalBinary, PickleBinary, GUID
from .utils import get_model_type
import sqlalchemy
from flask.ext.sqlalchemy import SQLAlchemy as FlaskSQLAlchemy
from sqlalchemy import event
from sqlalchemy.pool import Pool
from sqlalchemy.ext.hybrid import hybrid_property, Comparator
from invenio.utils.hash import md5
from flask_registry import RegistryProxy, ModuleAutoDiscoveryRegistry


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
    setattr(obj, 'UUID', GUID)

    if engine == 'mysql':
        from .engines import mysql as dummy_mysql
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
    obj.PickleBinary = PickleBinary

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
        pass
        #FIXME
        #from invenio.ext.logging import register_exception
        #register_exception()

## Possibly register globally.
#event.listen(Pool, 'checkin', autocommit_on_checkin)


class SQLAlchemy(FlaskSQLAlchemy):
    """Database object."""

    PasswordComparator = PasswordComparator

    def init_app(self, app):
        super(self.__class__, self).init_app(app)
        engine = app.config.get('CFG_DATABASE_TYPE', 'mysql')
        self.Model = get_model_type(self.Model)
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
        super(self.__class__, self).apply_driver_hacks(app, info, options)
        if info.drivername == 'mysql':
            options.setdefault('execution_options', {'autocommit': True,
                                                     'use_unicode': False  # , 'charset': 'utf8'
                                                     })
            event.listen(Pool, 'checkin', autocommit_on_checkin)


db = SQLAlchemy()
"""
    Provides access to :class:`~.SQLAlchemy` instance.
"""

models = RegistryProxy('models', ModuleAutoDiscoveryRegistry, 'models')


def setup_app(app):
    """Setup SQLAlchemy extension."""
    if 'SQLALCHEMY_DATABASE_URI' not in app.config:
        from sqlalchemy.engine.url import URL
        cfg = app.config

        app.config['SQLALCHEMY_DATABASE_URI'] = URL(
            cfg.get('CFG_DATABASE_TYPE', 'mysql'),
            username=cfg.get('CFG_DATABASE_USER'),
            password=cfg.get('CFG_DATABASE_PASS'),
            host=cfg.get('CFG_DATABASE_HOST'),
            database=cfg.get('CFG_DATABASE_NAME'),
            port=cfg.get('CFG_DATABASE_PORT'),
            )

    ## Let's initialize database.
    db.init_app(app)

    return app
