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

import warnings

## Import the remote debugger as a first thing, if allowed
#FIXME enable remote_debugger when invenio.config is ready
#try:
#    from invenio import remote_debugger
#except:
#    remote_debugger = None

from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.wrappers import BaseResponse

from flask import request, g, current_app, render_template, abort, \
    safe_join, send_from_directory

from .request_class import LegacyRequest


def setup_app(app):

    ## Legacy config support
    USE_X_SENDFILE = app.config.get('CFG_BIBDOCFILE_USE_XSENDFILE')
    DEBUG = app.config.get('CFG_DEVEL_SITE', 0) > 0
    app.config.setdefault('USE_X_SENDFILE', USE_X_SENDFILE)
    app.config.setdefault('DEBUG', DEBUG)
    app.debug = DEBUG

    class LegacyAppMiddleware(object):
        def __init__(self, app):
            self.app = app

        def __call__(self, environ, start_response):
            #FIXME
            #if remote_debugger:
            #    remote_debugger.start()

            with self.app.request_context(environ):
                g.start_response = start_response
                try:
                    response = self.app.full_dispatch_request()
                except Exception as e:
                    from invenio.ext.logging import register_exception
                    register_exception(req=request, alert_admin=True)
                    response = self.app.handle_exception(e)

                return response(environ, start_response)

    ## Set custom request class.
    app.request_class = LegacyRequest
    app.wsgi_app = LegacyAppMiddleware(app)

    @app.errorhandler(404)
    def page_not_found(error):
        try:
            from invenio.webinterface_handler_wsgi import \
                application as legacy_application
            response = legacy_application(request.environ, g.start_response)
            if not isinstance(response, BaseResponse):
                response = current_app.make_response(str(response))
            return response
        except HTTPException:
            return render_template("404.html"), 404

    @app.endpoint('static')
    @app.route(app.static_url_path + '/<path:filename>', methods=['POST', 'PUT'])
    def static_handler_with_legacy_publisher(*args, **kwargs):
        """
        Adds support for legacy publisher.

        NOTE: It changes order of url page lookup. First, the invenio_handler
        will be called and on 404 error the mp_legacy_publisher is called.
        """
        from invenio.webinterface_handler_wsgi import \
            is_mp_legacy_publisher_path, mp_legacy_publisher, \
            application as legacy_application
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
        if not app.config.get('CFG_FLASK_SERVE_STATIC_FILES'):
            abort(404)
        else:
            try:
                static_file_response = app.send_static_file(*args, **kwargs)
            except NotFound:
                static_file_response = send_from_directory(
                    safe_join(app.instance_path, 'static'), kwargs['filename'])
            if request.method in ['POST', 'PUT']:
                abort(405)
            else:
                return static_file_response

    try:
        # pylint: disable=E0611
        from invenio.webinterface_handler_local import customize_app
        # pylint: enable=E0611
        warnings.warn("Do not use 'invenio.webinterface_handler_local:"
                      "customize_app' directly. Please, adapt your function "
                      "into package and use configuration option "
                      "EXTENSIONS = ['mypackage.customize_app'] instead.",
                      DeprecationWarning)
    except ImportError:
        ## No customization needed.
        pass

    return app
