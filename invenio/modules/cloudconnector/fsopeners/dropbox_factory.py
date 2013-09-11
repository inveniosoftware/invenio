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

"""A factory for dropbox file system"""

import dropbox

from fs.errors import ResourceNotFoundError

from invenio.base.globals import cfg
from invenio.ext.fs.cloudfs.dropboxfs import DropboxFS
from invenio.ext.sqlalchemy import db
from invenio.modules.accounts.models import User
from invenio.modules.cloudconnector.errors import CloudRedirectUrl, \
    ErrorBuildingFS


class Factory(object):
    def build_fs(self, current_user, credentials, root=None,
                 callback_url=None, request=None, session=None):

            if session == None and credentials.get('access_token') == None:
                #Dropbox can't work if session and access_token are None
                raise ErrorBuildingFS("Session or credentials need to be set "
                                      "when building dropbox")
            elif credentials.get('access_token') != None:
                try:
                    filesystem = DropboxFS(root, credentials)
                    filesystem.about()
                    return filesystem
                except ResourceNotFoundError, e:
                    if(root != "/"):
                        filesystem = DropboxFS("/", credentials)
                    filesystem.makedir(root, recursive=True)
                    filesystem = DropboxFS(root, credentials)
                    return filesystem
                except:
                    #Remove the old stored credentials
                    new_data = {'dropbox':
                        {'uid': None,
                         'access_token': None,
                         }
                    }
                    self._update_cloudutils_settings(current_user, new_data)
                    flow = dropbox.client.DropboxOAuth2Flow(
                        cfg['CFG_DROPBOX_KEY'],
                        cfg['CFG_DROPBOX_SECRET'],
                        callback_url, session,
                        cfg['CFG_DROPBOX_CSRF_TOKEN'],
                    )

                    url = flow.start()
                    raise CloudRedirectUrl(url, __name__)
            elif 'code' in request.args:
                try:
                    access_token, uid, url_state = dropbox.client.DropboxOAuth2Flow(
                        cfg['CFG_DROPBOX_KEY'],
                        cfg['CFG_DROPBOX_SECRET'],
                        callback_url, session,
                        cfg['CFG_DROPBOX_CSRF_TOKEN'],
                    ).finish(request.args)
                except Exception, e:
                    raise ErrorBuildingFS(e)

                new_data = {
                            'dropbox': {
                                    'uid': uid,
                                    'access_token': access_token
                                    }
                           }
                self._update_cloudutils_settings(current_user, new_data)

                filesystem = DropboxFS(root, {"access_token": access_token})
                return filesystem
            elif session is not None:
                flow = dropbox.client.DropboxOAuth2Flow(
                    cfg['CFG_DROPBOX_KEY'],
                    cfg['CFG_DROPBOX_SECRET'],
                    callback_url, session,
                    cfg['CFG_DROPBOX_CSRF_TOKEN'],
                )

                url = flow.start()
                raise CloudRedirectUrl(url, __name__)

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
