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

"""GitHub Settings Blueprint."""

from __future__ import absolute_import

from flask import Blueprint, flash, g, redirect, render_template, request, \
    url_for

from flask_breadcrumbs import register_breadcrumb

from flask_login import current_user, login_required

from flask_menu import current_menu, register_menu

from invenio.base.i18n import _
from invenio.ext.login import reset_password
from invenio.ext.sslify import ssl_required

from ..forms import ChangePasswordForm, LostPasswordForm, ProfileForm, \
    VerificationForm
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
    """Register empty account breadcrumb."""
    item = current_menu.submenu('breadcrumbs.settings')
    item.register('', _('Account'))


@blueprint.route("/")
@ssl_required
@login_required
def index():
    """Index page."""
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
    """Change password form for authenticated users."""
    u = User.query.filter_by(id=current_user.get_id()).first()

    profile_form = ProfileForm(formdata=None, obj=u, prefix="profile")
    verification_form = VerificationForm(formdata=None, prefix="verification")
    password_form = ChangePasswordForm(formdata=None, prefix="password")

    form = request.form.get('submit', None)
    if form == 'password':
        password_form.process(formdata=request.form)
        if password_form.validate_on_submit():
            u.password = password_form.data['password']
            flash(_("Password changed."), category="success")
    elif form == 'profile':
        profile_form.process(formdata=request.form)
        if profile_form.validate_on_submit():
            changed_attrs = u.update_profile(profile_form.data)
            if 'email' in changed_attrs:
                flash(_("Profile updated. We have sent a verification email to"
                        " %(email)s. Please check it.", email=u.email),
                      category="success")
            elif changed_attrs:
                flash(_("Profile updated."), category="success")
            else:
                flash(_("No changes to profile."), category="success")
    elif form == 'verification':
        verification_form.process(formdata=request.form)
        if verification_form.validate_on_submit():
            if u.verify_email():
                flash(_("Verification email sent."), category="success")

    return render_template(
        "accounts/settings/profile.html",
        password_form=password_form,
        profile_form=profile_form,
        verification_form=verification_form,
        user=u,
    )


@blueprint.route("/profile/lost", methods=['GET', 'POST'])
@ssl_required
@login_required
@register_breadcrumb(
    blueprint, 'breadcrumbs.settings.profile.lost', _('Lost password')
)
def lost():
    """Lost password form for authenticated users."""
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
