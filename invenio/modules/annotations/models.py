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

from invenio.ext.sqlalchemy import db

from invenio.modules.accounts.models import User
from invenio.modules.records.models import Record as Bibrec


class CmtNOTECOLLAPSED(db.Model):
    """Represents a CmtNOTECOLLAPSED record."""

    __tablename__ = 'cmtNOTECOLLAPSED'

    id = \
        db.Column(db.Integer(15, unsigned=True),
                  primary_key=True,
                  autoincrement=True,
                  nullable=False,
                  unique=True)

    id_bibrec = \
        db.Column(db.MediumInteger(8, unsigned=True),
                  db.ForeignKey(Bibrec.id),
                  primary_key=False,
                  nullable=False,
                  unique=False)

    # e.g., P1-F2 is the path for a note on Page 1, Figure 2
    path = \
        db.Column(db.Text,
                  primary_key=False,
                  nullable=False,
                  unique=False)

    id_user = \
        db.Column(db.Integer(15, unsigned=True),
                  db.ForeignKey(User.id),
                  primary_key=False,
                  nullable=False,
                  unique=False)


__all__ = ['CmtNOTECOLLAPSED']
