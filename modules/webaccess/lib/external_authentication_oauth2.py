# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012 CERN.
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
This module contains functions and methods to authenticate with OAuth2
providers.
"""

__revision__ = \
    "$Id$"

from invenio.config import CFG_SITE_SECURE_URL
from invenio.external_authentication import ExternalAuth
from invenio.containerutils import treasure_hunter

class ExternalOAuth2(ExternalAuth):
    """
    Contains methods for authenticate with an OAuth2 provider.
    """

    def __init__(self, enforce_external_nicknames = False):
        """Initialization"""
        ExternalAuth.__init__(self, enforce_external_nicknames)

        self.provider_name = None
        self.response = None
        self.msg = 0
        self.debug = 0
        self.debug_msg = ""


    def auth_user(self, username, password, req = None):
        """
        Tries to find email and identity of the user from OAuth2 provider. If it
        doesn't find any of them, returns (None, None)

        @param username: Isn't used in this function
        @type username: str

        @param password: Isn't used in this function
        @type password: str

        @param req: request
        @type req: invenio.webinterface_handler_wsgi.SimulatedModPythonRequest

        @rtype: str|NoneType, str|NoneType
        """
        from invenio.webinterface_handler import wash_urlargd
        from invenio.access_control_config import CFG_OAUTH2_CONFIGURATIONS
        from rauth.service import OAuth2Service
        from invenio.access_control_config import CFG_OAUTH2_PROVIDERS

        args = wash_urlargd(req.form, {
                            'code': (str, ''),
                            'provider': (str, '')
                            })

        self.provider_name = args['provider']

        if not self.provider_name:
            # If provider name isn't given
            self.msg = 21
            return None, None

        # Some providers doesn't construct return uri properly.
        # Since the callback uri is:
        # /youraccount/login?login_method=oauth2&provider=something
        # they may return to:
        # /youraccount/login?login_method=oauth2&provider=something?code=#
        # instead of
        # /youraccount/login?login_method=oauth2&provider=something&code=#
        if '?' in self.provider_name:
            (self.provider_name, args['code']) = \
        (
         self.provider_name[:self.provider_name.index('?')],
         self.provider_name[self.provider_name.index('?') + 1 + len("code="):]
         )

        if not self.provider_name in CFG_OAUTH2_PROVIDERS:
            self.msg = 22
            return None, None

        # Load the configurations to construct OAuth2 service
        config = CFG_OAUTH2_CONFIGURATIONS[self.provider_name]

        self.debug = config.get('debug', 0)

        provider = OAuth2Service(
                                 name = self.provider_name,
                                 consumer_key = config['consumer_key'],
                                 consumer_secret = config['consumer_secret'],
                                 access_token_url = config['access_token_url'],
                                 authorize_url = config['authorize_url'])

        data = dict(
                    code = args['code'],
                    client_id = config['consumer_key'],
                    client_secret = config['consumer_secret'],
                    # Construct redirect uri without having '/' character at the
                    # left most of SITE_SECURE_URL
                    redirect_uri = (CFG_SITE_SECURE_URL[:-1]
                                    if
                                    CFG_SITE_SECURE_URL[-1] == '/'
                                    else CFG_SITE_SECURE_URL) + \
                        '/youraccount/login?login_method=oauth2&provider=' + \
                        self.provider_name
                    )

        # Get the access token
        token = provider.get_access_token('POST', data = data)

        if token.content.has_key('error') or not \
                                        token.content.has_key('access_token'):
            if token.content['error'] == 'access_denied':
                self.msg = 21
                return None, None
            else:
                self.msg = 22
                return None, None

        if self.debug:
            self.debug_msg = str(token.content) + "<br/>"
            
        # Some providers send the user information and access token together.
        email, identity = self._get_user_email_and_id(token.content)

        if not identity:
            profile = provider.request('GET', config['request_url'].format(
                                    access_token=token.content['access_token']
                                    ))
            if self.debug:
                self.debug_msg += str(profile.content)

            email, identity = self._get_user_email_and_id(profile.content)

        if identity:
            # If identity is found, add the name of the provider at the
            # beginning of the identity because different providers may have
            # different users with same id.
            identity = "%s:%s" % (self.provider_name, identity)
        else:
            self.msg = 23

        if self.debug:
            self.msg = "<code>%s</code>" % self.debug_msg.replace("\n", "<br/>")
            return None, None
            
        return email, identity

    def fetch_user_nickname(self, username, password = None, req = None):
        """
        Fetches the OAuth2 provider for nickname of the user. If it doesn't
            find any, returns None.

        This function doesn't need username, password or req. They are exist
            just because this class is derived from ExternalAuth

        @param username: Isn't used in this function
        @type username: str

        @param password: Isn't used in this function
        @type password: str

        @param req: Isn't used in this function
        @type req: invenio.webinterface_handler_wsgi.SimulatedModPythonRequest

        @rtype: str or NoneType
        """
        from invenio.access_control_config import CFG_OAUTH2_CONFIGURATIONS

        if self.provider_name and self.response:
            path = None
            if CFG_OAUTH2_CONFIGURATIONS[self.provider_name].has_key(
                                                                     'nickname'
                                                                     ):
                path = CFG_OAUTH2_CONFIGURATIONS[self.provider_name]['nickname']

            if path:
                return treasure_hunter(self.response, path)
        else:
            return None

    def user_exists(self, email, req = None):
        """
        This function cannot be implemented for OAuth2 authentication.
        """
        raise NotImplementedError()


    def fetch_user_groups_membership(self, username, password = None,
                                     req = None):
        """
        This function cannot be implemented for OAuth2 authentication.
        """
        return {}

    def fetch_user_preferences(self, username, password = None, req = None):
        """
        This function cannot be implemented for OAuth2 authentication.
        """
        raise NotImplementedError()
        #return {}

    def fetch_all_users_groups_membership(self, req = None):
        """
        This function cannot be implemented for OAuth2 authentication.
        """
        raise NotImplementedError()

    def robot_login_method_p():
        """Return True if this method is dedicated to robots and should
        not therefore be available as a choice to regular users upon login.
        """
        return False
    robot_login_method_p = staticmethod(robot_login_method_p)

    def _get_user_email_and_id(self, container):
        """
        Returns external identity and email address together. Since identity is
        essential for OAuth2 authentication, if it doesn't find external
        identity returns None, None.

        @param container: container which contains email and id
        @type container: list|dict

        @rtype str|NoneType, str|NoneType
        """
        from invenio.access_control_config import CFG_OAUTH2_CONFIGURATIONS

        identity = None
        email = None

        if CFG_OAUTH2_CONFIGURATIONS[self.provider_name].has_key('id'):
            path = CFG_OAUTH2_CONFIGURATIONS[self.provider_name]['id']
            identity = treasure_hunter(container, path)

        if identity:
            if CFG_OAUTH2_CONFIGURATIONS[self.provider_name].has_key('email'):
                path = CFG_OAUTH2_CONFIGURATIONS[self.provider_name]\
                    ['email']
                email = treasure_hunter(container, path)

            self.response = container

        return email, identity
