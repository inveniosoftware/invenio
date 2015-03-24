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
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA

"""Implement registries for formatter."""

import os

from flask_registry import (
    ModuleAutoDiscoveryRegistry,
    PkgResourcesDirDiscoveryRegistry,
    RegistryProxy,
)

from invenio.ext.registry import ModuleAutoDiscoverySubRegistry
from invenio.utils.datastructures import LazyDict

import yaml

format_elements = RegistryProxy(
    'format_elements',
    ModuleAutoDiscoverySubRegistry,
    'format_elements'
)

format_templates_directories = RegistryProxy(
    'format_templates_directories',
    ModuleAutoDiscoveryRegistry,
    'format_templates'
)

format_templates = RegistryProxy(
    'format_templates',
    PkgResourcesDirDiscoveryRegistry,
    '.', registry_namespace=format_templates_directories
)

output_formats_directories = RegistryProxy(
    'output_formats_directories',
    ModuleAutoDiscoveryRegistry,
    'output_formats'
)

output_formats_files = RegistryProxy(
    'output_formats_files',
    PkgResourcesDirDiscoveryRegistry,
    '.', registry_namespace=output_formats_directories
)

template_context_functions = RegistryProxy(
    'template_context_functions',
    ModuleAutoDiscoverySubRegistry,
    'template_context_functions'
)


def create_format_templates_lookup():
    """Create format templates."""
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

    for t in reversed(format_templates):
        _register(t)
    return out


format_templates_lookup = LazyDict(create_format_templates_lookup)


def create_output_formats_lookup():
    """Create output formats."""
    out = {}

    for f in output_formats_files:
        of = os.path.basename(f).lower()
        data = {'names': {}}
        if of.endswith('.yml'):
            of = of[:-4]
            with open(f, 'r') as f:
                data.update(yaml.load(f) or {})
                data['code'] = of
        else:
            continue  # unknown filetype
        if of in out:
            continue
        out[of] = data
    return out

output_formats = LazyDict(create_output_formats_lookup)

export_formats = LazyDict(lambda: dict(
    (code, of) for code, of in output_formats.items()
    if of.get('content_type', '') != 'text/html' and of.get('visibility', 0)
))
