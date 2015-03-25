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

"""
The oauthclient module provides OAuth web authorization support in Invenio.

OAuth client support is typically used to allow features such as social login
(e.g. Sign in with Twitter) and access to resources owner by a specific user
at a remote service. Both OAuth 1.0 and OAuth 2.0 are supported.

The module contains:

- Views: OAuth login and authorized endpoints, linked account settings and
  sign-up handling.
- Client: A client to interact with remote applications.
- Contrib: Ready-to-use GitHub and ORCID remote applications.
- Models: Persistence layer for OAuth access tokens including support for
  storing extra data together with a token.
- Handlers: Customizable handlers for deciding what happens when a user
  authorizes a request.

Authorization Flow Overview
---------------------------
OAuth 2.0 defines several possible *authorization flows* depending on the type
of client you are authorizing (e.g. web application, browser-based app or
mobile apps). The *web application client* is the only authorization flow
supported by this module.

A typical web application authorization flow involves the following roles:

- **Client** (i.e. a third-party application in this case your Invenio
  instance).
- **Resource server** (i.e. the remote service).
- **Resource owner** (i.e. the user).

The web application authorization flow is used to e.g. allow sign in with
service X. The end result of a completed authorization flow is an
*access token* which allows the *client* to access a *resource
owner's* resources on the *resource server*.

Before the authorization flow is started, the *client* must be registered with
the *resource server*. The resource server will provide a *client key* and
*client secret* to the client. Following is an example of the authorization
flow with ORCID:

1. The resource owner (i.e. the user) clicks "Sign in with ORCID":

   .. code-block:: http

      GET /oauth/login/orcid/ HTTP/1.1

   The *client* redirects the user to the resource server's *authorize URL*.

   .. code-block:: http

      HTTP/1.1 302 FOUND
      Location: https://orcid.org/oauth/authorize?response_type=code&client_id=<CLIENT KEY>&redirect_uri=https://localhost/oauth/authorized/orcid/&scope=/authenticate&state=...

  Note, following query parameters in the authorize URL:

   - ``response_type`` - Must be ``code`` for web application flow (named
     authorization code grant).
   - ``client_id`` - The client key provided by the resource server when the
     client was registered.
   - ``redirect_uri`` - The URL the resource server will redirect the resource
     owner back to after having authorized the request. Usually the redirect
     URL must be provided when registering the client application with the
     resource server.
   - ``scope`` - Defines the level of access (defined by the resource server)
   - ``state`` - A token to mitigate against cross-site request forgery (CRSF).
     In Invenio this state is a JSON Web Signature (JWS) that by default
     expires after 5 minutes.

2. The *resource server* asks the user to sign-in (if not already signed in).

3. The *resource server* asks the *resource owner* to authorize or reject the
   client's request for access.

4. If the *resource owner* authorizes the request, the *resource server*
   redirects the *resource owner* back to the *client* web application (using
   the ``redirect_uri`` provided in step 1):

   .. code-block:: http

       HTTP/1.1 302 FOUND
       Location: https://localhost/oauth/authorized/orcid/?code=<CODE>&state=...

   Included in the redirect is a one-time *auth code* which is typically only
   valid for short time (seconds), as well as the ``state`` token initially
   provided.

5. The client now exchanges the one time *auth code* for an *access token*
   using the resource server's *access token URL*:


   .. code-block:: http

      POST https://pub.orcid.org/oauth/token HTTP/1.1
      Content-Type: application/x-www-form-urlencoded

      grant_type=authorization_code&
      code=<CODE>&
      redirect_uri=<REDIRECT_URI>&
      client_id=<CLIENT KEY>&
      client_secret=<CLIENT SECRET>

   The resource server replies with an access token:

   .. code-block:: json

      {"access_token": "<ACCESS TOKEN>}

   The client stores the access token, and can use it to make authenticated
   requests to the *resource server*:

   .. code-block:: http

      GET https://api.example.org/ HTTP/1.1
      Authorization: Bearer <ACCESS TOKEN>


Further reading:

- `RFC6749 - The OAuth 2.0 Authorization Framework <http://tools.ietf.org/html/rfc6749>`_

- `OAuth 2 Simplified <http://aaronparecki.com/articles/2012/07/29/1/oauth2-simplified>`_

- `Flask-OAuthlib <http://flask-oauthlib.readthedocs.org/en/latest/client.html>`_

- `OAuthlib <http://oauthlib.readthedocs.org/en/latest/>`_

Usage
-----

1. Edit your configuration. Ensure ``invenio.modules.oauthclient`` is included
   in ``PACKAGES`` (by default it's included).


2. Define remote resource serves in the ``OAUTHCLIENT_REMOTE_APPS``.

   .. code-block:: python

    PACKAGES = [
        # ...
        'invenio.modules.oauthclient',
        # ...
    ]

    OAUTHCLIENT_REMOTE_APPS = dict(
        # ...
    )

See :ref:`module_oauthclient_conf` for how to define remote applications in
``OAUTHCLIENT_REMOTE_APPS``.
"""
