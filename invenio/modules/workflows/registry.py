# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2014, 2015 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import inspect
from invenio.ext.registry import DictModuleAutoDiscoverySubRegistry
from flask_registry import RegistryError, RegistryProxy


class WorkflowsRegistry(DictModuleAutoDiscoverySubRegistry):
    def keygetter(self, key, orig_value, class_):
        return class_.__name__ \
            if hasattr(class_, '__name__') and key is None else key

    def valuegetter(self, class_or_module):
        if inspect.ismodule(class_or_module):
            attr_name = class_or_module.__name__.split('.')[-1]
            if attr_name == '__init__':
                # Ignore __init__ modules.
                return None

            if hasattr(class_or_module, attr_name):
                #key = attr_name if key is None else key
                return getattr(class_or_module, attr_name)
            else:
                all_ = getattr(class_or_module, '__all__', [])
                if len(all_) == 0:
                    raise RegistryError(
                        "Workflow class not found. Class name must match "
                        "module name or be first element in  __all__. "
                        "Please check: {0}.{1}".format(class_or_module,
                                                       attr_name)
                    )
                return getattr(class_or_module, all_[0])
        return class_or_module


workflows = RegistryProxy('workflows', WorkflowsRegistry, 'workflows')
actions = RegistryProxy('workflows.actions', WorkflowsRegistry, 'actions')

__all__ = ['actions', 'workflows']
