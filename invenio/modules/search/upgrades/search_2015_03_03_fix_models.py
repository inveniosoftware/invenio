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

"""Upgrade Search models."""

from invenio.ext.sqlalchemy import db
from invenio.legacy.dbquery import run_sql
from invenio.modules.upgrader.api import op


depends_on = [u'search_2014_07_21_facets_per_collection']


def info():
    """Info."""
    return "Add a autoincrement id in collection_field_fieldvalue table."""


def do_upgrade():
    """Implement your upgrades here."""
    # add column "id" in the table
    op.add_column('collection_field_fieldvalue',
                  db.Column('id', db.MediumInteger(9, unsigned=True),
                            nullable=False))

    # set all new ids
    records = run_sql("""SELECT id_collection, id_field, id_fieldvalue,
                      type, score, score_fieldvalue
                      FROM collection_field_fieldvalue AS cff
                      ORDER BY cff.id_collection, id_field, id_fieldvalue,
                      type, score, score_fieldvalue""")
    for index, rec in enumerate(records):
        sql = """UPDATE collection_field_fieldvalue
                 SET id = %%s
                 WHERE id_collection = %%s AND id_field = %%s
                 AND type = %%s AND score = %%s AND score_fieldvalue = %%s
                 AND id_fieldvalue %s
              """ % ('=%s' % (rec[2], ) if rec[2] is not None else 'is NULL', )
        run_sql(sql, (index + 1, rec[0], rec[1], rec[3], rec[4], rec[5]))

    # create new primary key with id
    op.create_primary_key('pk_collection_field_fieldvalue_id',
                          'collection_field_fieldvalue', ['id'])

    # set id as autoincrement
    op.alter_column('collection_field_fieldvalue', 'id',
                    existing_type=db.MediumInteger(9, unsigned=True),
                    existing_nullable=False, autoincrement=True)


def estimate():
    """Estimate running time of upgrade in seconds (optional)."""
    total = run_sql("SELECT count(*) FROM collection_field_fieldvalue")
    return int(float(total[0][0]) / 1000) + 1


def pre_upgrade():
    """Run pre-upgrade checks (optional)."""
    # Example of raising errors:
    # raise RuntimeError("Description of error 1", "Description of error 2")


def post_upgrade():
    """Run post-upgrade checks (optional)."""
    # Example of issuing warnings:
    # warnings.warn("A continuable error occurred")
