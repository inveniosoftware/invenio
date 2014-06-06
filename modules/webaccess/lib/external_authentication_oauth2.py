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

import requests
from urllib import urlencode
from rauth.service import process_token_request

from invenio.jsonutils import json, json_unicode_to_utf8
from invenio.config import CFG_SITE_URL
from invenio.external_authentication import ExternalAuth
from invenio.containerutils import get_substructure

class ExternalOAuth2(ExternalAuth):
    """
    Contains methods for authenticate with an OAuth2 provider.
    """

    @staticmethod
    def __init_req(req):
        req.g['oauth2_provider_name'] = ''
        req.g['oauth2_debug'] = 0
        req.g['oauth2_msg'] = ''
        req.g['oauth2_debug_msg'] = ''
        req.g['oauth2_response'] = None

    def auth_user(self, username, password, req=None):
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

        self.__init_req(req)

        args = wash_urlargd(req.form, {
                            'code': (str, ''),
                            'provider': (str, '')
                            })

        req.g['oauth2_provider_name'] = args['provider']

        if not req.g['oauth2_provider_name']:
            # If provider name isn't given
            req.g['oauth2_msg'] = 21
            return None, None

        # Some providers doesn't construct return uri properly.
        # Since the callback uri is:
        # /youraccount/login?login_method=oauth2&provider=something
        # they may return to:
        # /youraccount/login?login_method=oauth2&provider=something?code=#
        # instead of
        # /youraccount/login?login_method=oauth2&provider=something&code=#
        if '?' in req.g['oauth2_provider_name']:
            (req.g['oauth2_provider_name'], args['code']) = \
        (
         req.g['oauth2_provider_name'][:req.g['oauth2_provider_name'].index('?')],
         req.g['oauth2_provider_name'][req.g['oauth2_provider_name'].index('?') + 1 + len("code="):]
         )

        if not req.g['oauth2_provider_name'] in CFG_OAUTH2_PROVIDERS:
            req.g['oauth2_msg'] = 22
            return None, None

        # Load the configurations to construct OAuth2 service
        config = CFG_OAUTH2_CONFIGURATIONS[req.g['oauth2_provider_name']]

        req.g['oauth2_debug'] = config.get('debug', 0)

        provider = OAuth2Service(
                                 name = req.g['oauth2_provider_name'],
                                 client_id = config['consumer_key'],
                                 client_secret = config['consumer_secret'],
                                 access_token_url = config['access_token_url'],
                                 authorize_url = config['authorize_url'])

        data = dict(code = args['code'],
                    client_id = config['consumer_key'],
                    client_secret = config['consumer_secret'],
                    grant_type = "authorization_code",
                    # Construct redirect uri without having '/' character at the
                    # left most of SITE_SECURE_URL
                    redirect_uri =  CFG_SITE_URL + '/youraccount/login?' +
                        urlencode({'login_method': 'oauth2', 'provider': req.g['oauth2_provider_name']}))
        headers = dict(Accept = "application/json")
        kwargs = dict(data = data, headers = headers)
        # Get the access token
        r = provider.get_raw_access_token(method='POST', **kwargs)

        keys = ['access_token', 'orcid']
        try:
            access_token, orcid = process_token_request(r, json.loads, *keys)
            token_content = {'access_token': access_token, 'orcid': orcid}
        except:
            req.g['oauth2_msg'] = 22
            return None, None

        req.g['oauth2_access_token'] = token_content['access_token']

        if req.g['oauth2_debug']:
            req.g['oauth2_debug_msg'] = str(token_content) + "<br/>"

        if req.g['oauth2_provider_name'] == 'orcid':
            req.g['oauth2_orcid'] = token_content['orcid']
            email, identity = self._get_user_email_and_id_from_orcid(req)
        else:
            # Some providers send the user information and access token together.
            email, identity = self._get_user_email_and_id(token_content, req)

        if not identity:
            profile = provider.request('GET', config['request_url'].format(
            access_token = token_content['access_token'], id=identity))
            req.g['oauth2_access_token'] = token_content['access_token']

            if req.g['oauth2_debug']:
                req.g['oauth2_debug_msg'] += str(profile.content)

            email, identity = self._get_user_email_and_id(profile.content, req)

        if identity:
            # If identity is found, add the name of the provider at the
            # beginning of the identity because different providers may have
            # different users with same id.
            identity = "%s:%s" % (req.g['oauth2_provider_name'], identity)
        else:
            req.g['oauth2_msg'] = 23

        if req.g['oauth2_debug']:
            req.g['oauth2_msg'] = "<code>%s</code>" % req.g['oauth2_debug_msg'].replace("\n", "<br/>")
            return None, None

        return email, identity

    def fetch_user_nickname(self, username, password=None, req=None):
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

        if req.g['oauth2_provider_name'] and req.g['oauth2_response']:
            path = None
            if CFG_OAUTH2_CONFIGURATIONS[req.g['oauth2_provider_name']].has_key(
                                                                     'nickname'
                                                                     ):
                path = CFG_OAUTH2_CONFIGURATIONS[req.g['oauth2_provider_name']]['nickname']

            if path:
                return get_substructure(req.g['oauth2_response'], path)
        else:
            return None

    @staticmethod
    def _get_user_email_and_id(container, req):
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

        #if req.g['oauth2_provider_name'] == 'orcid':


        if CFG_OAUTH2_CONFIGURATIONS[req.g['oauth2_provider_name']].has_key('id'):
            path = CFG_OAUTH2_CONFIGURATIONS[req.g['oauth2_provider_name']]['id']
            identity = get_substructure(container, path)

        if identity:
            if CFG_OAUTH2_CONFIGURATIONS[req.g['oauth2_provider_name']].has_key('email'):
                path = CFG_OAUTH2_CONFIGURATIONS[req.g['oauth2_provider_name']]\
                    ['email']
                email = get_substructure(container, path)

            req.g['oauth2_response'] = container

        return email, identity

    @staticmethod
    def _get_user_email_and_id_from_orcid(req):
        """
        Since we are dealing with orcid we can fetch tons of information
        from the user profile.
        """
        from invenio.access_control_config import CFG_OAUTH2_CONFIGURATIONS

        profile = requests.get(CFG_OAUTH2_CONFIGURATIONS['orcid']['request_url'].format(id=req.g['oauth2_orcid']), headers={'Accept': 'application/orcid+json', 'Authorization': 'Bearer %s' % req.g['oauth2_access_token']})
        orcid_record = req.g['orcid_record'] = json_unicode_to_utf8(profile.json())['orcid-profile']
        try:
            orcidid = orcid_record['orcid-identifier']['path']
        except (TypeError, KeyError) as e:
            import cPickle, os, datetime
            from invenio.config import CFG_TMPSHAREDDIR
            ts = str(datetime.datetime.today()).replace(' ', ':')
            fname = os.path.join(CFG_TMPSHAREDDIR,
                                 'orcid_dictionary_problem_%s.cPickle' % str(ts))
            f = open(fname, 'w')
            cPickle.dump((e, profile, orcid_record), f)
            f.close()
            raise Exception("Something is wrong with the dictionary we got from ORCID."
                            "Dumped to temporary file %s" % fname)

        emails = orcid_record['orcid-bio'].get('contact-details', dict()).get('email', list())
        if emails:
            return emails[0], orcidid
        else:
            return None, orcidid

    @staticmethod
    def get_limited_access_data_from_orcid(orcid_id, access_token):
        """
        Since we are dealing with orcid we can fetch tons of information
        from the user profile.
        """
        from invenio.access_control_config import CFG_OAUTH2_CONFIGURATIONS

        profile = requests.get(CFG_OAUTH2_CONFIGURATIONS['orcid']['request_url'].format(id=orcid_id), headers={'Accept': 'application/orcid+json', 'Authorization': 'Bearer %s' % access_token})
        if profile.status_code != 200:
            raise NotImplementedError()
        orcid_data = json_unicode_to_utf8(profile.json())['orcid-profile']
        return orcid_data

    @staticmethod
    def get_msg(req):
        return req.g['oauth2_msg']

    def fetch_user_preferences(self, username, password=None, req=None):
        """Fetch user preferences/settings from the SSO account.
        the external key will be '1' if the account is external to SSO,
        otherwise 0
        @return: a dictionary.
        Note: for SSO the parameter are discarded and overloaded by Shibboleth
        variables
        """
        if req and req.g['oauth2_provider_name'] == 'orcid':
            return req.g.get('orcid_record', {})
        else:
            raise NotImplementedError()
