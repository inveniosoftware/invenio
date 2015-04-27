# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012 CERN.
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
bibclassify database models.
"""

# General imports.
from invenio.ext.sqlalchemy import db

# Create your models here.

from invenio.modules.collections.models import Collection

class ClsMETHOD(db.Model):
    """Represents a ClsMETHOD record."""
    def __init__(self):
        pass
    __tablename__ = 'clsMETHOD'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True) #,
            #autoincrement=True)
    name = db.Column(db.String(50), nullable=False, unique=True,
                server_default='')
    location = db.Column(db.String(255), nullable=False,
                server_default='')
    description = db.Column(db.String(255), nullable=False,
                server_default='')
    last_updated = db.Column(db.DateTime, nullable=False,
            server_default='1900-01-01 00:00:00')


class CollectionClsMETHOD(db.Model):
    """Represents a Collection_clsMETHOD record."""
    __tablename__ = 'collection_clsMETHOD'
    id_collection = db.Column(db.MediumInteger(9, unsigned=True),
                db.ForeignKey(Collection.id), primary_key=True, nullable=False)
    id_clsMETHOD = db.Column(db.MediumInteger(9, unsigned=True),
                db.ForeignKey(ClsMETHOD.id), primary_key=True, nullable=False)
    collection = db.relationship(Collection, backref='clsMETHODs')
    clsMETHOD = db.relationship(ClsMETHOD, backref='collections')


__all__ = ['ClsMETHOD',
           'CollectionClsMETHOD']
