# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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

"""WebMessage User Settings"""

from flask import Blueprint, session, make_response, g, render_template, \
                  request, flash, jsonify, redirect, url_for, current_app
from invenio.websession_model import User, Usergroup, UserUsergroup
from invenio.webinterface_handler_flask_utils import _

from invenio.webmessage_config import CFG_WEBMESSAGE_ROLES_WITHOUT_QUOTA, \
                                      CFG_WEBMESSAGE_STATUS_CODE, \
                                      CFG_WEBMESSAGE_SEPARATOR, \
                                      CFG_WEBMESSAGE_EMAIL_ALERT

from invenio.sqlalchemyutils import db
from invenio.jinja2utils import render_template_to_string
from invenio.settings import Settings, UserSettingsStorage, \
                             ModelSettingsStorageBuilder
from invenio.webmessage_model import MsgMESSAGE, UserMsgMESSAGE
from invenio.webmessage_forms import WebMessageUserSettingsForm
from invenio.webuser_flask import current_user

class WebMessageSettings(Settings):

    keys = ['webmessage_email_alert']
    storage_builder = UserSettingsStorage
    form_builder = WebMessageUserSettingsForm

    def __init__(self):
        super(WebMessageSettings, self).__init__()
        self.icon = 'envelope'
        self.title = _('Messages')
        self.view = url_for('yourmessages.index')
        if True or CFG_WEBMESSAGE_EMAIL_ALERT:
            self.edit = url_for('youraccount.edit',
                                name=__name__.split('.')[-1])

    def commit(self):
        pass

    def widget(self):
        uid = current_user.get_id()
        unread = db.session.query(db.func.count(UserMsgMESSAGE.id_msgMESSAGE)).\
            filter(db.and_(
                UserMsgMESSAGE.id_user_to == uid,
                UserMsgMESSAGE.status == CFG_WEBMESSAGE_STATUS_CODE['NEW']
            )).scalar()

        total = db.session.query(db.func.count(UserMsgMESSAGE.id_msgMESSAGE)).\
            filter(
                UserMsgMESSAGE.id_user_to == uid
            ).scalar()

        template = """
{{  _("You have %d new messages out of %d messages.") | format(unread, total) }}
"""
        return render_template_to_string(template, _from_string=True,
                    unread=unread, total=total)

    widget.size = 4

    @property
    def is_authorized(self):
        return current_user.is_authenticated() and \
               current_user.is_authorized('usemessages')

## Compulsory plugin interface
settings = WebMessageSettings
#__all__ = ['WebMessageSettings']
