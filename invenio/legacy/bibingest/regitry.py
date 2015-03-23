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

from flask_registry import PkgResourcesDirDiscoveryRegistry, \
    ModuleAutoDiscoveryRegistry, RegistryProxy, ImportPathRegistry
from werkzeug.local import LocalProxy

from invenio.utils.datastructures import LazyDict
from invenio.ext.registry import ModuleAutoDiscoverySubRegistry
from invenio.legacy.registry import legacy_modules


ingestion_packages_proxy = RegistryProxy(
    'legacy.bibingest.ingestion_packages', ModuleAutoDiscoverySubRegistry,
    'ingestion_packages', registry_namespace=legacy_modules)

ingestion_packages = LazyDict(
    lambda: dict((module.__name__.split('.')[-1], module.package)
                 for module in ingestion_packages_proxy))


storage_engines_proxy = RegistryProxy(
    'legacy.bibingest.storage_engines', ModuleAutoDiscoverySubRegistry,
    'storage_engines', registry_namespace=legacy_modules)

storage_engines = LazyDict(
    lambda: dict((module.storage_engine.__engine_name__, module.storage_engine)
                 for module in storage_engines_proxy))
