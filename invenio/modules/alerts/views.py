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

"""Alert interface."""

# Flask
from flask import render_template, request, Blueprint
from flask.ext.breadcrumbs import default_breadcrumb_root, register_breadcrumb
from flask.ext.login import current_user, login_required
from flask.ext.menu import register_menu

# Internal imports
from invenio.base.i18n import _
from invenio.modules.search.models import UserQuery

from .models import UserQueryBasket

blueprint = Blueprint('alerts', __name__, url_prefix='/youralerts',
                      template_folder='templates', static_folder='static')

default_breadcrumb_root(blueprint, '.settings.alerts')


@blueprint.route('/', methods=['GET', 'POST'])
@blueprint.route('/display2', methods=['GET', 'POST'])
@login_required
@register_menu(
    blueprint, 'settings.alerts',
    _('%(icon)s Search Alerts', icon='<i class="fa fa-search fa-fw"></i>'),
    order=10,
    active_when=lambda: request.endpoint.startswith("alerts.")
)
@register_breadcrumb(blueprint, '.index', _('Your Searches'))
def index():
    """List users' search queries."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    return render_template(
        'alerts/index.html',
        queries=UserQuery.query.join(UserQuery.webquery).filter(
            UserQuery.id_user == current_user.get_id()
        ).paginate(page, per_page)
    )


@blueprint.route('/', methods=['GET', 'POST'])
@blueprint.route('/display2', methods=['GET', 'POST'])
@login_required
@register_breadcrumb(blueprint, '.', _('Search Alerts'))
def list():
    """List users' search alerts."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    return render_template(
        'alerts/list.html',
        alerts=UserQueryBasket.query.filter(
            UserQueryBasket.id_user == current_user.get_id()
        ).paginate(page, per_page)
    )


@blueprint.route('/add22', methods=['GET', 'POST'])
@blueprint.route('/input2', methods=['GET', 'POST'])
@login_required
@register_breadcrumb(blueprint, '.add', _('Register Alert'))
def add():
    """List users' search queries."""
    return 'Foo'
    return render_template(
        'alerts/add.html',
    )
