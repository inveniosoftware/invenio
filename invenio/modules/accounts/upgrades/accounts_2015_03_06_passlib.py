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

"""Upgrade for new password hashing."""

import hashlib

from invenio.ext.passlib.hash import mysql_aes_encrypt
from invenio.ext.sqlalchemy import db
from invenio.modules.upgrader.api import op

from sqlalchemy import select
from sqlalchemy.dialects import mysql


depends_on = [u'accounts_2014_11_07_usergroup_name_column_unique']


def info():
    """Return documentation."""
    return "Migrate password salt to separate column."


def do_upgrade():
    """Upgrade recipe.

    Adds two new columns (password_salt and password_scheme) and migrates
    emails to password salt.
    """
    op.add_column('user', db.Column('password_salt', db.String(length=255),
                                    nullable=True))
    op.add_column('user', db.Column('password_scheme', db.String(length=50),
                                    nullable=False))

    # Temporary column needed for data migration
    op.add_column('user', db.Column('new_password', db.String(length=255)))

    # Migrate emails to password_salt
    m = db.MetaData(bind=db.engine)
    m.reflect()
    u = m.tables['user']

    conn = db.engine.connect()
    conn.execute(u.update().values(
        password_salt=u.c.email,
        password_scheme='invenio_aes_encrypted_email'
    ))

    # Migrate password blob to password varchar.
    for row in conn.execute(select([u])):
        # NOTE: Empty string passwords were stored as empty strings
        # instead of a hashed version, hence they must be treated differently.
        legacy_pw = row[u.c.password] or mysql_aes_encrypt(row[u.c.email], "")

        stmt = u.update().where(
            u.c.id == row[u.c.id]
        ).values(
            new_password=hashlib.sha256(legacy_pw).hexdigest()
        )
        conn.execute(stmt)

    # Create index
    op.create_index(
        op.f('ix_user_password_scheme'),
        'user',
        ['password_scheme'],
        unique=False
    )

    # Drop old database column and rename new.
    op.drop_column('user', 'password')
    op.alter_column(
        'user', 'new_password',
        new_column_name='password',
        existing_type=mysql.VARCHAR(255),
        existing_nullable=True,
    )


def estimate():
    """Estimate running time of upgrade in seconds (optional)."""
    return 1
