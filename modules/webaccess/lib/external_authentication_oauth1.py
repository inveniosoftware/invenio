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
This module contains functions and methods to authenticate with OAuth1
providers.
"""

__revision__ = \
    "$Id$"

from invenio.containerutils import treasure_hunter
from invenio.dbquery import run_sql
from invenio.external_authentication import ExternalAuth

class ExternalOAuth1(ExternalAuth):
    """
    Contains methods for authenticate with an OpenID provider.
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
        Tries to find email and identity of the user from OAuth1 provider. If it
        doesn't find any of them, returns (None, None)

        @param username: Isn't used in this function
        @type username: str

        @param password: Isn't used in this function
        @type password: str

        @param req: request
        @type req: invenio.webinterface_handler_wsgi.SimulatedModPythonRequest

        @rtype: str|NoneType, str|NoneType
        """
        from invenio.access_control_config import CFG_OAUTH1_CONFIGURATIONS
        from invenio.access_control_config import CFG_OAUTH1_PROVIDERS
        from invenio.webinterface_handler import wash_urlargd
        from rauth.service import OAuth1Service

        args = wash_urlargd(req.form, {'provider': (str, ''),
                            'login_method': (str, ''),
                            'oauth_token': (str, ''),
                            'oauth_verifier': (str, ''),
                            'denied': (str, '')
                            })
        self.provider_name = args['provider']

        if not self.provider_name in CFG_OAUTH1_PROVIDERS:
            self.msg = 22
            return None, None

        # Load the configurations to construct OAuth1 service
        config = CFG_OAUTH1_CONFIGURATIONS[args['provider']]

        self.debug = config.get('debug', 0)

        if not args['oauth_token']:
            # In case of an error, display corresponding message
            if args['denied']:
                self.msg = 21
                return None, None
            else:
                self.msg = 22
                return None, None

        provider = OAuth1Service(
                                name = self.provider_name,
                                consumer_key = config['consumer_key'],
                                consumer_secret = config['consumer_secret'],
                                request_token_url = config['request_token_url'],
                                access_token_url = config['access_token_url'],
                                authorize_url = config['authorize_url'],
                                header_auth = True)

        # Get the request token secret from database and exchange it with the
        # access token.
        query = """SELECT secret FROM oauth1_storage WHERE token = %s"""
        params = (args['oauth_token'],)
        try:
            # If the request token is already used, return
            request_token_secret = run_sql(query, params)[0][0]
        except IndexError:
            self.msg = 22
            return None, None

        response = provider.get_access_token(
                            'GET',
                            request_token = args['oauth_token'],
                            request_token_secret = request_token_secret,
                            params = {
                                'oauth_verifier': args['oauth_verifier']
                            }
                        )

        if self.debug:
            self.debug_msg = str(response.content) + "<br/>"

        # Some providers send the identity and access token together.
        email, identity = self._get_user_email_and_id(response.content)

        if not identity and config.has_key('request_url'):
            # For some providers, to reach user profile we need to make request
            # to a specific url.
            params = config.get('request_parameters', {})
            response = provider.get(config['request_url'],
                    params = params,
                    access_token = response.content['oauth_token'],
                    access_token_secret = response.content['oauth_token_secret']
                    )

            if self.debug:
                self.debug_msg += str(response.content) + "<br/>"

            email, identity = self._get_user_email_and_id(response.content)

        if identity:
            # If identity is found, add the name of the provider at the
            # beginning of the identity because different providers may have
            # different users with same id.
            identity = "%s:%s" % (self.provider_name, identity)
        else:
            self.msg = 23

        # Delete the token saved in the database since it is useless now.
        query = """
            DELETE FROM     oauth1_storage
            WHERE           token=%s
                OR          date_creation < DATE_SUB(NOW(), INTERVAL 1 HOUR)
            """
        params = (args['oauth_token'],)
        run_sql(query, params)

        if self.debug:
            self.msg = "<code>%s</code>" % self.debug_msg.replace("\n", "<br/>")
            return None, None
        
        return email, identity

    def fetch_user_nickname(self, username, password = None, req = None):
        """
        Fetches the OAuth1 provider for nickname of the user. If it doesn't
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
        from invenio.access_control_config import CFG_OAUTH1_CONFIGURATIONS

        if self.provider_name and self.response:
            path = None
            if CFG_OAUTH1_CONFIGURATIONS[self.provider_name].has_key(
                                                                     'nickname'
                                                                     ):
                path = CFG_OAUTH1_CONFIGURATIONS[self.provider_name]['nickname']

            if path:
                return treasure_hunter(self.response, path)
        else:
            return None

    def user_exists(self, email, req = None):
        """
        This function cannot be implemented for OAuth1 authentication.
        """
        raise NotImplementedError()


    def fetch_user_groups_membership(self, username, password = None,
                                     req = None):
        """
        This function cannot be implemented for OAuth1 authentication.
        """
        return {}

    def fetch_user_preferences(self, username, password = None, req = None):
        """
        This function cannot be implemented for OAuth1 authentication.
        """
        raise NotImplementedError()
        #return {}

    def fetch_all_users_groups_membership(self, req = None):
        """
        This function cannot be implemented for OAuth1 authentication.
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
        essential for OAuth1 authentication, if it doesn't find external
        identity returns None, None.

        @param container: container which contains email and id
        @type container: list|dict

        @rtype str|NoneType, str|NoneType
        """
        from invenio.access_control_config import CFG_OAUTH1_CONFIGURATIONS

        identity = None
        email = None

        if CFG_OAUTH1_CONFIGURATIONS[self.provider_name].has_key('id'):
            path = CFG_OAUTH1_CONFIGURATIONS[self.provider_name]['id']
            identity = treasure_hunter(container, path)

        if identity:
            if CFG_OAUTH1_CONFIGURATIONS[self.provider_name].has_key('email'):
                path = CFG_OAUTH1_CONFIGURATIONS[self.provider_name]\
                    ['email']
                email = treasure_hunter(container, path)

            self.response = container

        return email, identity
