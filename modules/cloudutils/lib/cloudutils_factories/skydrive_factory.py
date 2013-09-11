# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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

"""
 A factory for skydrive file system
 Please note, when using skydrive and this factory the redirect url has
 to be a real web site e.g. "https://invenio.com" and not localhost.
"""

from datetime import datetime
from skydrive import api_v5
from fs.errors import ResourceNotFoundError
from invenio.websession_model import User
from invenio.sqlalchemyutils import db 
from invenio.cloudutils_config import * 
from invenio.SkyDriveFS import SkyDriveFS

from invenio.cloudutils import CloudRedirectUrl, \
                               ErrorBuildingFS
                               
class Factory(object):
    def build_fs(self, current_user, credentials, root=None, 
                          callback_url=None, request=None, session=None):
        
        if( root == "/"):
            root = CFG_SKYDRIVE_ROOT
            
        if credentials.get('access_token') != None:
            try:
                filesystem = SkyDriveFS(root, credentials)
                filesystem.about()
                filesystem.getinfo(root)
                return filesystem
            except ResourceNotFoundError, e:
                if(root != "/"):
                    filesystem = SkyDriveFS("/", credentials)
                
                #Fix for skydrive, if a folder with the same name exists
                # it returns a 400 error, but that error is returned in 
                # most cases so it's impossible to know what happened.
                # This is a monkey workaround, where I hope that
                # this folder already exits
                try:
                    resp = filesystem.makedir("/invenio")
                    filesystem = SkyDriveFS(resp, credentials)
                    credentials['root'] = resp
                    self._update_cloudutils_settings(current_user, {'skydrive': credentials})
                    return filesystem
                except:
                    filesystem = SkyDriveFS("/", credentials)
                    info = filesystem.listdirinfo()
                    for one in info:
                        if( one[1]['title'] == "invenio" ):
                            credentials['root'] = one[1]['id']
                            break
                    self._update_cloudutils_settings(current_user, {'skydrive': credentials})
                    raise ErrorBuildingFS()
            except:
                new_data = {
                    'skydrive': {
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
                x = api_v5.SkyDriveAPI()
                x.auth_redirect_uri = callback_url
                x.client_id = CFG_SKYDRIVE_CLIENT_ID
                x.client_secret = CFG_SKYDRIVE_CLIENT_SECRET
                x.auth_scope = CFG_SKYDRIVE_SCOPE
                url = x.auth_user_get_url()
                raise CloudRedirectUrl(url)
          
        elif  request.args.has_key('code'):
            try:
                x = api_v5.SkyDriveAPI()
                x.auth_redirect_uri = callback_url
                x.client_id = CFG_SKYDRIVE_CLIENT_ID
                x.client_secret = CFG_SKYDRIVE_CLIENT_SECRET
                x.auth_scope = CFG_SKYDRIVE_SCOPE
                x.auth_code = request.args['code']
                x.auth_get_token()

                credentials_new = {'access_token': x.auth_access_token, 
                                   'refresh_token': x.auth_refresh_token,
                                   }
            except Exception, e:
                raise ErrorBuildingFS(e)
            
            new_data = {
                'skydrive': {
                    'access_token': credentials_new['access_token'],
                    'refresh_token': credentials_new['refresh_token'],
                    'redirect_uri': callback_url,
                    'scope': CFG_SKYDRIVE_SCOPE,
                    'client_id': CFG_SKYDRIVE_CLIENT_ID,
                    'client_secret': CFG_SKYDRIVE_CLIENT_SECRET,
                    'root': credentials.get("root", "/")
                }
            }
            self._update_cloudutils_settings(current_user, new_data)
            
            return self.build_fs(current_user, new_data.get('skydrive'),
                                 new_data.get('skydrive').get('root'), 
                                 callback_url, None, session)
            
        elif callback_url != None:
            new_data = {
                    'skydrive': {
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
            x = api_v5.SkyDriveAPI()
            x.auth_redirect_uri = callback_url
            x.client_id = CFG_SKYDRIVE_CLIENT_ID
            x.client_secret = CFG_SKYDRIVE_CLIENT_SECRET
            x.auth_scope = CFG_SKYDRIVE_SCOPE
            url = x.auth_user_get_url()
            raise CloudRedirectUrl(url)
        else:
            raise ErrorBuildingFS("Insufficient data provided to the cloud builder")
        
    def _update_cloudutils_settings(self, current_user, new_data):
        # Updates cloudutils settings in DataBase and refreshes current user
        user = User.query.get(current_user.get_id())
        settings = user.settings
        cloudutils_settings = settings.get("cloudutils_settings")
        
        if( cloudutils_settings ):
            cloudutils_settings.update( new_data )
            
            settings.update(settings)
        else:
            settings.update({"cloudutils_settings" : new_data})
        
        user.settings = settings
        db.session.merge(user)
        db.session.commit()
        current_user.reload()