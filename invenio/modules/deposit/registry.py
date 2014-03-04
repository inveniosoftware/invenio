# -*- coding: utf-8 -*-
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
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


from flask import current_app
from flask.ext.registry import ImportPathRegistry, SingletonRegistry, \
    RegistryProxy
from invenio.modules.workflows.loader import workflows


class DepositSingletonRegistry(SingletonRegistry):
    def get(self):
        """ Ensure deposit types are loaded before getting the object """
        if 'deposit_types' not in current_app.extensions['registry']:
            list(deposit_types)
        return super(DepositSingletonRegistry, self).get()


class DepositionTypeRegistry(ImportPathRegistry):
    """
    Import path registry, that will load deposition types when accessed, and
    also register the default deposition type.
    """
    def __init__(self):
        super(DepositionTypeRegistry, self).__init__(
            initial=current_app.config['DEPOSIT_TYPES'],
            load_modules=True,
        )

    def _load_import_path(self, import_path):
        obj = super(DepositionTypeRegistry, self)._load_import_path(
            import_path
        )

        # Ensure DepositionType is actually a loaded workflow
        # FIXME
        #if obj.__name__ not in workflows or obj != workflows[obj.__name__]:
        #    raise RuntimeError("Import path '%s' is not a loaded workflow.")

        if import_path == current_app.config['DEPOSIT_DEFAULT_TYPE']:
            deposit_default_type.register(obj)

        return obj

    def mapping(self):
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
