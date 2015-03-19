# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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

"""
    invenio.modules.workflows.views.settings
    ----------------------------------------

    Represents the Holding Pen on user settings page with overview
    over any actions assigned to user.

    WORK IN PROGRESS
"""

from __future__ import absolute_import

from flask import Blueprint, render_template, request
#from flask import redirect, url_for
from flask_login import login_required
from flask_breadcrumbs import register_breadcrumb
from flask_menu import register_menu
from invenio.base.i18n import _
from .holdingpen import get_holdingpen_objects, get_action_list

blueprint = Blueprint(
    'workflows_settings',
    __name__,
    url_prefix="/account/settings/workflows",
    static_folder="../static",
    template_folder="../templates",
)


@blueprint.route("/", methods=['GET', 'POST'])
@login_required
@register_menu(
    blueprint, 'settings.workflows',
    _('%(icon)s Your actions', icon='<i class="fa fa-list-alt fa-fw"></i>'),
    order=3,
    active_when=lambda: request.endpoint.startswith("workflows_settings.")
)
@register_breadcrumb(
    blueprint, 'breadcrumbs.settings.workflows', _('Your actions')
)
def index():
    bwolist = get_holdingpen_objects()
    action_list = get_action_list(bwolist)

    return render_template(
        "workflows/settings/index.html",
        tasks=action_list
    )
