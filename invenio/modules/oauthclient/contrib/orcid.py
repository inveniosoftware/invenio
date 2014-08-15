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

""" Pre-configured remote application for enabling sign in/up with ORCID.

**Usage:**

1. Edit your configuration and add:

   .. code-block:: python

       from invenio.modules.oauthclient.contrib import orcid
       OAUTHCLIENT_REMOTE_APPS = dict(
           orcid=orcid.REMOTE_APP,
       )

       ORCID_APP_CREDENTIALS = dict(
           consumer_key="changeme",
           consumer_secret="changeme",
       )

  Note, if you want to use the ORCID sandbox, use ``orcid.REMOTE_SANDBOX_APP``
  instead of ``orcid.REMOTE_APP``.

2. Register a new application with ORCID. When registering the
   application ensure that the *Redirect URI* points to:
   ``CFG_SITE_SECURE_URL/oauth/authorized/orcid/`` (note, ORCID does not
   allow localhost to be used, thus testing on development machines is
   somewhat complicated by this).


3. Grab the *Client ID* and *Client Secret* after registering the application
   and add them to your instance configuration (``invenio.cfg``):

   .. code-block:: python

       ORCID_APP_CREDENTIALS = dict(
           consumer_key="<CLIENT ID>",
           consumer_secret="<CLIENT SECRET>",
       )

4. Now go to ``CFG_SITE_SECURE_URL/oauth/login/orcid/`` (e.g.
   http://localhost:4000/oauth/login/orcid/)

5. Also, you should see ORCID listed under Linked accounts:
   http://localhost:4000//account/settings/linkedaccounts/

By default the ORCID module will try first look if a link already exists
between a ORCID account and a user. If no link is found, the user is asked
to provide an email address to sign-up.

In templates you can add a sign in/up link:

.. code-block:: jinja

    <a href="{{url_for('oauthclient.login', remote_app='orcid')}}">Sign in with ORCID</a>

"""

import copy

REMOTE_APP = dict(
    title='ORCID',
    description='Connecting Research and Researchers.',
    icon='',
    authorized_handler="invenio.modules.oauthclient.handlers"
                       ":authorized_signup_handler",
    disconnect_handler="invenio.modules.oauthclient.handlers"
                       ":disconnect_handler",
    signup_handler=dict(
        info="invenio.modules.oauthclient.contrib.orcid:account_info",
        setup="invenio.modules.oauthclient.contrib.orcid:account_setup",
        view="invenio.modules.oauthclient.handlers:signup_handler",
    ),
    params=dict(
        request_token_params={'scope': '/authenticate'},
        base_url='https://pub.orcid.com/',
        request_token_url=None,
        access_token_url="https://pub.orcid.org/oauth/token",
        access_token_method='POST',
        authorize_url="https://orcid.org/oauth/authorize",
        app_key="ORCID_APP_CREDENTIALS",
        content_type="application/json",
    )
)
""" ORCID Remote Application. """

REMOTE_SANDBOX_APP = copy.deepcopy(REMOTE_APP)
"""ORCID Sandbox Remote Application."""

REMOTE_SANDBOX_APP['params'].update(dict(
    base_url="https://api.sandbox.orcid.org/",
    access_token_url="https://api.sandbox.orcid.org/oauth/token",
    authorize_url="https://sandbox.orcid.org/oauth/authorize",
))


def account_info(remote, resp):
    """ Retrieve remote account information used to find local user. """
    return dict(email=None, nickname=None)


def account_setup(remote, token):
    """ Perform additional setup after user have been logged in. """
    pass
