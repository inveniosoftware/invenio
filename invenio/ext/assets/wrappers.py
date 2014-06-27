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

"""Custom modified classes."""


import os

from flask import current_app
from flask.ext.assets import Bundle as BundleBase, ManageAssets
from flask.ext.registry import ModuleAutoDiscoveryRegistry
from werkzeug.utils import import_string


class Bundle(BundleBase):

    """
    Bundle extension with a name and bower dependencies.

    The name is only used for assets ordering and requirements.

    The bower dependencies are used to generate a bower.json file.
    """

    def __init__(self, *contents, **options):
        """
        Initialize the named bundle.

        :param name: name of the bundle
        :type name: str
        :param bower: bower dependencies
        :type bower: dict
        """
        self.name = options.pop("name", None)
        self.bower = options.pop("bower", {})
        super(Bundle, self).__init__(*contents, **options)

        # ease the bundle modification
        self.contents = list(self.contents)
        self.app = options.pop("app", None)
        if self.name is None:
            self.name = os.path.basename(self.output)


class BundlesAutoDiscoveryRegistry(ModuleAutoDiscoveryRegistry):

    """
    Registry that searches for bundles.

    Its registry is a list of the package name and the bundle itself. This way
    you can keep track of where a bundle was loaded from.
    """

    def __init__(self, module_name=None, app=None, with_setup=False,
                 silent=False):
        """
        Initialize the bundle auto discovery registry.

        :param module_name: where to look for bundles (default: bundles)
        :type module_name: str

        """
        super(BundlesAutoDiscoveryRegistry, self).__init__(
            module_name or 'bundles', app=app, with_setup=with_setup,
            silent=silent)

    def _discover_module(self, module):
        """Discover the bundles in the given module."""
        import_str = module + '.' + self.module_name

        # FIXME this boilerplate code should be factored out in Flask-Registry.
        try:
            bundles = import_string(import_str, silent=self.silent)
        except ImportError as e:
            self._handle_importerror(e, module, import_str)
        except SyntaxError as e:
            self._handle_syntaxerror(e, module, import_str)
        else:
            variables = getattr(bundles, "__all__", dir(bundles))
            for var in variables:
                # ignore private/protected fields
                if var.startswith('_'):
                    continue
                bundle = getattr(bundles, var)
                if isinstance(bundle, Bundle):
                    self.register((module, bundle))


class Command(ManageAssets):

    """Command-line operation for assets."""

    def run(self, args):
        """Run the command-line.

        It loads the bundles from the :py:data:`bundles registry
        <invenio.ext.assets.registry.bundles>`.

        """
        if not self.env:
            self.env = current_app.jinja_env.assets_environment

        from .registry import bundles
        for pkg, bundle in bundles:
            current_app.logger.info("{0}: {1.name} -> {1.output}"
                                    .format(pkg, bundle))
            self.env.register(bundle.name, bundle)

        return super(Command, self).run(args)
