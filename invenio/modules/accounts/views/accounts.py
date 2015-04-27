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

"""WebAccount Flask Blueprint."""

from __future__ import absolute_import

from flask import Blueprint, abort, current_app, flash, g, redirect, \
    render_template, request, url_for

from flask_breadcrumbs import register_breadcrumb

from flask_login import current_user, login_required

from flask_menu import register_menu

from sqlalchemy.exc import SQLAlchemyError

from werkzeug import CombinedMultiDict, ImmutableMultiDict

from invenio.base.decorators import wash_arguments
from invenio.base.globals import cfg
from invenio.base.i18n import _
from invenio.ext.login import UserInfo, authenticate, login_redirect, \
    login_user, logout_user, reset_password
from invenio.ext.sqlalchemy import db
from invenio.ext.sslify import ssl_required
from invenio.legacy import webuser
from invenio.modules.access.mailcookie import mail_cookie_check_mail_activation
from invenio.utils.datastructures import LazyDict, flatten_multidict

from ..forms import LoginForm, LostPasswordForm, RegisterForm
from ..models import User
from ..validators import wash_login_method

blueprint = Blueprint('webaccount', __name__, url_prefix="/youraccount",
                      template_folder='../templates',
                      static_folder='../static')


@blueprint.route('/login', methods=['GET', 'POST'])
@wash_arguments({'nickname': (unicode, None),
                 'password': (unicode, None),
                 'login_method': (wash_login_method, 'Local'),
                 'action': (unicode, ''),
                 'remember': (bool, False),
                 'referer': (unicode, None)})
@register_breadcrumb(blueprint, '.login', _('Login'))
@ssl_required
def login(nickname=None, password=None, login_method=None, action='',
          remember=False, referer=None):
    if cfg.get('CFG_ACCESS_CONTROL_LEVEL_SITE') > 0:
        return abort(401)  # page is not authorized

    if action:
        from invenio.modules.access.mailcookie import \
            InvenioWebAccessMailCookieError, \
            mail_cookie_check_authorize_action
        try:
            action, arguments = mail_cookie_check_authorize_action(action)
        except InvenioWebAccessMailCookieError:
            pass
    form = LoginForm(CombinedMultiDict(
        [ImmutableMultiDict({'referer': referer, 'login_method': 'Local'}
                            if referer else {'login_method': 'Local'}),
         request.values]), csrf_enabled=False)

    if request.method == "POST":
        try:
            if login_method == 'Local' and form.validate_on_submit() and \
               authenticate(nickname, password, login_method=login_method,
                            remember=remember):
                flash(
                    _("You are logged in as %(nick)s.", nick=nickname),
                    "success"
                )
                return login_redirect(referer)

            else:
                flash(_("Invalid credentials."), "error")
        except Exception as e:
            current_app.logger.error(
                'Exception during login process: %s', str(e)
            )
            flash(_("Problem with login."), "error")

    return render_template('accounts/login.html', form=form), 401


@blueprint.route('/register', methods=['GET', 'POST'])
@register_breadcrumb(blueprint, '.register', _('Register'))
@ssl_required
def register():
    req = request.get_legacy_request()

    # FIXME
    if cfg.get('CFG_ACCESS_CONTROL_LEVEL_SITE') > 0:
        return webuser.page_not_authorized(req, "../youraccount/register?ln=%s" % g.ln,
                                           navmenuid='youraccount')

    form = RegisterForm(request.values, csrf_enabled=False)
    #uid = current_user.get_id()

    title = _("Register")
    messages = []
    state = ""

    if form.validate_on_submit():
        ruid = webuser.registerUser(req, form.email.data.encode('utf8'),
                                    form.password.data.encode('utf8'),
                                    form.nickname.data.encode('utf8'),
                                    ln=g.ln)
        if ruid == 0:
            title = _("Account created")
            messages.append(_("Your account has been successfully created."))
            state = "success"
            if cfg.get('CFG_ACCESS_CONTROL_NOTIFY_USER_ABOUT_NEW_ACCOUNT') == 1:
                messages.append(_("In order to confirm its validity, an email message containing an account activation key has been sent to the given email address."))
                messages.append(_("Please follow instructions presented there in order to complete the account registration process."))
            if cfg.get('CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS') >= 1:
                messages.append(_("A second email will be sent when the account has been activated and can be used."))
            elif cfg.get('CFG_ACCESS_CONTROL_NOTIFY_USER_ABOUT_NEW_ACCOUNT') != 1:
                user = User.query.filter(User.email == form.email.data.lower()).one()
                login_user(user.get_id())
                messages.append(_("You can now access your account."))
        else:
            title = _("Registration failure")
            state = "danger"
            if ruid == 5:
                messages.append(_("Users cannot register themselves, only admin can register them."))
            elif ruid == 6 or ruid == 1:
                # Note, code 1 is used both for invalid email, and email sending
                # problems, however the email address is validated by the form,
                # so we only have to report a problem sending the email here
                messages.append(_("The site is having troubles in sending you an email for confirming your email address."))
                messages.append(_("The error has been logged and will be taken in consideration as soon as possible."))
            else:
                # Errors [-2, (1), 2, 3, 4] taken care of by form validation
                messages.append(_("Internal error %(ruid)s", ruid=ruid))
    elif request.method == 'POST':
        title = _("Registration failure")
        state = "warning"

    return render_template('accounts/register.html', form=form, title=title,
                           messages=messages, state=state)


