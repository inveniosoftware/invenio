# -*- coding: utf-8 -*-
#
## This file is part of Invenio.
## Copyright (C) 2011, 2012, 2013, 2014 CERN.
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

"""Account database models."""

# General imports.
from invenio.ext.sqlalchemy import db
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_utils.types.choice import ChoiceType
# Create your models here.


def get_default_user_preferences():
    """Return default user preferences."""
    from invenio.modules.access.local_config import CFG_EXTERNAL_AUTHENTICATION, \
        CFG_EXTERNAL_AUTH_DEFAULT

    user_preference = {
        'login_method': 'Local'}

    if CFG_EXTERNAL_AUTH_DEFAULT in CFG_EXTERNAL_AUTHENTICATION:
        user_preference['login_method'] = CFG_EXTERNAL_AUTH_DEFAULT
    return user_preference


class User(db.Model):

    """Represents a User record."""

    def __str__(self):
        return "%s <%s>" % (self.nickname, self.email)

    __tablename__ = 'user'
    id = db.Column(db.Integer(15, unsigned=True), primary_key=True,
                   autoincrement=True)
    email = db.Column(db.String(255), nullable=False, server_default='',
                      index=True)
    _password = db.Column(db.LargeBinary, name="password",
                          nullable=False)
    note = db.Column(db.String(255), nullable=True)
    settings = db.Column(db.MutableDict.as_mutable(db.MarshalBinary(
        default_value=get_default_user_preferences, force_type=dict)),
        nullable=True)
    nickname = db.Column(db.String(255), nullable=False, server_default='',
                         index=True)
    last_login = db.Column(db.DateTime, nullable=False,
                           server_default='1900-01-01 00:00:00')

    #TODO re_invalid_nickname = re.compile(""".*[,'@]+.*""")

    _password_comparator = db.PasswordComparator(_password)

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def password(self, password):
        self._password = self._password_comparator.hash(password)

    @password.comparator
    def password(self):
        return self._password_comparator

    @property
    def guest(self):
        return False if self.email else True

    #
    # Basic functions for user authentification.
    #
    def get_id(self):
        return self.id

    def is_guest(self):
        return self.guest

    def is_authenticated(self):
        return True if self.email else False

    def is_active(self):
        return True


class Usergroup(db.Model):

    """Represent a Usergroup record."""

    def __str__(self):
        return "%s <%s>" % (self.name, self.description)

    __tablename__ = 'usergroup'

    JOIN_POLICIES = {
        'VISIBLEOPEN': 'VO',
        'VISIBLEMAIL': 'VM',
        'INVISIBLEOPEN': 'IO',
        'INVISIBLEMAIL': 'IM',
        'VISIBLEEXTERNAL': 'VE',
    }

    LOGIN_METHODS = {
        'INTERNAL': 'INTERNAL',
        'EXTERNAL': 'EXTERNAL',
    }

    id = db.Column(db.Integer(15, unsigned=True), nullable=False,
                   primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False,
                     server_default='', index=True)
    description = db.Column(db.Text, nullable=True)
    join_policy = db.Column(
        ChoiceType(
            map(lambda (k, v): (v, k), JOIN_POLICIES.items()),
            impl=db.CHAR(2)
        ), nullable=False, server_default='')
    login_method = db.Column(
        ChoiceType(map(lambda (k, v): (v, k), LOGIN_METHODS.items())),
        nullable=False, server_default='INTERNAL')

    # FIXME Unique(login_method(70), name)
    __table_args__ = (db.Index('login_method_name', login_method, name,
                               mysql_length=[60, None]),
                      db.Model.__table_args__)

    @classmethod
    def filter_visible(cls):
        """Return query object with filtered out invisible groups."""
        visible = filter(lambda k: k[0] == 0,
                         cls.JOIN_POLICIES.values())
        assert len(visible) > 1  # if implementation chage use == instead of in
        return cls.query.filter(cls.join_policy.in_(visible))

    def join(self, id_user=None, status=None):
        """Join user to group.

        If ``id_user`` is not defined the current user's id is used.

        :param id_user: User identifier.
        """
        if id_user is None:
            from flask.ext.login import current_user
            id_user = current_user.get_id()
        self.users.append(
            UserUsergroup(
                id_user=id_user or current_user.get_id(),
                user_status=status or self.new_user_status,
            )
        )

    def leave(self, id_user=None):
        """Remove user from group.

        If ``id_user`` is not defined the current user's id is used.

        :param id_user: User identifier.
        """
        if id_user is None:
            from flask.ext.login import current_user
            id_user = current_user.get_id()

        # FIXME check that I'm not the last admin before leaving the group.
        UserUsergroup.query.filter_by(
            id_usergroup=self.id,
            id_user=id_user,
        ).delete()

    @property
    def new_user_status(self):
        """Return user status for new user."""
        if not self.join_policy.code.endswith('O'):
            return UserUsergroup.USER_STATUS['PENDING']
        return UserUsergroup.USER_STATUS['MEMBER']


class UserUsergroup(db.Model):

    """Represent a UserUsergroup record."""

    USER_STATUS = {
        'ADMIN': 'A',
        'MEMBER': 'M',
        'PENDING': 'P',
    }

    def __str__(self):
        return "%s:%s" % (self.user.nickname, self.usergroup.name)

    __tablename__ = 'user_usergroup'

    id_user = db.Column(db.Integer(15, unsigned=True),
                        db.ForeignKey(User.id),
                        nullable=False, server_default='0',
                        primary_key=True)
    id_usergroup = db.Column(db.Integer(15, unsigned=True),
                             db.ForeignKey(Usergroup.id),
                             nullable=False, server_default='0',
                             primary_key=True)
    user_status = db.Column(db.CHAR(1), nullable=False, server_default='')
    user_status_date = db.Column(db.DateTime, nullable=False,
                                 server_default='1900-01-01 00:00:00')
    user = db.relationship(User, backref='usergroups')
    usergroup = db.relationship(Usergroup, backref='users')


class UserEXT(db.Model):

    """Represent a UserEXT record."""

    __tablename__ = 'userEXT'

    id = db.Column(db.VARBINARY(255), primary_key=True, nullable=False)
    method = db.Column(db.String(50), primary_key=True, nullable=False)
    id_user = db.Column(db.Integer(15, unsigned=True),
                        db.ForeignKey(User.id), nullable=False)

    __table_args__ = (db.Index('id_user', id_user, method, unique=True),
                      db.Model.__table_args__)

__all__ = ['User',
           'Usergroup',
           'UserUsergroup',
           'UserEXT']
