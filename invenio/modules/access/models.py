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
webaccess database models.
"""

# General imports.
from invenio.ext.sqlalchemy import db

# Create your models here.

from invenio.modules.accounts.models import User

class AccACTION(db.Model):
    """Represents a AccACTION record."""
    __tablename__ = 'accACTION'
    id = db.Column(db.Integer(15, unsigned=True),
                primary_key=True,
                autoincrement=True)
    name = db.Column(db.String(32), unique=True,
                nullable=True)
    description = db.Column(db.String(255), nullable=True)
    allowedkeywords = db.Column(db.String(255), nullable=True)
    optional = db.Column(db.Enum('yes', 'no'), nullable=False,
                server_default='no')

class AccARGUMENT(db.Model):
    """Represents a AccARGUMENT record."""
    __tablename__ = 'accARGUMENT'
    id = db.Column(db.Integer(15),  # , unsigned=True),
                primary_key=True,
                autoincrement=True)
    keyword = db.Column(db.String(32), nullable=True)
    value = db.Column(db.String(255), nullable=True)
    __table_args__ = (db.Index('KEYVAL', keyword, value),
                      db.Model.__table_args__)

class AccMAILCOOKIE(db.Model):
    """Represents a AccMAILCOOKIE record."""
    __tablename__ = 'accMAILCOOKIE'
    id = db.Column(db.Integer(15, unsigned=True),
                primary_key=True,
                autoincrement=True)
    data = db.Column(db.iBinary, nullable=False)
    expiration = db.Column(db.DateTime, nullable=False,
                server_default='9999-12-31 23:59:59',
                index=True)
    kind = db.Column(db.String(32), nullable=False)
    onetime = db.Column(db.TinyInteger(1), nullable=False,
                server_default='0')
    status = db.Column(db.Char(1), nullable=False,
                server_default='W')

class AccROLE(db.Model):
    """Represents a AccROLE record."""
    __tablename__ = 'accROLE'
    id = db.Column(db.Integer(15, unsigned=True),
                primary_key=True,
                autoincrement=True)
    name = db.Column(db.String(32), unique=True,
                nullable=True)
    description = db.Column(db.String(255), nullable=True)
    firerole_def_ser = db.Column(db.iBinary, nullable=True)
    firerole_def_src = db.Column(db.Text, nullable=True)

class AccAuthorization(db.Model):
    """Represents a AccAssociation record."""
    __tablename__ = 'accROLE_accACTION_accARGUMENT'
    id_accROLE = db.Column(db.Integer(15, unsigned=True),
                db.ForeignKey(AccROLE.id),
                nullable=True,
                autoincrement=False,
                primary_key=True, index=True)
    id_accACTION = db.Column(db.Integer(15, unsigned=True),
                db.ForeignKey(AccACTION.id),
                nullable=True,
                autoincrement=False,
                primary_key=True, index=True)
    id_accARGUMENT = db.Column(db.Integer(15),  # , unsigned=True),
                db.ForeignKey(AccARGUMENT.id),
                nullable=True, primary_key=True,
                autoincrement=False,
                index=True)
    argumentlistid = db.Column(db.MediumInteger(8), nullable=True,
                autoincrement=False,
                primary_key=True)
    role = db.relationship(AccROLE, backref='authorizations')
    action = db.relationship(AccACTION, backref='authorizations')
    argument = db.relationship(AccARGUMENT, backref='authorizations')

class UserAccROLE(db.Model):
    """Represents a UserAccROLE record."""
    __tablename__ = 'user_accROLE'
    id_user = db.Column(db.Integer(15, unsigned=True),
                db.ForeignKey(User.id),
                nullable=False, primary_key=True)
    id_accROLE = db.Column(db.Integer(15, unsigned=True),
                db.ForeignKey(AccROLE.id),
                nullable=False, primary_key=True)
    expiration = db.Column(db.DateTime, nullable=False,
                server_default='9999-12-31 23:59:59')
    user = db.relationship(User, backref='roles')
    role = db.relationship(AccROLE, backref='users')

__all__ = ['AccACTION',
           'AccARGUMENT',
           'AccMAILCOOKIE',
           'AccROLE',
           'AccAuthorization',
           'UserAccROLE']
