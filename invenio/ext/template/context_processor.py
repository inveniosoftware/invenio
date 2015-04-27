# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2014 CERN.
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

"""Additional decorator for extending template context with new objects."""

import six

from flask import g, request, current_app, has_app_context
from werkzeug.utils import cached_property


def register_template_context_processor(f):
    """Register globally the context processor."""
    g._template_context_processor.append(f)


class template_args(object):

    """Register a context processor function for given endpoint.

    If you need to pass some extra parameters to the template,
    you can override particular template context of any view function.
    Decorated function is executed for **every** single ``render_template``
    executed within you view. For any execution heavy functions use
    caching per request.

    These arguments are local for this request and will be discarded
    in the next request.

    Any value passed through ``_invenio_template_args`` will override whatever
    parent view function passed to the template.

    Example of usage in an extension:

    .. code-block:: python

        def setup_app(app):

            @template_args('collections.index', app=app)
            def foo():
                return dict(foo='bar')


    Example of usage in an overlay ``views.py``:

    .. code-block:: python

        from invenio.modules.collections.views.collections import index

        @template_args(index)
        def bar():
            return {'baz': 'bar'}

    If you define endpoint as string then ``template_args`` should only be
    called from an extensions ``setup_app``.

    .. note::

        Make sure that each ``@template_args`` is called (initialized)
        **only** once.

    """

    def __init__(self, endpoint, app=None):
        """Initialize decorator."""
        self._endpoint = endpoint
        self._app = app

    @cached_property
    def endpoint(self):
        """Return view function for given endpoint."""
        if isinstance(self._endpoint, six.string_types):
            return self.app.view_functions[self._endpoint]
        return self._endpoint

    @cached_property
    def app(self):
        """Return ``app`` from constructor or ``current_app``."""
        if self._app is None and has_app_context():
            return current_app._get_current_object()
        if self._app is None:
            raise Exception('Application context or app argument needed.')
        return self._app

    def _register(self, func):
        """Register a context processor function."""
        if not hasattr(self.endpoint, '_invenio_template_args'):
            setattr(self.endpoint, '_invenio_template_args', [])
        self.endpoint._invenio_template_args.append(func)

    def __call__(self, func):
        """Decorator."""
        if isinstance(self._endpoint, six.string_types):
            @self.app.before_first_request
            def appender():
                self._register(func)
        else:
            self._register(func)


def setup_app(app):
    """Initialize template context processor extension."""
    @app.before_request
    def reset_template_context():
        """Reset custom template context buffer."""
        g._template_context_processor = []

    @app.context_processor
    def inject_template_context():
        """Update `Jinja2` context by dynamic context processors."""
        context = {}
        for func in getattr(g, '_template_context_processor', []):
            context.update(func())

        # used by ``template_args`` decorator.
        endpoint = current_app.view_functions.get(request.endpoint)
        for func in getattr(endpoint, '_invenio_template_args', []):
            context.update(func())

        reset_template_context()
        return context

    return app
