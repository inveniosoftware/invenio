
# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2014, 2015 CERN.
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

"""WebSearch User Settings."""

from flask import url_for
from flask_login import current_user
from invenio.base.i18n import _
from invenio.ext.sqlalchemy import db
from invenio.ext.template import render_template_to_string
from .models import UserQuery
from .forms import WebSearchUserSettingsForm
from invenio.modules.dashboard.settings import Settings, UserSettingsStorage


class WebSearchSettings(Settings):

    """WebSearch User Settings."""

    keys = ['rg', 'websearch_hotkeys', 'c', 'of']
    form_builder = WebSearchUserSettingsForm
    storage_builder = UserSettingsStorage

    def __init__(self):
        super(WebSearchSettings, self).__init__()
        self.icon = 'search'
        self.title = _('Searches')
        self.view = '/youralerts/display'  # FIXME url_for('youralerts.index')
        self.edit = url_for('webaccount.edit', name=self.name)

    def widget(self):
        """Display search settings widget."""
        uid = current_user.get_id()
        queries = db.session.query(db.func.count(UserQuery.id_query)).filter(
            UserQuery.id_user == uid
            ).scalar()

        template = """
{{ _('You have made %(x_num_queries)d queries. A detailed list is available with a possibility to
(a) view search results and (b) subscribe to an automatic email alerting service
for these queries.', x_num_queries=queries) }}
"""

        return render_template_to_string(template, _from_string=True,
                                         queries=queries)

    widget.size = 4

    @property
    def is_authorized(self):
        return not current_user.is_guest

# Compulsory plugin interface
settings = WebSearchSettings
#__all__ = ['WebSearchSettings']
