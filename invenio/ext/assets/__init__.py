# -*- coding: utf-8 -*-
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
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Additional extensions and functions for the `flask.ext.assets` module."""

import six
from webassets.bundle import is_url
from flask import current_app
from flask.ext.assets import Environment, Bundle, FlaskResolver
from .extensions import CollectionExtension


__all__ = ('CollectionExtension', 'setup_app')


class InvenioResolver(FlaskResolver):

    """Custom resource resolver for webassets."""

    def resolve_source(self, ctx, item):
        """Return the absolute path of the resource.

        .. seealso:: :py:function:`webassets.env.Resolver:resolve_source`
        """
        if not isinstance(item, six.string_types) or is_url(item):
            return item
        if item.startswith(ctx.url):
            item = item[len(ctx.url):]
        return self.search_for_source(ctx, item)

    def resolve_source_to_url(self, ctx, filepath, item):
        """Return the url of the resource.

        Displaying them as is in debug mode as the webserver knows where to
        search for them.

        .. seealso::

            :py:function:`webassets.env.Resolver:resolve_source_to_url`
        """
        if ctx.debug:
            return item
        return super(InvenioResolver, self).resolve_source_to_url(ctx,
                                                                  filepath,
                                                                  item)

    def search_for_source(self, ctx, item):
        """Return absolute path of the resource.

        :param item: resource filename
        :return: absolute path
        .. seealso:: :py:function:`webassets.env.Resolver:search_for_source`
        """
        try:
            abspath = super(InvenioResolver, self).search_env_directory(ctx, item)
        except:
            # If a file is missing in production (non-debug mode), we want
            # to not break and will use /dev/null instead. The exception
            # is caught and logged.
            if not current_app.debug:
                error = "Missing asset file: {0}".format(item)
                current_app.logger.exception(error)
                abspath = "/dev/null"
            else:
                raise

        return abspath

Environment.resolver_class = InvenioResolver


def setup_app(app):
    """Initialize Assets extension."""
    assets = Environment(app)
    assets.url = app.static_url_path + "/"
    assets.directory = app.static_folder

    commands = (("LESS_BIN", "lessc"),
                ("CLEANCSS_BIN", "cleancss"),
                ("REQUIREJS_BIN", "r.js"),
                ("UGLIFYJS_BIN", "uglifyjs"))
    import subprocess
    for key, cmd in commands:
        try:
            command = app.config.get(key, cmd)
            subprocess.call([command, "--version"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
        except OSError:
            app.logger.error("Executable `{0}` was not found. You can specify "
                             "it via {1}."
                             .format(cmd, key))
            app.config["ASSETS_DEBUG"] = True
            app.config.setdefault("LESS_RUN_IN_DEBUG", False)
            app.config.setdefault("REQUIREJS_RUN_IN_DEBUG", False)
            assets.debug = True

    def _jinja2_new_bundle(tag, collection, name=None, filters=None):
        if len(collection):
            name = "invenio" if name is None else name
            sig = hash(",".join(collection) + "|" + str(filters))
            kwargs = {
                "output": "{0}/{1}-{2}.{0}".format(tag, name, sig),
                "filters": filters,
                "extra": {"rel": "stylesheet"}
            }

            # If LESS_RUN_IN_DEBUG is set to False, then the filters are
            # removed and each less file will be parsed by the less JavaScript
            # library.
            if tag is "css" and assets.debug and \
                    not app.config.get("LESS_RUN_IN_DEBUG", True):
                kwargs["extra"]["rel"] = "stylesheet/less"
                kwargs["filters"] = None
            # If REQUIREJS_RUN_IN_DEBUG is set to False, then the filters are
            # removed and dependencies will be loaded via require.js
            if tag is "js" and filters and "requirejs" in filters:
                if not assets.debug or \
                        app.config.get("REQUIREJS_RUN_IN_DEBUG", True):
                    collection = [c[1:] for c in collection]
                else:
                    kwargs["filters"] = None

            return Bundle(*collection, **kwargs)

    app.jinja_env.extend(new_bundle=_jinja2_new_bundle,
                         default_bundle_name='90-invenio')
    app.jinja_env.add_extension(CollectionExtension)

    return app
