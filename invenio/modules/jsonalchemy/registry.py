# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014, 2015 CERN.
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

from flask_registry import PkgResourcesDirDiscoveryRegistry, \
    ModuleAutoDiscoveryRegistry, RegistryProxy

from invenio.ext.registry import ModuleAutoDiscoverySubRegistry
from invenio.utils.datastructures import LazyDict

jsonext = lambda namespace: RegistryProxy(
    namespace, ModuleAutoDiscoveryRegistry, namespace)


fields_proxy = lambda namespace: RegistryProxy(
    namespace + '.fields', PkgResourcesDirDiscoveryRegistry, 'fields',
    registry_namespace=jsonext(namespace))


def fields_definitions(namespace=None):
    field_defs = list(fields_proxy('jsonext'))
    if namespace is not None:
        field_defs.extend(list(fields_proxy(namespace)))
    return field_defs


models_proxy = lambda namespace: RegistryProxy(
    namespace + '.models', PkgResourcesDirDiscoveryRegistry, 'models',
    registry_namespace=jsonext(namespace))


def models_definitions(namespace=None):
    models_defs = list(models_proxy('jsonext'))
    if namespace is not None:
        models_defs.extend(list(models_proxy(namespace)))
    return models_defs


function_proxy = lambda namespace: RegistryProxy(
    namespace + '.functions', ModuleAutoDiscoverySubRegistry, 'functions',
    registry_namespace=jsonext(namespace))


def functions(namespace=None):
    funcs = dict((module.__name__.split('.')[-1],
                 getattr(module, module.__name__.split('.')[-1]))
                 for module in function_proxy('jsonext'))
    if namespace is not None:
        funcs.update((module.__name__.split('.')[-1],
                     getattr(module, module.__name__.split('.')[-1]))
                     for module in function_proxy(namespace))
    return funcs


parsers = RegistryProxy('jsonext.parsers', ModuleAutoDiscoverySubRegistry,
                        'parsers', registry_namespace=jsonext('jsonext'))


producers_proxy = RegistryProxy('jsonext.producers',
                                ModuleAutoDiscoverySubRegistry,
                                'producers',
                                registry_namespace=jsonext('jsonext'))


producers = LazyDict(lambda: dict((module.__name__.split('.')[-1],
                                   module.produce)
                                  for module in producers_proxy))


readers_proxy = RegistryProxy('jsonext.readers',
                              ModuleAutoDiscoverySubRegistry,
                              'readers', registry_namespace=jsonext('jsonext'))


readers = LazyDict(lambda: dict((module.reader.__master_format__,
                                 module.reader)
                                for module in readers_proxy))


contexts_proxy = lambda namespace: RegistryProxy(
    namespace + '.contexts', ModuleAutoDiscoverySubRegistry, 'contexts',
    registry_namespace=jsonext(namespace))


def contexts(namespace=None):
    contexts = dict((module.__name__.split('.')[-1],
                     getattr(module, 'context'))
                    for module in contexts_proxy('jsonext'))
    if namespace is not None:
        contexts.update((module.__name__.split('.')[-1],
                         getattr(module, 'context'))
                        for module in contexts_proxy(namespace))
    return contexts
