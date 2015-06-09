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

"""Pre-configured remote application for enabling sign in/up with CERN.

**Usage:**

1. Edit your configuration and add:

   .. code-block:: python

       import copy

       from invenio.modules.oauthclient.contrib import cern

       CERN_REMOTE_APP = copy.deepcopy(cern.REMOTE_APP)
       CERN_REMOTE_APP["params"].update(dict(request_token_params={
           "resource": "changeme.cern.ch",  # replace with your server
           "scope": "Name Email Bio Groups",
       }))

       OAUTHCLIENT_REMOTE_APPS = dict(
           cern=CERN_REMOTE_APP,
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
   http://localhost:4000/account/settings/linkedaccounts/

By default the CERN module will try first look if a link already exists
between a CERN account and a user. If no link is found, the user is asked
to provide an email address to sign-up.

In templates you can add a sign in/up link:

.. code-block:: jinja

    <a href="{{url_for("oauthclient.login", remote_app="cern")}}">
      Sign in with CERN
    </a>
"""

import copy
import re

from flask import current_app

from flask_login import current_user

import requests

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
    base_url="https://test-oauth.web.cern.ch/",
    access_token_url="https://test-oauth.web.cern.ch/OAuth/Token",
    authorize_url="https://test-oauth.web.cern.ch/OAuth/Authorize",
))

REMOTE_APP_RESOURCE_API_URL = "https://oauthresource.web.cern.ch/api/Me"
REMOTE_APP_RESOURCE_SCHEMA = "http://schemas.xmlsoap.org/claims"


def fetch_groups(groups):
    """Prepare list of allowed group names."""
    hidden_groups = current_app.config.get(
        'CFG_EXTERNAL_AUTH_HIDDEN_GROUPS', CFG_EXTERNAL_AUTH_HIDDEN_GROUPS)
    hidden_groups_re = current_app.config.get(
        'CFG_EXTERNAL_AUTH_HIDDEN_GROUPS_RE',
        CFG_EXTERNAL_AUTH_HIDDEN_GROUPS_RE)
    groups = [group for group in groups if group not in hidden_groups]
    filter_groups = []
    for regexp in hidden_groups_re:
        for group in groups:
            if regexp.match(group):
                filter_groups.append(group)
    groups = [group for group in groups if group not in filter_groups]

    return groups


def get_dict_from_response(response):
    """Prepare new mapping with 'Value's groupped by 'Type'."""
    result = {}
    for i in response.data:
        k = i['Type']
        result.setdefault(k, list())
        result[k].append(i['Value'])
    return result


def account_info(remote, resp):
    """Retrieve remote account information used to find local user."""
    # Query CERN Resources to get user info and groups
    response = remote.get(REMOTE_APP_RESOURCE_API_URL)
    res = get_dict_from_response(response)
    email = res['{0}/{1}'.format(REMOTE_APP_RESOURCE_SCHEMA,
                                 'EmailAddress')][0]
    return dict(email=email, nickname=email)


def account_setup(remote, token):
    """Perform additional setup after user have been logged in."""
    response = remote.get(REMOTE_APP_RESOURCE_API_URL)

    if response.status == requests.codes.ok:
        res = get_dict_from_response(response)
        current_user.info['group'] = fetch_groups(res['{0}/{1}'.format(
            REMOTE_APP_RESOURCE_SCHEMA, 'Group'
        )])
        current_user.modified = True
        current_user.save()
