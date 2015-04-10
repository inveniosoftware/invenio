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

"""Configuration variables for defining remote applications.

================================ ==============================================
`OAUTHCLIENT_REMOTE_APPS`        Dictionary of remote applications. See example
                                 below. **Default:** ``{}``.
`OAUTHCLIENT_SESSION_KEY_PREFIX` Prefix for the session key used to store the
                                 an access token. **Default:** ``oauth_token``.
`OAUTHCLIENT_STATE_EXPIRES`      Number of seconds after which the state token
                                 expires. Defaults to 300 seconds.
================================ ==============================================

Each remote application must be defined in the ``OAUTHCLIENT_REMOTE_APPS``
dictionary, where the keys are the application names and the values the
configuration parameters for the application.

.. code-block:: python

    OAUTHCLIENT_REMOTE_APPS = dict(
        myapp=dict(
            # configuration values for myapp ...
        ),
    )

The application name is used in the login, authorized, sign-up and disconnect
endpoints:

- Login endpoint: ``/oauth/login/<REMOTE APP>/``.
- Authorized endpoint: ``/oauth/authorized/<REMOTE APP>/``.
- Disconnect endpoint: ``/oauth/disconnect/<REMOTE APP>/``.
- Sign up endpoint: ``/oauth/login/<REMOTE APP>/``.


Remote application
^^^^^^^^^^^^^^^^^^
Configuration of a single remote application is a dictionary with the following
keys:

- ``title`` - Title of remote application. Displayed to end-users under Account
  > Linked accounts.
- ``description`` - Short description of remote application. Displayed to
  end-users under Account > Linked accounts.
- ``icon`` - CSS class for icon of service (e.g. ``fa fa-github`` for using the
  Font-Awesome GitHub icon). Displayed to end-users.
- ``params`` - Flask-OAuthlib remote application parameters..
- ``authorized_handler`` - Import path to authorized callback handler.
- ``disconnect_handler`` - Import path to disconnect callback handler.
- ``signup_handler`` - A dictionary of import path to sign up callback handler.
- ``remember`` - Boolean indicating if the session should be permament.

.. code-block:: python

    OAUTHCLIENT_REMOTE_APPS = dict(
        myapp=dict(
            title='...',
            description='...',
            icon='...',
            authorized_handler="...",
            disconnect_handler="...",
            signup_handler=dict(
                info="...",
                setup="...",
                view="...",
            ),
            params=dict(...),
            remember=True
            )
        )
    )


Flask-OAuthlib parameters
^^^^^^^^^^^^^^^^^^^^^^^^^
The Flask-OAuthlib parameters defines the remote application OAuth endpoints as
well as the client id and secret. Full description of these parameters are
given in the `Flask-OAuthlib documentation <https://flask-oauthlib.readthedocs.org/en/latest/client.html>`_.

Normally you will have to browse the remote application's API documentation to
find which URLs and scopes to use.

Below is an example for GitHub:

.. code-block:: python

    OAUTHCLIENT_REMOTE_APPS = dict(
        github=dict(
            # ...
            params=dict(
                request_token_params={'scope': 'user:email'},
                base_url='https://api.github.com/',
                request_token_url=None,
                access_token_url="https://github.com/login/oauth/access_token",
                access_token_method='POST',
                authorize_url="https://github.com/login/oauth/authorize",
                app_key="GITHUB_APP_CREDENTIALS",
            )
        )
    )

    GITHUB_APP_CREDENTIALS=dict(
        consumer_key="changeme"
        consumer_secret="changeme"
    )

The ``app_key`` parameter allows you to put your sensitive client id and secret
in your instance configuration (``var/invenio.base-instance/invenio.cfg``).

Handlers
^^^^^^^^
Handlers allow customizing oauthclient endpoints for each remote
application:

- Authorized endpoint: ``/oauth/authorized/<REMOTE APP>/``.
- Disconnect endpoint: ``/oauth/disconnect/<REMOTE APP>/``.
- Sign up endpoint: ``/oauth/login/<REMOTE APP>/``.

By default only authorized and disconnect handlers are required, and Invenio
provide default implementation that stores the access token in the user session
as well as to the database if the user is authenticated:


.. code-block:: python

    OAUTHCLIENT_REMOTE_APPS = dict(
        myapp=dict(
            # ...
            authorized_handler="invenio.modules.oauthclient.handlers"
                       ":authorized_default_handler",
            disconnect_handler="invenio.modules.oauthclient.handlers"
                       ":disconnect_handler",
            )
            # ...
        )
    )

If you want to provide sign in/up functionality using oauthclient, Invenio
comes with a default handler that will try to find a matching local user for
a given authorize request.

.. code-block:: python

    OAUTHCLIENT_REMOTE_APPS = dict(
        orcid=dict(
            # ...
            authorized_handler="invenio.modules.oauthclient.handlers"
                       ":authorized_signup_handler",
            disconnect_handler="invenio.modules.oauthclient.handlers"
                       ":disconnect_handler",
            )
            signup_handler=dict(
                info="invenio.modules.oauthclient.contrib.orcid:account_info",
                setup="invenio.modules.oauthclient.contrib.orcid:account_setup",
                view="invenio.modules.oauthclient.handlers:signup_handler",
            ),
            # ...
        )
    )
"""

from __future__ import unicode_literals

OAUTHCLIENT_REMOTE_APPS = {}
"""Configuration of remote applications."""

OAUTHCLIENT_SESSION_KEY_PREFIX = "oauth_token"
"""Session key prefix used when storing the access token for a remote app."""

OAUTHCLIENT_STATE_EXPIRES = 300
"""Number of seconds after which the state token expires."""

OAUTHCLIENT_STATE_ENABLED = True
"""Internal variable used to disable state validation during tests."""
