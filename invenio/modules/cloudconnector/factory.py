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
 A general factory for cloudutils, use this factory to build all cloud
 services.
"""

from invenio.utils.datastructures import LaziestDict
from invenio.modules.cloudconnector.config import CFG_CLOUD_UTILS_ENABLED_SERVICES
from werkzeug.utils import import_string
from flask.ext.login import current_user
from flask import session, request

from invenio.modules.cloudconnector.errors import ErrorBuildingFS
from flask.helpers import url_for

def _find_factory(key):
    if key in CFG_CLOUD_UTILS_ENABLED_SERVICES:
        return import_string('invenio.modules.cloudconnector.fsopeners.%s_factory:Factory' % key)
    else:
        raise ErrorBuildingFS("Unknown File system")

FACTORIES = LaziestDict(_find_factory)


class CloudServiceFactory(object):
    def get_fs(self, uri):
        service_name = uri.split("://")[0]
        root = uri.split("://")[1]
        cloudutils_settings = current_user.get('cloudutils_settings', {})
        credentials = cloudutils_settings.get(service_name, {})

        #Fix, if credentials are None, this will never happen when using this
        # software but can happen if someone manually sets stuff
        if credentials == None:
            credentials = {}

        #Get the root directory, every user can have his own root directory inside of
        # every service settings
        if(root == None or root == "/" or root == ""):
            root = credentials.get("root", "/")

        Factory = FACTORIES.get(service_name)()
        callback_url = url_for('cloudutils.callback', service=service_name, _external = True)

        filesystem = Factory.build_fs(current_user, credentials,
                                  root, callback_url,
                                  request, session
                                  )

        return filesystem
