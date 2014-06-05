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

REMOTE_APP = dict(
    title='GitHub',
    description='Software collaboration platform.',
    icon='fa fa-github',
    authorized_handler="invenio.modules.oauthclient.handlers"
                       ":authorized_signup_handler",
    disconnect_handler="invenio.modules.oauthclient.handlers:disconnect",
    signup_handler=dict(
        info="invenio.modules.oauthclient.contrib.github:account_info",
        setup="invenio.modules.oauthclient.contrib.github:account_setup",
        view="invenio.modules.oauthclient.handlers:signup_handler",
    ),
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


def account_info(remote, resp):
    return dict(email=None, nickname=None)


def account_setup(remote, token):
    pass
