# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012, 2013 CERN.
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

import os
from pprint import pformat
from flask import render_template, request, flash, redirect, url_for, g, abort
from werkzeug.datastructures import CombinedMultiDict, ImmutableMultiDict, \
    MultiDict

from invenio.sqlalchemyutils import db
from invenio.websession_model import User
from invenio.webinterface_handler_flask_utils import _, InvenioBlueprint
from invenio.config import \
    CFG_SITE_URL, \
    CFG_PYLIBDIR, \
    CFG_LOGDIR, \
    CFG_SITE_SECURE_URL, \
    CFG_ACCESS_CONTROL_LEVEL_SITE, \
    CFG_ACCESS_CONTROL_NOTIFY_USER_ABOUT_NEW_ACCOUNT, \
    CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS
from invenio.access_control_config import \
    CFG_EXTERNAL_AUTH_USING_SSO, \
    CFG_EXTERNAL_AUTH_LOGOUT_SSO
from invenio import webuser
from invenio.access_control_mailcookie import \
    InvenioWebAccessMailCookieError, \
    mail_cookie_check_authorize_action
from invenio.pluginutils import PluginContainer
from invenio.webaccount_forms import LoginForm, RegisterForm
from invenio.webuser_flask import login_user, logout_user, current_user
from invenio.websession_webinterface import wash_login_method


CFG_HAS_HTTPS_SUPPORT = CFG_SITE_SECURE_URL.startswith("https://")
CFG_FULL_HTTPS = CFG_SITE_URL.lower().startswith("https://")

blueprint = InvenioBlueprint('webaccount', __name__,
                             url_prefix="/youraccount",
                             breadcrumbs=[(_("Your Account"),
                                           'webaccount.index')],
                             menubuilder=[('personalize', _('Personalize'),
                                           'webaccount.index')])


def update_login(nickname, password=None, remember_me=False):
    where = [db.or_(User.nickname == nickname, User.email == nickname)]
    if password is not None:
        where.append(User.password == password)
    user = User.query.filter(*where).one()
    login_user(user.get_id(), remember_me=remember_me)
    return user


@blueprint.route('/login/', methods=['GET', 'POST'])
@blueprint.invenio_wash_urlargd({'nickname': (unicode, None),
                                 'password': (unicode, None),
                                 'login_method': (wash_login_method, 'Local'),
                                 'action': (unicode, ''),
                                 'remember_me': (bool, False),
                                 'referer': (unicode, None)})
@blueprint.invenio_set_breadcrumb(_("Login"))
@blueprint.invenio_force_https
def login(nickname=None, password=None, login_method=None, action='',
          remember_me=False, referer=None):

    if CFG_ACCESS_CONTROL_LEVEL_SITE > 0:
        return abort(401)  # page is not authorized

    if action:
        try:
            action, arguments = mail_cookie_check_authorize_action(action)
        except InvenioWebAccessMailCookieError:
            pass
    form = LoginForm(CombinedMultiDict([ImmutableMultiDict({'referer': referer}
                                        if referer else {}),
                                        request.values]),
                     csrf_enabled=False)
    try:
        user = None
        if not CFG_EXTERNAL_AUTH_USING_SSO:
            if login_method is 'Local':
                if form.validate_on_submit():
                    user = update_login(nickname, password, remember_me)
            elif login_method in ['openid', 'oauth1', 'oauth2']:
                pass
                req = request.get_legacy_request()
                (iden, nickname, password, msgcode) = webuser.loginUser(req, nickname,
                                                                        password,
                                                                        login_method)
                if iden:
                    user = update_login(nickname)
            else:
                flash(_('Invalid login method.'), 'error')

        else:
            req = request.get_legacy_request()
            # Fake parameters for p_un & p_pw because SSO takes them from the environment
            (iden, nickname, password, msgcode) = webuser.loginUser(req, '', '', CFG_EXTERNAL_AUTH_USING_SSO)
            if iden:
                user = update_login(nickname)

        if user:
            flash(_("You are logged in as %s.") % user.nickname, "info")
            if referer is not None:
                # Change HTTP method to https if needed.
                referer = referer.replace(CFG_SITE_URL, CFG_SITE_SECURE_URL)
                return redirect(referer)
    except:
        flash(_("Problem with login."), "error")

    from invenio import websession_config
    from flask import current_app
    current_app.config.update(dict((k, v) for k, v in
                              vars(websession_config).iteritems()
                              if "CFG_" == k[:4]))

    return render_template('webaccount_login.html', form=form)


