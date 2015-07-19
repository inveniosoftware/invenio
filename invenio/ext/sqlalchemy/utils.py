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

"""Implements various utility functions.

For example, session_manager used to handle commit/rollback:

    .. code-block:: python

        class SomeModel(db.Model):
            @session_manager
            def save(self):
                db.session.add(self)
"""

from __future__ import print_function

import os
import re
import sys

import base64
import sqlalchemy
from intbitset import intbitset

from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.mutable import MutableComposite
from sqlalchemy.orm import class_mapper, properties
from sqlalchemy.orm.collections import InstrumentedList, collection



first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')


class CompositeItems(MutableComposite):
    """MutableComposite for easier generation of dictionaries.

    In order to generate predictably keyed and structured dictionaries out of
    `MutableComposite`s, one needs to inform the `MutableComposite` of the
    correspondence of the items in the composite with their names in the
    model. This abstract class defines an interface for a way of achieving that.
    """

    def __composite_items__(self):
        """Return list of supported names.

        This is neccessary for figuring out keys for a dictionary made out of
        this composite, since we have no other way of knowing which properties
        to read.

        For example if this composite is built from the following columns:
        .. code-block:: python
            config_a = Column(..)
            config_b = Column(..)
            config = composite(Config, config_a, config_b)
        where
            `config_a` is 'foo' and `config_b` is 'bar', and
            column `config_a` is stored as `self.a` and column `config_b` as `b`,
        then this method must return (('a', 'foo',
                                       'b', 'bar'))

        The presence of `__composite_keys__` and `__composite_items__` is also
        recommended but not yet enforced.
        """
        raise NotImplementedError

    def __composite_orig_keys__(self):
        """Return the key names as defined in the database model.

        These key names must be explicitly stated so that we can resolve the
        name of the column that each composite has derived from.

        For example if this composite is built from the following columns:
        .. code-block:: python
            config_a = Column(..)
            config_b = Column(..)
            config = composite(Config, config_a, config_b)
        then this method must return ('config_a', 'config_b')

        The order of the returned values must match the one of
        `__composite_items__`.
        """
        raise NotImplementedError


class CompositeMapping(CompositeItems):

    def __init__(self):
        """Ensure that there are no mistakes in the mapper."""
        for key in self.__composite_mapper__().keys():
            assert hasattr(self, key)
        # TODO Also assert that the mapper items are in the model.

    def __repr__(self):
        """Generic representation of the contents."""
        repr_values = ', '.join(self.__composite_items__())
        return "{cls}: ({values})".format(cls=type(self).__name__,
                                          values=str(repr_values))

    def __setattr__(self, key, value):
        """Intercept set events."""
        object.__setattr__(self, key, value)
        self.changed()

    def __composite_values__(self):
        """Iterate over the values of this composite."""
        for key, val in self.__composite_items__():
            yield val

    def __composite_keys__(self):
        """Iterate over the keys of this composite."""
        for key, val in self.__composite_items__():
            yield key

    def __composite_items__(self):
        """Iterate over (key, value) pairs of this composite."""
        for key, val in self.__composite_mapper__().items():
            yield key, getattr(self, key)

    def __composite_orig_keys__(self):
        """Iterate over the key names as defined in the database model."""
        for orig_key in self.__composite_mapper__().values():
            yield orig_key

    def __composite_mapper__(self):
        """Define the relationship between the model and local names.

        For example if this composite is built from the following columns:
        .. code-block:: python
            config_a = Column(..)
            config_b = Column(..)
            config = composite(Config, config_a, config_b)
        and
            column `config_a` is stored as `self.a` and column `config_b` as `b`,
        then this method must return (('a', 'config_a'),
                                      ('b', 'config_b')
        """
        raise NotImplementedError


class TableNameMixin(object):

    """Define table name from class name."""

    @declared_attr
    def __tablename__(cls):
        """Generate table name as class name with lower starting character."""
        return cls.__name__[0].lower() + cls.__name__[1:]


