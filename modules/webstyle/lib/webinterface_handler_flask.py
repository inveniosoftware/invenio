# -*- coding: utf-8 -*-
## This file is part of Invenio.
## Copyright (C) 2011 CERN.
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

import os
from os.path import join, exists, getmtime, splitext
from pprint import pformat
from logging.handlers import RotatingFileHandler
from logging import Formatter
from flask import Blueprint, Flask, logging, session, request, g, url_for, current_app
from jinja2 import FileSystemLoader
from werkzeug.routing import BuildError, NotFound, RequestRedirect

from invenio import config
from invenio.errorlib import register_exception
from invenio.webinterface_handler_wsgi import application as _legacy_app
from invenio.webinterface_handler_flask_utils import _, InvenioBlueprint, unicodifier
from invenio.pluginutils import PluginContainer, create_enhanced_plugin_builder
from invenio.config import CFG_PYLIBDIR, CFG_WEBSESSION_EXPIRY_LIMIT_REMEMBER, CFG_BIBDOCFILE_USE_XSENDFILE, CFG_LOGDIR, CFG_SITE_LANG, CFG_WEBDIR, CFG_ETCDIR, CFG_DEVEL_SITE
from invenio.websession_config import CFG_WEBSESSION_COOKIE_NAME, CFG_WEBSESSION_ONE_DAY
from invenio.session_flask import InvenioSessionInterface
from invenio.messages import wash_language, gettext_set_language, language_list_long, is_language_rtl
from invenio.dateutils import convert_datetext_to_dategui
from invenio.urlutils import create_url
from invenio.webuser import collect_user_info


__all__ = ["application"]

## The Flask application instance
_app = Flask(__name__,
    static_url_path='/', ## We assume anything under '/' which is static to be handled directly by Apache
    static_folder=CFG_WEBDIR)

## Let's customize the template loader to first look into
## /opt/invenio/etc-local/templates and then into /opt/invenio/etc/templates
_app.jinja_loader = FileSystemLoader([join(CFG_ETCDIR + '-local', 'templates'), join(CFG_ETCDIR, 'templates')])

## Let's attach our session handling (which is bridging with the native Invenio session handling
_app.session_interface = InvenioSessionInterface()

## Let's load the whole invenio.config into Flask :-) ...
_app.config.from_object(config)

## ... and map certain common parameters
_app.config['SESSION_COOKIE_NAME'] = CFG_WEBSESSION_COOKIE_NAME
_app.config['PERMANENT_SESSION_LIFETIME'] = CFG_WEBSESSION_EXPIRY_LIMIT_REMEMBER * CFG_WEBSESSION_ONE_DAY
_app.config['USE_X_SENDFILE'] = CFG_BIBDOCFILE_USE_XSENDFILE
_app.config['DEBUG'] = CFG_DEVEL_SITE
_app.debug = CFG_DEVEL_SITE
_app.config['CFG_LANGUAGE_LIST_LONG'] = [(lang, longname.decode('utf-8')) for (lang, longname) in language_list_long()]

## Invenio is all using str objects. Let's change them to unicode
_app.config.update(unicodifier(dict(_app.config)))



_flask_log_handler = RotatingFileHandler(os.path.join(CFG_LOGDIR, 'flask.log'))
_flask_log_handler.setFormatter(Formatter(
    '%(asctime)s %(levelname)s: %(message)s '
    '[in %(pathname)s:%(lineno)d]'
))
_app.logger.addHandler(_flask_log_handler)

@_app.before_request
def _populate_user_info():
    """
    Before every request being handled, let's compute the user_info dictionary
    which is used everywhere in Invenio to describe a user.

    This user_info dictionary is also stored in the session (under the 'user_info'
    key) and in the Flask global variable (under the 'user_info' attribute).
    """
    g.user_info = session['user_info'] = collect_user_info(request._get_current_object())

@_app.before_request
def _guess_language():
    """
    Before every request being handled, let's compute the language needed to
    return the answer to the client.

    This information will then be available in the session['ln'] and in g.ln.

    Additionally under g._ an already configured internationalization function
    will be available (configured to return unicode objects).
    """
    required_ln = None
    if "ln" in request.values:
        ## If ln is specified explictly as a GET or POST argument
        ## let's take it!
        passed_ln = str(request.values["ln"])
        required_ln = wash_language(passed_ln)
        if passed_ln != required_ln:
            ## But only if it was a valid language
            required_ln = None
    if required_ln:
        ## Ok it was. We store it in the session.
        session["ln"] = required_ln
    if not "ln" in session:
        ## If there is no language saved into the session...
        if "user_info" in session and session["user_info"].get("language"):
            ## ... and the user is logged in, we try to take it from its
            ## settings.
            session["ln"] = session["user_info"]["language"]
        else:
            ## Otherwise we try to guess it from its request headers
            for value, quality in request.accept_languages:
                value = str(value)
                ln = wash_language(value)
                if ln == value or ln[:2] == value[:2]:
                    session["ln"] = ln
                    break
            else:
                ## Too bad! We stick to the default :-)
                session["ln"] = CFG_SITE_LANG
    ## Well, let's make it global now
    g.ln = session["ln"]
    g._ = gettext_set_language(g.ln, use_unicode=True)

