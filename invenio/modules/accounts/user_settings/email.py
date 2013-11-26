# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012, 2013 CERN.
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

"""WebAccount User Settings"""

from flask import url_for, g
from invenio.modules.accounts.models import User
from flask.ext.login import current_user
from invenio.ext.template import render_template_to_string
from invenio.modules.dashboard.settings import Settings, ModelSettingsStorageBuilder
from invenio.modules.accounts.forms import ChangeUserEmailSettingsForm


class WebAccountSettings(Settings):

    keys = ['email']
    form_builder = ChangeUserEmailSettingsForm
    storage_builder = ModelSettingsStorageBuilder(
        lambda: User.query.get(current_user.get_id()))

    def __init__(self):
        super(WebAccountSettings, self).__init__()
        self.icon = 'user'
        self.title = g._('Account')
        self.edit = url_for('webaccount.edit', name=self.name)

    def widget(self):
        return render_template_to_string('accounts/widget.html')

    widget.size = 4

    @property
    def is_authorized(self):
        return current_user.is_authenticated()

## Compulsory plugin interface
settings = WebAccountSettings
#__all__ = ['WebAccountSettings']
