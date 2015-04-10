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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Custom `Jinja2` extensions."""

import copy
import os

from flask import _request_ctx_stack, current_app

from flask_assets import Environment, FlaskResolver

from jinja2 import nodes
from jinja2.ext import Extension

import six

from webassets.bundle import is_url

from . import registry


class BundleExtension(Extension):

    """
    Jinja extension for css and js bundles.

    Definition of the required bundles.

    .. code-block:: jinja

        {%- bundles "jquery.js", "invenio.css" -%}
        {%- bundle "require.js" -%}

    Usage.

    .. code-block:: jinja

        {%- for bundle in get_bundle('js') %}
          <!-- {{ bundle.output }} -->
          {%- assets bundle %}
            <script type="text/javascript" src="{{ ASSET_URL }}"></script>
          {%- endassets %}
        {%- endfor %}
        </body>
        </html>
    """

    tags = set(('bundle', 'bundles'))

    @classmethod
    def storage(cls):
        """Store used bundles on request context stack."""
        ctx = _request_ctx_stack.top
        if ctx is not None:
            if not hasattr(ctx, "_bundles"):
                setattr(ctx, "_bundles", set())
            return ctx._bundles

    @classmethod
    def install(cls, app):
        """Install the extension into the application."""
        Environment.resolver_class = InvenioResolver
        env = Environment(app)
        env.url = "{0}/{1}/".format(app.static_url_path,
                                    app.config["ASSETS_BUNDLES_DIR"])
        env.directory = os.path.join(app.static_folder,
                                     app.config["ASSETS_BUNDLES_DIR"])
        env.append_path(app.static_folder)
        env.auto_build = app.config.get("ASSETS_AUTO_BUILD", True)

        # The filters less and requirejs don't have the same behaviour by
        # default. Make sure we are respecting that.
        app.config.setdefault("REQUIREJS_RUN_IN_DEBUG", False)
        # Fixing some paths as we forced the output directory with the
        # .directory
        app.config.setdefault("REQUIREJS_BASEURL", app.static_folder)
        requirejs_config = os.path.join(env.directory,
                                        app.config["REQUIREJS_CONFIG"])
        if not os.path.exists(requirejs_config):
            app.config["REQUIREJS_CONFIG"] = os.path.relpath(
                os.path.join(app.static_folder,
                             app.config["REQUIREJS_CONFIG"]),
                env.directory)

        app.jinja_env.add_extension(BundleExtension)
        app.context_processor(BundleExtension.inject)

    @classmethod
    def inject(cls):
        """Inject the get_bundle function into the jinja templates."""
        _bundles = {}

        def get_bundle(suffix):
            # lazy build the bundles
            if not _bundles:
                for pkg, bundle in registry.bundles:
                    if bundle.output in _bundles:
                        raise ValueError("{0} was already defined!"
                                         .format(bundle.output))
                    _bundles[bundle.output] = bundle

            env = current_app.jinja_env.assets_environment

            requirejs_debug = env.debug and \
                not current_app.config.get("REQUIREJS_RUN_IN_DEBUG")

            static_url_path = current_app.static_url_path + "/"
            bundles = []
            for bundle_name in cls.storage():
                if bundle_name.endswith(suffix):
                    bundle = _bundles[bundle_name]
                    if suffix == "css":
                        bundle.extra.update(rel="stylesheet")
                    bundles.append((bundle.weight, bundle))

            from webassets.filter import option

            def option__deepcopy__(value, memo):
                """Custom deepcopy implementation for ``option`` class."""
                return option(copy.deepcopy(value[0]),
                              copy.deepcopy(value[1]),
                              copy.deepcopy(value[2]))

            option.__deepcopy__ = option__deepcopy__

            for _, bundle in sorted(bundles):
                # A little bit of madness to read the "/" at the
                # beginning of the assets in ran in debug mode as well as
                # killing the filters if they are not wanted in debug mode.
                if env.debug:
                    # Create a deep copy to avoid filter removal from
                    # being cached
                    bundle_copy = copy.deepcopy(bundle)
                    bundle_copy.extra.update(static_url_path=static_url_path)
                    if bundle.has_filter("less"):
                        bundle_copy.extra.update(static_url_path="")
                    if bundle.has_filter("requirejs"):
                        if requirejs_debug:
                            bundle_copy.filters = None
                        else:
                            bundle_copy.extra.update(static_url_path="")
                    yield bundle_copy
                else:
                    yield bundle

        return dict(get_bundle=get_bundle)

    def __init__(self, environment):
        """Initialize the extension."""
        super(BundleExtension, self).__init__(environment)

    def _update(self, filename, bundles, caller):
        """Update the environment bundles.

        :return: empty html or html comment in debug mode.
        :rtype: str
        """
        self.storage().update(bundles)
        if current_app.debug:
            return "<!-- {0}: {1} -->\n".format(filename, ", ".join(bundles))
        else:
            return ''

    def parse(self, parser):
        """Parse the bundles block and feed the bundles environment.

        Bundles entries are replaced by an empty string.
        """
        lineno = next(parser.stream).lineno

        bundles = []
        while parser.stream.current.type != "block_end":
            value = parser.parse_expression()
            bundles.append(value)
            parser.stream.skip_if("comma")

        call = self.call_method("_update", args=[nodes.Const(parser.name),
                                                 nodes.List(bundles)])
        call_block = nodes.CallBlock(call, [], [], '')
        call_block.set_lineno(lineno)
        return call_block


class InvenioResolver(FlaskResolver):

    """Custom resource resolver for webassets."""

    def resolve_source(self, ctx, item):
        """Return the absolute path of the resource."""
        if not isinstance(item, six.string_types) or is_url(item):
            return item
        if item.startswith(ctx.url):
            item = item[len(ctx.url):]
        return self.search_for_source(ctx, item)

    def resolve_source_to_url(self, ctx, filepath, item):
        """Return the url of the resource.

        Displaying them as is in debug mode as the web server knows where to
        search for them.

        :py:meth:`webassets.env.Resolver.resolve_source_to_url`
        """
        if ctx.debug:
            return item
        return super(InvenioResolver, self).resolve_source_to_url(ctx,
                                                                  filepath,
                                                                  item)

    def search_for_source(self, ctx, item):
        """Return absolute path of the resource.

        :py:meth:`webassets.env.Resolver.search_for_source`

        :param ctx: environment
        :param item: resource filename
        :return: absolute path
        """
        try:
            if ctx.load_path:
                abspath = super(InvenioResolver, self) \
                    .search_load_path(ctx, item)
            else:
                abspath = super(InvenioResolver, self) \
                    .search_env_directory(ctx, item)
        except Exception:  # FIXME do not catch all!
            # If a file is missing in production (non-debug mode), we want
            # to not break and will use /dev/null instead. The exception
            # is caught and logged.
            if not current_app.debug:
                error = "Error loading asset file: {0}".format(item)
                current_app.logger.exception(error)
                abspath = "/dev/null"
            else:
                raise

        return abspath
