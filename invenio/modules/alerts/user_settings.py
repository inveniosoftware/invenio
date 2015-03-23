# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2015 CERN.
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

"""WebAlert User Settings"""

from invenio.base.i18n import _
from invenio.ext.template import render_template_to_string
from invenio.modules.alerts.models import UserQueryBasket
from flask_login import current_user
from invenio.modules.dashboard.settings import Settings, UserSettingsStorage

class WebAlertSettings(Settings):

    keys = ['webalert_email_notification']
    #form_builder = WebAlertUserSettingsForm
    storage_builder = UserSettingsStorage

    def __init__(self):
        super(WebAlertSettings, self).__init__()
        self.storage = {} #User.query.get(current_user.get_id()).settings
        self.icon = 'bell'
        self.title = _('Alerts WIP')
        #self.view = url_for('webalert.index')
        #self.edit = url_for('webaccount.edit', name=self.name)

    def widget(self):
        uid = current_user.get_id()
        query_baskets = UserQueryBasket.query.filter(
            UserQueryBasket.id_user == uid
            ).all()

        template = """
{{ _('You own the following') }}
<div class="btn-group">
  <a class="btn dropdown-toggle" data-toggle="dropdown" href="#">
     <strong class="text-info">{{ query_baskets|length }}</strong>
     {{ _('alerts') }}
    <span class="caret"></span>
  </a>
  <ul class="dropdown-menu">
  {%- for a in query_baskets -%}
    <li>
        <a href="#">
            {{ a.alert_name }}
        </a>
    </li>
  {%- endfor -%}
  </ul>
</div>"""

        return render_template_to_string(template, _from_string=True,
                                         query_baskets=query_baskets)

    widget.size = 4

    @property
    def is_authorized(self):
        return current_user.is_authenticated() and \
               current_user.is_authorized('usealerts')

# Compulsory plugin interface
settings = WebAlertSettings
#__all__ = ['WebAlertSettings']
