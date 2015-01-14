# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2014, 2015 CERN.
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

"""Pre-configured remote application for enabling sign in/up with ORCID.

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

from flask import current_app, session
from flask.ext.login import current_user

from invenio.ext.sqlalchemy.utils import session_manager


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
        authorize_url="https://orcid.org/oauth/authorize#show_login",
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
    authorize_url="https://sandbox.orcid.org/oauth/authorize#show_login",
))


def account_info(remote, resp):
    """Retrieve remote account information used to find local user."""
    account_info = dict(external_id=resp.get("orcid"), external_method="orcid")

    return account_info


@session_manager
def account_setup(remote, token):
    """Perform additional setup after user have been logged in."""
    from invenio.modules.accounts.models import User, UserEXT
    from invenio.ext.sqlalchemy import db
    from ..handlers import token_session_key

    from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

    import json
    import requests

    orcid = session.get(token_session_key(remote.name) +
                        "_account_info").get("external_id")

    extra_data = {
        "orcid": orcid
        }
    token.remote_account.extra_data = extra_data

    try:
        user = User.query.join(UserEXT).filter_by(id=orcid,
                                                  method="orcid").one()
    except (MultipleResultsFound, NoResultFound):
        current_app.logger.exception("No user entry in userEXT.")

    # Fill user full name if not already set
    if user and not any([user.given_names, user.family_name]):
        # Query ORCID to get the real name
        request_url = 'http://orcid.org/{0}/orcid-bio'.format(orcid)

        headers = {'Accept': 'application/orcid+json'}
        response = requests.get(request_url, headers=headers)
        code = response.status_code

        if code == requests.codes.ok:
            try:
                orcid_bio = json.loads(response.content)
            except ValueError:
                current_app.logger.exception("Not valid JSON response from " +
                                             "ORCID:\n {0}".format(repr(orcid_bio)))
                return
            try:
                name = orcid_bio["orcid-profile"]["orcid-bio"]["personal-details"]
                user.given_names = name["given-names"]["value"]
                user.family_name = name["family-name"]["value"]
            except KeyError:
                current_app.logger.exception("Unexpected return format " +
                                             "from ORCID:\n {0}".format(repr(orcid_bio)))
                return
            db.session.add(user)
            # Refresh user cache
            current_user.reload()
