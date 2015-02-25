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

"""Add is_api_accessible and slug in the knwKB table."""

from invenio.ext.sqlalchemy import db
from invenio.legacy.dbquery import run_sql
from invenio.modules.upgrader.api import op
from invenio.utils.text import slugify

depends_on = [u'knowledge_2014_10_30_knwKBRVAL_id_column_removal']


def generate_slug(name):
    """Generate a slug for the knowledge.

    :param name: text to slugify
    :return: slugified text
    """
    slug = slugify(unicode(name))

    i = run_sql("SELECT count(*) FROM knwKB "
                "WHERE knwKB.slug LIKE %s OR knwKB.slug LIKE %s",
                (slug, slug + '-%'))[0][0]

    return slug + ('-{0}'.format(i) if i > 0 else '')


def info():
    """Return info about the upgrade."""
    return "Add is_api_accessible and slug in the knwKB table."


def do_upgrade():
    """Implement your upgrades here."""
    # modify the database
    op.add_column('knwKB',
                  db.Column('is_api_accessible',
                            db.Boolean(), nullable=False))
    op.add_column('knwKB',
                  db.Column('slug',
                            db.String(length=255),
                            nullable=False,
                            default=True))

    # update knwKB table values
    res = run_sql("SELECT name FROM knwKB")
    for record in res:
        name = record[0]
        slug = generate_slug(name)
        run_sql("UPDATE knwKB SET is_api_accessible = 1, slug = %s "
                "WHERE name = %s", (slug, name))

    # define unique constraint
    op.create_unique_constraint(None, 'knwKB', ['slug'])


def estimate():
    """Estimate running time of upgrade in seconds (optional)."""
    number_of_records = run_sql("SELECT count(*) FROM knwKB")
    return int(float(number_of_records[0][0]) / 1000) + 1


def pre_upgrade():
    """Run pre-upgrade checks (optional)."""
    pass


def post_upgrade():
    """Run post-upgrade checks (optional)."""
    pass
