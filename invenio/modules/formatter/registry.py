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
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA

import os

from invenio.ext.registry import PkgResourcesDiscoverRegistry, AutoDiscoverRegistry, RegistryProxy, AutoDiscoverSubRegistry
from invenio.utils.datastructures import LazyDict

format_elements = RegistryProxy('format_elements',
                                AutoDiscoverSubRegistry,
                                'format_elements')

format_templates_directories = RegistryProxy('format_templates_directories',
                                             AutoDiscoverRegistry,
                                             'format_templates')

format_templates = RegistryProxy('format_templates',
                                 PkgResourcesDiscoverRegistry,
                                 '.', registry_namespace=format_templates_directories)


def create_format_templates_lookup():
    out = {}

    def _register(path, level=1):
        if level > 4:
            return
        normpath = os.path.normpath(path)
        if os.path.isdir(normpath):
            for p in os.listdir(normpath):
                _register(os.path.join(normpath, p), level=level+1)
        else:
            parts = normpath.split(os.path.sep)
            out[os.path.sep.join(parts[-level:])] = normpath

    for t in format_templates:
        _register(t)
    return out


format_templates_lookup = LazyDict(create_format_templates_lookup)
