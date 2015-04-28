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

"""Upgrade Submit models."""

import warnings

from invenio.ext.sqlalchemy import db
from invenio.legacy.dbquery import run_sql
from invenio.modules.upgrader.api import op

from sqlalchemy.exc import OperationalError

depends_on = ['invenio_release_1_1_0']


def info():
    """Info."""
    return "Add a autoincrement id in sbmCOLLECTION_sbmDOCTYPE " + \
        "and sbmCOLLECTION_sbmCOLLECTION table"


def do_upgrade():
    """Implement your upgrades here."""
    # Table sbmCOLLECTION_sbmCOLLECTION

    # add column "id" in the table
    op.add_column('sbmCOLLECTION_sbmCOLLECTION',
                  db.Column('id', db.Integer(11), nullable=False))

    # set all new ids
    records = run_sql("""SELECT id_father, id_son FROM """
                      """sbmCOLLECTION_sbmCOLLECTION AS ssc """
                      """ORDER BY ssc.id_father, ssc.id_son""")
    for index, rec in enumerate(records):
        run_sql("""UPDATE sbmCOLLECTION_sbmCOLLECTION
                SET id = %s WHERE id_father = %s AND id_son = %s """,
                (index + 1, rec[0], rec[1]))

    # drop primary keys
    try:
        op.drop_constraint(None, 'sbmCOLLECTION_sbmCOLLECTION',
                           type_='primary')
    except OperationalError:
        # the primary key is already dropped
        warnings.warn("""Primary key of sbmCOLLECTION_sbmCOLLECTION """
                      """table has been already dropped.""")

    # create new primary key with id
    op.create_primary_key('pk_sbmCOLLECTION_sbmCOLLECTION_id',
                          'sbmCOLLECTION_sbmCOLLECTION', ['id'])
    # set id as autoincrement
    op.alter_column('sbmCOLLECTION_sbmCOLLECTION', 'id',
                    existing_type=db.Integer(11),
                    existing_nullable=False, autoincrement=True)
    # fix columns id_father and id_son
    op.alter_column('sbmCOLLECTION_sbmCOLLECTION', 'id_father',
                    existing_type=db.Integer(11),
                    nullable=True, server_default=None)
    op.alter_column('sbmCOLLECTION_sbmCOLLECTION', 'id_son',
                    existing_type=db.Integer(11),
                    nullable=False, server_default=None)
    op.create_index('id_father', 'sbmCOLLECTION_sbmCOLLECTION',
                    columns=['id_father'])

    # Table sbmCOLLECTION_sbmDOCTYPE

    # add column "id" in the table
    op.add_column('sbmCOLLECTION_sbmDOCTYPE',
                  db.Column('id', db.Integer(11), nullable=False))

    # set all new ids
    records = run_sql("""SELECT id_father, id_son
                      FROM sbmCOLLECTION_sbmDOCTYPE AS ssd
                      ORDER BY ssd.id_father, ssd.id_son""")
    for index, rec in enumerate(records):
        run_sql("""UPDATE sbmCOLLECTION_sbmDOCTYPE
                SET id = %s WHERE id_father = %s AND id_son = %s """,
                (index + 1, rec[0], rec[1]))

    # drop primary keys
    try:
        op.drop_constraint('id_father', 'sbmCOLLECTION_sbmDOCTYPE',
                           type_='primary')
    except OperationalError:
        # the primary key is already dropped
        warnings.warn("""Primary key of sbmCOLLECTION_sbmDOCTYPE """
                      """table has been already dropped.""")

    # create new primary key with id
    op.create_primary_key('pk_sbmCOLLECTION_sbmDOCTYPE_id',
                          'sbmCOLLECTION_sbmDOCTYPE', ['id'])
    # set id as autoincrement
    op.alter_column('sbmCOLLECTION_sbmDOCTYPE', 'id',
                    existing_type=db.Integer(11),
                    existing_nullable=False, autoincrement=True)
    # fix columns id_father and id_son
    op.alter_column('sbmCOLLECTION_sbmDOCTYPE', 'id_father',
                    existing_type=db.Integer(11),
                    nullable=True, server_default=None)
    op.alter_column('sbmCOLLECTION_sbmDOCTYPE', 'id_son',
                    existing_type=db.Char(10),
                    nullable=False, server_default=None)
    op.create_index('id_father', 'sbmCOLLECTION_sbmDOCTYPE',
                    columns=['id_father'])


def estimate():
    """Estimate running time of upgrade in seconds (optional)."""
    num_ssc = run_sql("SELECT count(*) FROM sbmCOLLECTION_sbmCOLLECTION")
    num_ssd = run_sql("SELECT count(*) FROM sbmCOLLECTION_sbmDOCTYPE")
    total = int(num_ssc[0][0]) + int(num_ssd[0][0])
    return int(float(total) / 1000) + 1


def pre_upgrade():
    """Run pre-upgrade checks (optional)."""
    # Example of raising errors:
    # raise RuntimeError("Description of error 1", "Description of error 2")


def post_upgrade():
    """Run post-upgrade checks (optional)."""
    # Example of issuing warnings:
    # warnings.warn("A continuable error occurred")
