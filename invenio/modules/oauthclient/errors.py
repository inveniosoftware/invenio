# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
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

"""OAuth Client Exceptions."""


class OAuthError(Exception):

    """Define general OAuth exception."""

    def __init__(self, message, remote):
        self.message = message
        self.remote = remote


class OAuthResponseError(OAuthError):

    """Define response exception during OAuth process."""

    def __init__(self, message, remote, response):
        super(OAuthResponseError, self).__init__(message, remote)
        self.response = response


class OAuthRejectedRequestError(OAuthResponseError):

    """Define exception of rejected response during OAuth process."""


class OAuthClientError(OAuthResponseError):

    """Define OAuth client exception."""

    def __init__(self, message, remote, response):
        # Only OAuth2 specifies how to send error messages
        self.code = response['error']
        self.uri = response.get('error_uri', None)
        self.description = response.get('error_description', None)
        super(OAuthClientError, self).__init__(
            self.description or message, remote, response
        )
