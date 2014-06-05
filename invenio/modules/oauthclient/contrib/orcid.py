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
        access_token_method='GET',
        authorize_url="https://orcid.org/oauth/authorize",
        app_key="ORCID_APP_CREDENTIALS",
    )
)


def account_info(remote, resp):
    return dict(email=None, nickname=None)


def account_setup(remote, token):
    pass
