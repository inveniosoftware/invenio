# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2015 CERN.
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

"""WebMessage User Settings"""

from flask import url_for, current_app
from flask_login import current_user

from invenio.base.i18n import _
from invenio.ext.sqlalchemy import db
from invenio.ext.template import render_template_to_string
from invenio.modules.dashboard.settings import Settings, UserSettingsStorage

from .models import UserMsgMESSAGE
from .forms import WebMessageUserSettingsForm


class WebMessageSettings(Settings):

    keys = ['webmessage_email_alert']
    storage_builder = UserSettingsStorage
    form_builder = WebMessageUserSettingsForm

    def __init__(self):
        super(WebMessageSettings, self).__init__()
        self.icon = 'envelope'
        self.title = _('Messages')
        self.view = url_for('webmessage.index')
        self.edit = url_for('webaccount.edit', name=self.name)

    def commit(self):
        pass

    def widget(self):
        uid = current_user.get_id()
        unread = db.session.query(db.func.count(UserMsgMESSAGE.id_msgMESSAGE)).\
            filter(db.and_(
                UserMsgMESSAGE.id_user_to == uid,
                UserMsgMESSAGE.status == current_app.config[
                    'CFG_WEBMESSAGE_STATUS_CODE']['NEW']
            )).scalar()

        total = db.session.query(db.func.count(UserMsgMESSAGE.id_msgMESSAGE)).\
            filter(
                UserMsgMESSAGE.id_user_to == uid
            ).scalar()

        template = """
{{  _("You have %(x_num_new)d new messages out of %(x_num_total)d messages.",
      x_num_new=unread, x_num_total=total) }}
"""
        return render_template_to_string(template, _from_string=True,
                    unread=unread, total=total)

    widget.size = 4

    @property
    def is_authorized(self):
        return current_user.is_authenticated() and \
               current_user.is_authorized('usemessages')

# Compulsory plugin interface
settings = WebMessageSettings
#__all__ = ['WebMessageSettings']
