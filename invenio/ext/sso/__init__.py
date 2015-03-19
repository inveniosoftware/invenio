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

"""Initialize and configure *Flask-SSO* extension."""

import re

from flask import flash, redirect
from flask_sso import SSO

#: Tunable list of settings to be hidden.
#: e.g.: CFG_EXTERNAL_AUTH_HIDDEN_SETTINGS = ('auth', 'respccid', 'personid')
CFG_EXTERNAL_AUTH_HIDDEN_SETTINGS = ()

#: Tunable list of groups to be hidden.
CFG_EXTERNAL_AUTH_HIDDEN_GROUPS = (
    'All Exchange People',
    'CERN Users',
    'cern-computing-postmasters',
    'cern-nice2000-postmasters',
    'CMF FrontEnd Users',
    'CMF_NSC_259_NSU',
    'Domain Users',
    'GP Apply Favorites Redirection',
    'GP Apply NoAdmin',
    'info-terminalservices',
    'info-terminalservices-members',
    'IT Web IT',
    'NICE Deny Enforce Password-protected Screensaver',
    'NICE Enforce Password-protected Screensaver',
    'NICE LightWeight Authentication WS Users',
    'NICE MyDocuments Redirection (New)',
    'NICE Profile Redirection',
    'NICE Terminal Services Users',
    'NICE Users',
    'NICE VPN Users',
    )

#: Tunable list of regexps of groups to be hidden.
CFG_EXTERNAL_AUTH_HIDDEN_GROUPS_RE = (
    re.compile(r'Users by Letter [A-Z]'),
    re.compile(r'building-[\d]+'),
    re.compile(r'Users by Home CERNHOME[A-Z]'),
    )

#: Default attribute map
SSO_ATTRIBUTE_MAP = {
    'ADFS_AUTHLEVEL': (False, 'authlevel'),
    'ADFS_GROUP': (True, 'group'),
    'ADFS_LOGIN': (True, 'nickname'),
    'ADFS_ROLE': (False, 'role'),
    'ADFS_EMAIL': (True, 'email'),
    'ADFS_IDENTITYCLASS': (False, 'external'),
    'HTTP_SHIB_AUTHENTICATION_METHOD': (False, 'authmethod'),
}

sso = SSO()


def setup_app(app):
    """Setup SSO extension."""
    app.config['CFG_EXTERNAL_AUTH_USING_SSO'] = True
    app.config.setdefault('SSO_ATTRIBUTE_MAP', SSO_ATTRIBUTE_MAP)
    sso.init_app(app)

    def fetch_groups(groups):
        groups = groups.split(
            app.config.get('CFG_EXTERNAL_AUTH_SSO_GROUPS_SEPARATOR', ';'))
        # Filtering out uncomfortable groups
        groups = [group for group in groups if group not in app.config.get(
            'CFG_EXTERNAL_AUTH_HIDDEN_GROUPS',
            CFG_EXTERNAL_AUTH_HIDDEN_GROUPS)]
        for regexp in app.config.get('CFG_EXTERNAL_AUTH_HIDDEN_GROUPS_RE',
                                     CFG_EXTERNAL_AUTH_HIDDEN_GROUPS_RE):
            for group in groups:
                if regexp.match(group):
                    groups.remove(group)
        return dict(map(lambda x: (x, '@' in x and x + ' (Mailing list)'
                                   or x + ' (Group)'), groups))

    def fetch_external(external):
        return '0' if external in ('CERN Registered', 'CERN Shared') else '1'

    @sso.login_handler
    def login_callback(user_info):
        """Login user base on SSO context (create one if necessary).

        Function should not raise an exception if `user_info` is not valid
        or `User` was not found in database.
        """
        from invenio.modules.accounts.models import User
        from invenio.ext.login import (authenticate, login_redirect,
                                       current_user)
        from invenio.ext.sqlalchemy import db

        user_info['group'] = fetch_groups(user_info['group']).values()
        user_info['external'] = fetch_external(user_info.get('external'))
        try:
            auth = authenticate(user_info['email'], login_method='SSO')
            if auth is None:
                user = User()
                user.nickname = user_info['nickname']
                user.email = user_info['email']
                user.password = ''
                user.settings = {'login_method': 'SSO'}
                db.session.add(user)
                db.session.commit()
                auth = authenticate(user_info['email'], login_method='SSO')
                if auth is None:
                    return redirect('/')

            current_user.info['group'] = current_user.get('group', []) + \
                user_info['group']
            current_user.save()
        except:
            flash('Problem with login (%s)' % (str(user_info)), 'error')
            return redirect('/')

        return login_redirect()

    return app
