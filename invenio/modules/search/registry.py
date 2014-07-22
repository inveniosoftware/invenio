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

"""Registries for search module."""

from flask.ext.registry import RegistryError, ModuleAutoDiscoveryRegistry, \
    RegistryProxy

from invenio.ext.registry import ModuleAutoDiscoverySubRegistry


searchext = RegistryProxy('searchext', ModuleAutoDiscoveryRegistry,
                          'searchext')

facets = RegistryProxy('facets', ModuleAutoDiscoverySubRegistry, 'facets')


class SearchServiceRegistry(ModuleAutoDiscoverySubRegistry):

    """Search Service Registry."""

    __required_plugin_API_version__ = "Search Service Plugin API 1.0"

    def register(self, item):
        """Check plugin version and instantiate search service plugin."""
        if item.__plugin_version__ != self.__required_plugin_API_version__:
            raise RegistryError(
                'Invalid plugin version {0} required {1}'.format(
                    item.__plugin_version__,
                    self.__required_plugin_API_version__
                ))
        service = getattr(item, item.__name__.split('.')[-1])
        return super(SearchServiceRegistry, self).register(service())

services = RegistryProxy('searchext.services', SearchServiceRegistry,
                         'services', registry_namespace=searchext)
