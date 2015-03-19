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

"""Custom modified classes."""

from __future__ import absolute_import, print_function, unicode_literals

import os
from flask import current_app
from flask_assets import Bundle as BundleBase
from flask_registry import ModuleAutoDiscoveryRegistry
from werkzeug.utils import import_string
from webassets.filter.requirejs import RequireJSFilter as RequireJSFilterBase
from webassets.filter import ExternalTool


class Bundle(BundleBase):

    """
    Bundle extension with a name and bower dependencies.

    The name is only used for the requirements from the templates and the
    weight does the bundle ordering.

    The bower dependencies are used to generate a bower.json file.
    """

    def __init__(self, *contents, **options):
        """
        Initialize the named bundle.

        :param name: name of the bundle
        :type name: str
        :param bower: bower dependencies
        :type bower: dict
        :param weight: weight of the bundle, lighter are loaded first.
        :type weight: int
        """
        self.bower = options.pop("bower", {})
        self.weight = int(options.pop("weight", 50))
        super(Bundle, self).__init__(*contents, **options)

        # ease the bundle modification
        self.contents = list(self.contents)
        self.app = options.pop("app", None)

    def has_filter(self, *filters):
        """Tell whether a given filter is set up for this bundle."""
        for f in self.filters:
            if f.name in filters:
                return True
        return False


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


class RequireJSFilter(RequireJSFilterBase):

    """Optimize AMD-style modularized JavaScript into a single asset.

    Adds support for exclusion of files already in defined in other bundles.
    """

    def __init__(self, *args, **kwargs):
        """Initialize filter."""
        self.excluded_bundles = kwargs.pop('exclude', [])
        super(RequireJSFilter, self).__init__(*args, **kwargs)

    def setup(self):
        """Setup filter (only called when filter is actually used)."""
        super(RequireJSFilter, self).setup()

        excluded_files = []
        for bundle in self.excluded_bundles:
            excluded_files.extend(
                map(lambda f: os.path.splitext(f)[0],
                    bundle.contents)
            )

        if excluded_files:
            self.argv.append(
                "exclude={0}".format(",".join(excluded_files))
            )


class CleanCSSFilter(ExternalTool):

    """Minify css using cleancss.

    Implements opener capable of rebasing relative CSS URLs against
    ``COLLECT_STATIC_ROOT``.
    """

    name = 'cleancssurl'
    method = 'open'
    options = {
        'binary': 'CLEANCSS_BIN',
    }

    def setup(self):
        """Initialize filter just before it will be used."""
        super(CleanCSSFilter, self).setup()
        self.root = current_app.config.get('COLLECT_STATIC_ROOT')

    def open(self, out, source_path, **kw):
        """Open source."""
        self.subprocess(
            [self.binary or 'cleancss', '--root', self.root, source_path],
            out
        )

    def output(self, _in, out, **kw):
        """Output filtering."""
        self.subprocess([self.binary or 'cleancss'], out, _in)

    def input(self, _in, out, **kw):
        """Input filtering."""
        self.subprocess([self.binary or 'cleancss'], out, _in)
