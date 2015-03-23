# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2013, 2014, 2015 CERN.
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

"""Account database models."""

# General imports.
from datetime import datetime
from flask_login import current_user
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_utils.types.choice import ChoiceType

# Invenio import
from invenio.ext.sqlalchemy import db

from .errors import AccountSecurityError, IntegrityUsergroupError

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
        """Return string representation."""
        return "%s <%s>" % (self.nickname, self.email)

    __tablename__ = 'user'
    __mapper_args__ = {'confirm_deleted_rows': False}
    id = db.Column(db.Integer(15, unsigned=True), primary_key=True,
                   autoincrement=True)
    email = db.Column(db.String(255), nullable=False, server_default='',
                      index=True)
    _password = db.Column(db.LargeBinary, name="password",
                          nullable=False)
    note = db.Column(db.String(255), nullable=True)
    given_names = db.Column(db.String(255), nullable=True)
    family_name = db.Column(db.String(255), nullable=True)
    settings = db.Column(db.MutableDict.as_mutable(db.MarshalBinary(
        default_value=get_default_user_preferences, force_type=dict)),
        nullable=True)
    nickname = db.Column(db.String(255), nullable=False, server_default='',
                         index=True)
    last_login = db.Column(db.DateTime, nullable=False,
                           server_default='1900-01-01 00:00:00')

    # TODO re_invalid_nickname = re.compile(""".*[,'@]+.*""")

    _password_comparator = db.PasswordComparator(_password)

    @hybrid_property
    def password(self):
        """Return the password."""
        return self._password

    @password.setter
    def password(self, password):
        """Set the password."""
        self._password = self._password_comparator.hash(password)

    @password.comparator
    def password(self):
        """Compare password."""
        return self._password_comparator

    @property
    def guest(self):
        """Return True if the user is a guest."""
        return False if self.email else True

    #
    # Basic functions for user authentification.
    #
    def get_id(self):
        """Return the id."""
        return self.id

    def is_guest(self):
        """Return if the user is a guest."""
        return self.guest

    def is_authenticated(self):
        """Return True if user is a authenticated user."""
        return True if self.email else False

    def is_active(self):
        """Return True if use is active."""
        return True


def get_groups_user_not_joined(id_user, group_name=None):
    """Return the list of group that user not joined."""
    query = Usergroup.query.outerjoin(
        Usergroup.users).filter(
            Usergroup.id.notin_(
                db.select([UserUsergroup.id_usergroup],
                          UserUsergroup.id_user == id_user)))
    if group_name:
        query = query.filter(Usergroup.name.like(group_name))
    return query


class Usergroup(db.Model):

    """Represent a Usergroup record."""

    def __str__(self):
        """Return string representation."""
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
                     server_default='', unique=True, index=True)
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

    @property
    def login_method_is_external(self):
        """Return True if the group is external."""
        return self.login_method == Usergroup.LOGIN_METHODS['EXTERNAL']

    def join(self, user, status=None):
        """Join user to group.

        :param user: User to add into the group.
        :param status: status of user
        """
        # if I want to join another user from the group
        if(user.id != current_user.get_id()
           # I need to be an admin of the group
           and not self.is_admin(current_user.get_id())):
            raise AccountSecurityError(
                'Not enough right to '
                'add user "{0}" from group "{1}"'
                .format(user.nickname, self.name))

        # join group
        self.users.append(
            UserUsergroup(
                id_user=user.id,
                user_status=status or self.new_user_status,
            )
        )
        try:
            db.session.commit()
        except:
            db.session.rollback()
            raise

    def leave(self, user):
        """Remove user from group.

        :param user: User to remove from the group.
        """
        # if I want to remove another user from the group
        if(user.id != current_user.get_id()
           # I need to be an admin of the group
           and not self.is_admin(current_user.get_id())):
            raise AccountSecurityError(
                'Not enough right to '
                'remove user "{0}" from group "{1}"'
                .format(user.nickname, self.name))

        # check that I'm not the last admin before leaving the group.
        if self.is_admin(user.id) and self.admins.count() == 1:
            raise IntegrityUsergroupError(
                'User can leave the group '
                'without admins, please delete the '
                'group if you want to leave.')

        # leave the group
        UserUsergroup.query.filter_by(
            id_usergroup=self.id,
            id_user=user.id,
        ).delete()
        try:
            db.session.commit()
        except:
            db.session.rollback()
            raise

    def is_admin(self, id_user):
        """Return True if the user is an admin of the group."""
        return db.session.query(self.admins.filter(
            UserUsergroup.id_user == id_user).exists()).scalar()

    def get_users_not_in_this_group(self, nickname=None, email=None,
                                    limit=None):
        """Return users that not joined this group."""
        # base query
        query = User.query.outerjoin(User.usergroups).filter(
            User.id.notin_(db.select([UserUsergroup.id_user],
                           UserUsergroup.id_usergroup == self.id)))
        # additional optional filters
        if nickname:
            query = query.filter(User.nickname.like(nickname))
        if email:
            query = query.filter(User.email.like(email))
        if limit:
            query = query.limit(limit)
        # return results
        return query

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
        """Return string representation."""
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
                                 default=datetime.now,
                                 onupdate=datetime.now)
    user = db.relationship(
        User,
        backref=db.backref('usergroups'))
    usergroup = db.relationship(
        Usergroup,
        backref=db.backref('users', cascade="all, delete-orphan"))

    def is_admin(self):
        """Return True if user is a admin."""
        return self.user_status == self.USER_STATUS['ADMIN']

# define query to get admins
Usergroup.admins = db.relationship(
    UserUsergroup,
    lazy="dynamic",
    primaryjoin=db.and_(
        Usergroup.id == UserUsergroup.id_usergroup,
        UserUsergroup.user_status == UserUsergroup.USER_STATUS['ADMIN']))


class UserEXT(db.Model):

    """Represent a UserEXT record."""

    __tablename__ = 'userEXT'

    id = db.Column(db.VARBINARY(255), primary_key=True, nullable=False)
    method = db.Column(db.String(50), primary_key=True, nullable=False)
    id_user = db.Column(db.Integer(15, unsigned=True),
                        db.ForeignKey(User.id), nullable=False)

    user = db.relationship(User, backref="external_identifiers")

    __table_args__ = (db.Index('id_user', id_user, method, unique=True),
                      db.Model.__table_args__)

__all__ = ['User',
           'Usergroup',
           'UserUsergroup',
           'UserEXT']
