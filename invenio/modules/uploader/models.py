# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2014 CERN.
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

"""
bibupload database models.
"""

from invenio.ext.sqlalchemy import db
from invenio.modules.scheduler.models import SchTASK


class HstBATCHUPLOAD(db.Model):
    """Represents a HstBATCHUPLOAD record."""
    __tablename__ = 'hstBATCHUPLOAD'

    id = db.Column(
        db.Integer(15, unsigned=True),
        nullable=False,
        primary_key=True,
        autoincrement=True)

    user = db.Column(
        db.String(50),
        nullable=False,
        index=True)

    submitdate = db.Column(
        db.DateTime,
        nullable=False)

    filename = db.Column(
        db.String(255),
        nullable=False)

    execdate = db.Column(
        db.DateTime,
        nullable=False)

    id_schTASK = db.Column(
        db.Integer(15, unsigned=True),
        db.ForeignKey(SchTASK.id),
        nullable=False)

    batch_mode = db.Column(
        db.String(15),
        nullable=False)

    task = db.relationship(SchTASK, backref='batchuploads')


__all__ = ['HstBATCHUPLOAD']
