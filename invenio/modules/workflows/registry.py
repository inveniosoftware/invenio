# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012, 2013 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from invenio.ext.registry import ModuleAutoDiscoverySubRegistry
from flask.ext.registry import RegistryProxy
from invenio.utils.datastructures import LazyDict


def plugin_builder(plugin):
    plugin_name = plugin.__name__.split('.')[-1]
    if plugin_name == '__init__':
        return

    plugin_candidate = getattr(plugin, plugin_name, None)
    if plugin_candidate is None:
        all_plugins = getattr(plugin, '__all__', [])
        for name in all_plugins:
            candidate = getattr(plugin, name)
            return candidate
    else:
        return plugin_candidate


workflows_registry = RegistryProxy(
    'workflows',
    ModuleAutoDiscoverySubRegistry,
    'workflows'
)


widgets_registry = RegistryProxy(
    'widgets',
    ModuleAutoDiscoverySubRegistry,
    'widgets'
)


def load_modules_from_registry(registry):
    def load_me():
        loaded_dict = {}
        for package in registry:
            name = package.__name__.split('.')[-1]
            loaded_dict[name] = plugin_builder(package)
        return loaded_dict
    return load_me


workflows = LazyDict(load_modules_from_registry(workflows_registry))
widgets = LazyDict(load_modules_from_registry(widgets_registry))

__all__ = ['widgets', 'workflows']
