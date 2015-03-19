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

"""Classifier registries."""

import os

from flask_registry import PkgResourcesDirDiscoveryRegistry, \
    ModuleAutoDiscoveryRegistry, RegistryProxy
from invenio.utils.datastructures import LazyDict

classifierext = RegistryProxy(
    'classifierext', ModuleAutoDiscoveryRegistry, 'classifierext'
)

taxonomies_proxy = RegistryProxy('classifierext.taxonomies',
                                 PkgResourcesDirDiscoveryRegistry,
                                 'taxonomies',
                                 registry_namespace=classifierext)

taxonomies = LazyDict(lambda: dict((os.path.basename(f), f)
                      for f in taxonomies_proxy))

kb = LazyDict(lambda: dict((os.path.basename(f), f)
              for f in RegistryProxy('converterext.kb',
                                     PkgResourcesDirDiscoveryRegistry,
                                     'kb', registry_namespace=classifierext)))

templates = LazyDict(lambda: dict((os.path.basename(f), f)
                     for f in RegistryProxy('converterext.templates',
                                            PkgResourcesDirDiscoveryRegistry,
                                            'templates',
                                            registry_namespace=classifierext)))

__all__ = ('classfierext', 'taxonomies_proxy', 'taxonomies', 'kb', 'templates')
