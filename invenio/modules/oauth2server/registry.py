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

"""Registries for OAuth2 Server."""

from __future__ import absolute_import

from flask_registry import RegistryProxy, DictRegistry, RegistryError
from .models import Scope


class ScopesRegistry(DictRegistry):

    """Registry for OAuth scopes."""

    def register(self, scope):
        """ Register an OAuth scope. """
        if not isinstance(scope, Scope):
            raise RegistryError("Invalid scope value.")
        super(ScopesRegistry, self).register(scope.id, scope)

    def choices(self, exclude_internal=True):
        items = self.items()
        items.sort()
        return [(k, scope) for k, scope in items if
                not exclude_internal or not scope.is_internal]


scopes = RegistryProxy('oauth2server.scopes', ScopesRegistry)
