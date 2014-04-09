# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012, 2013, 2014 CERN.
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

import inspect
from invenio.ext.registry import ModuleAutoDiscoverySubRegistry
from flask.ext.registry import RegistryError, RegistryProxy


class WorkflowsRegistry(ModuleAutoDiscoverySubRegistry):
    def __init__(self, *args, **kwargs):
        self._registry = {}
        self.registry = None
        super(WorkflowsRegistry, self).__init__(*args, **kwargs)

    def register(self, class_or_module, key=None):  # pylint: disable=W0221
        """
        Workflow discovery:

            .workflows.<module name>:<class name>

        where module name and class name are identical.

        :param key: Key to register object under
        :param item: Object to register
        """
        if inspect.ismodule(class_or_module):
            attr_name = class_or_module.__name__.split('.')[-1]
            if attr_name == '__init__':
                # Ignore __init__ modules.
                return

            if hasattr(class_or_module, attr_name):
                key = attr_name if key is None else key
                class_or_module = getattr(class_or_module, attr_name)
            else:
                all_ = getattr(class_or_module, '__all__', [])
                if len(all_) == 0:
                    raise RegistryError(
                        "Workflow class not found. Class name must match "
                        "module name or be first element in  __all__."
                    )
                class_or_module = getattr(class_or_module, all_[0])

        key = class_or_module.__name__ if key is None else key

        if key in self._registry:
            raise RegistryError("Key %s already registered." % key)

        self._registry[key] = class_or_module

    def unregister(self, key):  # pylint: disable=W0221
        """
        Unregister an object under a given key. Raises ``KeyError`` in case
        the given key doesn't exists.
        """
        del self[key]

    def __iter__(self):
        # pylint: disable=R0921
        return self._registry.__iter__()

    def __len__(self):
        return self._registry.__len__()

    def __contains__(self, item):
        return self._registry.__contains__(item)

    def __getitem__(self, key):
        return self._registry[key]

    def __setitem__(self, key, value):
        return self.register(value, key=key)

    def __delitem__(self, key):
        return self._registry.__delitem__(key)

    def items(self):
        """
        Get list of key/value pairs.

        :param item: Object to register
        """
        return self._registry.items()


workflows = RegistryProxy('workflows', WorkflowsRegistry, 'workflows')
widgets = RegistryProxy('workflows.widgets', WorkflowsRegistry, 'widgets')

__all__ = ['widgets', 'workflows']
