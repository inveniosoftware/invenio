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
from flask_registry import ModuleAutoDiscoveryRegistry


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
