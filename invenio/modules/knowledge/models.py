# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011, 2012, 2014 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Knowledge database models."""

# General imports.
from invenio.ext.sqlalchemy import db

# Create your models here.

from invenio.modules.search.models import Collection


class KnwKB(db.Model):

    """Represent a KnwKB record."""

    __tablename__ = 'knwKB'
    id = db.Column(db.MediumInteger(8, unsigned=True), nullable=False,
                   primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), server_default='', unique=True)
    description = db.Column(db.Text, nullable=True)
    kbtype = db.Column(db.Char(1), nullable=True)

    def to_dict(self):
        """ Return a dict representation of KnwKB."""
        return {'id': self.id, 'name': self.name,
                'description': self.description,
                'kbtype': self.kbtype}


class KnwKBDDEF(db.Model):

    """Represent a KnwKBDDEF record."""

    __tablename__ = 'knwKBDDEF'
    id_knwKB = db.Column(db.MediumInteger(8, unsigned=True),
                         db.ForeignKey(KnwKB.id), nullable=False,
                         primary_key=True)
    id_collection = db.Column(db.MediumInteger(9, unsigned=True),
                              db.ForeignKey(Collection.id), nullable=True)
    output_tag = db.Column(db.Text, nullable=True)
    search_expression = db.Column(db.Text, nullable=True)
    kb = db.relationship(KnwKB, backref='kbdefs')
    collection = db.relationship(Collection, backref='kbdefs')

    def to_dict(self):
        """ Return a dict representation of KnwKBDDEF."""
        return {'field': self.output_tag,
                'expression': self.search_expression,
                'coll_id': self.id_collection,
                'collection': self.collection.name if self.collection else None}


class KnwKBRVAL(db.Model):

    """Represent a KnwKBRVAL record."""

    __tablename__ = 'knwKBRVAL'
    id = db.Column(db.MediumInteger(8, unsigned=True), nullable=False,
                   primary_key=True, autoincrement=True)
    m_key = db.Column(db.String(255), nullable=False, server_default='',
                      index=True)
    m_value = db.Column(db.Text(30), nullable=False, index=True)
    id_knwKB = db.Column(db.MediumInteger(8), db.ForeignKey(KnwKB.id),
                         nullable=False, server_default='0')
    kb = db.relationship(KnwKB, backref='kbrvals')

    def to_dict(self):
        """ Return a dict representation of KnwKBRVAL."""
        return {'id': self.id, 'key': self.m_key,
                'value': self.m_value,
                'kbid': self.kb.id if self.kb else None,
                'kbname': self.kb.name if self.kb else None}

__all__ = ('KnwKB',
           'KnwKBDDEF',
           'KnwKBRVAL',
           )
