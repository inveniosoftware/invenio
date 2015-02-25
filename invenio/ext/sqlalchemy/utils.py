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

"""Implements various utility functions.

For example, session_manager used to handle commit/rollback:

    .. code-block:: python

        class SomeModel(db.Model):
            @session_manager
            def save(self):
                db.session.add(self)
"""

from __future__ import print_function

import base64
import os
import re
import sqlalchemy
import sys

from intbitset import intbitset
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import class_mapper, properties

first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')


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

    def todict(self):
        """Convert model to dictionary."""
        def convert_datetime(value):
            try:
                return value.strftime("%Y-%m-%d %H:%M:%S")
            except:
                return ''

        for c in self.__table__.columns:
            # NOTE This hack is not needed if you redefine types.TypeDecorator
            # for desired classes (Binary, LargeBinary, ...)

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
        # NOTE Why not to do things simple ...
        self.__dict__.update(args)

        # for c in self.__table__.columns:
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
invenio-local.conf file and rerun 'inveniocfg --update-all' first.


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
