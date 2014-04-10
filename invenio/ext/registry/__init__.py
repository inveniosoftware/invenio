# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013, 2014 CERN.
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

"""
Addtional registries for Flask-Registry
"""

from werkzeug.utils import import_string, find_modules
from flask.ext.registry import ModuleAutoDiscoveryRegistry
from flask.ext.registry import RegistryError


class ModuleAutoDiscoverySubRegistry(ModuleAutoDiscoveryRegistry):
    def _discover_module(self, pkg):
        import_str = pkg + '.' + self.module_name

        try:
            import_string(import_str, silent=self.silent)
        except ImportError as e:  # pylint: disable=C0103
            self._handle_importerror(e, pkg, import_str)
            return
        except SyntaxError as e:
            self._handle_syntaxerror(e, pkg, import_str)
            return

        for m in find_modules(import_str):
            try:
                module = import_string(m, silent=self.silent)
                if module is not None:
                    self.register(module)
            except ImportError as e:  # pylint: disable=C0103
                self._handle_importerror(e, import_str, m)
            except SyntaxError as e:
                self._handle_syntaxerror(e, import_str, m)


class DictModuleAutoDiscoverySubRegistry(ModuleAutoDiscoverySubRegistry):
    """
    ModuleAutoDiscoverySubRegistry that behaves like a dictionary.

    You should either provide the ``keygetter`` keyword argument or subclass
    and override the ``keygetter()`` method.
    """
    def __init__(self, *args, **kwargs):
        self._registry = {}
        self.registry = None  # Kill internal registry from ListRegistry
        self._keygetter = kwargs.pop('keygetter', None)
        self._valuegetter = kwargs.pop('valuegetter', None)
        super(DictModuleAutoDiscoverySubRegistry, self).__init__(
            *args, **kwargs
        )

    def keygetter(self, key, value):
        """
        Method used to compute the key for a value being registered.

        Either use the ``keygetter`` argument during initialization or subclass
        and override this method to customize the behaviour.

        :param key: Key if provided by the user. Defaults to None.
        :param value: Value being registered.
        """
        if self._keygetter:
            return self._keygetter(key, value)
        raise RegistryError("Please provide a key or keygetter function.")

    def valuegetter(self, value):
        """
        Method use to modify the value being registered. By default it just
        returns the same object.
        """
        return self._valuegetter(value) if self._valuegetter else value

    def register(self, value, key=None):  # pylint: disable=W0221
        """
        :param value: Value being registered.
        :param key: Key, if provided by the user.
        """
        value = self.valuegetter(value)
        key = self.keygetter(key, value)

        if key in self._registry:
            raise RegistryError("Key %s already registered." % key)

        if value:
            self._registry[key] = value

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

    def keys(self):
        """
        Get list of keys.

        :param item: Object to register
        """
        return self._registry.keys()

    def values(self):
        """
        Get list of keys.

        :param item: Object to register
        """
        return self._registry.values()
