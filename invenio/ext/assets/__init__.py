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

"""
Additional extensions and functions for the `flask.ext.assets` module.

.. py:data:: command

    Flask-Script command that deals with assets.

    Documentation is on: `webassets` :ref:`webassets:script-commands`

    .. code-block:: python

        # How to install it
        from flask.ext.script import Manager
        manager = Manager()
        manager.add_command("assets", command)

.. py:data:: registry

    Flask-Registry registry that handles the bundles. Use it directly as it's
    lazy loaded.
"""

import os
import six
import pkg_resources
from webassets.bundle import is_url
from flask import current_app, json
from flask.ext.assets import Environment, FlaskResolver

from .extensions import BundleExtension, CollectionExtension
from .registry import bundles
from .wrappers import Bundle, Command


__all__ = ("bower", "bundles", "command", "setup_app", "Bundle")

command = Command()


def bower():
    """Generate a bower.json file.

    It comes with default values for the ignore. Name and version are set to
    be invenio's.

    """
    output = {
        "name": "invenio",
        "version": pkg_resources.get_distribution("invenio").version,
        "ignore": [".jshintrc", "**/*.txt"],
        "dependencies": {},
    }

    if os.path.exists("bower.json"):
        current_app.logger.debug("updating bower.json")
        with open("bower.json") as f:
            output = json.load(f)

    for pkg, bundle in bundles:
        if bundle.bower:
            current_app.logger.debug((pkg, bundle.bower))
        output['dependencies'].update(bundle.bower)

    print(json.dumps(output, indent=4))


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
            abspath = super(InvenioResolver, self).search_env_directory(ctx,
                                                                        item)
        except:  # FIXME do not catch all!
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

Environment.resolver_class = InvenioResolver


def setup_app(app):
    """Initialize Assets extension."""
    env = Environment(app)
    env.url = app.static_url_path + "/"
    env.directory = app.static_folder
    # The filters less and requirejs don't have the same behaviour by default.
    # Respecting that.
    app.config.setdefault("LESS_RUN_IN_DEBUG", True)
    app.config.setdefault("REQUIREJS_RUN_IN_DEBUG", False)

    # FIXME to be removed
    def _jinja2_new_bundle(tag, collection, name=None, filters=None):
        if len(collection):
            name = "invenio" if name is None else name
            sig = hash(",".join(collection) + "|" + str(filters))
            kwargs = {
                "output": "{0}/{1}-{2}.{0}".format(tag, name, sig),
                "filters": filters,
                "extra": {"rel": "stylesheet"}
            }

            if tag is "css" and env.debug and \
                    not app.config.get("LESS_RUN_IN_DEBUG"):
                kwargs["extra"]["rel"] = "stylesheet/less"
                kwargs["filters"] = None

            if tag is "js" and filters and "requirejs" in filters:
                if env.debug and \
                        not app.config.get("REQUIREJS_RUN_IN_DEBUG"):
                    # removing the filters to avoid the default "merge" filter.
                    kwargs["filters"] = None
                else:
                    # removing the initial "/", r.js would get confused
                    # otherwise
                    collection = [c[1:] for c in collection]

            return Bundle(*collection, **kwargs)

    app.jinja_env.extend(new_bundle=_jinja2_new_bundle,
                         default_bundle_name='90-invenio')
    app.jinja_env.add_extension(BundleExtension)
    app.context_processor(BundleExtension.inject)
    # FIXME: remove me
    app.jinja_env.add_extension(CollectionExtension)

    return app
