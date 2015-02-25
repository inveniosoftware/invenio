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

"""DropBox Filesystem Factory.

A factory for dropbox file system.

You might need to add following config variable::

    OAUTHCLIENT_REMOTE_APPS = dict(
        dropbox=dict( # name of remote app used in urls
            title='Dropbox', # This is used in the linked account view to
                             # display a name and a description.
            description='Data collaboration platform.',
            icon='fa fa-dropbox',
            params=dict(
                request_token_params={},
                # usually important to define which scopes you want to request.
                base_url='https://api.dropbox.com/',
                request_token_url=None,
                access_token_url="https://api.dropbox.com/1/oauth2/token",
                authorize_url="https://www.dropbox.com/1/oauth2/authorize",
                access_token_method='POST',
                app_key="DROPBOX_APP_CREDENTIALS",
                # defines which other config variable stores the client
                # key/secret (oauth1 calls this consumer key/secret)
            )
        ),
    )

    DROPBOX_APP_CREDENTIALS = dict(
        consumer_key="changeme",
        consumer_secret="changeme",
    )
"""

from flask import url_for
from fs.errors import ResourceNotFoundError

from invenio.ext.fs.cloudfs.dropboxfs import DropboxFS
from invenio.modules.cloudconnector.errors import CloudRedirectUrl
from invenio.modules.oauthclient.models import RemoteToken
from invenio.modules.oauthclient.views.client import oauth


class Factory(object):

    """Dropbox Factory."""

    def build_fs(self, current_user, credentials, root=None,
                 callback_url=None, request=None, session=None):
        """Build dropbox filesystem."""
        url = url_for('oauthclient.login', remote_app='dropbox')
        client_id = oauth.remote_apps['dropbox'].consumer_key
        user_id = current_user.get_id()
        token = RemoteToken.get(user_id, client_id)

        if token is not None:
            credentials = {'access_token': token.access_token}
            try:
                filesystem = DropboxFS(root, credentials)
                filesystem.about()
                return filesystem
            except ResourceNotFoundError:
                if(root != "/"):
                    filesystem = DropboxFS("/", credentials)
                filesystem.makedir(root, recursive=True)
                filesystem = DropboxFS(root, credentials)
                return filesystem
            except:
                raise CloudRedirectUrl(url, __name__)
        else:
            raise CloudRedirectUrl(url, __name__)
