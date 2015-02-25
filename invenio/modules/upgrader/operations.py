# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013 CERN.
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

"""
Objects for inspect and manipulating the database structure. Based on Alembic.
"""

from __future__ import absolute_import

from werkzeug.local import LocalProxy
from alembic.environment import EnvironmentContext
from alembic.operations import Operations
from alembic.autogenerate.api import _produce_migration_diffs
from alembic.config import Config
from invenio.ext.sqlalchemy import db


op = LocalProxy(lambda: create_operations())
""" Alembic operations object used to modify the database structure. """


def has_table(table_name):
    """Return True if table exists, False otherwise."""
    return db.engine.dialect.has_table(
        db.engine.connect(),
        table_name
    )


def create_migration_ctx(**kwargs):
    """Create an alembic migration context."""
    env = EnvironmentContext(Config(), None)
    env.configure(
        connection=db.engine.connect(),
        sqlalchemy_module_prefix='db.',
        **kwargs
    )
    return env.get_context()


def create_operations(ctx=None, **kwargs):
    """Create an alembic operations object."""
    if ctx is None:
        ctx = create_migration_ctx(**kwargs)
    operations = Operations(ctx)
    operations.has_table = has_table
    return operations


def produce_upgrade_operations(
        ctx=None, metadata=None, include_symbol=None, include_object=None,
        **kwargs):
    """Produce a list of upgrade statements."""
    if metadata is None:
        # Note, all SQLAlchemy models must have been loaded to produce
        # accurate results.
        metadata = db.metadata
    if ctx is None:
        ctx = create_migration_ctx(target_metadata=metadata, **kwargs)

    template_args = {}
    imports = set()

    _produce_migration_diffs(
        ctx, template_args, imports,
        include_object=include_object,
        include_symbol=include_symbol,
        **kwargs
    )

    return template_args
