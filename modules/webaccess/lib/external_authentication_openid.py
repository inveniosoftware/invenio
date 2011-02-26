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
from invenio.external_authentication import ExternalAuth
from invenio.session import get_session

class ExternalOpenID(ExternalAuth):
    """
    Contains methods for authenticate with an OpenID provider.
    """

    def __init__(self, enforce_external_nicknames = False):
        """Initialization"""
        ExternalAuth.__init__(self, enforce_external_nicknames)

        # Response returned from OpenID provider.
        self.response = None

        # Error message code
        self.msg = 0

        # Name of the provider
        self.provider_name = ""

    def auth_user(self, username, password, req = None):
        """
        Tries to find email and OpenID identity of the user. If it
        doesn't find any of them, returns (None, None)

        @param username: Isn't used in this function
        @type username: str

        @param password: Isn't used in this function
        @type password: str

        @param req: request
        @type req: invenio.webinterface_handler_wsgi.SimulatedModPythonRequest

        @rtype: str|NoneType, str|NoneType
        """
        from openid.consumer import consumer
        self.get_response(req)

        identity = None
        email = None

        if self.response.status == consumer.SUCCESS:
            # In the first login of the user, fetches his/her email
            # from OpenID provider.
            email = self.get_email_from_success_response()
            identity = self.response.getDisplayIdentifier()

        elif self.response.status == consumer.CANCEL:
            # If user cancels the verification, set corresponding message.
            self.msg = 21
        elif self.response.status == consumer.FAILURE:
            # If verification fails, set corresponding message.
            self.msg = 22

        return email, identity

    def user_exists(self, email, req = None):
        """
        This function cannot be implemented for OpenID authentication.
        """
        raise NotImplementedError()


    def fetch_user_groups_membership(self, username, password = None,
                                     req = None):
        """
        This function cannot be implemented for OpenID authentication.
        """
        raise NotImplementedError()

    def fetch_user_nickname(self, username, password = None, req = None):
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
        @type req: invenio.webinterface_handler_wsgi.SimulatedModPythonRequest

        @rtype: str|NoneType
        """
        from openid.extensions import ax
        from openid.extensions import sreg

        nickname = None

        # May be either Simple Registration (sreg) response or
        # Attribute Exchange (ax) response.
        sreg_resp = None
        ax_resp = None

        sreg_resp = sreg.SRegResponse.fromSuccessResponse(self.response)
        if sreg_resp:
            if sreg_resp.getExtensionArgs().has_key('nickname'):
                nickname = sreg_resp.getExtensionArgs()['nickname']

        ax_resp = ax.FetchResponse.fromSuccessResponse(self.response)
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

    def fetch_user_preferences(self, username, password = None, req = None):
        """
        This function cannot be implemented for OpenID authentication.
        """
        raise NotImplementedError()
        #return {}

    def fetch_all_users_groups_membership(self, req = None):
        """
        This function cannot be implemented for OpenID authentication.
        """
        raise NotImplementedError()

    def robot_login_method_p():
        """Return True if this method is dedicated to robots and should
        not therefore be available as a choice to regular users upon login.
        """
        return False
    robot_login_method_p = staticmethod(robot_login_method_p)

    def get_email_from_success_response(self):
        """
        Fetches the email from consumer.SuccessResponse. If it doesn't find any
            returns None.

        @rtype: str|NoneType
        """
        from openid.extensions import ax
        email = None
        ax_resp = ax.FetchResponse.fromSuccessResponse(self.response)

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

    def get_response(self, req):
        """
        Constructs the response returned from the OpenID provider

        @param req: request
        @type req: invenio.webinterface_handler_wsgi.SimulatedModPythonRequest
        """
        from invenio.webinterface_handler import wash_urlargd
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
        self.response = oidconsumer.complete(args, url)
        self.provider_name = args['provider']
