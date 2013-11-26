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
This module contains functions and methods to authenticate with OpenID
providers.
"""
__revision__ = \
    "$Id$"

from invenio.config import CFG_SITE_SECURE_URL
from invenio.legacy.external_authentication import ExternalAuth
from invenio.legacy.websession.session import get_session

class ExternalOpenID(ExternalAuth):
    """
    Contains methods for authenticate with an OpenID provider.
    """

    @staticmethod
    def __init_req(req):
        req.g['openid_provider_name'] = ''
        req.g['openid_debug'] = 0
        req.g['openid_msg'] = ''
        req.g['openid_debug_msg'] = ''
        req.g['openid_response'] = None

    def auth_user(self, username, password, req=None):
        """
        Tries to find email and OpenID identity of the user. If it
        doesn't find any of them, returns (None, None)

        @param username: Isn't used in this function
        @type username: str

        @param password: Isn't used in this function
        @type password: str

        @param req: request
        @type req: invenio.legacy.wsgi.SimulatedModPythonRequest

        @rtype: str|NoneType, str|NoneType
        """
        from openid.consumer import consumer
        self._get_response(req)
        response = req.g['openid_response']

        identity = None
        email = None

        if response.status == consumer.SUCCESS:
            # In the first login of the user, fetches his/her email
            # from OpenID provider.
            email = self._get_email_from_success_response(req)
            identity = response.getDisplayIdentifier()

        elif response.status == consumer.CANCEL:
            # If user cancels the verification, set corresponding message.
            req.openid_msg = 21
        elif response.status == consumer.FAILURE:
            # If verification fails, set corresponding message.
            req.openid_msg.msg = 22

        return email, identity

    @staticmethod
    def get_msg(req):
        return req.g['openid_msg']

    def fetch_user_nickname(self, username, password=None, req=None):
        """
        Fetches the OpenID provider for nickname of the user. If it doesn't
            find any, returns None.

        This function doesn't need username, password or req. They are exist
            just because this class is derived from ExternalAuth

        @param username: Isn't used in this function
        @type username: str

        @param password: Isn't used in this function
        @type password: str

        @param req: request
        @type req: invenio.legacy.wsgi.SimulatedModPythonRequest

        @rtype: str|NoneType
        """
        from openid.extensions import ax
        from openid.extensions import sreg

        nickname = None

        # May be either Simple Registration (sreg) response or
        # Attribute Exchange (ax) response.
        sreg_resp = None
        ax_resp = None

        response = req.g['openid_response']

        sreg_resp = sreg.SRegResponse.fromSuccessResponse(response)
        if sreg_resp:
            if sreg_resp.getExtensionArgs().has_key('nickname'):
                nickname = sreg_resp.getExtensionArgs()['nickname']

        ax_resp = ax.FetchResponse.fromSuccessResponse(response)
        if ax_resp and not nickname:
            extensions = ax_resp.getExtensionArgs()

            if extensions.has_key('type.ext0') and \
                extensions.has_key('value.ext0.1'):
                if extensions['type.ext0'] == \
                    'http://axschema.org/namePerson/friendly':
                    nickname = extensions['value.ext0.1']

            if extensions.has_key('type.ext1') and \
                extensions.has_key('value.ext1.1') and not nickname:
                if extensions['type.ext1'] == \
                    'http://axschema.org/namePerson/friendly':
                    nickname = extensions['value.ext1.1']
        return nickname

    @staticmethod
    def _get_email_from_success_response(req):
        """
        Fetches the email from consumer.SuccessResponse. If it doesn't find any
            returns None.

        @rtype: str|NoneType
        """
        from openid.extensions import ax
        email = None
        response = req.g['openid_response']
        ax_resp = ax.FetchResponse.fromSuccessResponse(response)

        if ax_resp:
            extensions = ax_resp.getExtensionArgs()
            if extensions.has_key('type.ext0') and \
                extensions.has_key('value.ext0.1'):
                if extensions['type.ext0'] == \
                    'http://axschema.org/contact/email':
                    email = extensions['value.ext0.1']

            if extensions.has_key('type.ext1') and \
                extensions.has_key('value.ext1.1') and not email:
                if extensions['type.ext1'] == \
                    'http://axschema.org/contact/email':
                    email = extensions['value.ext1.1']
        return email

    @staticmethod
    def _get_response(req):
        """
        Constructs the response returned from the OpenID provider

        @param req: request
        @type req: invenio.legacy.wsgi.SimulatedModPythonRequest
        """
        from invenio.ext.legacy.handler import wash_urlargd
        from openid.consumer import consumer

        content = {}
        for key in req.form.keys():
            content[key] = (str, '')

        args = wash_urlargd(req.form, content)

        if args.has_key('ln'):
            del args['ln']

        if args.has_key('referer'):
            if not args['referer']:
                del args['referer']

        oidconsumer = consumer.Consumer({"id": get_session(req)}, None)
        url = CFG_SITE_SECURE_URL + "/youraccount/login"
        req.g['openid_provider_name'] = args['provider']
        req.g['openid_response'] = oidconsumer.complete(args, url)