@blueprint.route('/logout', methods=['GET', 'POST'])
@register_breadcrumb(blueprint, '.logout', _('Logout'))
@login_required
def logout():
    logout_user()

    from invenio.modules.access.local_config import \
        CFG_EXTERNAL_AUTH_USING_SSO, \
        CFG_EXTERNAL_AUTH_LOGOUT_SSO

    if CFG_EXTERNAL_AUTH_USING_SSO:
        return redirect(CFG_EXTERNAL_AUTH_LOGOUT_SSO)

    return render_template('accounts/logout.html',
                           using_sso=CFG_EXTERNAL_AUTH_USING_SSO,
                           logout_sso=CFG_EXTERNAL_AUTH_LOGOUT_SSO)


def load_user_settings():
    """Handy function to populate LazyDic with user settings."""
    from invenio.modules.dashboard.settings import Settings
    from invenio.base.utils import autodiscover_user_settings
    modules = autodiscover_user_settings()
    user_settings = {}
    for module in modules:
        candidates = getattr(module, 'settings')
        if candidates is not None:
            if type(candidates) is not list:
                candidates = [candidates]
            for candidate in candidates:
                if issubclass(candidate, Settings):
                    if candidate.__name__ in user_settings:
                        raise Exception(candidate.__name__,
                                        'duplicate user settings')
                    user_settings[candidate.__name__] = candidate
    return user_settings

_USER_SETTINGS = LazyDict(load_user_settings)


@blueprint.route('/', methods=['GET', 'POST'])
@blueprint.route('/display', methods=['GET', 'POST'])
@login_required
@register_menu(blueprint, 'personalize', _('Personalize'))
@register_breadcrumb(blueprint, '.', _('Your account'))
def index():
    # load plugins
    plugins = filter(lambda x: x.is_authorized and x.widget,
                     map(lambda x: x(), _USER_SETTINGS.values()))
    closed_plugins = []
    plugin_sort = (lambda w, x: x.index(w.name) if w.name in x else len(x))

    dashboard_settings = current_user.get('dashboard_settings', {})

    if current_user.is_super_admin:
        # Check for a new release of Invenio
        from invenio.ext.script import check_for_software_updates
        check_for_software_updates(flash_message=True)

    if dashboard_settings:
        order_left = dashboard_settings.get('orderLeft', []) or []
        order_middle = dashboard_settings.get('orderMiddle', []) or []
        order_right = dashboard_settings.get('orderRight', []) or []

        def extract_plugins(x):
            return [p for p in plugins if p.name in x if p]

        plugins_left = sorted(extract_plugins(order_left),
                              key=lambda w: plugin_sort(w, order_left))
        plugins_middle = sorted(extract_plugins(order_middle),
                                key=lambda w: plugin_sort(w, order_middle))
        plugins_right = sorted(extract_plugins(order_right),
                               key=lambda w: plugin_sort(w, order_right))
        closed_plugins = [p for p in plugins if p not in plugins_left and
                          p not in plugins_middle and
                          p not in plugins_right]
        plugins = [plugins_left, plugins_middle, plugins_right]
    else:
        plugins = sorted(plugins, key=lambda w: plugin_sort(w, plugins))
        plugins = [plugins[i:i+3] for i in range(0, len(plugins), 3)]
    return render_template('accounts/index.html',
                           plugins=plugins, closed_plugins=closed_plugins)


@blueprint.route('/edit/<name>', methods=['GET', 'POST'])
@register_breadcrumb(blueprint, '.edit', _('Edit'))
@login_required
def edit(name):
    if name not in _USER_SETTINGS:
        flash(_('Invalid plugin name'), 'error')
        return redirect(url_for('.index'))

    plugin = _USER_SETTINGS[name]()
    form = None

    if request.method == 'POST':
        if plugin.form_builder:
            form = plugin.form_builder(request.form)

        if not form or form.validate():
            if form:
                # use the form to interpret data
                settings_data = form.data
            else:
                # no form provided, save the POST request values
                settings_data = flatten_multidict(request.values)

            plugin.store(settings_data)
            plugin.save()
            flash(_('Data has been saved.'), 'success')
            return redirect(url_for('.index'))

        flash(_('Please, corrent errors.'), 'error')

    # get post data or load data from settings
    if not form and plugin.form_builder:
        form = plugin.build_form()

    return render_template(getattr(plugin, 'edit_template', '') or
                           'accounts/edit.html', plugin=plugin, form=form)


@blueprint.route('/view', methods=['GET'])
@login_required
@wash_arguments({'name': (unicode, "")})
def view(name):
    if name not in _USER_SETTINGS:
        return "1", 406

    widget = _USER_SETTINGS[name]()
    if widget.is_authorized and widget.widget:
        return render_template('accounts/widget.html', widget=widget)
    else:
        return "2", 406


@blueprint.route('/lost', methods=['GET', 'POST'])
@register_breadcrumb(blueprint, '.edit', _('Edit'))
@ssl_required
def lost():
    form = LostPasswordForm(request.values)
    if form.validate_on_submit():
        if reset_password(request.values['email'], g.ln):
            flash(_('A password reset link has been sent to %(whom)s',
                    whom=request.values['email']), 'success')
    return render_template('accounts/lost.html', form=form)


@blueprint.route('/access', methods=['GET', 'POST'])
@ssl_required
def access():
    try:
        mail = mail_cookie_check_mail_activation(request.values['mailcookie'])

        u = User.query.filter(User.email == mail).one()
        u.note = 1
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash(_('Authorization failled.'), 'error')
            redirect('/')

        if current_user.is_authenticated():
            current_user.reload()
            flash(_('Your email address has been validated'), 'success')
        else:
            UserInfo(u.id).reload()
            flash(
                _('Your email address has been validated, and you can '
                  'now proceed to sign-in.'),
                'success'
            )
    except Exception:
        current_app.logger.exception("Authorization failed.")
        flash(_('The authorization token is invalid.'), 'error')
    return redirect('/')
