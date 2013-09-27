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
WebSession database models.
"""

# General imports.
from invenio.ext.sqlalchemy import db
from sqlalchemy.ext.hybrid import hybrid_property
# Create your models here.


def get_default_user_preferences():
    from invenio.access_control_config import CFG_EXTERNAL_AUTHENTICATION, \
        CFG_EXTERNAL_AUTH_DEFAULT

    user_preference = {
        'login_method': ''}

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
    """Represents a Usergroup record."""
    def __str__(self):
        return "%s <%s>" % (self.name, self.description)
    __tablename__ = 'usergroup'
    #FIXME Unique(login_method(70), name)
    id = db.Column(db.Integer(15, unsigned=True),
                nullable=False,
                primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False,
                server_default='', index=True)
    description = db.Column(db.Text, nullable=True)
    join_policy = db.Column(db.CHAR(2), nullable=False,
                server_default='')
    login_method = db.Column(db.String(255), nullable=False,
                server_default='INTERNAL')
    #all_users = db.relationship(User, secondary=lambda: UserUsergroup.__table__,
    #                       collection_class=set)

    __table_args__ = (db.Index('login_method_name', login_method, name,
                               mysql_length=[60, None]),
                      db.Model.__table_args__)

class UserUsergroup(db.Model):
    """Represents a UserUsergroup record."""
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
    user_status = db.Column(db.CHAR(1), nullable=False,
                server_default='')
    user_status_date = db.Column(db.DateTime, nullable=False,
                server_default='1900-01-01 00:00:00')
    user = db.relationship(User, backref='usergroups')
    usergroup = db.relationship(Usergroup, backref='users')


class UserEXT(db.Model):
    """Represents a UserEXT record."""
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
