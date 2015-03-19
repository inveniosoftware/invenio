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

"""Cloud Connector User Settings"""

from flask import url_for
from flask_login import current_user

from invenio.base.i18n import _
#from invenio.ext.sqlalchemy import db
#from invenio.ext.template import render_template_to_string
from invenio.modules.dashboard.settings import Settings, \
    UserSettingsAttributeStorage


class CloudConnectorSettings(Settings):

    @property
    def keys(self):
        return [] #FIXME enabled services

    storage_builder = UserSettingsAttributeStorage('cloudutils_settings')
    #form_builder = FIXME

    def __init__(self):
        super(self.__class__, self).__init__()
        self.icon = 'file'
        self.title = _('Cloud Connections')
        self.view = url_for('cloudutils.index')

    def widget(self):
        return 'TODO'

    widget.size = 4

    @property
    def is_authorized(self):
        return current_user.is_authenticated()

# Compulsory plugin interface
settings = CloudConnectorSettings
#__all__ = ['WebMessageSettings']