@_app.template_filter('invenio_format_date')
def _format_date(date):
    """
    This is a special Jinja2 filter that will call convert_datetext_to_dategui
    to print a human friendly date.
    """
    return convert_datetext_to_dategui(date, g.ln).decode('utf-8')

@_app.context_processor
def _inject_utils():
    """
    This will add some more variables and functions to the Jinja2 to execution
    context. In particular it will add:

    - `url_for`: an Invenio specific wrapper of Flask url_for, that will let you
                 obtain URLs for non Flask-native handlers (i.e. not yet ported
                 Invenio URLs)
    - `breadcrumbs`: this will be a list of two-elements tuples, containing
                 the hierarchy of Label -> URLs of navtrails/breadcrumbs.
    - `_`: this can be used to automatically translate a given string.
    - `is_language_rtl`: is True if the chosen language should be read right to left
    """
    def invenio_url_for(endpoint, **values):
        try:
            return url_for(endpoint, **values)
        except BuildError:
            if endpoint.startswith('.'):
                endpoint = request.blueprint + endpoint
            return create_url('/' + '/'.join(endpoint.split('.')), values, False).decode('utf-8')

    if request.endpoint in current_app.config['breadcrumbs_map']:
        breadcrumbs = current_app.config['breadcrumbs_map'][request.endpoint]
    else:
        breadcrumbs = [(_('Home'), '')]+ current_app.config['breadcrumbs_map'].get(request.endpoint.split('.')[0], [])

    return dict(_=g._,
                is_language_rtl=is_language_rtl(g.ln),
                url_for=invenio_url_for,
                breadcrumbs=breadcrumbs)

def _invenio_blueprint_plugin_builder(plugin_name, plugin_code):
    """
    Handy function to bridge pluginutils with (Invenio) blueprints.
    """
    if 'blueprint' in dir(plugin_code):
        candidate = getattr(plugin_code, 'blueprint')
        if isinstance(candidate, InvenioBlueprint):
            return candidate
    raise ValueError('%s is not a valid external authentication plugin' % plugin_name)


## Let's load all the blueprints that are composing this Invenio instance
_BLUEPRINTS = PluginContainer(
    os.path.join(CFG_PYLIBDIR, 'invenio', '*_blueprint.py'),
    plugin_builder=_invenio_blueprint_plugin_builder)

## Let's report about broken plugins
open(join(CFG_LOGDIR, 'broken-blueprints.log'), 'w').write(
    pformat(_BLUEPRINTS.get_broken_plugins()))

_app.config['breadcrumbs_map'] = {}

## Let's attach all the blueprints
for plugin in _BLUEPRINTS.values():
    _app.register_blueprint(plugin)
    if plugin.config:
        ## Let's include the configuration parameters of the config file.
        ## E.g. if the blueprint specify the config string 'invenio.webmessage_config'
        ## any uppercase variable defined in the module invenio.webmessage_config
        ## is loaded into the system.
        _app.config.from_object(plugin.config)
    if plugin.breadcrumbs:
        _app.config['breadcrumbs_map'][plugin.name] = plugin.breadcrumbs
    _app.config['breadcrumbs_map'].update(plugin.breadcrumbs_map)

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

## assuming there is a flask_application

class InvenioFlaskDispatcher(object):
    """
    This class has to be instantiated only once and is implementing a
    WSGI application wrapping Flask and Invenio legacy web interface
    handler.
    If the Flask handler can not resolve a given URL request then this
    will be resolved (if possible) via the Invenio handler.
    """
    def __init__(self, flask_application, legacy_application):
        self.flask_application = flask_application
        self.legacy_application = legacy_application

    def __call__(self, environ, start_response):
        """
        Special method to implement the WSGI application protocol
        """
        try:
            urls = self.flask_application.url_map.bind_to_environ(environ)
            try:
                _endpoint, _args = urls.match()
            except NotFound, e:
                ## This should be handled by Invenio legacy_application
                return self.legacy_application(environ, start_response)
            except RequestRedirect:
                return self.flask_application(environ, start_response)
            else:
                ## OK this is a brand new Flask application :-)
                return self.flask_application(environ, start_response)
        except:
            register_exception(alert_admin=True)
            raise

application = InvenioFlaskDispatcher(_app, _legacy_app)
del _app, _legacy_app
