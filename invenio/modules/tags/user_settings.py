# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2015 CERN.
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

"""WebTag User Settings"""

# Flask
from flask import url_for
from invenio.ext.template import render_template_to_string
from invenio.base.i18n import _
from flask_login import current_user
from invenio.modules.dashboard.settings import \
    Settings, \
    UserSettingsAttributeStorage

# Related models
from invenio.modules.accounts.models import User
from invenio.modules.records.models import Record as Bibrec

# Internal
from .models import WtgTAG, WtgTAGRecord
from .forms import WebTagUserSettingsForm


class WebTagSettings(Settings):

    keys = \
        [
            'display_tags',
            'display_tags_group',
            'display_tags_public',
        ]

    form_builder = WebTagUserSettingsForm
    storage_builder = UserSettingsAttributeStorage('webtag')

    def __init__(self):
        super(WebTagSettings, self).__init__()
        self.icon = 'tags'
        self.title = _('Tags')
        self.view = url_for('webtag.display_cloud')
        self.edit = url_for('webaccount.edit', name=self.name)

    def widget(self):
        user = User.query.get(current_user.get_id())
        tag_count = user.tags_query.count()

        record_count = Bibrec.query.join(WtgTAGRecord)\
            .join(WtgTAG)\
            .filter(WtgTAG.user == user).count()

        return render_template_to_string(
            'tags/user_settings.html',
            tag_count=tag_count,
            record_count=record_count)

    widget.size = 4

    @property
    def is_authorized(self):
        return current_user.is_authenticated()
               # and current_user.is_authorized('usebaskets')

# Compulsory plugin interface
settings = WebTagSettings
