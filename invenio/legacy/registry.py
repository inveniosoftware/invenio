# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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

import os
import inspect

from flask import current_app
from flask_registry import RegistryProxy, ImportPathRegistry, \
    ModuleAutoDiscoveryRegistry

from invenio.ext.registry import ModuleAutoDiscoverySubRegistry
from invenio.utils.datastructures import LazyDict

legacy_modules = RegistryProxy('legacy', ImportPathRegistry,
                               initial=['invenio.legacy.*'])

webadmin_proxy = RegistryProxy('legacy.webadmin', \
        ModuleAutoDiscoverySubRegistry, 'web.admin',
        registry_namespace=legacy_modules)

def _admin_handler_name(name):
    parts = name.split('.')
    return '%s/%s' % (parts[2], parts[5])

webadmin = LazyDict(lambda: dict((_admin_handler_name(module.__name__), module)
                                 for module in webadmin_proxy))

webinterface_proxy = RegistryProxy(
    'legacy.webinterface', ModuleAutoDiscoveryRegistry, 'webinterface',
    registry_namespace=legacy_modules)

def _webinterface(module):
    from invenio.ext.legacy.handler import WebInterfaceDirectory
    parts = module.__name__.split('.')
    for value in dir(module):
        webinterface = getattr(module, value)
        if inspect.isclass(webinterface) and \
                issubclass(webinterface, WebInterfaceDirectory) and \
                webinterface.__module__ == module.__name__:
            yield webinterface.__name__, webinterface

def _webinterfaces(modules):
    for module in modules:
        for value in _webinterface(module):
            yield value

webinterfaces = LazyDict(lambda: dict(_webinterfaces(webinterface_proxy)))
