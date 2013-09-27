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
    invenio.base.wrappers
    ---------------------

    Implements the Flask application wrapper.

    The function `url_for` in standard :class:`~flask.Flask` application
    changes only protocol for secure sites (http -> https). However, in case
    the application uses non standard ports (http://example.org:4000,
    https://example:4001) or even different urls (http://www.example.org,
    https://secure.example.org) following :class:`Flask` wrapper is necessary.

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

"""

from functools import wraps
from flask import Flask as FlaskBase, current_app
from werkzeug import import_string
from werkzeug.exceptions import NotFound
from werkzeug.local import LocalProxy


def _decorate_url_adapter_build(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        url_scheme_prefixes = {
            'http': current_app.config['CFG_SITE_URL'],
            'https': current_app.config['CFG_SITE_SECURE_URL']
        }
        force_external = kwargs.get('force_external', True)
        url_scheme = getattr(f.im_self, 'url_scheme', 'http')
        kwargs['force_external'] = False
        url = f(*args, **kwargs)
        if force_external:
            url = url_scheme_prefixes.get(url_scheme) + url
        return url
    return decorator


class Flask(FlaskBase):
    """For more information about :class:`Flask` see :class:`~flask.Flask`."""

    def create_url_adapter(self, request):
        url_adapter = super(self.__class__, self).create_url_adapter(request)
        if url_adapter is not None and hasattr(url_adapter, 'build'):
            url_adapter.build = _decorate_url_adapter_build(url_adapter.build)
        return url_adapter

    def static_dispatchers(self):
        yield super(self.__class__, self).send_static_file
        for blueprint in self.blueprints.values():
            yield blueprint.send_static_file

    def send_static_file(self, filename):
        last_exception = NotFound
        for static_dispatcher in self.static_dispatchers():
            try:
                return static_dispatcher(filename)
            except NotFound as e:
                last_exception = e
            except Exception as e:
                self.logger.error(e)
                last_exception = e
        raise last_exception


def lazy_import(name):
    """
    Lazy import of name using `Werzeug.local.import_string`.
    """
    return LocalProxy(lambda: import_string(name))
