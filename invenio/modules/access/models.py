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

from __future__ import unicode_literals

from cPickle import dumps, loads

from datetime import datetime, timedelta

from invenio.ext.passlib.hash import mysql_aes_decrypt, mysql_aes_encrypt
from invenio.ext.sqlalchemy import db
from invenio.ext.sqlalchemy.utils import session_manager
from invenio.modules.access.errors import AccessFactoryError, \
    InvenioWebAccessMailCookieDeletedError, InvenioWebAccessMailCookieError
from invenio.modules.access.firerole import acc_firerole_check_user, \
    compile_role_definition, deserialize, serialize
from invenio.modules.access.local_config import CFG_ACC_ACTIVITIES_URLS, \
    CFG_ACC_EMPTY_ROLE_DEFINITION_SER, CFG_ACC_EMPTY_ROLE_DEFINITION_SRC, \
    SUPERADMINROLE
from invenio.utils.hash import md5

from invenio_accounts.models import User

from random import random

from six import iteritems, text_type

from sqlalchemy.orm import validates
from sqlalchemy.orm.exc import NoResultFound


class AccACTION(db.Model):

    """Represent an access action."""

    __tablename__ = 'accACTION'
    id = db.Column(db.Integer(15, unsigned=True),
                   primary_key=True, autoincrement=True)
    name = db.Column(db.String(32), unique=True, nullable=True)
    description = db.Column(db.String(255), nullable=True)
    _allowedkeywords = db.Column(db.String(255), nullable=True,
                                 name="allowedkeywords")
    _optional = db.Column(db.Enum('yes', 'no', name='yes_no'), nullable=False,
                          server_default='no', name="optional")

    def __init__(self, allowedkeywords=None, *args, **kwargs):
        """Init."""
        self.allowedkeywords = allowedkeywords or []
        super(AccACTION, self).__init__(*args, **kwargs)

    def __repr__(self):
        """Repr."""
        return "{0.name}".format(self)

    @db.hybrid_property
    def allowedkeywords(self):
        """Get allowedkeywords."""
        return self._allowedkeywords.split(u',') \
            if self._allowedkeywords else []

    @allowedkeywords.setter
    def allowedkeywords(self, value):
        """Set allowedkeywords.

        Note: if value chage, then delete connected authorizations.
        """
        # set new value (accept string or list)
        if not isinstance(value, str) and not isinstance(value, text_type):
            value = text_type.join(u',', sorted(value))

        if self.id and self._allowedkeywords != value:
            # delete authorizations
            filters = [AccAuthorization.id_accACTION == self.id]
            if value:
                filters.append(
                    db.or_(
                        AccAuthorization.id_accARGUMENT != -1,
                        AccAuthorization.id_accARGUMENT.is_(None)
                    )
                )
            AccAuthorization.delete(*filters)

        self._allowedkeywords = value

    @db.hybrid_property
    def optional(self):
        """Get optional."""
        return self._optional

    @optional.setter
    def optional(self, value):
        """Set optional.

        note: if value change to no, then delete connected authorizations.
        """
        if self.id and self._optional != value and value == 'no':
            AccAuthorization.delete(*[
                AccAuthorization.id_accACTION == self.id,
                AccAuthorization.id_accARGUMENT == -1,
                AccAuthorization.argumentlistid == -1,
            ])

        # set new value
        self._optional = value

    def is_optional(self):
        """Return True if it's optional."""
        return True if self.optional == 'yes' else False

    @classmethod
    @session_manager
    def delete(cls, *criteria, **filters):
        """Delete action."""
        objs = cls.query.filter(*criteria).filter_by(**filters).all()
        for obj in objs:
            db.session.delete(obj)

    @classmethod
    @session_manager
    def update(cls, criteria, updates):
        """Update values.

        :param criteria: filter list
        :param updates: list of update
        """
        objs = cls.query.filter(*criteria).all()
        for obj in objs:
            for (k, v) in iteritems(updates):
                obj.__setattr__(k, v)
            db.session.merge(obj)

    @classmethod
    def count(cls, *criteria, **filters):
        """Count how much actions."""
        return cls.query.filter(*criteria).filter_by(**filters).count()

    @classmethod
    @session_manager
    def factory(cls, name, description=None, optional=None,
                allowedkeywords=None):
        """Create or update a action.

        :return: a AccACTION
        """
        if not name:
            raise AccessFactoryError
        optional = 'yes' if bool(optional) else 'no'
        try:
            action = AccACTION.query.filter(
                AccACTION.name == name).one()
            if description:
                action.description = description
            if optional:
                action.optional = optional
            if allowedkeywords:
                action.allowedkeywords = allowedkeywords
            db.session.merge(action)
        except NoResultFound:
            action = AccACTION(
                name=name,
                description=description,
                optional=optional,
                allowedkeywords=allowedkeywords
            )
            db.session.add(action)

        return action


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

    @classmethod
    @session_manager
    def delete(cls, *criteria, **filters):
        """Delete argument."""
        objs = cls.query.filter(*criteria).filter_by(**filters).all()
        for obj in objs:
            db.session.delete(obj)

    @classmethod
    def exists(cls, *criteria, **filters):
        """Check if authorization exists."""
        return db.session.query(
            cls.query.filter(*criteria).filter_by(**filters).exists()
        ).scalar()

    @classmethod
    @session_manager
    def factory(cls, keyword=None, value=None):
        """Add new or get existing argument.

        :param keyword: if add new, set keyword, or use to filter
        :param value: if add new, set value, or use to filter
        :return: a AccARGUMENT
        """
        if not keyword:
            raise AccessFactoryError
        try:
            argument = AccARGUMENT.query.filter(
                AccARGUMENT.keyword == keyword,
                AccARGUMENT.value == value
            ).one()
        except NoResultFound:
            argument = AccARGUMENT(keyword=keyword, value=value)
            db.session.add(argument)

        return argument


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
            AccMAILCOOKIE._data
        ).filter_by(id=cookie_id).one()
        obj.data = loads(mysql_aes_decrypt(data, password))

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
        cookie._data = mysql_aes_encrypt(dumps(data), password)
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
    _firerole_def_ser = db.Column(db.iBinary, nullable=True,
                                  name="firerole_def_ser")
    _firerole_def_src = db.Column(db.Text, nullable=True,
                                  name="firerole_def_src")

    def __repr__(self):
        """Repr."""
        return "{0.name} - {0.description}".format(self)

    @db.hybrid_property
    def firerole_def_ser(self):
        """Get firerole_def_ser."""
        return deserialize(self._firerole_def_ser)

    @firerole_def_ser.setter
    def firerole_def_ser(self, value):
        """Ensure to not directly set the compiled version."""
        raise Exception("Can't set attribute. Please set firerole_def_src "
                        "value")

    @db.hybrid_property
    def firerole_def_src(self):
        """Get firerole_def_src."""
        return self._firerole_def_src

    @firerole_def_src.setter
    def firerole_def_src(self, value):
        """Set firerole_def_src."""
        # update compiled version
        compiled_version = serialize(compile_role_definition(value))
        self._firerole_def_ser = bytearray(compiled_version) \
            if compiled_version is not None \
            else CFG_ACC_EMPTY_ROLE_DEFINITION_SER
        # set new value
        self._firerole_def_src = value

    @classmethod
    @session_manager
    def delete(cls, *criteria, **filters):
        """Delete role."""
        # delete objects
        objs = cls.query.filter(*criteria).filter_by(**filters).all()
        for obj in objs:
            db.session.delete(obj)

    @classmethod
    @session_manager
    def update(cls, criteria, updates):
        """Update values.

        :param criteria: filter list
        :param updates: list of update
        """
        objs = cls.query.filter(*criteria).all()
        for obj in objs:
            for (k, v) in iteritems(updates):
                obj.__setattr__(k, v)
            db.session.merge(obj)

    @classmethod
    @session_manager
    def factory(cls, name, description=None,
                firerole_def_src=None):
        """Add (and insert in DB if already not exists) a new role.

        :param name: role name
        :param description: role description
        :param firerole_def_src: firewall definition
        :return: the new role
        """
        if not name:
            raise AccessFactoryError
        try:
            role = AccROLE.query.filter_by(name=name).one()
            if description:
                role.description = description
            if firerole_def_src:
                role.firerole_def_src = firerole_def_src
            db.session.merge(role)
        except NoResultFound:
            firerole_def_src = firerole_def_src or \
                CFG_ACC_EMPTY_ROLE_DEFINITION_SRC

            role = AccROLE(name=name,
                           description=description,
                           firerole_def_src=firerole_def_src)
            db.session.add(role)
        return role

    @classmethod
    def exists(cls, *criteria, **filters):
        """Check if role exists."""
        return db.session.query(
            cls.query.filter(*criteria).filter_by(**filters).exists()
        ).scalar()


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
    _id_accARGUMENT = db.Column(db.Integer(15),
                                nullable=True, name="id_accARGUMENT",
                                index=True)
    argumentlistid = db.Column(db.MediumInteger(8), nullable=True)

    role = db.relationship(
        AccROLE,
        backref=db.backref(
            'authorizations',
            cascade="all, delete-orphan",
        ))
    action = db.relationship(
        AccACTION,
        backref=db.backref(
            'authorizations',
            cascade="all, delete-orphan",
        ))
    argument = db.relationship(
        AccARGUMENT, backref='authorizations',
        primaryjoin=db.and_(
            AccARGUMENT.id == _id_accARGUMENT,
            _id_accARGUMENT != -1,
            _id_accARGUMENT is not None
        ),
        foreign_keys=_id_accARGUMENT,
        uselist=False,
        cascade="all, delete",
    )

    @db.hybrid_property
    def id_accARGUMENT(self):
        """get id_accARGUMENT."""
        return self._id_accARGUMENT

    @id_accARGUMENT.setter
    def id_accARGUMENT(self, value):
        """set id_accARGUMENT."""
        self._id_accARGUMENT = value or None

    @classmethod
    @session_manager
    def delete(cls, *criteria, **filters):
        """Delete authorization."""
        objs = cls.query.filter(*criteria).filter_by(**filters).all()
        for obj in objs:
            db.session.delete(obj)

    @classmethod
    def exists(cls, *criteria, **filters):
        """Check if authorization exists."""
        return db.session.query(
            cls.query.filter(*criteria).filter_by(**filters).exists()
        ).scalar()

    @classmethod
    def count(cls, *criteria, **filters):
        """Count how much authorizations."""
        return cls.query.filter(*criteria).filter_by(**filters).count()

    @classmethod
    @session_manager
    def _factory(cls, role, action, argumentlistid=-1, id_accARGUMENT=-1):
        """Simply create or update authorization without special control."""
        basic_filters = [
            AccAuthorization.id_accROLE == role.id,
            AccAuthorization.id_accACTION == action.id,
        ]
        # ready to add/read
        try:
            # get auth
            return [AccAuthorization.query.filter(*(
                basic_filters + [
                    AccAuthorization.argumentlistid == argumentlistid,
                    AccAuthorization._id_accARGUMENT == id_accARGUMENT
                ])).one()]
        except NoResultFound:
            # create new
            auth = AccAuthorization(
                id_accROLE=role.id,
                id_accACTION=action.id,
                argumentlistid=argumentlistid,
                id_accARGUMENT=id_accARGUMENT
            )
            db.session.add(auth)
            return [auth]

    @classmethod
    def factory(cls, role, action, argumentlistid=-1, arguments=None):
        """Create or update a authorization.

        :param role: role associated
        :param action: action associated
        :param arglistid: argumentlistid for the inserted entries
            if -1: create new group
            other values: add to this group, if it exists or not
        :param arguments: list of arguments
        """
        basic_filters = [
            AccAuthorization.id_accROLE == role.id,
            AccAuthorization.id_accACTION == action.id,
        ]
        if action.is_optional():
            return cls._factory(role=role, action=action, argumentlistid=-1,
                                id_accARGUMENT=-1)
        if not action.allowedkeywords:
            return cls._factory(role=role, action=action, argumentlistid=0,
                                id_accARGUMENT=None)
        # check all the arguments if someone is not allowed
        if arguments:
            for argument in arguments:
                if argument.keyword not in action.allowedkeywords:
                    raise AccessFactoryError("Not permitted argument.")
        if argumentlistid < 0:
            # list id arguments
            argument_ids = [a.id for a in arguments]
            # check if equal authorization exists
            for argumentlistid in db.session.query(
                AccAuthorization.argumentlistid).filter(
                    *basic_filters).distinct().all():
                # list length
                listlength = AccAuthorization.count(*(
                    basic_filters + [
                        AccAuthorization.argumentlistid == argumentlistid,
                        AccAuthorization._id_accARGUMENT.in_(argument_ids)
                    ]))
                # not list
                notlist = AccAuthorization.count(*(
                    basic_filters + [
                        AccAuthorization.argumentlistid == argumentlistid,
                        AccAuthorization._id_accARGUMENT.notin_(argument_ids)
                    ]))
                # this means that a duplicate already exists
                if not notlist and listlength == len(argument_ids):
                    return []
            # find new arglistid, highest + 1
            argumentlistid = db.session.query(
                db.func.max(AccAuthorization.argumentlistid)).filter(
                    *basic_filters
                ).scalar() or 1
        # all references are valid, insert: one entry in raa for each argument
        auths = []
        for argument_id in argument_ids:
            auth = AccAuthorization(
                id_accROLE=role.id,
                id_accACTION=action.id,
                argumentlistid=argumentlistid,
                id_accARGUMENT=None
            )
            db.session.add(auth)
            auths.append(auth)

        return auths


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

    user = db.relationship(
        User,
        backref=db.backref(
            'roles',
            cascade="all, delete-orphan",
        )
    )
    role = db.relationship(
        AccROLE,
        backref=db.backref(
            'users',
            cascade="all, delete-orphan",
        )
    )

    @classmethod
    @session_manager
    def delete(cls, *criteria, **filters):
        """Delete useraccrole."""
        objs = cls.query.filter(*criteria).filter_by(**filters).all()
        for obj in objs:
            db.session.delete(obj)

    @classmethod
    @session_manager
    def update(cls, criteria, updates):
        """Update values.

        :param criteria: filter list
        :param updates: list of update
        """
        objs = cls.query.filter(*criteria).all()
        for obj in objs:
            for (k, v) in iteritems(updates):
                obj.__setattr__(k, v)
            db.session.merge(obj)

    @classmethod
    def count(cls, *criteria, **filters):
        """Count how much authorizations."""
        return cls.query.filter(*criteria).filter_by(**filters).count()

    @classmethod
    @session_manager
    def factory(cls, id_user, id_accROLE, expiration=None):
        """Add (and insert in DB if already not exists) a new role.

        :param id_user: user id
        :param id_accROLE: role id
        :param expiration: datetime of new expiration (if create new)
        :return: the UserAccROLE
        """
        expiration = expiration or datetime.strptime(
            '9999-12-31 23:59', '%Y-%m-%d %H:%M')
        try:
            # get one
            user_acc_role = UserAccROLE.query.filter_by(
                id_user=id_user, id_accROLE=id_accROLE
            ).one()
            # update expiration
            if user_acc_role.expiration < expiration:
                user_acc_role.expiration = expiration
                db.session.merge(user_acc_role)
        except NoResultFound:
            # insert new
            user_acc_role = UserAccROLE(
                id_user=id_user, id_accROLE=id_accROLE, expiration=expiration
            )
            db.session.add(user_acc_role)

        return user_acc_role

    @classmethod
    def get_roles_emails(cls, id_roles):
        """Get emails by roles.

        :param id_roles: list of roles
        :return: list of user's email that have at least one of these roles
        """
        return set(
            map(lambda u: u.email.lower().strip(),
                db.session.query(
                    db.func.distinct(User.email)).join(
                        User.active_roles
                    ).filter(UserAccROLE.id_accROLE.in_(id_roles)).all()))

    @classmethod
    def is_user_in_any_role(cls, user_info, id_roles):
        """Check if the user have at least one of that roles.

        :param user_info: user info (id, ...)
        :param roles: list of roles
        :return: True if the user have at least one of that roles
        """
        filters = [
            UserAccROLE.id_user == user_info['uid'],
            UserAccROLE.expiration >= db.func.now(),
            UserAccROLE.id_accROLE.in_(id_roles)
        ]

        if UserAccROLE.count(*filters) > 0:
            return True

        roles = AccROLE.query.filter(*filters).all()
        for role in roles:
            if acc_firerole_check_user(user_info, role.firerole_def_ser):
                return True

        return False

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
