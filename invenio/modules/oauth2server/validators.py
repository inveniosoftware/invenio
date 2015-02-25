# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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

"""Validators for OAuth 2.0 redirect URIs and scopes."""

from __future__ import absolute_import

from oauthlib.oauth2.rfc6749.errors import InsecureTransportError, \
    InvalidRedirectURIError
from six.moves.urllib_parse import urlparse

from .errors import ScopeDoesNotExists


def validate_redirect_uri(value):
    """Validate a redirect URI.

    Redirect URIs must be a valid URL and use https unless the host is
    localhost for which http is accepted.
    """
    sch, netloc, path, par, query, fra = urlparse(value)
    if not (sch and netloc):
        raise InvalidRedirectURIError()
    if sch != 'https':
        if ':' in netloc:
            netloc, port = netloc.split(':', 1)
        if not (netloc in ('localhost', '127.0.0.1') and sch == 'http'):
            raise InsecureTransportError()


def validate_scopes(value_list):
    """Validate if each element in a list is a registered scope."""
    from .registry import scopes as scopes_registry

    for value in value_list:
        if value not in scopes_registry:
            raise ScopeDoesNotExists(value)
    return True
