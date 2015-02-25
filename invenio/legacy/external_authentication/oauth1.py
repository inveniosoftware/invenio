# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012 CERN.
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
This module contains functions and methods to authenticate with OAuth1
providers.
"""

__revision__ = \
    "$Id$"

from invenio.utils.container import get_substructure
from invenio.legacy.dbquery import run_sql
from invenio.legacy.external_authentication import ExternalAuth

class ExternalOAuth1(ExternalAuth):
    """
    Contains methods for authenticate with an OpenID provider.
    """

    @staticmethod
    def __init_req(req):
        req.g['oauth1_provider_name'] = ''
        req.g['oauth1_debug'] = 0
        req.g['oauth1_msg'] = ''
        req.g['oauth1_debug_msg'] = ''
        req.g['oauth1_response'] = None

    def auth_user(self, username, password, req=None):
        """
        Tries to find email and identity of the user from OAuth1 provider. If it
        doesn't find any of them, returns (None, None)

        @param username: Isn't used in this function
        @type username: str

        @param password: Isn't used in this function
        @type password: str

        @param req: request
        @type req: invenio.legacy.wsgi.SimulatedModPythonRequest

        @rtype: str|NoneType, str|NoneType
        """
        from invenio.modules.access.local_config import CFG_OAUTH1_CONFIGURATIONS
        from invenio.modules.access.local_config import CFG_OAUTH1_PROVIDERS
        from invenio.ext.legacy.handler import wash_urlargd
        from rauth.service import OAuth1Service

        self.__init_req(req)

        args = wash_urlargd(req.form, {'provider': (str, ''),
                            'login_method': (str, ''),
                            'oauth_token': (str, ''),
                            'oauth_verifier': (str, ''),
                            'denied': (str, '')
                            })
        provider_name = req.g['oauth1_provider_name'] = args['provider']

        if not provider_name in CFG_OAUTH1_PROVIDERS:
            req.g['oauth1_msg'] = 22
            return None, None

        # Load the configurations to construct OAuth1 service
        config = CFG_OAUTH1_CONFIGURATIONS[args['provider']]

        req.g['oauth1_debug'] = config.get('debug', 0)

        if not args['oauth_token']:
            # In case of an error, display corresponding message
            if args['denied']:
                req.g['oauth1_msg'] = 21
                return None, None
            else:
                req.g['oauth1_msg'] = 22
                return None, None

        provider = OAuth1Service(
                                name = req.g['oauth1_provider_name'],
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
            req.g['oauth1_msg'] = 22
            return None, None

        response = provider.get_access_token(
                            'GET',
                            request_token = args['oauth_token'],
                            request_token_secret = request_token_secret,
                            params = {
                                'oauth_verifier': args['oauth_verifier']
                            }
                        )

        if req.g['oauth1_debug']:
            req.g['oauth1_debug_msg'] = str(response.content) + "<br/>"

        # Some providers send the identity and access token together.
        email, identity = self._get_user_email_and_id(response.content, req)

        if not identity and 'request_url' in config:
            # For some providers, to reach user profile we need to make request
            # to a specific url.
            params = config.get('request_parameters', {})
            response = provider.get(config['request_url'],
                    params = params,
                    access_token = response.content['oauth_token'],
                    access_token_secret = response.content['oauth_token_secret']
                    )

            if req.oauth1_debug:
                req.g['oauth1_debug_msg'] += str(response.content) + "<br/>"

            email, identity = self._get_user_email_and_id(response.content, req)

        if identity:
            # If identity is found, add the name of the provider at the
            # beginning of the identity because different providers may have
            # different users with same id.
            identity = "%s:%s" % (req.g['oauth1_provider_name'], identity)
        else:
            req.g['oauth1_msg'] = 23

        # Delete the token saved in the database since it is useless now.
        query = """
            DELETE FROM     oauth1_storage
            WHERE           token=%s
                OR          date_creation < DATE_SUB(NOW(), INTERVAL 1 HOUR)
            """
        params = (args['oauth_token'],)
        run_sql(query, params)

        if req.g['oauth1_debug']:
            req.g['oauth1_msg'] = "<code>%s</code>" % req.g['oauth1_debug_msg'].replace("\n", "<br/>")
            return None, None

        return email, identity

    def fetch_user_nickname(self, username, password=None, req=None):
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
        @type req: invenio.legacy.wsgi.SimulatedModPythonRequest

        @rtype: str or NoneType
        """
        from invenio.modules.access.local_config import CFG_OAUTH1_CONFIGURATIONS

        if req.g['oauth1_provider_name']:
            path = None
            if 'nickname' in CFG_OAUTH1_CONFIGURATIONS[req.g['oauth1_provider_name']]:
                path = CFG_OAUTH1_CONFIGURATIONS[req.g['oauth1_provider_name']]['nickname']

            if path:
                return get_substructure(req.oauth1_response, path)
        else:
            return None

    def _get_user_email_and_id(self, container, req):
        """
        Returns external identity and email address together. Since identity is
        essential for OAuth1 authentication, if it doesn't find external
        identity returns None, None.

        @param container: container which contains email and id
        @type container: list|dict

        @rtype str|NoneType, str|NoneType
        """
        from invenio.modules.access.local_config import CFG_OAUTH1_CONFIGURATIONS

        identity = None
        email = None

        if 'id' in CFG_OAUTH1_CONFIGURATIONS[req.g['oauth1_provider_name']]:
            path = CFG_OAUTH1_CONFIGURATIONS[req.g['oauth1_provider_name']]['id']
            identity = get_substructure(container, path)

        if identity:
            if 'email' in CFG_OAUTH1_CONFIGURATIONS[req.g['oauth1_provider_name']]:
                path = CFG_OAUTH1_CONFIGURATIONS[req.g['oauth1_provider_name']]['email']
                email = get_substructure(container, path)

            req.g['oauth1_response'] = container

        return email, identity

    @staticmethod
    def get_msg(req):
        return req.g['oauth1_msg']
