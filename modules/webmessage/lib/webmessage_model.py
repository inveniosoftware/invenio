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

"""
WebMessage database models.
"""

# General imports
from invenio.sqlalchemyutils import db

# Create your models here.
from string import strip
from invenio.websession_model import User, Usergroup
from invenio.webmessage_config import CFG_WEBMESSAGE_SEPARATOR

from sqlalchemy.ext.associationproxy import association_proxy

class MsgMESSAGE(db.Model):
    """Represents a MsgMESSAGE record."""
    def __str__(self):
        return "From: %s<%s>, Subject: <%s> %s" % \
            (self.user_from.nickname or _('None'),
            self.user_from.email or _('unknown'),
            self.subject, self.body)
    __tablename__ = 'msgMESSAGE'
    id = db.Column(db.Integer(15, unsigned=True), nullable=False,
                primary_key=True,
                autoincrement=True)
    id_user_from = db.Column(db.Integer(15, unsigned=True),
                db.ForeignKey(User.id),
                nullable=True, server_default='0')
    _sent_to_user_nicks = db.Column(db.Text, name='sent_to_user_nicks',
                nullable=False)
    _sent_to_group_names = db.Column(db.Text, name='sent_to_group_names',
                nullable=False)
    subject = db.Column(db.Text, nullable=False)
    body = db.Column(db.Text, nullable=True)
    sent_date = db.Column(db.DateTime, nullable=False,
        server_default='0001-01-01 00:00:00') # db.func.now() -> 'NOW()'
    received_date = db.Column(db.DateTime,
        server_default='0001-01-01 00:00:00')
    user_from = db.relationship(User, backref='sent_messages')
    #recipients = db.relationship(User,
    #                             secondary=lambda: UserMsgMESSAGE.__table__,
    #                             collection_class=set)

    recipients = association_proxy('sent_to_users', 'user_to',
            creator=lambda u:UserMsgMESSAGE(user_to=u))

    @db.hybrid_property
    def sent_to_user_nicks(self):
        """ Alias for column 'sent_to_user_nicks'. """
        return self._sent_to_user_nicks

    @db.hybrid_property
    def sent_to_group_names(self):
        """ Alias for column 'sent_to_group_names'. """
        return self._sent_to_group_names

    @db.validates('_sent_to_user_nicks')
    def validate_sent_to_user_nicks(self, key, value):
        user_nicks = filter(len, map(strip,
            value.split(CFG_WEBMESSAGE_SEPARATOR)))
        assert len(user_nicks) == len(set(user_nicks))
        if len(user_nicks) > 0:
            assert len(user_nicks) == \
                User.query.filter(User.nickname.in_(user_nicks)).count()
        return CFG_WEBMESSAGE_SEPARATOR.join(user_nicks)

    @db.validates('_sent_to_group_names')
    def validate_sent_to_group_names(self, key, value):
        group_names = filter(len, map(strip,
            value.split(CFG_WEBMESSAGE_SEPARATOR)))
        assert len(group_names) == len(set(group_names))
        if len(group_names) > 0:
            assert len(group_names) == \
                Usergroup.query.filter(Usergroup.name.in_(group_names)).count()
        return CFG_WEBMESSAGE_SEPARATOR.join(group_names)


    @sent_to_user_nicks.setter
    def sent_to_user_nicks(self, value):
        old_user_nicks = self.user_nicks
        self._sent_to_user_nicks = value
        to_add = set(self.user_nicks)-set(old_user_nicks)
        to_del = set(old_user_nicks)-set(self.user_nicks)
        if len(self.group_names):
            to_del = to_del-set([u.nickname for u in User.query.\
                join(User.usergroups).filter(
                Usergroup.name.in_(self.group_names)).\
                all()])
        if len(to_del):
            is_to_del = lambda u: u.nickname in to_del
            remove_old = filter(is_to_del, self.recipients)
            for u in remove_old:
                self.recipients.remove(u)
        if len(to_add):
            for u in User.query.filter(User.nickname.\
                in_(to_add)).all():
                if u not in self.recipients:
                    self.recipients.append(u)

    @sent_to_group_names.setter
    def sent_to_group_names(self, value):
        old_group_names = self.group_names
        self._sent_to_group_names = value
        groups_to_add = set(self.group_names)-set(old_group_names)
        groups_to_del = set(old_group_names)-set(self.group_names)
        if len(groups_to_del):
            to_del = set([u.nickname for u in User.query.\
                join(User.usergroups).filter(
                Usergroup.name.in_(groups_to_del)).\
                all()])-set(self.user_nicks)
            is_to_del = lambda u: u.nickname in to_del
            remove_old = filter(is_to_del, self.recipients)
            for u in remove_old:
                self.recipients.remove(u)
        if len(groups_to_add):
            for u in User.query.join(User.usergroups).filter(db.and_(
                Usergroup.name.in_(groups_to_add),
                db.not_(User.nickname.in_(self.user_nicks)))).all():
                if u not in self.recipients:
                    self.recipients.append(u)

    @property
    def user_nicks(self):
        if not self._sent_to_user_nicks:
            return []
        return filter(len, map(strip,
            self._sent_to_user_nicks.split(CFG_WEBMESSAGE_SEPARATOR)))

    @property
    def group_names(self):
        if not self._sent_to_group_names:
            return []
        return filter(len, map(strip,
            self.sent_to_group_names.split(CFG_WEBMESSAGE_SEPARATOR)))


#TODO consider moving following lines to separate file.

from invenio.webmessage_config import CFG_WEBMESSAGE_EMAIL_ALERT
from invenio.config import CFG_WEBCOMMENT_ALERT_ENGINE_EMAIL
from invenio.mailutils import send_email, scheduled_send_email
from invenio.jinja2utils import render_template_to_string
from invenio.dateutils import datetext_format
from datetime import datetime

def email_alert(mapper, connection, target):
    """ Sends email alerts to message recipients. """
    m = target
    is_reminder =  m.received_date is not None \
                   and m.received_date > datetime.now()

    alert = send_email
    if is_reminder:
        alert = lambda *args, **kwargs: scheduled_send_email(*args,
                    other_bibtasklet_arguments=[
                        m.received_date.strftime(datetext_format)],
                    **kwargs)

    for u in m.recipients:
        if isinstance(u.settings, dict) and \
            u.settings.get('webmessage_email_alert', True):
            try:
                alert(
                    CFG_WEBCOMMENT_ALERT_ENGINE_EMAIL,
                    u.email,
                    subject = m.subject,
                    content = render_template_to_string(
                            'webmessage_email_alert.html',
                            message=m, user=u))
            except:
                # FIXME tests are not in request context
                pass


if CFG_WEBMESSAGE_EMAIL_ALERT:
    from sqlalchemy import event
    # Register after insert callback.
    event.listen(MsgMESSAGE, 'after_insert', email_alert)


class UserMsgMESSAGE(db.Model):
    """Represents a UserMsgMESSAGE record."""
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
    user_to = db.relationship(User, backref='received_messages',
                              collection_class=set)
    message = db.relationship(MsgMESSAGE, backref='sent_to_users',
                              collection_class=set)

__all__ = ['MsgMESSAGE',
           'UserMsgMESSAGE']
