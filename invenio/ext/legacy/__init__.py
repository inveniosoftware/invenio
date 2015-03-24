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

from flask import (abort, current_app, g, render_template, request,
                   send_from_directory, url_for)
from flask_admin.menu import MenuLink
from werkzeug.exceptions import HTTPException
from werkzeug.wrappers import BaseResponse

from .request_class import LegacyRequest
from invenio.base import signals
from invenio.base.scripts.database import create, recreate
from invenio.base.utils import run_py_func


def cli_cmd_reset(sender, yes_i_know=False, drop=True, **kwargs):
    """Reset legacy values."""
    from invenio.ext.sqlalchemy import db
    from invenio.modules.accounts.models import User
    # from invenio.legacy.inveniocfg import cli_cmd_reset_sitename
    # from invenio.legacy.inveniocfg import cli_cmd_reset_fieldnames
    from invenio.legacy.bibsort.daemon import main as bibsort
    from invenio.modules.access.scripts.webaccessadmin import main as \
        webaccessadmin

    # FIXME refactor fixtures so these calls are not needed
    # cli_cmd_reset_sitename(conf)
    User.query.filter_by(id=1).delete()
    siteadminemail = current_app.config.get('CFG_SITE_ADMIN_EMAIL')
    u = User(id=1, email=siteadminemail, password='', note=1, nickname='admin')
    db.session.add(u)
    db.session.commit()
    # cli_cmd_reset_fieldnames(conf)

    for cmd in (
        (webaccessadmin, "webaccessadmin -u admin -c -a -D"),
        (bibsort, "bibsort -u admin --load-config"),
        (bibsort, "bibsort 1"),
    ):
        if run_py_func(*cmd, passthrough=True).exit_code:
            print("ERROR: failed execution of", *cmd)
            sys.exit(1)

signals.post_command.connect(cli_cmd_reset, sender=create)
signals.post_command.connect(cli_cmd_reset, sender=recreate)


def setup_app(app):
    """Setup up the app."""
    # Legacy config support
    _use_x_sendfile = app.config.get('CFG_BIBDOCFILE_USE_XSENDFILE')
    _debug = app.config.get('CFG_DEVEL_SITE', 0) > 0
    app.config.setdefault('USE_X_SENDFILE', _use_x_sendfile)
    app.config.setdefault('DEBUG', _debug)
    app.debug = app.config['DEBUG']

    # Legacy directory that must exist
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
            """Wrapper for legacy calls."""
            with self.app.request_context(environ):
                g.start_response = start_response
                try:
                    response = self.app.full_dispatch_request()
                except Exception as e:
                    from invenio.ext.logging import register_exception
                    register_exception(req=request, alert_admin=True)
                    response = self.app.handle_exception(e)

                return response(environ, start_response)

    # Set custom request class.
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

            def legacy_publisher(req):
                return mp_legacy_publisher(req, possible_module,
                                           possible_handler)
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
