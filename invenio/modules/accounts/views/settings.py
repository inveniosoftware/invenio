# -*- coding: utf-8 -*-
#
## This file is part of ZENODO.
## Copyright (C) 2014 CERN.
##
## ZENODO is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## ZENODO is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with ZENODO. If not, see <http://www.gnu.org/licenses/>.
##
## In applying this licence, CERN does not waive the privileges and immunities
## granted to it by virtue of its status as an Intergovernmental Organization
## or submit itself to any jurisdiction.


"""
GitHub Settings Blueprint
"""

from __future__ import absolute_import

from flask import Blueprint, render_template, redirect, url_for, request, \
    flash, g
from flask.ext.login import login_required, current_user
from flask.ext.breadcrumbs import register_breadcrumb
from flask.ext.menu import register_menu, current_menu

from invenio.base.i18n import _
from invenio.ext.sslify import ssl_required
from invenio.ext.login import reset_password


from ..forms import ChangePasswordForm, LostPasswordForm
from ..models import User


blueprint = Blueprint(
    'accounts_settings',
    __name__,
    url_prefix="/account/settings",
    static_folder="../static",
    template_folder="../templates",
)


@blueprint.before_app_first_request
def register_menu_items():
    item = current_menu.submenu('breadcrumbs.settings')
    item.register('', _('Account'))


@blueprint.route("/")
@ssl_required
@login_required
def index():
    return redirect(url_for(".profile"))


@blueprint.route("/profile", methods=['GET', 'POST'])
@ssl_required
@login_required
@register_menu(
    blueprint, 'settings.profile',
    _('%(icon)s Profile', icon='<i class="fa fa-user fa-fw"></i>'),
    order=0,
    active_when=lambda: request.endpoint.startswith("accounts_settings.")
)
@register_breadcrumb(blueprint, 'breadcrumbs.settings.profile', _('Profile'))
def profile():
    form = ChangePasswordForm(request.form)
    if form.validate_on_submit():
        u = User.query.filter_by(id=current_user.get_id()).first()
        u.password = form.data['password']
        flash("Password changed.", category="success")

    return render_template(
        "accounts/settings/profile.html",
        form=form,
    )


@blueprint.route("/profile/lost", methods=['GET', 'POST'])
@ssl_required
@login_required
@register_breadcrumb(
    blueprint, 'breadcrumbs.settings.profile.lost', _('Lost password')
)
def lost():
    """ Lost password form for authenticated users """
    form = LostPasswordForm(request.form)
    if form.validate_on_submit():
        if reset_password(form.data['email'], g.ln):
            flash(_('A password reset link has been sent to %(whom)s',
                    whom=request.values['email']), 'success')
        return redirect(url_for('.profile'))

    return render_template(
        "accounts/settings/lost.html",
        form=form,
    )
