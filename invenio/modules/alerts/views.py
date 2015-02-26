# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
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
from flask import render_template, request, Blueprint, flash, redirect, url_for
from flask.ext.breadcrumbs import default_breadcrumb_root, register_breadcrumb
from flask.ext.login import current_user, login_required
from flask.ext.menu import register_menu

# Internal imports
from invenio.base.decorators import wash_arguments
from invenio.base.i18n import _
from invenio.ext.sqlalchemy import db
from invenio.modules.baskets.models import BskBASKET
from invenio.modules.search.models import UserQuery

from .models import UserQueryBasket
from .forms import AlertForm

blueprint = Blueprint('alerts', __name__, url_prefix='/youralerts',
                      template_folder='templates', static_folder='static')

default_breadcrumb_root(blueprint, '.settings.alerts')


@blueprint.route('/', methods=['GET', 'POST'])
@blueprint.route('/display', methods=['GET', 'POST'])
@register_menu(
    blueprint, 'settings.alerts',
    _('%(icon)s Search Alerts', icon='<i class="fa fa-search fa-fw"></i>'),
    order=10,
    active_when=lambda: request.endpoint.startswith("alerts.")
)
@register_breadcrumb(blueprint, '.index', _('Search History'))
@login_required
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


@blueprint.route('/list', methods=['GET', 'POST'])
@register_breadcrumb(blueprint, '.', _('Alerts'))
@login_required
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


@blueprint.route('/add', methods=['GET', 'POST'])
@wash_arguments({"id_query": (int, 0)})
@register_breadcrumb(blueprint, '.add', _('Register Alert'))
@login_required
def add(id_query=None):
    """Add new alert for search queries."""
    already_exist = UserQueryBasket.exists(id_query)
    # check if already exists the alert
    if id_query and already_exist:
        # and load the alert
        alert = UserQueryBasket.query.filter_by(
            id_query=id_query).first()
    else:
        alert = UserQueryBasket()

    form = AlertForm(request.form, obj=alert)
    id_user = current_user.get_id()

    # fill the remaining fields
    form.id_user.data = id_user
    form.id_query.data = id_query or 0
    # fill list of baskets available
    form.id_basket.choices = [(0, _('- Nothing Selected -'))] + [
        (basket.id, basket.name)
        for basket in BskBASKET.query.filter_by(id_owner=id_user).all()
    ]

    # if user submit the form
    if form.validate_on_submit():
        alert = UserQueryBasket()
        form.populate_obj(alert)
        if already_exist:
            db.session.merge(alert)
        else:
            db.session.add(alert)
        try:
            db.session.commit()
            flash(_('Alert "%(name)s" successfully created',
                    name=alert.alert_name), 'success')
        except:
            db.session.rollback()
        return redirect(url_for('.index'))

        form.populate_obj(alert)

    return render_template(
        'alerts/new.html',
        form=form,
        action=_('Save'),
        subtitle=_("Alert"),
        alert=alert
    )
