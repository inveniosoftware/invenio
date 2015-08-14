# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2013, 2014, 2015 CERN.
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

"""Implements the application factory."""

from __future__ import absolute_import

import os
import sys
import urllib
import warnings

from flask_appfactory.app import base_app, load_application, load_config

from pkg_resources import iter_entry_points

from six.moves.urllib.parse import urlparse

from werkzeug.local import LocalProxy

from .helpers import unicodifier, with_app_context
from .wrappers import Flask


__all__ = ('create_app', 'with_app_context')


class WSGIScriptAliasFix(object):

    """WSGI ScriptAlias fix middleware.

    It relies on the fact that the ``WSGI_SCRIPT_ALIAS`` environment variable
    exists in the Apache configuration and identifies the virtual path to
    the invenio application.

    This setup will first look for the present of a file on disk. If the file
    exists, it will serve it otherwise it calls the WSGI application.

    If no ``WSGI_SCRIPT_ALIAS`` is defined, it does not alter anything.

    .. code-block:: apacheconf

       SetEnv WSGI_SCRIPT_ALIAS /wsgi
       WSGIScriptAlias /wsgi /opt/invenio/invenio/invenio.wsgi

       RewriteEngine on
       RewriteCond %{REQUEST_FILENAME} !-f
       RewriteRule ^(.*)$ /wsgi$1 [PT,L]

    .. seealso::

       `modwsgi Configuration Guidelines
       <https://code.google.com/p/modwsgi/wiki/ConfigurationGuidelines>`_
    """

    def __init__(self, app):
        """Initialize wsgi app wrapper."""
        self.app = app

    def __call__(self, environ, start_response):
        """Parse path from ``REQUEST_URI`` to fix ``PATH_INFO``."""
        if environ.get('WSGI_SCRIPT_ALIAS') == environ['SCRIPT_NAME']:
            path_info = urllib.unquote_plus(
                urlparse(environ.get('REQUEST_URI')).path
            )  # addresses issue with url encoded arguments in Flask routes
            environ['SCRIPT_NAME'] = ''
            environ['PATH_INFO'] = path_info
        return self.app(environ, start_response)


def cleanup_legacy_configuration(app):
    """Cleanup legacy issue in configuration."""
    from .i18n import language_list_long
    # Invenio is all using str objects. Let's change them to unicode
    app.config.update(unicodifier(dict(app.config)))
    # ... and map certain common parameters
    app.config['CFG_LANGUAGE_LIST_LONG'] = LocalProxy(language_list_long)
    app.config['CFG_WEBDIR'] = app.static_folder


def get_site_config():
    """Get default site-configuration via entry points."""
    entry_points = list(iter_entry_points("invenio.config"))
    if len(entry_points) > 1:
        warnings.warn(
            "Found multiple site configurations. This may lead to unexpected "
            "results.",
            UserWarning
        )

    return entry_points[0].module_name if entry_points else None


def create_app(instance_path=None, static_folder=None, load=True,
               **kwargs_config):
    """Prepare Invenio application based on Flask.

    Invenio consists of a new Flask application with legacy support for
    the old WSGI legacy application and the old Python legacy
    scripts (URLs to ``*.py`` files).

    For configuration variables detected from environment variables, a prefix
    will be used which is the uppercase version of the app name, excluding
    any non-alphabetic ('[^A-Z]') characters.

    If `instance_path` is `None`, the `<PREFIX>_INSTANCE_PATH` environment
    variable will be used. If that one does not exist, a path inside
    `sys.prefix` will be used.

    .. versionadded:: 2.2
        If `static_folder` is `None`, the `<PREFIX>_STATIC_FOLDER` environment
        variable will be used. If that one does not exist, a path inside the
        detected `instance_path` will be used.
    """
    # Legacy instance path
    instance_path = instance_path or \
        os.getenv('INVENIO_INSTANCE_PATH') or \
        os.path.join(sys.prefix, 'var', 'invenio.base-instance')

    app = base_app("invenio", static_url_path='', instance_path=instance_path,
                   flask_cls=Flask)

    # Handle both URLs with and without trailing slashes by Flask.
    # @blueprint.route('/test')
    # @blueprint.route('/test/') -> not necessary when strict_slashes == False
    app.url_map.strict_slashes = False

    # Load Invenio default configuration
    app.config.from_object('invenio.base.config')

    # Load configuration
    load_config(app, get_site_config(), **kwargs_config)

    if load:
        load_application(app)

    # Legacy conf cleanup
    cleanup_legacy_configuration(app)

    return app


def create_wsgi_app(*args, **kwargs):
    """Create WSGI application."""
    app = create_app(*args, **kwargs)

    if app.debug:
        from werkzeug.debug import DebuggedApplication
        app.wsgi_app = DebuggedApplication(app.wsgi_app, evalex=True)

    app.wsgi_app = WSGIScriptAliasFix(app.wsgi_app)
    return app
