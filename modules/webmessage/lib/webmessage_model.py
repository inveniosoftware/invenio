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
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
WebMessage database models.
"""

# General imports
from invenio.sqlalchemyutils import db

# Create your models here.
from invenio.websession_model import User
from invenio.webmessage_config import CFG_WEBMESSAGE_SEPARATOR

class MsgMESSAGE(db.Model):
    """Represents a MsgMESSAGE record."""
    def __init__(self):
        pass
    def __repr__(self):
        return "From: %s<%s>, Subject: <%s> %s" % (self.user_from.nickname,
            self.user_from.email, self.subject, self.body)
    __tablename__ = 'msgMESSAGE'
    id = db.Column(db.Integer(15, unsigned=True), nullable=False,
                primary_key=True,
                autoincrement=True)
    id_user_from = db.Column(db.Integer(15, unsigned=True),
                db.ForeignKey(User.id),
                nullable=False, server_default='0')
    sent_to_user_nicks = db.Column(db.Text, nullable=False)
    sent_to_group_names = db.Column(db.Text, nullable=False)
    subject = db.Column(db.Text, nullable=False)
    body = db.Column(db.Text, nullable=True)
    sent_date = db.Column(db.DateTime, nullable=False,
        server_default='0000-00-00 00:00:00')
    received_date = db.Column(db.DateTime,
        server_default='0000-00-00 00:00:00')
    user_from = db.relationship(User, backref='sent_messages')

    @property
    def user_nicks(self):
        return self.sent_to_user_nicks.split(CFG_WEBMESSAGE_SEPARATOR)

    @property
    def group_names(self):
        return self.sent_to_group_names.split(CFG_WEBMESSAGE_SEPARATOR)

class UserMsgMESSAGE(db.Model):
    """Represents a UserMsgMESSAGE record."""
    def __init__(self):
        pass
    __tablename__ = 'user_msgMESSAGE'
    id_user_to = db.Column(db.Integer(15, unsigned=True),
                db.ForeignKey(User.id), nullable=False,
                server_default='0', primary_key=True)
    id_msgMESSAGE = db.Column(db.Integer(15, unsigned=True),
                db.ForeignKey(MsgMESSAGE.id),
                nullable=False, server_default='0',
                primary_key=True)
    status = db.Column(db.Char(1), nullable=False,
                server_default='N')
    user_to = db.relationship(User, backref='received_messages')
    message = db.relationship(MsgMESSAGE, backref='sent_to_users')
