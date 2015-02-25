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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Pre-configured remote application for enabling sign in/up with CERN.

**Usage:**

1. Edit your configuration and add:

   .. code-block:: python

       from invenio.modules.oauthclient.contrib import cern
       OAUTHCLIENT_REMOTE_APPS = dict(
           cern=cern.REMOTE_APP,
       )

       CERN_APP_CREDENTIALS = dict(
           consumer_key="changeme",
           consumer_secret="changeme",
       )

  Note, if you want to use the CERN sandbox, use ``cern.REMOTE_SANDBOX_APP``
  instead of ``cern.REMOTE_APP``.

2. Register a new application with CERN. When registering the
   application ensure that the *Redirect URI* points to:
   ``CFG_SITE_SECURE_URL/oauth/authorized/cern/`` (note, CERN does not
   allow localhost to be used, thus testing on development machines is
   somewhat complicated by this).


3. Grab the *Client ID* and *Client Secret* after registering the application
   and add them to your instance configuration (``invenio.cfg``):

   .. code-block:: python

       CERN_APP_CREDENTIALS = dict(
           consumer_key="<CLIENT ID>",
           consumer_secret="<CLIENT SECRET>",
       )

4. Now go to ``CFG_SITE_SECURE_URL/oauth/login/cern/`` (e.g.
   http://localhost:4000/oauth/login/cern/)

5. Also, you should see CERN listed under Linked accounts:
   http://localhost:4000//account/settings/linkedaccounts/

By default the CERN module will try first look if a link already exists
between a CERN account and a user. If no link is found, the user is asked
to provide an email address to sign-up.

In templates you can add a sign in/up link:

.. code-block:: jinja

    <a href="{{url_for("oauthclient.login", remote_app="cern")}}">Sign in with CERN</a>

"""

import copy, re
import requests
from flask import session, current_app
from invenio.ext.sqlalchemy import db
from flask.ext.login import current_user

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

REMOTE_APP = dict(
    title="CERN",
    description="Connecting to CERN Organization.",
    icon="",
    authorized_handler="invenio.modules.oauthclient.handlers"
                       ":authorized_signup_handler",
    disconnect_handler="invenio.modules.oauthclient.handlers"
                       ":disconnect_handler",
    signup_handler=dict(
        info="invenio.modules.oauthclient.contrib.cern:account_info",
        setup="invenio.modules.oauthclient.contrib.cern:account_setup",
        view="invenio.modules.oauthclient.handlers:signup_handler",
    ),
    params=dict(
        request_token_params={
                "resource": "datadev00.cern.ch",
                "scope": "Name Email Bio Groups",
        },
        base_url="https://oauth.web.cern.ch/",
        request_token_url=None,
        access_token_url="https://oauth.web.cern.ch/OAuth/Token",
        access_token_method="POST",
        authorize_url="https://oauth.web.cern.ch/OAuth/Authorize",
        app_key="CERN_APP_CREDENTIALS",
        content_type="application/json",
    )
)
"""CERN Remote Application."""

REMOTE_SANDBOX_APP = copy.deepcopy(REMOTE_APP)
"""CERN Sandbox Remote Application."""

REMOTE_SANDBOX_APP["params"].update(dict(
    base_url="https://oauth.web.cern.ch/",
    access_token_url="https://oauth.web.cern.ch/OAuth/Token",
    authorize_url="https://oauth.web.cern.ch/OAuth/Authorize",
))

def fetch_groups(groups):
    groups = [group for group in groups if group not in
              CFG_EXTERNAL_AUTH_HIDDEN_GROUPS]
    for regexp in CFG_EXTERNAL_AUTH_HIDDEN_GROUPS_RE:
        for group in groups:
            if regexp.match(group):
               groups.remove(group)

    return dict(map(lambda x: (x, '@' in x and x + ' (Mailing list)'
                                   or x + ' (Group)'), groups))

def get_dict_from_response(response):
    result = {}
    for i in response.json():
        k = str(i['Type'])
        if not result.get(k, None):
            result[k] = []
        result[k].append(str(i['Value']))

    return result

def account_info(remote, resp):
    """Retrieve remote account information used to find local user."""
    from flask import current_app
    current_app.logger.info(remote)
    current_app.logger.info(resp)

    # Query CERN Resources to get user info and groups
    url = 'https://oauthresource.web.cern.ch/api/Me'
    headers =  {'Authorization': 'Bearer '+resp['access_token']}
    response = requests.get(url, headers=headers)
    res = {}
    res = get_dict_from_response(response)
    email = res['http://schemas.xmlsoap.org/claims/EmailAddress']
    nickname = res['http://schemas.xmlsoap.org/claims/Firstname']
    return dict(email=email, nickname=nickname, resp = res)

def account_setup(remote, token):
    """Perform additional setup after user have been logged in."""
    from invenio.modules.accounts.models import User, UserEXT, Usergroup
    from invenio.ext.sqlalchemy import db
    from ..handlers import token_session_key

    from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

    url = 'https://oauthresource.web.cern.ch/api/Me'
    headers =  {'Authorization': 'Bearer '+token.token()[0]}
    response = requests.get(url, headers=headers)
    res = {}
    code = response.status_code
    current_app.logger.info(code)
    current_app.logger.info(requests.codes.ok)

    if code == requests.codes.ok:
        res = get_dict_from_response(response)
        email = res['http://schemas.xmlsoap.org/claims/EmailAddress']
        try:
            #user = User.query.filter_by(email=email).one()
            ###current_user.info['group'] = res['http://schemas.xmlsoap.org/claims/Group']
            current_user.info['group'] = fetch_groups(res['http://schemas.xmlsoap.org/claims/Group'])
            current_user.modified = True
            current_user.save()
            current_app.logger.info('SETUP')
        except:
            raise

#    if user:
#       current_user.info['group'] = res['http://schemas.xmlsoap.org/claims/Group']
#       for g in res['http://schemas.xmlsoap.org/claims/Group']:
#           ug = Usergroup()
#           id_user = current_user.get_id()
#           user2join = User.query.get_or_404(id_user)
#           ug.name = g
#           ug.join_policy = 'VE'
#           ug.login_method = 'EXTERNAL'
#
#           ug.join( user=user2join, status = 'M')
#           db.session.add(ug)
#
#       try:
#            db.session.commit()
#       except:
#            db.session.rollback()
#            raise
#
#       db.session.add(user)
#       db.session.commit()
#       current_user.reload()
#       pass