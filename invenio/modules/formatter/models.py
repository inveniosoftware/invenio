# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2015 CERN.
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

"""Database cache for formatter."""

from invenio.ext.sqlalchemy import db
from invenio.modules.records.models import Record as Bibrec


class Bibfmt(db.Model):
    """Represent a Bibfmt record."""

    __tablename__ = 'bibfmt'

    id_bibrec = db.Column(
        db.MediumInteger(8, unsigned=True),
        db.ForeignKey(Bibrec.id),
        nullable=False,
        server_default='0',
        primary_key=True,
        autoincrement=False)

    format = db.Column(
        db.String(10),
        nullable=False,
        server_default='',
        primary_key=True,
        index=True)

    kind = db.Column(
        db.String(10),
        nullable=False,
        server_default='',
        index=True
        )

    last_updated = db.Column(
        db.DateTime,
        nullable=False,
        server_default='1900-01-01 00:00:00',
        index=True)

    value = db.Column(db.iLargeBinary)

    needs_2nd_pass = db.Column(db.TinyInteger(1), server_default='0')

    bibrec = db.relationship(Bibrec, backref='bibfmt')

__all__ = ('Bibfmt', )
