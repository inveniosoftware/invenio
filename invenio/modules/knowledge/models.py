# -*- coding: utf-8 -*-
#
## This file is part of Invenio.
## Copyright (C) 2011, 2012 CERN.
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
## 59 Temple Place, Suite 330, Boston, MA 02D111-1307, USA.

"""
bibknowledge database models.
"""

# General imports.
from invenio.ext.sqlalchemy import db

# Create your models here.

from invenio.modules.search.models import Collection

class KnwKB(db.Model):
    """Represents a KnwKB record."""
    def __init__(self):
        pass
    __tablename__ = 'knwKB'
    id = db.Column(db.MediumInteger(8, unsigned=True), nullable=False,
                primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), server_default='', unique=True)
    description = db.Column(db.Text, nullable=True)
    kbtype = db.Column(db.Char(1), nullable=True)

class KnwKBDDEF(db.Model):
    """Represents a KnwKBDDEF record."""
    def __init__(self):
        pass
    __tablename__ = 'knwKBDDEF'
    id_knwKB = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(KnwKB.id), nullable=False, primary_key=True)
    id_collection = db.Column(db.MediumInteger(9, unsigned=True),
                db.ForeignKey(Collection.id), nullable=True)
    output_tag = db.Column(db.Text, nullable=True)
    search_expression = db.Column(db.Text, nullable=True)
    kb = db.relationship(KnwKB, backref='kbdefs')
    collection = db.relationship(Collection, backref='kbdefs')

class KnwKBRVAL(db.Model):
    """Represents a KnwKBRVAL record."""
    def __init__(self):
        pass
    __tablename__ = 'knwKBRVAL'
    id = db.Column(db.MediumInteger(8, unsigned=True), nullable=False,
                primary_key=True,
                autoincrement=True)
    m_key = db.Column(db.String(255), nullable=False, server_default='',
                index=True)
    m_value = db.Column(db.Text(30), nullable=False,
                index=True)
    id_knwKB = db.Column(db.MediumInteger(8), db.ForeignKey(KnwKB.id), nullable=False,
                server_default='0')
    kb = db.relationship(KnwKB, backref='kbrvals')


__all__ = ['KnwKB',
           'KnwKBDDEF',
           'KnwKBRVAL']
