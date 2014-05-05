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
    invenio.ext.assets
    ------------------

    Additional extensions and functions for the `flask.ext.assets` module.
"""

import os
import six
from webassets.bundle import is_url
from flask import current_app
from flask.ext.assets import Environment, Bundle, FlaskResolver
from .extensions import CollectionExtension

from invenio.base.wrappers import STATIC_MAP


__all__ = ('CollectionExtension', 'setup_app')


class InvenioResolver(FlaskResolver):

    """Custom resource resolver for webassets."""

    def resolve_source(self, item):
        """Return the absolute path of the resource.

        .. seealso:: :py:function:`webassets.env.Resolver:resolve_source`
        """
        if not isinstance(item, six.string_types) or is_url(item):
            return item
        if item.startswith(self.env.url):
            item = item[len(self.env.url):]
        return self.search_for_source(item)

    def resolve_source_to_url(self, filepath, item):
        """Return the url of the resource.

        Displaying them as is in debug mode as the webserver knows where to
        search for them.

        .. seealso:: :py:function:`webassets.env.Resolver:resolve_source_to_url`
        """
        if self.env.debug:
            return item
        return super(InvenioResolver, self).resolve_source_to_url(filepath,
                                                                  item)

    def search_for_source(self, item):
        """Return absolute path of the resource.

        It uses the :py:data:`invenio.base.wrappers.STATIC_MAP` to identify
        which items are within a module static directory or are coming from
        the instance static directory.

        :param item: resource filename
        :return: absolute path
        .. seealso:: :py:function:`webassets.env.Resolver:search_for_source`
        """
        abspath = STATIC_MAP.get(item)
        if abspath and not os.path.exists(abspath):
            abspath = None

        if not abspath:
            try:
                abspath = super(InvenioResolver, self).search_env_directory(item)
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

    def _jinja2_new_bundle(tag, collection, name=None):
        if len(collection):
            return Bundle(output="%s/%s-%s.%s" %
                          (tag, 'invenio' if name is None else name,
                           hash('|'.join(collection)), tag), *collection)

    app.jinja_env.extend(new_bundle=_jinja2_new_bundle,
                         default_bundle_name='90-invenio')
    app.jinja_env.add_extension(CollectionExtension)

    return app
