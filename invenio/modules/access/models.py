# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2014, 2015 CERN.
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

"""Access database models."""

# General imports.
from cPickle import dumps, loads

from datetime import datetime, timedelta

from invenio.base.wrappers import lazy_import
from invenio.ext.sqlalchemy import db
from invenio.ext.sqlalchemy.utils import session_manager
from invenio.modules.accounts.models import User
from invenio.utils.hash import md5

from random import random

from sqlalchemy import bindparam
from sqlalchemy.orm import validates

from .errors import \
    InvenioWebAccessMailCookieDeletedError, InvenioWebAccessMailCookieError

SUPERADMINROLE = lazy_import(
    'invenio.modules.access.local_config.SUPERADMINROLE')
CFG_ACC_ACTIVITIES_URLS = lazy_import(
    'invenio.modules.access.local_config.CFG_ACC_ACTIVITIES_URLS')


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
        """Repr."""
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
        """Repr."""
        return "{0.keyword}={0.value}".format(self)


class AccMAILCOOKIE(db.Model):

    """Represent an email cookie."""

    __tablename__ = 'accMAILCOOKIE'

    AUTHORIZATIONS_KIND = (
        'pw_reset', 'mail_activation', 'role', 'authorize_action',
        'comment_msg', 'generic'
    )

    id = db.Column(db.Integer(15, unsigned=True), primary_key=True,
                   autoincrement=True)
    _data = db.Column('data', db.iBinary, nullable=False)
    expiration = db.Column(db.DateTime, nullable=False,
                           server_default='9999-12-31 23:59:59', index=True)
    kind = db.Column(db.String(32), nullable=False)
    onetime = db.Column(db.TinyInteger(1), nullable=False, server_default='0')
    status = db.Column(db.Char(1), nullable=False, server_default='W')

    @validates('kind')
    def validate_kind(self, key, kind):
        """Validate cookie kind."""
        assert kind in self.AUTHORIZATIONS_KIND
        return kind

    @classmethod
    def get(cls, cookie, delete=False):
        """Get cookie if it is valid."""
        password = cookie[:16]+cookie[-16:]
        cookie_id = int(cookie[16:-16], 16)

        obj, data = db.session.query(
            cls,
            db.func.aes_decrypt(
                cls._data, bindparam('password')
            ).label('decrypted')
        ).params(password=password).filter_by(id=cookie_id).one()
        obj.data = loads(data)

        (kind_check, params, expiration, onetime_check) = obj.data
        assert obj.kind in cls.AUTHORIZATIONS_KIND

        if not (obj.kind == kind_check and obj.onetime == onetime_check):
            raise InvenioWebAccessMailCookieError("Cookie is corrupted")
        if obj.status == 'D':
            raise InvenioWebAccessMailCookieDeletedError(
                "Cookie has been deleted")
        if obj.onetime or delete:
            obj.status = 'D'
            db.session.merge(obj)
            db.session.commit()
        return obj

    @classmethod
    def create(cls, kind, params, cookie_timeout=timedelta(days=1),
               onetime=False):
        """Create cookie with given params."""
        expiration = datetime.today() + cookie_timeout
        data = (kind, params, expiration, onetime)
        password = md5(str(random())).hexdigest()
        cookie = cls(
            expiration=expiration,
            kind=kind,
            onetime=int(onetime),
        )
        # FIXME aes_encrypt exists?
        cookie._data = db.func.aes_encrypt(dumps(data), password)
        db.session.add(cookie)
        db.session.commit()
        db.session.refresh(cookie)
        return password[:16]+hex(cookie.id)[2:-1]+password[-16:]

    @classmethod
    @session_manager
    def gc(cls):
        """Remove expired items."""
        return cls.query.filter(cls.expiration < db.func.now()).delete()


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
        """Repr."""
        return "{0.name} - {0.description}".format(self)


class AccAuthorization(db.Model):

    """Represent an authorization."""

    __tablename__ = 'accROLE_accACTION_accARGUMENT'
    id = db.Column(db.Integer(15, unsigned=True), primary_key=True,
                   autoincrement=True)
    id_accROLE = db.Column(db.Integer(15, unsigned=True),
                           db.ForeignKey(AccROLE.id), nullable=True,
                           index=True)
    id_accACTION = db.Column(db.Integer(15, unsigned=True),
                             db.ForeignKey(AccACTION.id), nullable=True,
                             index=True)
    _id_accARGUMENT = db.Column(db.Integer(15), db.ForeignKey(AccARGUMENT.id),
                                nullable=True, name="id_accARGUMENT",
                                index=True)
    argumentlistid = db.Column(db.MediumInteger(8), nullable=True)

    role = db.relationship(AccROLE, backref='authorizations')
    action = db.relationship(AccACTION, backref='authorizations')
    argument = db.relationship(AccARGUMENT, backref='authorizations')

    @db.hybrid_property
    def id_accARGUMENT(self):
        """get id_accARGUMENT."""
        return self.id_accARGUMENT

    @id_accARGUMENT.setter
    def id_accARGUMENT(self, value):
        """set id_accARGUMENT."""
        self._id_accARGUMENT = value or None


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

User.has_admin_role = property(
    lambda self:
    self.has_super_admin_role or db.object_session(self).query(
        db.func.count(User.id) > 0
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

User.has_super_admin_role = property(
    lambda self:
    db.object_session(self).query(db.func.count(User.id) > 0).join(
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
