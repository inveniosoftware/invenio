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
    invenio.base.wrappers
    ---------------------

    Implements the Flask application wrapper.

    The function :func:`~flask.url_for` in standard :class:`~flask.Flask`
    application changes only protocol for secure sites from 'http' to 'https'.
    However, in case the application uses non standard ports (e.g.
    http://example.org:4000, https://example:4001) or even different urls (e.g.
    http://www.example.org, https://secure.example.org) following
    :class:`Flask` wrapper is necessary.

    Configuration:

    ===================== ====================================================
    `CFG_SITE_URL`        specify URL under which your installation will be
                          visible.  For example, use "http://your.site.com".
                          Do not leave trailing slash.
    `CFG_SITE_SECURE_URL` specify secure URL under which your installation
                          secure pages such as login or registration will be
                          visible.  For example, use "https://your.site.com".
                          Do not leave trailing slash. If you don't plan on
                          using HTTPS, then you may leave this empty.
    ===================== ====================================================



    Following example shows how to make http and https url scheme loos the
    same::

        >>> from flask import url_for
        >>> from invenio.base.factory import create_app
        >>> app = create_app()
        >>> app.config['CFG_SITE_URL'] = 'http://localhost:4000'
        >>> app.config['CFG_SITE_SECURE_URL'] = 'http://localhost:4000'
        >>> ctx = app.test_request_context()
        >>> ctx.push()
        >>> url_for('search.search')
        '/search'
        >>> url_for('search.search', _external=True)
        'http://localhost:4000/search'
        >>> url_for('search.search', _external=True, _scheme='https')
        'http://localhost:4000/search'

    There is also special wrapper for static files that serves them from
    corresponding static folder depending on class:`~flask.Blueprint` or
    application.

        >>> url_for('static', filename='favicon.ico', _external=True)
        'http://localhost:4000/favicon.ico'
        >>> app.send_static_file('favicon.ico')
        <Response streamed [200 OK]>
        >>> url_for('search.static', filename='js/search/facet.js')
        '/js/search/facet.js'
        >>> app.send_static_file('js/search/facet.js')
        <Response streamed [200 OK]>
        >>> app.send_static_file('sorry-i-am-not-here.txt')
        Traceback (most recent call last):
         ...
        NotFound: 404: Not Found
        >>> ctx.pop()
"""
import os

from functools import wraps
from flask import Flask as FlaskBase, current_app, send_file
from werkzeug.utils import import_string
from werkzeug.exceptions import NotFound
from werkzeug.local import LocalProxy
from invenio.utils.datastructures import LazyDict

from .signals import before_handle_user_exception


def _decorate_url_adapter_build(wrapped):
    """Changes behavior of :func:`flask.url_for` for http and https scheme."""

    @wraps(wrapped)
    def decorator(*args, **kwargs):
        """Overwrites blueprint static url.

        :note: Custom blueprint 'static' endpoint will **NOT** work!
        """
        args = list(args)
        if args[0].endswith('.static'):
            args[0] = 'static'

        url_scheme_prefixes = {
            'http': current_app.config['CFG_SITE_URL'],
            'https': current_app.config['CFG_SITE_SECURE_URL']
        }
        force_external = kwargs.get('force_external', True)
        url_scheme = getattr(wrapped.im_self, 'url_scheme', 'http')
        kwargs['force_external'] = False
        url = wrapped(*args, **kwargs)
        if force_external:
            url = url_scheme_prefixes.get(url_scheme) + url
        return url
    return decorator


def get_static_map():
    """Generates static map from all static folders."""

    out = {}

    def generator(app, directory, files):
        """Inserts files from all static directories to `STATIC_MAP`."""
        prefix = app.static_folder
        for file_ in files:
            path = os.path.join(directory, file_)
            if os.path.isdir(path):
                continue
            filename = os.path.relpath(path, prefix.rstrip('/'))
            if filename not in out:
                out[filename] = path
            else:
                current_app.logger.info(
                    'Filename "%s" already exists: "%s" (%s)',
                    path, out[filename], app.name)

    # There are files into base/static which must be part of the STATIC_MAP
    # as well. static_folder is pointing to the generated assets.
    old = current_app.static_folder
    current_app.static_folder = os.path.join(current_app.root_path, 'static')
    os.path.walk(current_app.static_folder, generator, current_app)
    current_app.static_folder = old

    for blueprint in current_app.blueprints.values():
        if not blueprint.has_static_folder:
            continue
        os.path.walk(blueprint.static_folder, generator, blueprint)

    return out

STATIC_MAP = LazyDict(get_static_map)


class Flask(FlaskBase):  # pylint: disable=R0904
    """For more information about :class:`Flask` class see the official
    documentation of :class:`flask.Flask`."""

    def create_url_adapter(self, request):
        """Changes behavior of default `create_url_adapter` method to allow
        advance url generation."""
        url_adapter = super(self.__class__, self).create_url_adapter(request)
        if url_adapter is not None and hasattr(url_adapter, 'build'):
            url_adapter.build = _decorate_url_adapter_build(url_adapter.build)
        return url_adapter

    def send_static_file(self, filename):
        """Sends the contents of a file to the client only for filenames from
        `STATIC_MAP`.

        :param filename: name or relative path of a static file
        :returns: result of :func:`flask.send_file`
        :raises: :class:`werkzeug.exceptions.NotFound` if `filename` is not
            in `STATIC_MAP`
        """
        if filename not in STATIC_MAP:
            raise NotFound
        return send_file(STATIC_MAP[filename])

    def handle_user_exception(self, e):
        before_handle_user_exception.send(e)
        return super(Flask, self).handle_user_exception(e)


def lazy_import(name):
    """Lazy import of `name` using :func:`werkzeug.utils.import_string`
    and :class:`werkzeug.local.LocalProxy`.

    :param name: importable string
    :return: proxy to result of :func:`~werkzeug.utils.import_string`
    """
    return LocalProxy(lambda: import_string(name))
