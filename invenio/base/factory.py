# -*- coding: utf-8 -*-
## This file is part of Invenio.
## Copyright (C) 2011, 2012, 2013, 2014 CERN.
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
invenio.base.factory
--------------------

Implements application factory.
"""

import warnings
import sys
import os

#from invenio.ext.logging import register_exception
from .helpers import with_app_context, unicodifier
from .wrappers import Flask
from invenio.ext.registry import Registry, ExtensionRegistry, \
    PackageRegistry, ConfigurationRegistry, \
    ImportPathRegistry, BlueprintAutoDiscoveryRegistry


__all__ = ['create_app', 'with_app_context']


def cleanup_legacy_configuration(app):
    """
    Cleanup legacy issue in configuration
    """
    def language_list_long():
        return []

    ## ... and map certain common parameters
    app.config['CFG_LANGUAGE_LIST_LONG'] = [
        (lang, longname.decode('utf-8'))
        for (lang, longname) in language_list_long()
    ]

    ## Invenio is all using str objects. Let's change them to unicode
    app.config.update(unicodifier(dict(app.config)))


def register_legacy_blueprints(app):
    """
    Register some legacy blueprints
    """
    @app.route('/testing')
    def testing():
        from flask import render_template
        return render_template('404.html')


def register_secret_key(app):
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


def create_app(instance_path=None, **kwargs_config):
    """
    Prepare Invenio application based on Flask.

    Invenio consists of a new Flask application with legacy support for
    the old WSGI legacy application and the old Python legacy
    scripts (URLs to *.py files).
    """
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
        ## Static files are usually handled directly by the webserver (e.g.
        ## Apache) However in case WSGI is required to handle static files too
        ## (such as when running simple server), then this flag can be
        ## turned on (it is done automatically by wsgi_handler_test).
        ## We assume anything under '/' which is static to be server directly
        ## by the webserver from CFG_WEBDIR. In order to generate independent
        ## url for static files use func:`url_for('static', filename='test')`.
        static_url_path='',
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

    # Load invenio.cfg from instance folder
    app.config.from_pyfile('invenio.cfg', silent=True)

    ## Update application config from parameters.
    app.config.update(kwargs_config)

    # Ensure SECRET_KEY has a value in the application configuration
    register_secret_key(app)

    # ====================
    # Application assembly
    # ====================
    # Initialize application registry, used for discovery and loading of
    # configuration, extensions and Invenio packages
    Registry(app=app)

    # Register packages listed in invenio.cfg
    app.extensions['registry']['packages'] = PackageRegistry(app)

    # Register extensions listed in invenio.cfg
    app.extensions['registry']['extensions'] = ExtensionRegistry(app)

    # Extend application config with configuration from packages (app config
    # takes precedence)
    ConfigurationRegistry(app)

    # Leagcy conf cleanup
    cleanup_legacy_configuration(app)

    # ======================
    # Blueprint registration
    # ======================
    app.extensions['registry']['blueprints'] = BlueprintAutoDiscoveryRegistry(
        app=app
    )

    register_legacy_blueprints(app)

    return app


def create_wsgi_app(*args, **kwargs):
    """
    """
    # wrap warnings (usually from sql queries) to log the traceback
    # of their origin for debugging
    try:
        from invenio.ext.logging import wrap_warn
        wrap_warn()
    except:
        pass

    app = create_app(*args, **kwargs)

    ## Start remote debugger if appropriate:
    if app.config.get('CFG_REMOTE_DEBUGGER_ENABLED'):
        try:
            from invenio.utils import remote_debugger
            remote_debugger.start_file_changes_monitor()
            if app.config.get('CFG_REMOTE_DEBUGGER_WSGI_LOADING'):
                remote_debugger.start()
        except Exception as e:
            app.logger.error('Remote debugger is not working', e)

    @app.before_first_request
    def pre_load():
        """
        Pre-load citation dictionaries upon WSGI application start-up (the
        citation dictionaries are loaded lazily, which is good for CLI
        processes such as bibsched, but for web user queries we want them to
        be available right after web server start-up)
        """
        #FIXME: move to invenio.modules.ranker.views when its created
        try:
            from invenio.legacy.bibrank.citation_searcher import \
                get_citedby_hitset, \
                get_refersto_hitset
            get_citedby_hitset(None)
            get_refersto_hitset(None)
        except:
            pass

    if 'werkzeug-debugger' in app.config.get('CFG_DEVEL_TOOLS', []):
        from werkzeug.debug import DebuggedApplication
        app = DebuggedApplication(app, evalex=True)

    return app
