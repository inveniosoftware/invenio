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

"""Mysql dialect."""

import base64

# SQLAlchemy
import sqlalchemy

import sqlalchemy.types as types
from sqlalchemy.ext.compiler import compiles

from sqlalchemy.schema import CreateIndex, PrimaryKeyConstraint


@compiles(CreateIndex, 'mysql')
def visit_create_index(element, compiler, **kw):
    """Return create index statement with defined length for text field.

    example:
    CREATE TABLE tableA
        ...
        description TEXT(40)
        ...
        INDEX ix_tableA_description ON (description(40))
    """
    index = element.element
    preparer = compiler.preparer
    table = preparer.format_table(index.table)
    name = preparer.quote(index.name, index.name.quote)

    text = "ALTER TABLE %s ADD " % (table, )
    if index.unique:
        text += "UNIQUE "
    text += "INDEX %s" % (name, )

    lst = index.kwargs.get('mysql_length', None)

    columns = []
    for i, c in enumerate(index.columns):
        cname = c.name
        suffix = ''
        if isinstance(lst, (list, tuple)) and len(lst) > i \
                and lst[i] is not None:
            suffix = '(%d)' % lst[i]
        elif c.type != types.NULLTYPE \
                and str(c.type).startswith('TEXT') \
                and (c.type.length is not None):
            suffix = '(%d)' % c.type.length
        columns.append(cname + suffix)

    text += '(' + ', '.join(columns) + ')'

    if 'mysql_using' in index.kwargs:
        using = index.kwargs['mysql_using']
        if using is not None:
            text += " USING %s" % (preparer.quote(using, index.quote))

    return text


@compiles(PrimaryKeyConstraint, 'mysql')
def visit_primary_key_constraint(*element):
    """
    Return create primary key constrains.

    Return create primary key constrains with defined length
    for text field.
    """
    constraint, compiler = element
    if len(constraint) == 0:
        return ''
    text = ""
    if constraint.name is not None:
        text += "CONSTRAINT %s " % \
                compiler.preparer.format_constraint(constraint)
    text += "PRIMARY KEY "
    text += "(%s)" % ', '.join(c.name +
                               (c.type != types.NULLTYPE
                                and (str(c.type).startswith('TEXT')
                                     and (c.type.length is not None))
                                and '(%d)' % c.type.length
                                or '')
                               for c in constraint)
    text += compiler.define_constraint_deferrability(constraint)
    return text


@compiles(types.Text, 'sqlite')
@compiles(sqlalchemy.dialects.mysql.TEXT, 'sqlite')
def compile_text(element, compiler, **kw):
    """Redefine Text filed type for SQLite and MySQL."""
    return 'TEXT'


@compiles(types.Binary, 'sqlite')
def compile_binary(element, compiler, **kw):
    """Redefine Binary filed type for SQLite."""
    return 'BLOB'


@compiles(types.LargeBinary, 'sqlite')
def compile_largebinary(element, compiler, **kw):
    """Redefine LargeBinary filed type for SQLite."""
    return 'LONGBLOB'


@compiles(types.Text, 'mysql')
@compiles(sqlalchemy.dialects.mysql.TEXT, 'mysql')
def compile_text(element, compiler, **kw):
    """Redefine Text filed type for MySQL."""
    return 'TEXT'


@compiles(types.Binary, 'mysql')
def compile_binary(element, compiler, **kw):
    """Redefine Binary filed type for MySQL."""
    return 'BLOB'


@compiles(types.LargeBinary, 'mysql')
def compile_largebinary(element, compiler, **kw):
    """Redefine LargeBinary filed type for MySQL."""
    return 'LONGBLOB'

from sqlalchemy.types import TypeDecorator


class iBinary(TypeDecorator):

    """Printable binary typea."""

    impl = types.Binary

    def __init__(self, *arg, **kw):
        """Init iBinary type."""
        self.__class__.impl = self.impl
        TypeDecorator.__init__(self, *arg, **kw)

    def process_bind_param(self, value, dialect):
        """Decode string before saving to database."""
        return (value is not None) and base64.decodestring(value) or None

    def process_result_value(self, value, dialect):
        """Encode binary data to string."""
        return (value is not None) and base64.encodestring(value) or None


class iLargeBinary(TypeDecorator):

    """Printable large binary type."""

    impl = types.LargeBinary

    def __init__(self, *arg, **kw):
        """Init iLargeBinary type."""
        self.__class__.impl = self.impl
        TypeDecorator.__init__(self, *arg, **kw)

    def process_bind_param(self, value, dialect):
        """Decode string before saving to database."""
        return (value is not None) and base64.decodestring(value) or None

    def process_result_value(self, value, dialect):
        """Encode binary data to string."""
        return (value is not None) and base64.encodestring(value) or None


class iMediumBinary(TypeDecorator):

    """Printable large binary type."""

    impl = sqlalchemy.dialects.mysql.MEDIUMBLOB

    def __init__(self, *arg, **kw):
        """Init iMediumBinary type."""
        self.__class__.impl = self.impl
        TypeDecorator.__init__(self, *arg, **kw)

    def process_bind_param(self, value, dialect):
        """Decode string before saving to database."""
        return (value is not None) and base64.decodestring(value) or None

    def process_result_value(self, value, dialect):
        """Encode binary data to string."""
        return (value is not None) and base64.encodestring(value) or None
