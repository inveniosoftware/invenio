# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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

"""Fixtures extension."""

from __future__ import print_function

from .registry import fixtures


def load_fixtures(sender, yes_i_know=False, drop=True, **kwargs):
    """Load fixtures.

    Loads classes found in 'packages' to the database. Names of the fixture
    classes should end with 'Data' suffix.

    :param packages: packages with fixture classes to load
    :param truncate_tables_first: if True truncates tables before loading
        the fixtures
    """
    from invenio.ext.sqlalchemy import db, models
    from fixture import SQLAlchemyFixture

    # Load SQLAlchemy models.
    list(models)
    models = dict((m.__name__ + 'Data', m) for m in db.Model.__subclasses__())

    missing = set(fixtures.keys()) - set(models.keys())
    if len(missing):
        raise Exception(
            'Cannot match models for the following fixtures classes {0}'.format(
                missing
            ))
    print(">>> There are", len(fixtures.keys()), "tables to be loaded.")
    SQLAlchemyFixture(
        env=models, engine=db.metadata.bind, session=db.session
    ).data(*fixtures.values()).setup()
    db.session.commit()


def fixture_dump(sender, **kwargs):
    """Dump fixtures."""
    print('ERROR: This feature is not implemented inside fixtures.')


def setup_app(app):
    """Set up the extension for the given app."""
    # Subscribe to database post create command
    from invenio.base import signals
    from invenio.base.scripts.database import create, recreate, dump
    signals.post_command.connect(load_fixtures, sender=create)
    signals.post_command.connect(load_fixtures, sender=recreate)
    signals.post_command.connect(fixture_dump, sender=dump)