@blueprint.route('/register', methods=['GET', 'POST'])
@blueprint.invenio_set_breadcrumb(_("Register"))
@blueprint.invenio_force_https
def register():
    req = request.get_legacy_request()

    # FIXME
    if CFG_ACCESS_CONTROL_LEVEL_SITE > 0:
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
            if CFG_ACCESS_CONTROL_NOTIFY_USER_ABOUT_NEW_ACCOUNT == 1:
                messages.append(_("In order to confirm its validity, an email message containing an account activation key has been sent to the given email address."))
                messages.append(_("Please follow instructions presented there in order to complete the account registration process."))
            if CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS >= 1:
                messages.append(_("A second email will be sent when the account has been activated and can be used."))
            elif CFG_ACCESS_CONTROL_NOTIFY_USER_ABOUT_NEW_ACCOUNT != 1:
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
                messages.append(_("Internal error %s") % ruid)
    elif request.method == 'POST':
        title = _("Registration failure")
        state = "warning"

    return render_template('webaccount_register.html', form=form, title=title,
                           messages=messages, state=state)


@blueprint.route('/logout', methods=['GET', 'POST'])
@blueprint.invenio_set_breadcrumb(_("Logout"))
@blueprint.invenio_authenticated
def logout():
    logout_user()

    if CFG_EXTERNAL_AUTH_USING_SSO:
        return redirect(CFG_EXTERNAL_AUTH_LOGOUT_SSO)

    return render_template('webaccount_logout.html',
                           using_sso=CFG_EXTERNAL_AUTH_USING_SSO,
                           logout_sso=CFG_EXTERNAL_AUTH_LOGOUT_SSO)


def _invenio_settings_plugin_builder(plugin_name, plugin_code):
    """
    Handy function to bridge pluginutils with (Invenio) user settings.
    """
    from invenio.settings import Settings
    if 'settings' in dir(plugin_code):
        candidate = getattr(plugin_code, 'settings')
        if issubclass(candidate, Settings):
            return candidate
    raise ValueError('%s is not a valid settings plugin' % plugin_name)


_USER_SETTINGS = PluginContainer(
    os.path.join(CFG_PYLIBDIR, 'invenio', '*_user_settings.py'),
    plugin_builder=_invenio_settings_plugin_builder)

## Let's report about broken plugins
open(os.path.join(CFG_LOGDIR, 'broken-user-settings.log'), 'w').write(
    pformat(_USER_SETTINGS.get_broken_plugins()))


@blueprint.route('/display', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
def index():
    # load plugins
    plugins = [a for a in [s() for (dummy, s) in _USER_SETTINGS.items() if s] \
               if a.is_authorized and a.widget]

    closed_plugins = []

    plugin_sort = (lambda w, x: x.index(w.__class__.__name__)
                       if w.__class__.__name__ in x else len(x))

    dashboard_settings = current_user.get('dashboard_settings', {})

    if dashboard_settings:
        order_left = dashboard_settings.get('orderLeft', []) or []
        order_middle = dashboard_settings.get('orderMiddle', []) or []
        order_right = dashboard_settings.get('orderRight', []) or []

        extract_plugins = lambda x: [p for p in plugins if p.__class__.__name__ in x if p]

        plugins_left = sorted(extract_plugins(order_left),
                              key=lambda w: plugin_sort(w, order_left))
        plugins_middle = sorted(extract_plugins(order_middle),
                                key=lambda w: plugin_sort(w, order_middle))
        plugins_right = sorted(extract_plugins(order_right),
                               key=lambda w: plugin_sort(w, order_right))
        closed_plugins = [p for p in plugins if not p in plugins_left and
                                                not p in plugins_middle and
                                                not p in plugins_right]
    else:
        slc = len(plugins) / 3 + 1 if len(plugins) % 3 else len(plugins)
        plugins = sorted(plugins, key=lambda w: plugin_sort(w, plugins))
        plugins_left = plugins[0:slc]
        plugins_middle = plugins[slc:slc * 2]
        plugins_right = plugins[slc * 2:]

    return render_template('webaccount_display.html',
                           plugins=[plugins_left,
                                    plugins_middle,
                                    plugins_right],
                           closed_plugins=closed_plugins)


@blueprint.route('/edit/<name>', methods=['GET', 'POST'])
@blueprint.invenio_set_breadcrumb(_("Edit"))
@blueprint.invenio_authenticated
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
            plugin.store(request.form)
            plugin.save()
            flash(_('Data has been saved.'), 'success')
            return redirect(url_for('.index'))

        flash(_('Please, corrent errors.'), 'error')

    # get post data or load data from settings
    if not form and plugin.form_builder:
        from werkzeug.datastructures import MultiDict
        form = plugin.form_builder(MultiDict(plugin.load()))

    return render_template(getattr(plugin, 'edit_template', '') or
                           'webaccount_edit.html', plugin=plugin, form=form)


@blueprint.route('/loadwidget/<widget_name>', methods=['GET'])
def loadwidget(widget_name):
    if not widget_name:
        return "1"

    # @todo: get plugin more effectively
    widget = [a for a in [s() for (dummy, s) in _USER_SETTINGS.items() if s] if a.is_authorized and a.widget and a.__class__.__name__ == widget_name]

    if widget:
        return render_template('webaccount_widget.html', widget=widget[0])
    else:
        return "2"
