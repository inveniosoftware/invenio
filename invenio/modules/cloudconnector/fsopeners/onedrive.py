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

"""
Factory for OneDrive.

--------------------

Please note, when using onedrive and this factory the redirect url has
to be a real web site e.g. "https://invenio.com" and not localhost.
"""

from fs.errors import ResourceNotFoundError

from invenio.base.globals import cfg
from invenio.ext.fs.cloudfs.onedrivefs import OneDriveFS
from invenio.ext.sqlalchemy import db
from invenio.modules.accounts.models import User
from invenio.modules.cloudconnector.errors import (CloudRedirectUrl,
                                                   ErrorBuildingFS)


class Factory(object):

    """OneDrive Factory."""

    def build_fs(self, current_user, credentials, root=None,
                 callback_url=None, request=None, session=None):
        """Build OneDrive filesystem."""
        from onedrive import api_v5

        if root == "/":
            root = cfg['CFG_ONEDRIVE_ROOT']

        if credentials.get('access_token') is not None:
            try:
                filesystem = OneDriveFS(root, credentials)
                filesystem.about()
                filesystem.getinfo(root)
                return filesystem
            except ResourceNotFoundError:
                if(root != "/"):
                    filesystem = OneDriveFS("/", credentials)

                # Fix for onedrive, if a folder with the same name exists
                # it returns a 400 error, but that error is returned in
                # most cases so it's impossible to know what happened.
                # This is a monkey workaround, where I hope that
                # this folder already exits
                try:
                    resp = filesystem.makedir("/invenio")
                    filesystem = OneDriveFS(resp, credentials)
                    credentials['root'] = resp
                    self._update_cloudutils_settings(
                        current_user, {'onedrive': credentials})
                    return filesystem
                except:
                    filesystem = OneDriveFS("/", credentials)
                    info = filesystem.listdirinfo()
                    for one in info:
                        if one[1]['title'] == "invenio":
                            credentials['root'] = one[1]['id']
                            break
                    self._update_cloudutils_settings(
                        current_user, {'onedrive': credentials})
                    raise ErrorBuildingFS()
            except:
                new_data = {
                    'onedrive': {
                        'access_token': None,
                        'refresh_token': None,
                        'redirect_uri': None,
                        'scope': None,
                        'client_id': None,
                        'client_secret': None,
                        'root': credentials.get("root", "/")
                        }
                    }
                self._update_cloudutils_settings(current_user, new_data)
                x = api_v5.OneDriveAPI()
                x.auth_redirect_uri = callback_url
                x.client_id = cfg['CFG_ONEDRIVE_CLIENT_ID']
                x.client_secret = cfg['CFG_ONEDRIVE_CLIENT_SECRET']
                x.auth_scope = cfg['CFG_ONEDRIVE_SCOPE']
                url = x.auth_user_get_url()
                raise CloudRedirectUrl(url)

        elif 'code' in request.args:
            try:
                x = api_v5.OneDriveAPI()
                x.auth_redirect_uri = callback_url
                x.client_id = cfg['CFG_ONEDRIVE_CLIENT_ID']
                x.client_secret = cfg['CFG_ONEDRIVE_CLIENT_SECRET']
                x.auth_scope = cfg['CFG_ONEDRIVE_SCOPE']
                x.auth_code = request.args['code']
                x.auth_get_token()

                credentials_new = {'access_token': x.auth_access_token,
                                   'refresh_token': x.auth_refresh_token,
                                   }
            except Exception as exc:
                raise ErrorBuildingFS(exc)

            new_data = {
                'onedrive': {
                    'access_token': credentials_new['access_token'],
                    'refresh_token': credentials_new['refresh_token'],
                    'redirect_uri': callback_url,
                    'scope': cfg['CFG_ONEDRIVE_SCOPE'],
                    'client_id': cfg['CFG_ONEDRIVE_CLIENT_ID'],
                    'client_secret': cfg['CFG_ONEDRIVE_CLIENT_SECRET'],
                    'root': credentials.get("root", "/")
                }
            }
            self._update_cloudutils_settings(current_user, new_data)

            return self.build_fs(current_user, new_data.get('onedrive'),
                                 new_data.get('onedrive').get('root'),
                                 callback_url, None, session)

        elif callback_url is not None:
            new_data = {'onedrive': {
                'access_token': None,
                'refresh_token': None,
                'redirect_uri': None,
                'scope': None,
                'client_id': None,
                'client_secret': None,
                'root': credentials.get("root", "/")
                }
            }
            self._update_cloudutils_settings(current_user, new_data)
            x = api_v5.OneDriveAPI()
            x.auth_redirect_uri = callback_url
            x.client_id = cfg['CFG_ONEDRIVE_CLIENT_ID']
            x.client_secret = cfg['CFG_ONEDRIVE_CLIENT_SECRET']
            x.auth_scope = cfg['CFG_ONEDRIVE_SCOPE']
            url = x.auth_user_get_url()
            raise CloudRedirectUrl(url)
        else:
            raise ErrorBuildingFS(
                "Insufficient data provided to the cloud builder")

    def _update_cloudutils_settings(self, current_user, new_data):
        """Update cloudutils settings for current user."""
        user = User.query.get(current_user.get_id())
        settings = user.settings
        cloudutils_settings = settings.get("cloudutils_settings")

        if cloudutils_settings:
            cloudutils_settings.update(new_data)

            settings.update(settings)
        else:
            settings.update({"cloudutils_settings": new_data})

        user.settings = settings
        db.session.merge(user)
        db.session.commit()
        current_user.reload()
