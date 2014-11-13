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
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Access database models."""

# General imports.
from invenio.ext.sqlalchemy import db
from invenio.base.wrappers import lazy_import

SUPERADMINROLE = lazy_import(
    'invenio.modules.access.local_config.SUPERADMINROLE')
CFG_ACC_ACTIVITIES_URLS = lazy_import(
    'invenio.modules.access.local_config.CFG_ACC_ACTIVITIES_URLS')


# Create your models here.

from invenio.modules.accounts.models import User


class AccACTION(db.Model):

    """Represent an access action."""

    __tablename__ = 'accACTION'
    id = db.Column(db.Integer(15, unsigned=True),
                   primary_key=True, autoincrement=True)
    name = db.Column(db.String(32), unique=True, nullable=True)
    description = db.Column(db.String(255), nullable=True)
    allowedkeywords = db.Column(db.String(255), nullable=True)
    optional = db.Column(db.Enum('yes', 'no', name='yes_no'), nullable=False,
                         server_default='no')

    def __repr__(self):
        return "{0.name}".format(self)


class AccARGUMENT(db.Model):

    """Represent an authorization argument."""

    __tablename__ = 'accARGUMENT'
    id = db.Column(db.Integer(15), primary_key=True, autoincrement=True)
    keyword = db.Column(db.String(32), nullable=True)
    value = db.Column(db.String(255), nullable=True)
    __table_args__ = (db.Index('KEYVAL', keyword, value),
                      db.Model.__table_args__)

    def __repr__(self):
        return "{0.keyword}={0.value}".format(self)


class AccMAILCOOKIE(db.Model):

    """Represent an email cookie."""

    __tablename__ = 'accMAILCOOKIE'
    id = db.Column(db.Integer(15, unsigned=True), primary_key=True,
                   autoincrement=True)
    data = db.Column(db.iBinary, nullable=False)
    expiration = db.Column(db.DateTime, nullable=False,
                           server_default='9999-12-31 23:59:59', index=True)
    kind = db.Column(db.String(32), nullable=False)
    onetime = db.Column(db.TinyInteger(1), nullable=False, server_default='0')
    status = db.Column(db.Char(1), nullable=False, server_default='W')


class AccROLE(db.Model):

    """Represent an access role."""

    __tablename__ = 'accROLE'
    id = db.Column(db.Integer(15, unsigned=True), primary_key=True,
                   autoincrement=True)
    name = db.Column(db.String(32), unique=True, nullable=True)
    description = db.Column(db.String(255), nullable=True)
    firerole_def_ser = db.Column(db.iBinary, nullable=True)
    firerole_def_src = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return "{0.name} - {0.description}".format(self)


class AccAuthorization(db.Model):

    """Represent an authorization."""

    __tablename__ = 'accROLE_accACTION_accARGUMENT'
    id_accROLE = db.Column(db.Integer(15, unsigned=True),
                           db.ForeignKey(AccROLE.id), nullable=True,
                           autoincrement=False, primary_key=True, index=True)
    id_accACTION = db.Column(db.Integer(15, unsigned=True),
                             db.ForeignKey(AccACTION.id), nullable=True,
                             autoincrement=False, primary_key=True, index=True)
    id_accARGUMENT = db.Column(db.Integer(15), db.ForeignKey(AccARGUMENT.id),
                               nullable=True, primary_key=True,
                               autoincrement=False, index=True)
    argumentlistid = db.Column(db.MediumInteger(8), nullable=True,
                               autoincrement=False, primary_key=True)

    role = db.relationship(AccROLE, backref='authorizations')
    action = db.relationship(AccACTION, backref='authorizations')
    argument = db.relationship(AccARGUMENT, backref='authorizations')


class UserAccROLE(db.Model):

    """Represent an user role relationship."""

    __tablename__ = 'user_accROLE'
    id_user = db.Column(db.Integer(15, unsigned=True), db.ForeignKey(User.id),
                        nullable=False, primary_key=True)
    id_accROLE = db.Column(db.Integer(15, unsigned=True),
                           db.ForeignKey(AccROLE.id), nullable=False,
                           primary_key=True)
    expiration = db.Column(db.DateTime, nullable=False,
                           server_default='9999-12-31 23:59:59')

    user = db.relationship(User, backref='roles')
    role = db.relationship(AccROLE, backref='users')

User.active_roles = db.relationship(
    UserAccROLE,
    lazy="dynamic",
    primaryjoin=db.and_(
        User.id == UserAccROLE.id_user,
        UserAccROLE.expiration >= db.func.now()
    )
)

User.has_admin_role = property(lambda self:
    self.has_super_admin_role or db.object_session(self).query(
        db.func.count(User.id)>0
    ).join(
        User.active_roles,
        UserAccROLE.role,
        AccROLE.authorizations
    ).filter(
        AccAuthorization.id_accACTION.in_(
            db.select([AccACTION.id]).where(
                AccACTION.name.in_(CFG_ACC_ACTIVITIES_URLS.keys())
            )
        ),
        User.id == self.id
    ).scalar()
)

User.has_super_admin_role = property(lambda self:
    db.object_session(self).query(db.func.count(User.id)>0).join(
        User.active_roles,
        UserAccROLE.role
    ).filter(
        AccROLE.name == SUPERADMINROLE,
        User.id == self.id
    ).scalar()
)

__all__ = ('AccACTION',
           'AccARGUMENT',
           'AccMAILCOOKIE',
           'AccROLE',
           'AccAuthorization',
           'UserAccROLE')
