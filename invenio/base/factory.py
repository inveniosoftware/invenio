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

from flask_registry import (
    BlueprintAutoDiscoveryRegistry,
    ConfigurationRegistry,
    ExtensionRegistry,
    PackageRegistry,
    Registry
)

from pkg_resources import iter_entry_points

from six.moves.urllib.parse import urlparse

from werkzeug.local import LocalProxy

from .helpers import unicodifier, with_app_context
from .utils import captureWarnings
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


def register_legacy_blueprints(app):
    """Register some legacy blueprints."""
    @app.route('/testing')
    def testing():
        from flask import render_template
        return render_template('404.html')


def register_secret_key(app):
    """Register sercret key in application configuration."""
    SECRET_KEY = app.config.get('SECRET_KEY') or \
        app.config.get('CFG_SITE_SECRET_KEY', 'change_me')

    if not SECRET_KEY or SECRET_KEY == 'change_me':
        fill_secret_key = """
    Set variable SECRET_KEY with random string in invenio.cfg.

    You can use following commands:
    $ %s
        """ % ('inveniomanage config create secret-key', )
        warnings.warn(fill_secret_key, UserWarning)

    app.config["SECRET_KEY"] = SECRET_KEY


def load_site_config(app):
    """Load default site-configuration via entry points."""
    entry_points = list(iter_entry_points("invenio.config"))
    if len(entry_points) > 1:
        warnings.warn(
            "Found multiple site configurations. This may lead to unexpected "
            "results.",
            UserWarning
        )

    for ep in entry_points:
        app.config.from_object(ep.module_name)


def configure_warnings():
    """Configure warnings by routing warnings to the logging system.

    It also unhides DeprecationWarning.
    """
    if not sys.warnoptions:
        # Route warnings through python logging
        captureWarnings(True)

        # DeprecationWarning is by default hidden, hence we force the
        # "default" behavior on deprecation warnings which is not to hide
        # errors.
        warnings.simplefilter("default", DeprecationWarning)


def create_app(instance_path=None, **kwargs_config):
    """Prepare Invenio application based on Flask.

    Invenio consists of a new Flask application with legacy support for
    the old WSGI legacy application and the old Python legacy
    scripts (URLs to ``*.py`` files).
    """
    configure_warnings()

    # Flask application name
    app_name = '.'.join(__name__.split('.')[0:2])

    # Force instance folder to always be located in under system prefix
    instance_path = instance_path or os.path.join(
        sys.prefix, 'var', app_name + '-instance'
    )

    # Create instance path
    try:
        if not os.path.exists(instance_path):
            os.makedirs(instance_path)
    except Exception:
        pass

    # Create the Flask application instance
    app = Flask(
        app_name,
        # Static files are usually handled directly by the webserver (e.g.
        # Apache) However in case WSGI is required to handle static files too
        # (such as when running simple server), then this flag can be
        # turned on (it is done automatically by wsgi_handler_test).
        # We assume anything under '/' which is static to be server directly
        # by the webserver from CFG_WEBDIR. In order to generate independent
        # url for static files use func:`url_for('static', filename='test')`.
        static_url_path='',
        static_folder=os.path.join(instance_path, 'static'),
        template_folder='templates',
        instance_relative_config=True,
        instance_path=instance_path,
    )

    # Handle both URLs with and without trailing slashes by Flask.
    # @blueprint.route('/test')
    # @blueprint.route('/test/') -> not necessary when strict_slashes == False
    app.url_map.strict_slashes = False

    #
    # Configuration loading
    #

    # Load default configuration
    app.config.from_object('invenio.base.config')

    # Load site specific default configuration from entry points
    load_site_config(app)

    # Load invenio.cfg from instance folder
    app.config.from_pyfile('invenio.cfg', silent=True)

    # Update application config from parameters.
    app.config.update(kwargs_config)

    # Ensure SECRET_KEY has a value in the application configuration
    register_secret_key(app)

    # Update config with specified environment variables.
    for cfg_name in app.config.get('INVENIO_APP_CONFIG_ENVS',
                                   os.getenv('INVENIO_APP_CONFIG_ENVS',
                                             '').split(',')):
        cfg_name = cfg_name.strip().upper()
        if cfg_name:
            cfg_value = app.config.get(cfg_name)
            cfg_value = os.getenv(cfg_name, cfg_value)
            app.config[cfg_name] = cfg_value
            app.logger.debug("{0} = {1}".format(cfg_name, cfg_value))

    # ====================
    # Application assembly
    # ====================
    # Initialize application registry, used for discovery and loading of
    # configuration, extensions and Invenio packages
    Registry(app=app)

    app.extensions['registry'].update(
        # Register packages listed in invenio.cfg
        packages=PackageRegistry(app))

    app.extensions['registry'].update(
        # Register extensions listed in invenio.cfg
        extensions=ExtensionRegistry(app),
        # Register blueprints
        blueprints=BlueprintAutoDiscoveryRegistry(app=app),
    )

    # Extend application config with configuration from packages (app config
    # takes precedence)
    ConfigurationRegistry(app)

    # Legacy conf cleanup
    cleanup_legacy_configuration(app)

    register_legacy_blueprints(app)

    return app


def create_wsgi_app(*args, **kwargs):
    """Create WSGI application."""
    app = create_app(*args, **kwargs)

    @app.before_first_request
    def pre_load():
        """Pre-load citation dictionaries upon WSGI application start-up.

        The citation dictionaries are loaded lazily, which is good for CLI
        processes such as bibsched, but for web user queries we want them to
        be available right after web server start-up.
        """
        # FIXME: move to invenio.modules.ranker.views when its created
        try:
            from invenio.legacy.bibrank.citation_searcher import \
                get_citedby_hitset, \
                get_refersto_hitset
            get_citedby_hitset(None)
            get_refersto_hitset(None)
        except Exception:
            pass

    if app.debug:
        from werkzeug.debug import DebuggedApplication
        app.wsgi_app = DebuggedApplication(app.wsgi_app, evalex=True)

    app.wsgi_app = WSGIScriptAliasFix(app.wsgi_app)
    return app
