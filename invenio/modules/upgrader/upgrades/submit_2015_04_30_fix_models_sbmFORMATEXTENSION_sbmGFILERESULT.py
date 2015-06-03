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


depends_on = [u'submit_2015_03_03_fix_models']


def info():
    """Info."""
    return "Add a autoincrement id in sbmFORMATEXTENSION and " + \
        "sbmGFILERESULT tables"


def do_upgrade():
    """Implement your upgrades here."""
    # table sbmFORMATEXTENSION

    # add "id" column
    op.add_column('sbmFORMATEXTENSION',
                  db.Column('id', db.Integer(), nullable=False))
    # set all ids
    records = run_sql("""SELECT FILE_FORMAT, FILE_EXTENSION FROM """
                      """sbmFORMATEXTENSION AS sbm """
                      """ORDER BY sbm.FILE_FORMAT, sbm.FILE_EXTENSION""")
    for index, rec in enumerate(records):
        run_sql("""UPDATE sbmFORMATEXTENSION """
                """SET id = %s """
                """ WHERE FILE_FORMAT = %s AND """
                """       FILE_EXTENSION = %s """,
                (index + 1, rec[0], rec[1]))
    # remove primary key
    try:
        op.drop_constraint(None, 'sbmFORMATEXTENSION',
                           type_='primary')
    except OperationalError:
        # the primary key is already dropped
        warnings.warn("""Primary key of sbmFORMATEXTENSION """
                      """table has been already dropped.""")
    # set id as new primary key
    op.create_primary_key('pk_sbmFORMATEXTENSION_id',
                          'sbmFORMATEXTENSION', ['id'])
    # set id as autoincrement
    op.alter_column('sbmFORMATEXTENSION', 'id',
                    existing_type=db.Integer(),
                    existing_nullable=False, autoincrement=True)
    # create indices
    op.create_index('sbmformatextension_file_extension_idx',
                    'sbmFORMATEXTENSION', columns=['FILE_EXTENSION'],
                    unique=False, mysql_length=10)
    op.create_index('sbmformatextension_file_format_idx',
                    'sbmFORMATEXTENSION', columns=['FILE_FORMAT'],
                    unique=False, mysql_length=50)

    # table sbmGFILERESULT

    # add "id" column
    op.add_column('sbmGFILERESULT',
                  db.Column('id', db.Integer(), nullable=False))
    # set all ids
    records = run_sql("""SELECT FORMAT, RESULT FROM """
                      """sbmGFILERESULT AS sbm """
                      """ORDER BY sbm.FORMAT, sbm.RESULT""")
    for index, rec in enumerate(records):
        run_sql("""UPDATE sbmGFILERESULT """
                """SET id = %s """
                """ WHERE FORMAT = %s AND """
                """       RESULT = %s """,
                (index + 1, rec[0], rec[1]))
    # remove primary key
    try:
        op.drop_constraint(None, 'sbmGFILERESULT',
                           type_='primary')
    except OperationalError:
        # the primary key is already dropped
        warnings.warn("""Primary key of sbmGFILERESULT """
                      """table has been already dropped.""")
    # set id as new primary key
    op.create_primary_key('pk_sbmGFILERESULT_id',
                          'sbmGFILERESULT', ['id'])
    # set id as autoincrement
    op.alter_column('sbmGFILERESULT', 'id',
                    existing_type=db.Integer(),
                    existing_nullable=False, autoincrement=True)
    # create indices
    op.create_index('sbmgfileresult_format_idx',
                    'sbmGFILERESULT', columns=['FORMAT'],
                    unique=False, mysql_length=50)
    op.create_index('sbmgfileresult_result_idx',
                    'sbmGFILERESULT', columns=['RESULT'],
                    unique=False, mysql_length=50)


def estimate():
    """Estimate running time of upgrade in seconds (optional)."""
    num_sbmfe = run_sql("SELECT count(*) FROM sbmFORMATEXTENSION")
    num_sbmgf = run_sql("SELECT count(*) FROM sbmGFILERESULT")
    total = int(num_sbmfe[0][0]) + int(num_sbmgf[0][0])
    return int(float(total) / 1000) + 1


def pre_upgrade():
    """Run pre-upgrade checks (optional)."""
    pass


def post_upgrade():
    """Run post-upgrade checks (optional)."""
    pass
