# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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

from invenio.ext.registry import AutoDiscoverRegistry, AutoDiscoverSubRegistry, \
        PkgResourcesDiscoverRegistry, RegistryProxy
from invenio.utils.datastructures import LazyDict

jsonext = lambda namespace: RegistryProxy(namespace, AutoDiscoverRegistry, namespace)

fields_definitions = lambda namespace: RegistryProxy(
    namespace + '.fields', PkgResourcesDiscoverRegistry, 'fields',
    registry_namespace=jsonext(namespace))

models_definitions = lambda namespace: RegistryProxy(
    namespace + '.models', PkgResourcesDiscoverRegistry, 'models',
    registry_namespace=jsonext(namespace))

function_proxy = lambda namespace: RegistryProxy(
    namespace + '.functions', AutoDiscoverSubRegistry, 'functions',
    registry_namespace=jsonext(namespace))
def functions(namespace):
    funcs = dict((module.__name__.split('.')[-1],
                 getattr(module, module.__name__.split('.')[-1], ''))
                for module in function_proxy('jsonext'))
    funcs.update((module.__name__.split('.')[-1],
                 getattr(module, module.__name__.split('.')[-1], ''))
                for module in function_proxy(namespace))
    return funcs

parsers = RegistryProxy('jsonext.parsers', AutoDiscoverSubRegistry,
                        'parsers', registry_namespace=jsonext('jsonext'))

producers_proxy = RegistryProxy('jsonext.producers', AutoDiscoverSubRegistry,
                                'producers', registry_namespace=jsonext('jsonext'))
producers = LazyDict(lambda: dict((module.__name__.split('.')[-1], module.produce)
        for module in producers_proxy))

readers_proxy = RegistryProxy('jsonext.readers', AutoDiscoverSubRegistry,
                              'readers', registry_namespace=jsonext('jsonext'))
readers = LazyDict(lambda: dict((module.reader.__master_format__, module.reader)
        for module in readers_proxy))
