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
Invenio -> Flask adapter
"""

## Import the remote debugger as a first thing, if allowed
try:
    from invenio import remote_debugger
except:
    remote_debugger = None

import os
from os.path import join
from pprint import pformat
from functools import wraps
from logging.handlers import RotatingFileHandler
from logging import Formatter
from flask import Flask, session, request, g, url_for, current_app, \
    render_template, redirect, flash, abort, has_app_context
from jinja2 import FileSystemLoader, MemcachedBytecodeCache
from werkzeug.routing import BuildError

from invenio import config
from invenio.errorlib import register_exception
from invenio.config import CFG_PYLIBDIR, \
    CFG_WEBSESSION_EXPIRY_LIMIT_REMEMBER, \
    CFG_BIBDOCFILE_USE_XSENDFILE, \
    CFG_LOGDIR, CFG_SITE_LANG, CFG_WEBDIR, \
    CFG_ETCDIR, CFG_DEVEL_SITE, \
    CFG_FLASK_CACHE_TYPE, CFG_FLASK_DISABLED_BLUEPRINTS, \
    CFG_SITE_URL, CFG_SITE_SECURE_URL, CFG_FLASK_SERVE_STATIC_FILES, \
    CFG_SITE_SECRET_KEY, CFG_BINDIR
from invenio.websession_config import CFG_WEBSESSION_COOKIE_NAME, \
    CFG_WEBSESSION_ONE_DAY

CFG_HAS_HTTPS_SUPPORT = CFG_SITE_SECURE_URL.startswith("https://")
CFG_FULL_HTTPS = CFG_SITE_URL.lower().startswith("https://")


def create_invenio_flask_app(**kwargs_config):
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

    def decorate_build(f):
        @wraps(f)
        def decorator(*args, **kwargs):
            scheme_url = {
                'http': current_app.config['CFG_SITE_URL'],
                'https': current_app.config['CFG_SITE_SECURE_URL']
            }
            force_external = kwargs.get('force_external', False)
            url_scheme = getattr(f.im_self, 'url_scheme', 'http')
            kwargs['force_external'] = False
            url = f(*args, **kwargs)
            if force_external:
                url = scheme_url.get(url_scheme) + url
            return url
        return decorator

    class InvenioFlask(Flask):

        def create_url_adapter(self, request):
            url_adapter = super(InvenioFlask, self).create_url_adapter(request)
            if url_adapter is not None and hasattr(url_adapter, 'build'):
                url_adapter.build = decorate_build(url_adapter.build)
            return url_adapter

    ## The Flask application instance
    _app = InvenioFlask(__name__,
        ## Static files are usually handled directly by the webserver (e.g. Apache)
        ## However in case WSGI is required to handle static files too (such
        ## as when running simple server), then this flag can be
        ## turned on (it is done automatically by wsgi_handler_test).
        ## We assume anything under '/' which is static to be server directly
        ## by the webserver from CFG_WEBDIR. In order to generate independent
        ## url for static files use func:`url_for('static', filename='test')`.
        static_url_path='',
        static_folder=CFG_WEBDIR)

    ## Update application config from parameters.
    _app.config.update(kwargs_config)

    if 'SQLALCHEMY_DATABASE_URI' not in _app.config:
        from sqlalchemy.engine.url import URL
        # Global variables
        from invenio.dbquery import CFG_DATABASE_HOST, CFG_DATABASE_PORT,\
            CFG_DATABASE_NAME, CFG_DATABASE_USER, CFG_DATABASE_PASS, \
            CFG_DATABASE_TYPE

        _app.config['SQLALCHEMY_DATABASE_URI'] = URL(CFG_DATABASE_TYPE,
                                                     username=CFG_DATABASE_USER,
                                                     password=CFG_DATABASE_PASS,
                                                     host=CFG_DATABASE_HOST,
                                                     database=CFG_DATABASE_NAME,
                                                     port=CFG_DATABASE_PORT,
                                                     )

    ## Let's initialize database.
    from invenio.sqlalchemyutils import db
    db.init_app(_app)

    ## Make sure that all tables are loaded in `db.metadata.tables`.
    from invenio.importutils import autodiscover_modules
    autodiscover_modules(['invenio'], related_name_re=".+_model\.py")

    ## First check that you have all rights to logs
    from invenio.bibtask import check_running_process_user
    check_running_process_user()

    from invenio.pluginutils import PluginContainer
    from invenio.session_flask import InvenioSessionInterface
    from invenio.webuser_flask import InvenioLoginManager, current_user
    from invenio.messages import wash_language, gettext_set_language, \
                                 language_list_long, is_language_rtl
    from invenio.urlutils import create_url, get_canonical_and_alternates_urls
    from invenio.cache import cache
    from invenio.jinja2utils import CollectionExtension, \
                                    LangExtension, hack_jinja2_utf8decoding, \
                                    extend_application_template_filters
    from flask.ext.assets import Environment, Bundle
    from invenio.webinterface_handler_flask_utils import unicodifier, InvenioRequest
    from flaskext.gravatar import Gravatar
    from werkzeug.wrappers import BaseResponse
    from werkzeug.exceptions import HTTPException
    from invenio.flask_sslify import SSLify
    from invenio.webinterface_handler_wsgi import application as legacy_application
    from invenio.webinterface_handler_wsgi import is_mp_legacy_publisher_path, \
                                                  mp_legacy_publisher

    # See note on Jinja2 string decoding using ASCII codec instead of UTF8 in
    # function documentation
    hack_jinja2_utf8decoding()

    # Handle both url with and without trailing slashe by Flask.
    # @blueprint.route('/test')
    # @blueprint.route('/test/') -> not necessary when strict_slashes == False
    _app.url_map.strict_slashes = False

    # SECRET_KEY is needed by Flask Debug Toolbar
    SECRET_KEY = _app.config.get('SECRET_KEY') or CFG_SITE_SECRET_KEY
    if not SECRET_KEY or SECRET_KEY == '':
        fill_secret_key = """
    Set variable CFG_SITE_SECRET_KEY with random string in invenio-local.conf.

    You can use following commands:
    $ %s
    $ %s
        """ % (CFG_BINDIR + os.sep + 'inveniocfg --create-secret-key',
               CFG_BINDIR + os.sep + 'inveniocfg --update-config-py')
        try:
            raise Exception(fill_secret_key)
        except Exception:
            register_exception(alert_admin=True,
                               subject="Missing CFG_SITE_SECRET_KEY")
            raise Exception(fill_secret_key)

    _app.config["SECRET_KEY"] = SECRET_KEY

    # Enable Flask Debug Toolbar early to also catch HTTPS redirects
    if 'debug-toolbar' in getattr(config, 'CFG_DEVEL_TOOLS', []):
        _app.config["DEBUG_TB_ENABLED"] = True
        _app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = 'intercept-redirects' in getattr(config, 'CFG_DEVEL_TOOLS', [])
        from flask_debugtoolbar import DebugToolbarExtension
        DebugToolbarExtension(_app)

    # Set email backend for Flask-Email plugin
    from invenio.mailutils import initialize_email_backend
    initialize_email_backend(_app)

    if CFG_HAS_HTTPS_SUPPORT:
        # Makes request always run over HTTPS.
        _sslify = SSLify(_app)

        if not CFG_FULL_HTTPS:
            @_sslify.criteria_handler
            def criteria():
                """Extends criteria when to stay on HTTP site."""
                _force_https = False
                if request.blueprint in current_app.blueprints:
                    _force_https = current_app.blueprints[request.blueprint].\
                                   _force_https

                view_func = current_app.view_functions.get(request.endpoint)
                if view_func is not None and hasattr(view_func, '_force_https'):
                    _force_https = view_func._force_https

                return not (_force_https or session.need_https())

    class LegacyAppMiddleware(object):
        def __init__(self, app):
            self.app = app

        def __call__(self, environ, start_response):
            if remote_debugger:
                remote_debugger.start()

            with self.app.request_context(environ):
                g.start_response = start_response
                try:
                    response = self.app.full_dispatch_request()
                except Exception as e:
                    register_exception(req=request, alert_admin=True)
                    response = self.app.handle_exception(e)

                return response(environ, start_response)

    _app.wsgi_app = LegacyAppMiddleware(_app)

    @_app.errorhandler(404)
    def page_not_found(error):
        try:
            response = legacy_application(request.environ, g.start_response)
            if not isinstance(response, BaseResponse):
                response = current_app.make_response(str(response))
            return response
        except HTTPException:
            return render_template("404.html"), 404

    @_app.errorhandler(401)
    def do_login_first(error=401):
        """Displays login page when user is not authorised."""
        if request.is_xhr:
            return _("Authorization failure"), 401
        flash(_("Authorization failure"), 'error')
        from invenio.webaccount_blueprint import login
        return login(referer=request.referrer), 401

    @_app.endpoint('static')
    @_app.route(_app.static_url_path + '/<path:filename>', methods=['POST'])
    def static_handler_with_legacy_publisher(*args, **kwargs):
        """
        Adds support for legacy publisher.

        NOTE: It changes order of url page lookup. First, the invenio_handler
        will be called and on 404 error the mp_legacy_publisher is called.
        """
        possible_module, possible_handler = is_mp_legacy_publisher_path(
                                                request.environ['PATH_INFO'])
        if possible_module is not None:
            legacy_publisher = lambda req: \
                mp_legacy_publisher(req, possible_module, possible_handler)
            return legacy_application(request.environ, g.start_response,
                                      handler=legacy_publisher)

        # Static file serving for devserver
        # ---------------------------------
        # Apache normally serve all static files, but if we are using the
        # devserver we need to serve static files here. Werkzeugs default
        # behaviour is to return a '405 Method not allowed' for POST requests
        # to static files. However, if we abort all POST requests with 405, the
        # legacy_application (see page_not_found()) will not be given a chance
        # to serve static files as it only get's invokved when we abort with a
        # 404. Hence, on POST requests, we first check if the static file exists,
        # and if it does we return we abort the request with a 405.
        if not CFG_FLASK_SERVE_STATIC_FILES:
            abort(404)
        else:
            static_file_response = _app.send_static_file(*args, **kwargs)
            if request.method == 'POST':
                abort(405)
            else:
                return static_file_response

    if CFG_FLASK_CACHE_TYPE not in [None, 'null']:
        _app.jinja_options = dict(_app.jinja_options,
            auto_reload=False,
            cache_size=-1,
            bytecode_cache=MemcachedBytecodeCache(
                                cache, prefix="jinja::",
                                timeout=3600))

    ## Let's customize the template loader to first look into
    ## /opt/invenio/etc-local/templates and then into
    ## /opt/invenio/etc/templates
    _app.jinja_loader = FileSystemLoader([join(CFG_ETCDIR + '-local',
                                               'templates'),
                                          join(CFG_ETCDIR, 'templates')])

    ## Let's attach our session handling (which is bridging with the native
    ## Invenio session handling
    _app.session_interface = InvenioSessionInterface()

    ## Set custom request class
    _app.request_class = InvenioRequest

    ## Let's load the whole invenio.config into Flask :-) ...
    _app.config.from_object(config)

    ## ... and map certain common parameters
    _app.config['SESSION_COOKIE_NAME'] = CFG_WEBSESSION_COOKIE_NAME
    _app.config['PERMANENT_SESSION_LIFETIME'] = \
        CFG_WEBSESSION_EXPIRY_LIMIT_REMEMBER * CFG_WEBSESSION_ONE_DAY
    _app.config['USE_X_SENDFILE'] = CFG_BIBDOCFILE_USE_XSENDFILE
    _app.config['DEBUG'] = CFG_DEVEL_SITE > 0
    _app.debug = CFG_DEVEL_SITE > 0
    _app.config['CFG_LANGUAGE_LIST_LONG'] = [(lang, longname.decode('utf-8'))
        for (lang, longname) in language_list_long()]


    ## Invenio is all using str objects. Let's change them to unicode
    _app.config.update(unicodifier(dict(_app.config)))

    ## Cache
    _app.config['CACHE_TYPE'] = CFG_FLASK_CACHE_TYPE
    # FIXME problem in Flask-Cache==0.11.1
    cache.app = _app
    cache.init_app(_app)
    if CFG_FLASK_CACHE_TYPE == 'redis':
        def with_try_except_block(f):
            def decorator(*args, **kwargs):
                try:
                    return f(*args, **kwargs)
                except Exception:
                    register_exception(alert_admin=True)
                    pass
            return decorator

        ## When the redis is down, we would like to keep the site running.
        cache.cache._client.execute_command = with_try_except_block(
            cache.cache._client.execute_command)

    # FIXME problem in Flask-Cache==0.11.1
    cache.app = current_app


    _flask_log_handler = RotatingFileHandler(os.path.join(CFG_LOGDIR,
                                                          'flask.log'))
    _flask_log_handler.setFormatter(Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'
    ))
    _app.logger.addHandler(_flask_log_handler)

    # Let's create login manager.
    _login_manager = InvenioLoginManager()
    _login_manager.login_view = 'webaccount.login'
    _login_manager.setup_app(_app)
    _login_manager.unauthorized_handler(do_login_first)

        # Let's create main menu.
    class Menu(object):
        def __init__(self, id='', title='', url='', order=None, children=None,
                     display=lambda: True):
            self.id = id
            self.title = title
            self.url = url
            self.children = children or {}
            self.order = order or 100
            self.display = display

    # Let's create assets environment.
    _assets = Environment(_app)
    _assets.debug = 'assets-debug' in getattr(config, 'CFG_DEVEL_TOOLS', [])
    _assets.directory = config.CFG_WEBDIR

    def _jinja2_new_bundle(tag, collection, name=None):
        if not _assets.debug:
            files = [f for f in collection if os.path.isfile(
                     os.path.join(_assets.directory, f))]
            if len(files) != len(collection):
                ## Turn on debuging to generate 404 request on missing files.
                _assets.debug = True
                current_app.logger.error('Missing files: ' + ','.join(
                    set(collection) - set(files)))

        if len(collection):
            return Bundle(output="%s/%s-%s.%s" %
                          (tag, 'invenio' if name is None else name,
                           hash('|'.join(collection)), tag), *collection)

    _app.jinja_env.extend(new_bundle=_jinja2_new_bundle,
                          default_bundle_name='90-invenio')

    _app.jinja_env.add_extension(CollectionExtension)
    _app.jinja_env.add_extension(LangExtension)
    _app.jinja_env.add_extension('jinja2.ext.do')

    # Let's extend application with custom template filters.
    extend_application_template_filters(_app)

    # Let's create Gravatar bridge.
    _gravatar = Gravatar(_app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False)
    del _gravatar

    # Let's set the user language
    from invenio.webinterface_handler_flask_utils import guess_language
    _app.before_request(guess_language)

    # Let's extend application with more custom templete filters
    from invenio.jinja2utils import inject_utils
    _app.context_processor(inject_utils)

    @_login_manager.user_loader
    def _load_user(uid):
        """
        Function should not raise an exception if uid is not valid
        or User was not found in database.
        """
        from invenio.webuser_flask import UserInfo
        return UserInfo(uid)

    @_app.before_request
    def reset_template_context_processor():
        g._template_context_processor = []

    @_app.context_processor
    def _inject_template_context():
        context = {}
        if not hasattr(g, '_template_context_processor'):
            reset_template_context_processor()
        for func in g._template_context_processor:
            context.update(func())
        return context

    def _invenio_blueprint_plugin_builder(plugin_name, plugin_code):
        """
        Handy function to bridge pluginutils with (Invenio) blueprints.
        """
        if plugin_name in CFG_FLASK_DISABLED_BLUEPRINTS:
            raise ValueError('%s is excluded by CFG_FLASK_DISABLED_BLUEPRINTS' % plugin_name)
        from invenio.webinterface_handler_flask_utils import InvenioBlueprint
        if 'blueprint' in dir(plugin_code):
            candidate = getattr(plugin_code, 'blueprint')
            if isinstance(candidate, InvenioBlueprint):
                return candidate
        raise ValueError('%s is not a valid blueprint plugin' % plugin_name)

## Let's load all the blueprints that are composing this Invenio instance
    _BLUEPRINTS = PluginContainer(
        os.path.join(CFG_PYLIBDIR, 'invenio', '*_blueprint.py'),
        plugin_builder=_invenio_blueprint_plugin_builder)

## Let's report about broken plugins
    open(join(CFG_LOGDIR, 'broken-blueprints.log'), 'w').write(
        pformat(_BLUEPRINTS.get_broken_plugins()))

    _app.config['breadcrumbs_map'] = {}
    _app.config['menubuilder_map'] = {}

## Let's attach all the blueprints
    from invenio.webinterface_handler_flask_utils import _
    for plugin in _BLUEPRINTS.values():
        _app.register_blueprint(plugin)
        if plugin.config:
            ## Let's include the configuration parameters of the config file.
            ## E.g. if the blueprint specify the config string
            ## 'invenio.webmessage_config' any uppercase variable defined in
            ## the module invenio.webmessage_config is loaded into the system.
            _app.config.from_object(plugin.config)
        if plugin.breadcrumbs:
            _app.config['breadcrumbs_map'][plugin.name] = plugin.breadcrumbs
        _app.config['breadcrumbs_map'].update(plugin.breadcrumbs_map)

        ## Let's build global menu. Each blueprint can plug its own menu items.
        if plugin.menubuilder:
            _app.config['menubuilder_map'].update((m[0],
                Menu(*m)) for m in plugin.menubuilder)
        _app.config['menubuilder_map'].update(plugin.menubuilder_map)

    _app.config['menubuilder_map'].update({
            'main.admin': Menu('main.admin', _('Administration'),
                                'help.admin', 9998, [],
                                lambda: current_user.is_admin),
            'main.help': Menu('main.help', _('Help'), 'help', 9999)})

    menu = {'main': Menu('main', '', ''),
            'personalize': Menu('personalize', '', '')}
    for key, item in _app.config['menubuilder_map'].iteritems():
        start = menu

        if '.' not in key:
            if key in menu:
                menu[key] = item.children.update(menu[key].children)
            else:
                menu[key] = item
            continue

        keys = key.split('.')
        for k in keys[:-1]:
            try:
                start = start[k].children
            except:
                start[k] = Menu()
                start = start[k].children

        if keys[-1] in start:
            item.children.update(start[keys[-1]].children)
        start[keys[-1]] = item

    _app.config['menubuilder_map'] = menu

    # Flask-Admin
    from invenio.adminutils import register_admin
    register_admin(_app)

    try:
        ## When deploying Invenio, one can prepare a module called
        ## webinterface_handler_local.py to be deployed under
        ## CFG_PYLIBDIR/invenio directory, and containing a function called
        ## customize_app which should accept a Flask application.
        ## This function has a chance to modify the application as needed
        ## including changing the URL routing map.
        # pylint: disable=E0611
        from invenio.webinterface_handler_local import customize_app
        # pylint: enable=E0611
        customize_app(_app)
    except ImportError:
        ## No customization needed.
        pass

    return _app


def with_app_context(app=None, new_context=False, **kwargs_config):
    """Run function within application context"""

    def get_application():
        if app is None:
            application = create_invenio_flask_app(**kwargs_config)
        elif not isinstance(app, Flask) and callable(app):
            application = app(**kwargs_config)
        return application

    def decorator(f):
        @wraps(f)
        def decorated_func(*args, **kwargs):
            """This function has to run within application context."""

            if not has_app_context() or new_context:
                with get_application().app_context():
                    current_app.preprocess_request()
                    result = f(*args, **kwargs)
            else:
                result = f(*args, **kwargs)
            return result
        return decorated_func
    return decorator
