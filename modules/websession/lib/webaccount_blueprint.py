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
from invenio.sqlalchemyutils import db
from invenio.websession_model import User, Usergroup, UserUsergroup
from invenio.webinterface_handler_flask_utils import _, InvenioBlueprint
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

from invenio.webaccount_forms import LoginForm
from invenio.webuser_flask import login_user, logout_user

blueprint = InvenioBlueprint('youraccount', __name__, url_prefix="/youraccount",
                breadcrumbs=[(_("Your Account"), 'youraccount.index')],
                menubuilder=[('main.personalize', _('Personalize'),
                              'youraccount.display', 3)])


@blueprint.route('/login', methods=['GET', 'POST'])
@blueprint.invenio_set_breadcrumb(_("Login"))
def login():
    form = LoginForm(request.values, csrf_enabled=False)
    if form.validate_on_submit():
        try:
            #TODO add login_methods
            user = User.query.filter(db.and_(
                User.nickname==form.nickname.data,
                User.password==form.password.data)).one()
            login_user(user) #, remember=form.remember.data)
            flash(_("You have been logged in."), "info")
            return redirect(request.values.get("referer") or url_for(".login"))
        except:
            flash(_("Problem with login."), "error")

    return render_template('webaccount_login.html', form=form)


@blueprint.route('/logout', methods=['GET', 'POST'])
@blueprint.invenio_set_breadcrumb(_("Logout"))
@blueprint.invenio_cached()
def logout():
    logout_user()
    return render_template('webaccount_logout.html',
                            using_sso = CFG_EXTERNAL_AUTH_USING_SSO,
                            logout_sso = CFG_EXTERNAL_AUTH_LOGOUT_SSO)

