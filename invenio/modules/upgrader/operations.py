# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012, 2013 CERN.
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
Objects for inspect and manipulating the database structure. Based on Alembic.
"""

from __future__ import absolute_import

from werkzeug.local import LocalProxy
from sqlalchemy import MetaData
from alembic.environment import EnvironmentContext
from alembic.operations import Operations
from alembic.autogenerate import compare_metadata
from alembic.autogenerate.api import \
    _autogen_context, \
    _produce_upgrade_commands
from alembic.config import Config
from invenio.ext.sqlalchemy import db


op = LocalProxy(lambda: create_operations())
""" Alembic operations object used to modify the database structure. """


def create_migration_ctx(**kwargs):
    """
    Create an alembic migration context.
    """
    env = EnvironmentContext(Config(), None, **kwargs)
    env.configure(connection=db.engine.connect())
    return env.get_context()


def create_operations(ctx=None, **kwargs):
    """
    Create an alembic operations object.
    """
    if ctx is None:
        ctx = create_migration_ctx(**kwargs)
    return Operations(ctx)


def produce_diffs(ctx=None, metadata=None, **kwargs):
    """
    Generate diff between models and actual database.
    """
    if ctx is None:
        ctx = create_migration_ctx(**kwargs)
    if metadata is None:
        metadata = MetaData(bind=db.engine)
        metadata.reflect()

    # Create diff
    diff = compare_metadata(ctx, metadata)

    # Remove 'alembic_version' table.
    try:
        if diff[0][1].name == 'alembic_version':
            return diff[1:]
    except Exception:
        pass
    return diff


def produce_upgrade_operations(ctx=None, metadata=None, **kwargs):
    """
    Produce a list of upgrade statements
    """
    if ctx is None:
        ctx = create_migration_ctx(**kwargs)

    autogen_context, dummy = _autogen_context(ctx, set())

    diffs = produce_diffs(ctx=ctx, metadata=metadata)

    return _produce_upgrade_commands(diffs, autogen_context)
