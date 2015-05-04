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

"""
Implements the Flask application wrapper.

The function :func:`~flask.url_for` in standard :class:`~flask.Flask`
application changes only protocol for secure sites from 'http' to 'https'.
However, in case the application uses non standard ports (e.g.
http://example.org:4000, https://example:4001) or even different urls (e.g.
http://www.example.org, https://secure.example.org) following
:class:`Flask` wrapper is necessary.

Configuration:

+-----------------------+-----------------------------------------------------+
| `CFG_SITE_URL`        | specify URL under which your installation will be   |
|                       | visible.  For example, use "http://your.site.com".  |
|                       | Do not leave the trailing slash.                    |
+-----------------------+-----------------------------------------------------+
| `CFG_SITE_SECURE_URL` | specify secure URL under which your installation's  |
|                       | secure pages such as login or registration will be  |
|                       | visible.  For example, use "https://your.site.com". |
|                       | Do not leave the trailing slash. If you don't plan  |
|                       | using HTTPS, then you may leave this empty.         |
+-----------------------+-----------------------------------------------------+

The following example shows how to make http and https url scheme look the
same.

.. doctest::

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

"""

from __future__ import unicode_literals

from flask import Flask as FlaskBase, current_app

from functools import wraps

from six import text_type

from werkzeug.local import LocalProxy
from werkzeug.utils import import_string

from .signals import before_handle_user_exception


def _decorate_url_adapter_build(wrapped):
    """Change behavior of :func:`flask.url_for` for http and https scheme."""
    @wraps(wrapped)
    def decorator(*args, **kwargs):
        """Overwrite blueprint static url.

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
        if not isinstance(args[0], text_type):
            args[0] = args[0].decode('utf-8')
        url = wrapped(*args, **kwargs)
        if force_external:
            url = url_scheme_prefixes.get(url_scheme) + url
        return url
    return decorator


class Flask(FlaskBase):  # pylint: disable=R0904

    """
    Overriding the default Flask class.

    For more information about :class:`Flask` class see the official
    documentation of :class:`flask.Flask`.
    """

    def create_url_adapter(self, request):
        """Create the URL adapter.

        Change behavior of default `create_url_adapter` method to allow
        advance url generation.
        """
        url_adapter = super(self.__class__, self).create_url_adapter(request)
        if url_adapter is not None and hasattr(url_adapter, 'build'):
            url_adapter.build = _decorate_url_adapter_build(url_adapter.build)
        return url_adapter

    def handle_user_exception(self, e):
        """Handle the user exception.

        Hook a before handle to it.
        """
        before_handle_user_exception.send(e)
        return super(Flask, self).handle_user_exception(e)


def lazy_import(name):
    """Lazy import of the given `name`.

    :see: :func:`werkzeug.utils.import_string` and
          :class:`werkzeug.local.LocalProxy`
    :param name: importable string
    :return: proxy to result of :func:`~werkzeug.utils.import_string`
    """
    return LocalProxy(lambda: import_string(name))
