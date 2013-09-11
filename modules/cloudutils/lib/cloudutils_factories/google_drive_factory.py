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

"""A factory for google drive file system"""

from invenio.GoogleDriveFS import GoogleDriveFS
from oauth2client.client import OAuth2WebServerFlow
from datetime import datetime
from fs.errors import ResourceNotFoundError
from invenio.websession_model import User
from invenio.sqlalchemyutils import db 
from invenio.cloudutils_config import * 
from invenio.cloudutils import CloudRedirectUrl, \
                               ErrorBuildingFS

class Factory(object):
    def build_fs(self, current_user, credentials, root=None, callback_url=None, request=None, session=None):
        if( request == None and credentials.get('access_token') == None and callback_url==None ):
                #Google drive can't work if request and access_token are None
                raise ErrorBuildingFS("Insufficient data provided ")
        elif( credentials.get('access_token') != None  ):
            try:
                filesystem = GoogleDriveFS(root, credentials)
                filesystem.getinfo(root)
                return filesystem
            except ResourceNotFoundError, e:
                if(root != "/"):
                    filesystem = GoogleDriveFS("/", credentials)
                resp = filesystem.makedir("/invenio")
                filesystem = GoogleDriveFS(resp, credentials)
                credentials['root'] = resp
                self._update_cloudutils_settings(current_user, {'google_drive': credentials})
                return filesystem
            except Exception, e: 
                new_data = {
                    'google_drive': {
                        'access_token': None,
                        'client_id': None,
                        'client_secret': None,
                        'refresh_token': None,
                        'token_expiry': None,
                        'token_uri': None,
                        'user_agent': None,
                        'root': credentials.get("root", "/")
                        }
                    }
                self._update_cloudutils_settings(current_user, new_data)
                
                flow = OAuth2WebServerFlow(CFG_GOOGLE_DRIVE_CLIENT_ID, 
                                           CFG_GOOGLE_DRIVE_CLIENT_SECRET, 
                                           CFG_GOOGLE_DRIVE_SCOPE,
                                           callback_url,
                                           approval_prompt='force'
                                           )
                url = flow.step1_get_authorize_url()
                raise CloudRedirectUrl(url)
        elif request.args.has_key('code'):
            try:
                flow = OAuth2WebServerFlow(CFG_GOOGLE_DRIVE_CLIENT_ID, 
                                           CFG_GOOGLE_DRIVE_CLIENT_SECRET, 
                                           CFG_GOOGLE_DRIVE_SCOPE,
                                           callback_url,
                                           approval_prompt='force')
                credentials_new = flow.step2_exchange( request.args['code'] )
            except Exception, e:
                raise ErrorBuildingFS(e)
            
            
            new_data = {
                'google_drive': {
                    'access_token': credentials_new.access_token,
                    'client_id': credentials_new.client_id,
                    'client_secret': credentials_new.client_secret,
                    'refresh_token': credentials_new.refresh_token,
                    'token_expiry': datetime.strftime(credentials_new.token_expiry, "%Y, %m, %d, %H, %M, %S, %f" ),
                    'token_uri': credentials_new.token_uri,
                    'user_agent': credentials_new.user_agent,
                    'root': credentials.get("root", "/")
                }
            }
            
            
            self._update_cloudutils_settings(current_user, new_data)
            
            # Retry with new data, request is now None, we don't want it to process
            # the request again.
            return self.build_fs(current_user, 
                                               new_data.get('google_drive'), 
                                               new_data.get('google_drive').get('root'), 
                                               callback_url, 
                                               None
                                               )
        elif( callback_url != None ):
            new_data = {
                    'google_drive': {
                        'access_token': None,
                        'client_id': None,
                        'client_secret': None,
                        'refresh_token': None,
                        'token_expiry': None,
                        'token_uri': None,
                        'user_agent': None,
                        'root': credentials.get("root", "/")
                        }
                    }
            self._update_cloudutils_settings(current_user, new_data)
            flow = OAuth2WebServerFlow(CFG_GOOGLE_DRIVE_CLIENT_ID, 
                                           CFG_GOOGLE_DRIVE_CLIENT_SECRET, 
                                           CFG_GOOGLE_DRIVE_SCOPE,
                                           callback_url,
                                           approval_prompt='force'
                                           )
            url = flow.step1_get_authorize_url()
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