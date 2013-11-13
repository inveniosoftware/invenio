# -*- coding: utf-8 -*-
## This file is part of Invenio.
## Copyright (C) 2011, 2012, 2013 CERN.
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

#from invenio.ext.logging import register_exception
from .helpers import with_app_context, unicodifier
from .utils import collect_blueprints, register_extensions, \
    register_configurations
from .wrappers import Flask


__all__ = ['create_app', 'with_app_context']


def create_app(**kwargs_config):
    """
    Prepare WSGI Invenio application based on Flask.

    Invenio consists of a new Flask application with legacy support for
    the old WSGI legacy application and the old Python legacy
    scripts (URLs to *.py files).

    An incoming request is processed in the following manner:

     * The Flask application first routes request via its URL routing
       system (see LegacyAppMiddleware.__call__()).

     * One route in the Flask system, will match Python legacy
       scripts (see static_handler_with_legacy_publisher()).

     * If the Flask application aborts the request with a 404 error, the request
       is passed on to the WSGI legacy application (see page_not_found()). E.g.
       either the Flask application did not find a route, or a view aborted the
       request with a 404 error.
    """

    ## The Flask application instance
    _app = Flask('.'.join(__name__.split('.')[0:2]),
        ## Static files are usually handled directly by the webserver (e.g. Apache)
        ## However in case WSGI is required to handle static files too (such
        ## as when running simple server), then this flag can be
        ## turned on (it is done automatically by wsgi_handler_test).
        ## We assume anything under '/' which is static to be server directly
        ## by the webserver from CFG_WEBDIR. In order to generate independent
        ## url for static files use func:`url_for('static', filename='test')`.
        static_url_path='',
        template_folder='templates',
        instance_relative_config=True,
        )

    # Handle both url with and without trailing slashe by Flask.
    # @blueprint.route('/test')
    # @blueprint.route('/test/') -> not necessary when strict_slashes == False
    _app.url_map.strict_slashes = False

    # Load invenio.conf
    _app.config.from_object('invenio.base.config')

    try:
        #print _app.instance_path
        import os
        os.makedirs(_app.instance_path)
    except:
        pass

    # Load invenio.cfg
    _app.config.from_pyfile('invenio.cfg', silent=True)

    ## Update application config from parameters.
    _app.config.update(kwargs_config)

    ## Database was here.

    ## First check that you have all rights to logs
    #from invenio.bibtask import check_running_process_user
    #check_running_process_user()

    #from invenio.base.i18n import language_list_long
    def language_list_long():
        return []

    # Jinja2 hacks were here.
    # See note on Jinja2 string decoding using ASCII codec instead of UTF8 in
    # function documentation

    # SECRET_KEY is needed by Flask Debug Toolbar
    SECRET_KEY = _app.config.get('SECRET_KEY') or \
        _app.config.get('CFG_SITE_SECRET_KEY', 'change_me')
    if not SECRET_KEY or SECRET_KEY == 'change_me':
        fill_secret_key = """
    Set variable SECRET_KEY with random string in invenio.cfg.

    You can use following commands:
    $ %s
        """ % ('inveniomanage config create secret-key', )
        print fill_secret_key
        #try:
        #    raise Exception(fill_secret_key)
        #except Exception:
        #    #register_exception(alert_admin=True,
        #    #                   subject="Missing CFG_SITE_SECRET_KEY")
        #    raise Exception(fill_secret_key)

    _app.config["SECRET_KEY"] = SECRET_KEY

    # Register extendsions listed in invenio.cfg
    register_extensions(_app)

    # Extend application config with packages configuration.
    register_configurations(_app)

    # Debug toolbar was here

    # Set email backend for Flask-Email plugin

    # Mailutils were here

    # SSLify was here

    # Legacy was here

    # Jinja2 Memcache Bytecode Cache was here.

    # Jinja2 custom loader was here.

    # SessionInterface was here.

    ## Set custom request class was here.

    ## ... and map certain common parameters
    _app.config['CFG_LANGUAGE_LIST_LONG'] = [(lang, longname.decode('utf-8'))
        for (lang, longname) in language_list_long()]

    ## Invenio is all using str objects. Let's change them to unicode
    _app.config.update(unicodifier(dict(_app.config)))

    from invenio.base import before_request_functions
    before_request_functions.setup_app(_app)

    # Cache was here

    # Logging was here.

    # Login manager was here.

    # Main menu was here.

    # Jinja2 extensions loading was here.

    # Custom template filters were here.

    # Gravatar bridge was here.

    # Set the user language was here.

    # Custom templete filters loading was here.

    def _invenio_blueprint_plugin_builder(plugin):
        """
        Handy function to bridge pluginutils with (Invenio) blueprints.
        """
        from flask import Blueprint
        if 'blueprints' in dir(plugin):
            candidates = getattr(plugin, 'blueprints')
        elif 'blueprint' in dir(plugin):
            candidates = [getattr(plugin, 'blueprint')]
        else:
            candidates = []

        for candidate in candidates:
            if isinstance(candidate, Blueprint):
                if candidate.name in _app.config.get('CFG_FLASK_DISABLED_BLUEPRINTS', []):
                    _app.logger.info('%s is excluded by CFG_FLASK_DISABLED_BLUEPRINTS' % candidate.name)
                    return
                return candidate
        _app.logger.error('%s is not a valid blueprint plugin' % plugin.__name__)


    ## Let's load all the blueprints that are composing this Invenio instance
    _BLUEPRINTS = [m for m in map(_invenio_blueprint_plugin_builder,
                                  collect_blueprints(app=_app))
                   if m is not None]

    ## Let's attach all the blueprints
    for plugin in _BLUEPRINTS:
        _app.register_blueprint(plugin,
                                url_prefix=_app.config.get(
                                    'BLUEPRINTS_URL_PREFIXES',
                                    {}).get(plugin.name))

    # Flask-Admin was here.
    @_app.route('/testing')
    def testing():
        from flask import render_template
        return render_template('404.html')
    return _app
