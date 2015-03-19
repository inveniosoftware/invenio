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

"""Registries for redirector module."""

from flask_registry import RegistryProxy

from invenio.ext.registry import ModuleAutoDiscoverySubRegistry
from invenio.utils.datastructures import LazyDict

redirector_proxy = RegistryProxy('redirect_methods',
                                 ModuleAutoDiscoverySubRegistry,
                                 'redirect_methods')


def register_redirect_methods():
    """Register redirect methods."""
    out = {}
    for module in redirector_proxy:
        if hasattr(module, 'goto'):
            out[module.__name__.split('.')[-1]] = module.goto
    return out


def get_redirect_method(plugin_name):
    """Return the function from the plugin name."""
    return redirect_methods[plugin_name]

redirect_methods = LazyDict(register_redirect_methods)