class TableFromCamelNameMixin(object):

    """Define table name from class name."""

    @declared_attr
    def __tablename__(cls):
        """Generate underscored table name from camel cased class name."""
        s1 = first_cap_re.sub(r'\1_\2', cls.__name__)
        return all_cap_re.sub(r'\1_\2', s1).lower()


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
                # set with _userGroup, and rest of relationships

        for relationship in relationships:
            retval.append(synonyms[relationship])

        return retval

    def todict(self, composites=False, composite_drop_consumed=True, without_none=True):
        """Convert model to dictionary.

        :param composites: also return composites
        :type composites: bool

        :param composite_drop_consumed: do not return columns that were mapped
        to composites
        :type composite_drop_consumed: bool

        :param without_none: do not return any keys that map to `None`
        :type without_none: bool
        """
        def convert_datetime(value):
            try:
                return value.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                return ''

        ret = {}

        for c in self.__table__.columns:
            # NOTE This hack is not needed if you redefine types.TypeDecorator
            # for desired classes (Binary, LargeBinary, ...)

            value = getattr(self, c.name)
            if without_none and value is None:
                continue
            if isinstance(c.type, sqlalchemy.Binary):
                value = base64.encodestring(value)
            elif isinstance(c.type, sqlalchemy.DateTime):
                value = convert_datetime(value)
            elif isinstance(value, intbitset):
                value = value.tolist()
            ret[c.name] = value

        # TODO: Recursive composites
        if composites:
            for attr_name in dir(self):
                attr = getattr(self, attr_name)
                try:
                    for idx, comp_key in enumerate(attr.__composite_keys__()):
                        # Q: Why don't you get it from `__composite_values__`?
                        # A: Because there is no reverse mutation tracking
                        orig_key = attr.__composite_orig_keys__()[idx]
                        comp_val = getattr(self, orig_key)
                        if without_none and comp_val is None:
                            continue
                        if attr_name not in ret:
                            ret[attr_name] = {}
                        ret[attr_name][comp_key] = comp_val
                except AttributeError:
                    # `attr` doesn't have __composite_items__
                    continue
                else:
                    if composite_drop_consumed:
                        # Pop non-composite keys from `ret` to avoid duplication
                        try:
                            for orig_key in attr.__composite_orig_keys__():
                                try:
                                    del ret[orig_key]
                                except KeyError:
                                    # `key` was None and `without_none` is True
                                    # so it was never inserted for some reason.
                                    continue
                        except AttributeError as e:
                            # Woops, `attr` instance doesn't support
                            # `__composite_orig_keys__`! Revert what we've done.
                            del ret[attr_name]

        return iter(ret.items())

    def fromdict(self, args):
        """Update instance from a dictionary.

        :param args: dictionary to update from
        :type  args: dict
        """
        composites = self.__mapper__.composites

        # Simple columns
        for key, val in args.items():
            try:
                setattr(self, key, val)
            except ValueError:
                if key in composites.keys():
                    pass

        # Composites
        for composite_name, composite_columns in composites.items():
            composite = getattr(self, composite_name)
            # If the composite is `None`, then all its arguments are `None`.
            # Take a shot at instantiating it. Read why at:
            # sqlalchemy.orm.descriptor_props.py:CompositeProperty._create_descriptor
            if composite is None:
                mapper_composite = self.__mapper__.composites[composite_name]
                dummy_args = [None] * len(mapper_composite.columns)
                composite = mapper_composite.composite_class(*dummy_args)
            try:
                for idx, composite_key in enumerate(composite.__composite_keys__()):
                    try:
                        val = args[composite_name][composite_key]
                    except KeyError:
                        # `args` has no information on this key
                        continue
                    else:
                        column_name = composite.__composite_orig_keys__()[idx]
                        setattr(self, column_name, val)
            except AttributeError:
                # No `__composite_keys__` found
                continue

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
        except Exception:
            db.session.rollback()
            raise

    return new_func


def test_sqla_connection():
    """Test connection with the database."""
    print("Test connection... \t", end="")

    try:
        from sqlalchemy import inspect
        from invenio.ext.sqlalchemy import db
        inspector = inspect(db.engine)
        inspector.get_table_names()
    except OperationalError as err:
        from invenio.utils.text import wrap_text_in_a_box
        from invenio.config import CFG_DATABASE_HOST, \
            CFG_DATABASE_PORT, CFG_DATABASE_NAME, CFG_DATABASE_USER, \
            CFG_DATABASE_PASS
        print(" [ERROR]")
        print(wrap_text_in_a_box("""\
DATABASE CONNECTIVITY ERROR:

%(errmsg)s.\n

Perhaps you need to set up database and connection rights?
If yes, then please execute:

console> inveniomanage database init --yes-i-know

The values printed above were detected from your
configuration. If they are not right, then please edit your
instance configuration file (invenio.cfg).


If the problem is of different nature, then please inspect
the above error message and fix the problem before continuing.""" % {
            'errmsg': err.args[0],
            'dbname': CFG_DATABASE_NAME,
            'dbhost': CFG_DATABASE_HOST,
            'dbport': CFG_DATABASE_PORT,
            'dbuser': CFG_DATABASE_USER,
            'dbpass': CFG_DATABASE_PASS,
            'webhost': (CFG_DATABASE_HOST == 'localhost' and 'localhost' or
                        os.popen('hostname -f', 'r').read().strip()),
        }))
        sys.exit(1)
    print(" [OK]")


