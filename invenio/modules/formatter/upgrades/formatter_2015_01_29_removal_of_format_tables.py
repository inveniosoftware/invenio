# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

"""Removal of tables format and formatname."""

import warnings

from invenio.ext.sqlalchemy import db
from invenio.legacy.dbquery import run_sql
from invenio.modules.upgrader.api import op

depends_on = [u'formatter_2014_10_29_add_mime_type']


def info():
    """Return upgrade info."""
    return __doc__


def do_upgrade():
    """Migrate format references."""
    op.add_column('collection_format',
                  db.Column('format', db.String(length=10), nullable=False))
    run_sql('UPDATE collection_format cf JOIN format f ON f.id = cf.id_format '
            'SET cf.format = f.code')
    op.drop_constraint(None, 'collection_format', type_='primary')
    op.create_primary_key(None, 'collection_format',
                          ['id_collection', 'format'])
    op.drop_column('collection_format', 'id_format')
    op.drop_table('formatname')
    op.drop_table('format')


def estimate():
    """Estimate running time of upgrade in seconds (optional)."""
    return 1


def pre_upgrade():
    """Run pre-upgrade checks (optional)."""
    warnings.warn("Manually migrate custom *.bfo files using "
                  "'python scripts/output_format_migration_kit.py run'.")


def post_upgrade():
    """Run post-upgrade checks (optional)."""
    # Example of issuing warnings:
    # warnings.warn("A continuable error occurred")
