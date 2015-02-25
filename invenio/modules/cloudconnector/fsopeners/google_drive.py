# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014 CERN.
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

"""Google drive Filesystem Factory.

A factory for google drive file system.

You might need to add following config variable::

    OAUTHCLIENT_REMOTE_APPS = dict(
        google_drive=dict(  # name of remote app used in urls
            title='Google Drive', # This is used in the linked account view to
                                  # display a name and a description.
            description='Data collaboration platform.',
            params=dict(
                # usually important to define which scopes you want to request.
                request_token_params={"scope":"openid profile email
                https://www.googleapis.com/auth/drive",
                "approval_promt":"force", "access_type":"offline"},
                base_url='https://accounts.google.com/',
                request_token_url=None,
                access_token_url="https://accounts.google.com/o/oauth2/token",
                authorize_url="https://accounts.google.com/o/oauth2/auth",
                access_token_method='POST',
                app_key="GOOGLE_DRIVE_APP_CREDENTIALS",
                # defines which other config variable stores the client
                # key/secret
            )
        ),
    )

    GOOGLE_DRIVE_APP_CREDENTIALS = dict(
        consumer_key="changeme",
        consumer_secret="changeme",
    )
"""

from flask import url_for

from invenio.ext.fs.cloudfs.googledrivefs import GoogleDriveFS
from invenio.modules.cloudconnector.errors import CloudRedirectUrl
from invenio.modules.oauthclient.views.client import oauth
from invenio.modules.oauthclient.models import RemoteToken


class Factory(object):

    """Google drive Factory."""

    def build_fs(self, current_user, credentials, root=None,
                 callback_url=None, request=None, session=None):
        """Build google drive filesystem."""
        url = url_for('oauthclient.login', remote_app='google_drive')

        client_id = oauth.remote_apps['google_drive'].consumer_key
        client_secret = oauth.remote_apps['google_drive'].consumer_secret
        user_id = current_user.get_id()
        token = RemoteToken.get(user_id, client_id)

        if token is not None:
            credentials = {
                'access_token': token.access_token,
                'client_id': client_id,
                'client_secret': client_secret,
                'refresh_token':
                token.remote_account.extra_data.get('refresh_token'),
                'token_expiry': None,
                'token_uri':
                'https://accounts.google.com/o/oauth2/token'
                }
            try:
                filesystem = GoogleDriveFS(root, credentials)
                filesystem.about()
                return filesystem
            except Exception:
                raise CloudRedirectUrl(url, __name__)
        else:
            raise CloudRedirectUrl(url, __name__)
