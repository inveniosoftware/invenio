# -*- coding: utf-8 -*-
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

"""Tools for working with legacy application."""

from __future__ import print_function

import os
import sys

# Import the remote debugger as a first thing, if allowed
#FIXME enable remote_debugger when invenio.config is ready
#try:
#    from invenio.utils import remote_debugger
#except:
#    remote_debugger = None

from werkzeug.exceptions import HTTPException
from werkzeug.wrappers import BaseResponse
from flask import (request, g, current_app, render_template, abort,
                   send_from_directory, url_for)
from flask_admin.menu import MenuLink

from invenio.base import signals
from invenio.base.scripts.database import create, recreate

from .request_class import LegacyRequest


def cli_cmd_reset(sender, yes_i_know=False, drop=True, **kwargs):
    """Reset legacy values."""
    from invenio.config import CFG_PREFIX
    from invenio.base.scripts.config import get_conf
    # from invenio.legacy.inveniocfg import cli_cmd_reset_sitename
    from invenio.legacy.inveniocfg import cli_cmd_reset_siteadminemail
    # from invenio.legacy.inveniocfg import cli_cmd_reset_fieldnames

    conf = get_conf()
    # FIXME refactor fixtures so these calls are not needed
    # cli_cmd_reset_sitename(conf)
    cli_cmd_reset_siteadminemail(conf)
    # cli_cmd_reset_fieldnames(conf)

    for cmd in ["%s/bin/webaccessadmin -u admin -c -a -D" % CFG_PREFIX,
                "%s/bin/webcoll -u admin" % CFG_PREFIX,
                "%s/bin/webcoll 1" % CFG_PREFIX,
                "%s/bin/bibsort -u admin --load-config" % CFG_PREFIX,
                "%s/bin/bibsort 2" % CFG_PREFIX, ]:
        if os.system(cmd):
            print("ERROR: failed execution of", cmd)
            sys.exit(1)

signals.post_command.connect(cli_cmd_reset, sender=create)
signals.post_command.connect(cli_cmd_reset, sender=recreate)


def setup_app(app):
    """Setup up the app."""
    ## Legacy config support
    USE_X_SENDFILE = app.config.get('CFG_BIBDOCFILE_USE_XSENDFILE')
    DEBUG = app.config.get('CFG_DEVEL_SITE', 0) > 0
    app.config.setdefault('USE_X_SENDFILE', USE_X_SENDFILE)
    app.config.setdefault('DEBUG', DEBUG)
    app.debug = app.config['DEBUG']

    ## Legacy directory that must exist
    for cfg_dir in ['CFG_BATCHUPLOADER_DAEMON_DIR',
                    'CFG_BIBDOCFILE_FILEDIR',
                    'CFG_BIBENCODE_DAEMON_DIR_NEWJOBS',
                    'CFG_BIBENCODE_DAEMON_DIR_OLDJOBS',
                    'CFG_BIBENCODE_TARGET_DIRECTORY',
                    'CFG_BINDIR',
                    'CFG_CACHEDIR',
                    'CFG_ETCDIR',
                    'CFG_LOCALEDIR',
                    'CFG_LOGDIR',
                    'CFG_PYLIBDIR',
                    'CFG_RUNDIR',
                    'CFG_TMPDIR',
                    'CFG_TMPSHAREDDIR',
                    'CFG_BIBEDIT_CACHEDIR',
                    'CFG_WEBBASKET_DIRECTORY_BOX_NUMBER_OF_COLUMNS',
                    'CFG_WEBDIR',
                    'CFG_WEBSUBMIT_BIBCONVERTCONFIGDIR',
                    'CFG_WEBSUBMIT_COUNTERSDIR',
                    'CFG_WEBSUBMIT_STORAGEDIR']:
        path = app.config.get(cfg_dir)
        if path:
            try:
                if not os.path.exists(path):
                    os.makedirs(path)
            except OSError:
                app.logger.exception("Cannot property create directory {path} "
                                     "for legacy variable {cfg_dir}"
                                     .format(path=path, cfg_dir=cfg_dir))

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
    @app.errorhandler(405)
    def page_not_found(error):
        try:
            from invenio.legacy.wsgi import \
                application as legacy_application
            response = legacy_application(request.environ, g.start_response)
            if not isinstance(response, BaseResponse):
                response = current_app.make_response(str(response))
            return response
        except HTTPException as e:
            current_app.logger.exception(request.path)
            error = e
        if error.code == 404:
            return render_template('404.html'), 404
        return str(error), error.code

    @app.route('/admin/<module>/<action>.py', methods=['GET', 'POST', 'PUT'])
    @app.route('/admin/<module>/<action>.py/<path:arguments>',
               methods=['GET', 'POST', 'PUT'])
    def web_admin(module, action, arguments=None):
        """Add support for legacy mod publisher."""
        from invenio.legacy.wsgi import \
            is_mp_legacy_publisher_path, mp_legacy_publisher, \
            application as legacy_application
        possible_module, possible_handler = is_mp_legacy_publisher_path(
            request.environ['PATH_INFO'])
        if possible_module is not None:
            legacy_publisher = lambda req: \
                mp_legacy_publisher(req, possible_module, possible_handler)
            return legacy_application(request.environ, g.start_response,
                                      handler=legacy_publisher)
        return render_template('404.html'), 404

    @app.endpoint('static')
    def static_handler_with_legacy_publisher(*args, **kwargs):
        """Serve static files from instance path."""
        # Static file serving for devserver
        # ---------------------------------
        # Apache normally serve all static files, but if we are using the
        # devserver we need to serve static files here.
        filename = kwargs.get("filename")
        if not app.config.get('CFG_FLASK_SERVE_STATIC_FILES') \
                or filename is None or app.static_folder is None:
            abort(404)
        else:
            return send_from_directory(app.static_folder, filename)

    @app.before_first_request
    def _setup_legacy_admin_menu():
        """Add legacy menu admin to *Flask-Admin* interface."""
        from invenio.legacy.registry import webadmin
        for admin in app.extensions['admin']:
            for legacy_admin_link in webadmin.keys():
                module, action = legacy_admin_link.split('/')
                admin.add_link(MenuLink(
                    name=module,
                    category='Legacy Admin',
                    url=url_for('web_admin', module=module, action=action)))

    return app
