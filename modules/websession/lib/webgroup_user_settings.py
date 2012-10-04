# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012 CERN.
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

"""WebAccount Flask Blueprint"""

from flask import Blueprint, session, make_response, g, render_template, \
                  request, flash, jsonify, redirect, url_for, current_app
from invenio.websession_model import User, Usergroup, UserUsergroup
from invenio.webinterface_handler_flask_utils import _
from invenio.webinterface_handler import wash_urlargd
from invenio.config import CFG_SITE_LANG
from invenio.access_control_config import \
     CFG_EXTERNAL_AUTH_USING_SSO, \
     CFG_EXTERNAL_AUTH_LOGOUT_SSO

from invenio.websession_config import CFG_WEBSESSION_INFO_MESSAGES, \
      CFG_WEBSESSION_USERGROUP_STATUS, \
      CFG_WEBSESSION_GROUP_JOIN_POLICY, \
      InvenioWebSessionError, \
      InvenioWebSessionWarning

from invenio.sqlalchemyutils import db
from invenio.jinja2utils import render_template_to_string
from invenio.webuser_flask import current_user
from invenio.settings import Settings

class WebGroupSettings(Settings):


    def __init__(self):
        super(WebGroupSettings, self).__init__()
        self.icon = 'tags'
        self.title = _('Group')
        self.view = url_for('yourgroups.index')
        self.edit = url_for('yourgroups.index')

    def widget(self):
        uid = current_user.get_id()
        usergroups = UserUsergroup.query.filter(
            UserUsergroup.id_user == uid
            ).all()

        template = """
{%- if usergroups -%}
{{ _('You are involved in following groups:') }}
<div>
  {%- for ug in usergroups -%}
  <span class="label">
    {{ ug.usergroup.name }}
  </span>
  {%- endfor -%}
</div>
{%- else -%}
{{ _('You are not involved in any group.') }}
{%- endif -%}
"""

        rv = render_template_to_string(template, _from_string=True,
                                       usergroups=usergroups)
        return rv

    widget.size = 4

    @property
    def is_authorized(self):
        return current_user.is_authenticated() and \
               current_user.is_authorized('usegroups')

## Compulsory plugin interface
settings = WebGroupSettings
#__all__ = ['WebMessageSettings']
