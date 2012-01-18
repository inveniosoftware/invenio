# -*- coding: utf-8 -*-
#
## Author: Jiri Kuncar <jiri.kuncar@gmail.com> 
##
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
from invenio.sqlalchemyutils import db

# Create your models here.

class User(db.Model):
    """Represents a User record."""
    def __init__(self):
        pass
    def __repr__(self):
        return "%s <%s>" % (self.nickname, self.email)
    __tablename__ = 'user'
    id = db.Column(db.Integer(15, unsigned=True),
                primary_key=True,
                autoincrement=True)
    email = db.Column(db.String(255), nullable=False,
                server_default='')
    password = db.Column(db.iBinary, nullable=False)
    note = db.Column(db.String(255), nullable=True)
    settings = db.Column(db.iBinary, nullable=True)
    nickname = db.Column(db.String(255), nullable=False,
                server_default='')
    last_login = db.Column(db.DateTime, nullable=False,
        server_default='0000-00-00 00:00:00')

class Usergroup(db.Model):
    """Represents a Usergroup record."""
    def __init__(self):
        pass
    def __repr__(self):
        return "%s <%s>" % (self.name, self.description)
    __tablename__ = 'usergroup'
    id = db.Column(db.Integer(15, unsigned=True),
                nullable=False,
                primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False,
                server_default='')
    description = db.Column(db.Text, nullable=True)
    join_policy = db.Column(db.Char(2), nullable=False,
                server_default='')
    login_method = db.Column(db.String(255), nullable=False,
                server_default='INTERNAL')

class UserUsergroup(db.Model):
    """Represents a UserUsergroup record."""
    def __init__(self):
        pass
    def __repr__(self):
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
    user_status = db.Column(db.Char(1), nullable=False,
                server_default='')
    user_status_date = db.Column(db.DateTime, nullable=False,
                server_default='0000-00-00 00:00:00')
    user = db.relationship(User, backref='usergroups')
    usergroup = db.relationship(Usergroup, backref='users')

class Session(db.Model):
    """Represents a Session record."""
    def __init__(self):
        pass
    __tablename__ = 'session'
    session_key = db.Column(db.String(32), nullable=False,
                server_default='', primary_key=True)
    session_expiry = db.Column(db.Integer(11, unsigned=True), nullable=False,
                server_default='0')
    session_object = db.Column(db.iBinary, nullable=True)
    uid = db.Column(db.Integer(15, unsigned=True),
                nullable=False)

