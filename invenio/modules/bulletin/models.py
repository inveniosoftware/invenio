# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2013 CERN.
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
webjournal database models.
"""

# General imports.
from invenio.ext.sqlalchemy import db

# Create your models here.

class JrnJOURNAL(db.Model):
    """Represents a JrnJOURNAL record."""
    __tablename__ = 'jrnJOURNAL'
    id = db.Column(db.MediumInteger(9, unsigned=True), nullable=False,
                primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, unique=True,
                server_default='')

class JrnISSUE(db.Model):
    """Represents a JrnISSUE record."""
    __tablename__ = 'jrnISSUE'
    id_jrnJOURNAL = db.Column(db.MediumInteger(9, unsigned=True),
                db.ForeignKey(JrnJOURNAL.id), nullable=False,
                primary_key=True)
    issue_number = db.Column(db.String(50), nullable=False, server_default='',
                primary_key=True)
    issue_display = db.Column(db.String(50), nullable=False, server_default='')
    date_released = db.Column(db.DateTime, nullable=True)
    date_announced = db.Column(db.DateTime, nullable=True)
    journal = db.relationship(JrnJOURNAL, backref='issues')


__all__ = ['JrnJOURNAL',
           'JrnISSUE']
