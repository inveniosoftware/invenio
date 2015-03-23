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

"""WebBasket User Settings"""

from invenio.base.i18n import _
from invenio.ext.template import render_template_to_string
from flask_login import current_user
from invenio.modules.dashboard.settings import Settings, UserSettingsStorage
from invenio.legacy.webbasket.db_layer import get_all_personal_baskets_names


class WebBasketSettings(Settings):

    keys = []
    #form_builder = WebBasketUserSettingsForm
    storage_builder = UserSettingsStorage

    def __init__(self):
        super(WebBasketSettings, self).__init__()
        self.icon = 'shopping-cart'
        self.title = _('Your Baskets')
        self.view = '/yourbaskets'
        #self.edit = url_for('webaccount.edit', name=self.name)

    def widget(self):
        uid = current_user.get_id()

        baskets = []

        if(uid is not None and uid != 0):
            # list of tuples: (bskid, bsk_name, topic)
            bsk_from_db = get_all_personal_baskets_names(uid)

            baskets = [{'name': name, 'bskid': bskid}
                       for (bskid, name, dummy_topic) in bsk_from_db]

        template = """
{{ _('You have') }}
<div class="btn-group">
  <a class="btn dropdown-toggle" data-toggle="dropdown" href="#">
     <strong class="text-info">{{ baskets|length }}</strong>
     {{ _('personal baskets') }}
    <span class="caret"></span>
  </a>
  <ul class="dropdown-menu">
  {%- for b in baskets -%}
    <li>
        <a href="/yourbaskets/display?bskid={{ b.bskid }}">
            {{ b.name }}
        </a>
    </li>
  {%- endfor -%}
  </ul>
</div>"""

        # If the list is too long ( >= 2 items! ),
        # it will not be properlt displayed
        # (it appears that the list cannot be displayed outside the
        #  box, so the rest is cut off)

        return render_template_to_string(template, _from_string=True,
                                         baskets=baskets)

    widget.size = 4

    @property
    def is_authorized(self):
        return current_user.is_authenticated() and \
               current_user.is_authorized('usebaskets')

# Compulsory plugin interface
settings = WebBasketSettings
#__all__ = ['WebBasketSettings']