def test_sqla_utf8_chain():
    """Test insert and select of a UTF-8 string."""
    from sqlalchemy import Table, Column
    from sqlalchemy.types import CHAR, VARBINARY
    from sqlalchemy.ext.declarative import declarative_base

    from invenio.ext.sqlalchemy import db

    print("Test UTF-8 support... \t", end="")

    tmptable = "test__invenio__utf8"
    beta_in_utf8 = "β"  # Greek beta in UTF-8 is 0xCEB2

    Base = declarative_base()

    table = Table(tmptable, Base.metadata,
                  Column('x', CHAR(1)),
                  Column('y', VARBINARY(2)))

    if table.exists(bind=db.engine):
        table.drop(bind=db.engine)

    table.create(bind=db.engine)

    db.engine.execute(table.insert(), x=beta_in_utf8, y=beta_in_utf8)
    result = db.engine.execute(table.select().where(
        table.c.x == beta_in_utf8).where(table.c.y == beta_in_utf8))

    assert result.rowcount == 1

    for row in result:
        # Database is configured to always return Unicode.
        assert row['x'] == beta_in_utf8.decode('utf-8')
        assert row['y'] == beta_in_utf8

    table.drop(bind=db.engine)

    print(" [OK]")


class IntbitsetPickle(object):

    """Pickle implementation for intbitset."""

    def dumps(self, obj, protocol=None):
        """Dump intbitset to byte stream."""
        if obj is not None:
            return obj.fastdump()
        return intbitset([]).fastdump()

    def loads(self, obj):
        """Load byte stream to intbitset."""
        try:
            return intbitset(obj)
        except Exception:
            return intbitset()


def IntbitsetCmp(x, y):
    """Compare two intbitsets."""
    if x is None or y is None:
        return False
    else:
        return x == y


class OrderedList(InstrumentedList):

    """Implemented ordered instrumented list."""

    def append(self, item):
        """Append item."""
        if self:
            s = sorted(self, key=lambda obj: obj.score)
            item.score = s[-1].score + 1
        else:
            item.score = 1
        InstrumentedList.append(self, item)

    def set(self, item, index=0):
        """Set item."""
        if self:
            s = sorted(self, key=lambda obj: obj.score)
            if index >= len(s):
                item.score = s[-1].score + 1
            elif index < 0:
                item.score = s[0].score
                index = 0
            else:
                item.score = s[index].score + 1

            for i, it in enumerate(s[index:]):
                it.score = item.score + i + 1
                # if s[i+1].score more then break
        else:
            item.score = index
        InstrumentedList.append(self, item)

    def pop(self, item):
        """Pop item."""
        # FIXME
        if self:
            obj_list = sorted(self, key=lambda obj: obj.score)
            for i, it in enumerate(obj_list):
                if obj_list[i] == item:
                    return InstrumentedList.pop(self, i)


def attribute_multi_dict_collection(creator, key_attr, val_attr):
    """Define new attribute based mapping."""
    class MultiMappedCollection(dict):

        def __init__(self, data=None):
            self._data = data or {}

        @collection.appender
        def _append(self, obj):
            l = self._data.setdefault(key_attr(obj), [])
            l.append(obj)

        def __setitem__(self, key, value):
            self._append(creator(key, value))

        def __getitem__(self, key):
            return tuple(val_attr(obj) for obj in self._data[key])

        @collection.remover
        def _remove(self, obj):
            self._data[key_attr(obj)].remove(obj)

        @collection.iterator
        def _iterator(self):
            for objs in self._data.itervalues():
                for obj in objs:
                    yield obj

        def __repr__(self):
            return '%s(%r)' % (type(self).__name__, self._data)

    return MultiMappedCollection


def initialize_database_user(engine, database_name, database_user,
                             database_pass):
    """Grant user's privileges.

    :param engine: engine to use to execute queries
    :param database_name: database name
    :param database_user: the username that you want to init
    :param database_pass: password for the user
    """
    if engine.name == 'mysql':
        from MySQLdb import escape_string
        # create user and grant privileges
        for host in ['%%', 'localhost']:
            engine.execute((
                """GRANT ALL PRIVILEGES ON {0}.* """
                """TO {1}@'{2}' IDENTIFIED BY "{3}" """).format(
                    database_name,
                    database_user,
                    host,
                    escape_string(database_pass)
                ))
    elif engine.name == 'postgresql':
        # check if already exists
        res = engine.execute(
            """SELECT 1 FROM pg_roles WHERE rolname='{0}' """
            .format(database_user))
        # if already don't exists, create user
        if not res.first():
            from psycopg2.extensions import AsIs, adapt
            engine.execute(
                """CREATE USER %s WITH PASSWORD %s """,
                (AsIs(database_user), adapt(database_pass)))
        # grant privileges for user
        engine.execute(
            """grant all privileges on database """
            """ {0} to {1} """
            .format(
                database_name,
                database_user
            ))
    else:
        raise Exception((
            """Database engine %(engine)s not supported. """
            """You need to manually adds privileges to %(database_user)s """
            """in order to access to the database %(database_name)s.""") % {
                'engine': engine.name,
                'database_user': database_user,
                'database_name': database_name
            })
