# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011 CERN.
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

"""WebMessage Forms"""

from string import strip

from invenio.base.globals import cfg
from invenio.modules.messages.config import CFG_WEBMESSAGE_MAX_SIZE_OF_MESSAGE
from invenio.ext.sqlalchemy import db
from invenio.modules.accounts.models import User, Usergroup
from invenio.base.i18n import _
from invenio.utils.forms import InvenioBaseForm, FilterForm, DateTimePickerWidget, FilterTextField
from wtforms import DateTimeField, BooleanField, TextField, TextAreaField, \
                    PasswordField, RadioField, validators


def msg_split_addr(value):
    """Split message address value."""
    if not value:
        return []
    return filter(len, map(strip,
        value.split(cfg['CFG_WEBMESSAGE_SEPARATOR'])))


def validate_user_nicks(form, field):
    """Finds not valid users."""
    if field.data:
        test = set(msg_split_addr(field.data))
        comp = set([u for u, in db.session.query(User.nickname).\
            filter(User.nickname.in_(test)).all()])
        diff = test.difference(comp)
        if len(diff)>0:
            raise validators.ValidationError(
                _('Not valid users: %{diff}s', diff=', '.join(diff)))


def validate_group_names(form, field):
    """Finds not valid usergroups."""
    if field.data:
        test = set(msg_split_addr(field.data))
        comp = set([u for u, in db.session.query(Usergroup.name).\
            filter(Usergroup.name.in_(test)).all()])
        diff = test.difference(comp)
        if len(diff)>0:
            raise validators.ValidationError(
                _('Not valid groups: %s') % (', '.join(diff)))


class AddMsgMESSAGEForm(InvenioBaseForm):
    """Defines form for writing new message."""
    sent_to_user_nicks = TextField(_('Users'), [validate_user_nicks])
    sent_to_group_names = TextField(_('Groups'), [validate_group_names])
    subject = TextField(_('Subject'))
    body = TextAreaField(_('Message'), [
        validators.length(
            0, CFG_WEBMESSAGE_MAX_SIZE_OF_MESSAGE,
             message = _(
                "Your message is too long, please edit it. "
                "Maximum size allowed is %{length}i characters.",
                length=CFG_WEBMESSAGE_MAX_SIZE_OF_MESSAGE
            )
        )
    ])
    received_date = DateTimeField(_('Send later'), [validators.optional()],
                                  widget=DateTimePickerWidget())

    def validate_sent_to_user_nicks(self, field):
        """Checks whenever user nickname or group name was posted."""
        if len(msg_split_addr(self.sent_to_user_nicks.data)) == 0 and \
            len(msg_split_addr(self.sent_to_group_names.data)) == 0:
            raise validators.ValidationError(
                _('Enter a valid user nick or group name.'))


class FilterMsgMESSAGEForm(FilterForm):
    """Defines form for filter messages."""

    def __init__(self, *args, **kwargs):
        # This is trick how to use dot syntax in filter.
        from werkzeug.datastructures import MultiDict, CombinedMultiDict
        args = [MultiDict((k,l) for (k,l) in i.iteritems(True) if l!='') for i in list(args)]
        super(FilterMsgMESSAGEForm, self).__init__(*args, **kwargs)
        for n, f in self._fields.iteritems():
            if hasattr(f, 'alias') and f.alias:
                new = args[0].getlist(f.alias, None)
                if new is not None:
                    new.reverse()
                    f.raw_data = new
                f.name = f.alias

    nickname = FilterTextField(_('From'), alias='user_from.nickname')
    #sent_date = FilterTextField(_('Sent date'))
    subject = FilterTextField(_('Subject'))
    #body = TextAreaField(_('Body'))


class WebMessageUserSettingsForm(InvenioBaseForm):
    webmessage_email_alert = RadioField(_('Email notifications'),
    choices=[(0, _('Disable')), (1, _('Enable'))])

