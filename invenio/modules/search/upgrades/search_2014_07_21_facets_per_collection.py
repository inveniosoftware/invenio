# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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

"""Add a table for facets configuration."""

from __future__ import print_function

import warnings

from invenio.ext.sqlalchemy import db
from invenio.modules.upgrader.api import op
from sqlalchemy.dialects import mysql

depends_on = ['invenio_release_1_1_0']


def info():
    """Show module info message."""
    return "Adds the table with facets configuration."


def do_upgrade():
    """Add the table with facets configuration."""
    if not op.has_table('facet_collection'):
        op.create_table(
            'facet_collection',
            db.Column('id', mysql.INTEGER(), nullable=False),
            db.Column('id_collection', mysql.INTEGER(), nullable=False),
            db.Column('order', mysql.INTEGER(), nullable=False),
            db.Column('facet_name', db.String(length=80), nullable=False),
            db.ForeignKeyConstraint(['id_collection'], ['collection.id'], ),
            db.PrimaryKeyConstraint('id'),
            mysql_charset='utf8',
            mysql_engine='MyISAM'
        )
    else:
        warnings.warn("*** Creation of table 'facet_collection' skipped!")


def post_upgrade():
    """Facet configuration info."""
    print('NOTE: You need to configure facets to have them shown using\n'
          'flask-admin module at /admin/facetcollection. \n\n'
          'Adding them to the default collection with id 1 makes them the\n'
          'default set. The default set is shown for every collection which\n'
          'does not have facets set configured')
