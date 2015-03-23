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

"""Registry for Jasmine spec files."""

import os
import re
from werkzeug.utils import import_string
from flask_registry import RegistryProxy
from invenio.ext.registry import DictModuleAutoDiscoverySubRegistry


class JasmineSpecsAutoDiscoveryRegistry(DictModuleAutoDiscoverySubRegistry):

    """Registry for Jasmine spec files.

    Looks into /testsuite/js/*.spec.js in each module.
    """

    pattern = re.compile("(?:.+\.js$)|(?:.+\.html$)")
    specs_folder = 'js'

    def __init__(self, *args, **kwargs):
        """Initialize registry."""
        super(JasmineSpecsAutoDiscoveryRegistry, self).__init__(
            'testsuite', **kwargs
        )

    def keygetter(self, key, original_value, new_value):
        """No key mapping."""
        return key

    def _walk_dir(self, pkg, base, root):
        """Recursively register *.spec.js/*.js files."""
        for root, dirs, files in os.walk(root):
            for name in files:
                if JasmineSpecsAutoDiscoveryRegistry.pattern.match(name):
                    filename = os.path.join(root, name)
                    filepath = "{0}/{1}".format(
                        pkg,
                        filename[len(base)+1:]
                    )
                    self.register(filename, key=filepath)

    def _discover_module(self, pkg):
        """Load list of files from resource directory."""
        import_str = pkg + '.' + self.module_name

        try:
            module = import_string(import_str, silent=self.silent)
            if module is not None:
                for p in module.__path__:
                    specsfolder = os.path.join(p, self.specs_folder)
                    if os.path.isdir(specsfolder):
                        self._walk_dir(pkg, specsfolder, specsfolder)
        except ImportError as e:  # pylint: disable=C0103
            self._handle_importerror(e, pkg, import_str)
        except SyntaxError as e:
            self._handle_syntaxerror(e, pkg, import_str)


specs = RegistryProxy("jasmine.specs", JasmineSpecsAutoDiscoveryRegistry)
