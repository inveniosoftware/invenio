# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2013, 2014, 2015 CERN.
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

"""Initialization and configuration for `flask_sqlalchemy`."""

import sqlalchemy

from flask_registry import ModuleAutoDiscoveryRegistry, RegistryProxy

from flask_sqlalchemy import SQLAlchemy as FlaskSQLAlchemy

from invenio.ext.sqlalchemy.types import LegacyBigInteger, LegacyInteger, \
    LegacyMediumInteger, LegacySmallInteger, LegacyTinyInteger

from sqlalchemy import event, types as engine_types
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.pool import Pool

from sqlalchemy_utils import JSONType

from .expressions import AsBINARY
from .types import GUID, MarshalBinary, PickleBinary
from .utils import get_model_type


def _include_sqlalchemy(obj, engine=None):
    """Init all required SQLAlchemy's types."""
    # for module in sqlalchemy, sqlalchemy.orm:
    #    for key in module.__all__:
    #        if not hasattr(obj, key):
    #            setattr(obj, key,
    #                    getattr(module, key))

    if engine == 'mysql':
        from sqlalchemy.dialects import mysql as engine_types
    else:
        from sqlalchemy import types as engine_types

    # Length is provided to JSONType to ensure MySQL uses LONGTEXT instead
    # of TEXT which only provides for 64kb storage compared to 4gb for
    # LONGTEXT.
    setattr(obj, 'JSON', JSONType(length=2 ** 32 - 2))
    setattr(obj, 'Char', engine_types.CHAR)
    try:
        setattr(obj, 'TinyText', engine_types.TINYTEXT)
    except AttributeError:
        setattr(obj, 'TinyText', engine_types.TEXT)
    setattr(obj, 'hybrid_property', hybrid_property)
    try:
        setattr(obj, 'Double', engine_types.DOUBLE)
    except AttributeError:
        setattr(obj, 'Double', engine_types.FLOAT)
    setattr(obj, 'Binary', sqlalchemy.types.LargeBinary)
    setattr(obj, 'iBinary', sqlalchemy.types.LargeBinary)
    setattr(obj, 'iLargeBinary', sqlalchemy.types.LargeBinary)
    setattr(obj, 'iMediumBinary', sqlalchemy.types.LargeBinary)
    setattr(obj, 'UUID', GUID)
    setattr(obj, 'Integer', LegacyInteger)
    setattr(obj, 'MediumInteger', LegacyMediumInteger)
    setattr(obj, 'SmallInteger', LegacySmallInteger)
    setattr(obj, 'TinyInteger', LegacyTinyInteger)
    setattr(obj, 'BigInteger', LegacyBigInteger)

    if engine == 'mysql':
        from .engines import mysql as dummy_mysql  # noqa
    #    module = invenio.sqlalchemyutils_mysql
    #    for key in module.__dict__:
    #        setattr(obj, key,
    #                getattr(module, key))

    obj.AsBINARY = AsBINARY
    obj.MarshalBinary = MarshalBinary
    obj.PickleBinary = PickleBinary

    # Overwrite :meth:`MutableDick.update` to detect changes.
    from sqlalchemy.ext.mutable import MutableDict

    def update_mutable_dict(self, *args, **kwargs):
        super(MutableDict, self).update(*args, **kwargs)
        self.changed()

    MutableDict.update = update_mutable_dict
    obj.MutableDict = MutableDict


# TODO check if we can comment this without problems
# @compiles(types.Text, 'postgresql')
# @compiles(sqlalchemy.dialects.postgresql.TEXT, 'postgresql')
# def compile_text(element, compiler, **kw):
#     """Redefine Text filed type for PostgreSQL."""
#     return 'TEXT'


@compiles(engine_types.VARBINARY, 'postgresql')
def compile_text(element, compiler, **kw):
    """Redefine VARBINARY filed type for PostgreSQL."""
    return 'BYTEA'


def autocommit_on_checkin(dbapi_con, con_record):
    """Call autocommit on raw mysql connection for fixing bug in MySQL 5.5."""
    try:
        dbapi_con.autocommit(True)
    except Exception:
        pass
        # FIXME
        # from invenio.ext.logging import register_exception
        # register_exception()

# Possibly register globally.
# event.listen(Pool, 'checkin', autocommit_on_checkin)


class SQLAlchemy(FlaskSQLAlchemy):

    """Database object."""

    def init_app(self, app):
        """Init application."""
        super(self.__class__, self).init_app(app)
        engine = app.config.get('CFG_DATABASE_TYPE', 'mysql')
        self.Model = get_model_type(self.Model)
        if engine == 'mysql':
            # Override MySQL parameters to force MyISAM engine
            mysql_parameters = {'keep_existing': True,
                                'extend_existing': False,
                                'mysql_engine': 'MyISAM',
                                'mysql_charset': 'utf8',
                                'sql_mode': 'ansi_quotes'}

            original_table = self.Table

            def table_with_myisam(*args, **kwargs):
                """Use same MySQL parameters that are used for ORM models."""
                new_kwargs = dict(mysql_parameters)
                new_kwargs.update(kwargs)
                return original_table(*args, **new_kwargs)

            self.Table = table_with_myisam
            self.Model.__table_args__ = mysql_parameters

        _include_sqlalchemy(self, engine=engine)

    def __getattr__(self, name):
        """
        Called when the normal mechanism fails.

        This is only called when the normal mechanism fails,
        so in practice should never be called.
        It is only provided to satisfy pylint that it is okay not to
        raise E1101 errors in the client code.

        :see http://stackoverflow.com/a/3515234/780928
        """
        raise AttributeError("%r instance has no attribute %r" % (self, name))

    def schemadiff(self, excludeTables=None):
        """Generate a schema diff."""
        from migrate.versioning import schemadiff
        return schemadiff \
            .getDiffOfModelAgainstDatabase(self.metadata,
                                           self.engine,
                                           excludeTables=excludeTables)

    def apply_driver_hacks(self, app, info, options):
        """Called before engine creation."""
        # Don't forget to apply hacks defined on parent object.
        super(self.__class__, self).apply_driver_hacks(app, info, options)
        if info.drivername == 'mysql':
            options.setdefault('execution_options', {
                # Autocommit cause Exception in SQLAlchemy >= 0.9.
                # @see http://docs.sqlalchemy.org/en/rel_0_9/
                #   core/connections.html#understanding-autocommit
                # 'autocommit': True,
                'use_unicode': False,
                'charset': 'utf8mb4',
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

    # Let's initialize database.
    db.init_app(app)

    return app
