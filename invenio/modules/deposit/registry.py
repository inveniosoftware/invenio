# -*- coding: utf-8 -*-
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

"""Implement registries used in deposit module."""

from __future__ import absolute_import, print_function

from flask import current_app
from flask_registry import ImportPathRegistry, SingletonRegistry, \
    RegistryProxy, RegistryError
from invenio.modules.deposit.models import DepositionType
from invenio.modules.workflows.registry import workflows


class DepositSingletonRegistry(SingletonRegistry):

    """Specialized singleton registry for ``deposit_types``."""

    def get(self):
        """Ensure deposit types are loaded before getting the object."""
        if 'deposit_types' not in current_app.extensions['registry']:
            list(deposit_types)
        return super(DepositSingletonRegistry, self).get()


class DepositionTypeRegistry(ImportPathRegistry):

    """Specialized import path registry.

    It loads deposition types when accessed, and also register the default
    deposition type.
    """

    def __init__(self):
        """Initialize deposity types from application config."""
        super(DepositionTypeRegistry, self).__init__(
            initial=current_app.config['DEPOSIT_TYPES'],
            load_modules=True,
        )

    def _load_import_path(self, import_path):
        """Register default deposit type when it is imported."""
        obj = super(DepositionTypeRegistry, self)._load_import_path(
            import_path
        )

        if import_path == current_app.config['DEPOSIT_DEFAULT_TYPE']:
            deposit_default_type.register(obj)

        return obj

    def register(self, import_path_or_type):
        """Allow registering both import paths or deposition types.

        .. note:: If you manually register a deposition type instad of using
        the configuration variable you must also refresh your applications URL
        map using .url_converters.refresh_url_map() method.
        """
        if isinstance(import_path_or_type, type) and \
           issubclass(import_path_or_type, DepositionType):
            if import_path_or_type.__name__ in workflows:
                raise RegistryError("Workflow named %s already registered.")
            # Super call with ImportPathRegistry instead of
            # DepositionTypeRegistry on purpose.
            super(ImportPathRegistry, self).register(import_path_or_type)
            workflows[import_path_or_type.__name__] = import_path_or_type
        else:
            super(DepositionTypeRegistry, self).register(import_path_or_type)

    def unregister(self, deposition_type):
        """Allow unregistering deposition types."""
        if deposition_type.__name__ not in workflows:
            raise RegistryError("Deposition type not registered")
        # Super call with ImportPathRegistry instead of DepositionTypeRegistry
        # on purpose.
        super(ImportPathRegistry, self).unregister(deposition_type)
        del workflows[deposition_type.__name__]

    def mapping(self):
        """Define deposition type mapping by their ``__name__``."""
        return dict([(x.__name__, x) for x in self])


deposit_default_type = RegistryProxy(
    'deposit_default_type', DepositSingletonRegistry
)
"""
Registry of a single default deposition type - initialized
by DepositionTypeRegistry
"""


deposit_types = RegistryProxy('deposit_types', DepositionTypeRegistry)
""" Registry of loaded deposition types """
