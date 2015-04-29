# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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

"""Sentry logging backend.

Currently only Python application errors are sent to
`Sentry <http://getsentry.com>`_. Future extensions may allow for sending
JavaScript errors to Sentry as well.

**Configuration**

================================== ============================================
`SENTRY_DSN`                       Sentry DSN (get it from your Sentry account)
                                   . **Required**.
`LOGGING_SENTRY_LEVEL`             Log level threshold for handler.
                                   **Default:**  ``WARNING``.
`LOGGING_SENTRY_INCLUDE_WARNINGS`  Include messages from warnings module.
                                   **Default:**  ``True``.
`LOGGING_SENTRY_CELERY`            Log Celery messages to Sentry.
                                   **Default:**  ``True``.
`LOGGING_SENTRY_CELERY_TRANSPORT`  Transport mechanism for Celery.
                                   **Default:**  ``sync``.
================================== ============================================

`Raven <raven.readthedocs.org/en/latest/>`_ (the Python library responsible for
sending log messages to Sentry), supports some additionally configuration
variables. See https://github.com/getsentry/raven-python/blob/master/raven/contrib/flask.py
for further details.
"""

import logging
import pkg_resources
from functools import partial

from werkzeug.local import LocalProxy
from flask import current_app
from raven.handlers.logging import SentryHandler
from raven.contrib.flask import Sentry
from raven.processors import SanitizePasswordsProcessor
from celery.signals import after_setup_logger, after_setup_task_logger

import invenio


class InvenioSanitizeProcessor(SanitizePasswordsProcessor):

    """Remove additional sensitve configuration from Sentry data."""

    FIELDS = frozenset([
        'access_token'
    ])


def sentry_include_paths():
    """Detect Invenio dependencies and for use with SENTRY_INCLUDE_PATHS."""
    try:
        dist = pkg_resources.get_distribution('invenio')
        return map(lambda req: req.key, dist.requires())
    except pkg_resources.DistributionNotFound:
        pass


def setup_warnings(sentry):
    """Add sentry to warnings logger."""
    warnings = logging.getLogger('py.warnings')
    warnings.addHandler(SentryHandler(sentry.client, level=logging.WARNING))


def add_sentry_id_header(self, sender, response, *args, **kwargs):
    """Fix issue when last_event_id is not defined."""
    if hasattr(self, 'last_event_id'):
        response.headers['X-Sentry-ID'] = self.last_event_id
    return response


def celery_logger_setup(app=None, sender=None, logger=None, **kwargs):
    """Setup Sentry logging for Celery."""
    add_handler(logger, app)


def celery_dsn_fix(app):
    """Fix SENTRY_DSN for Celery.

    Celery does not handle threaded transport very well, so allow overriding
    default transport mechanism for Celery.
    """
    if app.config.get('CELERY_CONTEXT', False) and \
       app.config['LOGGING_SENTRY_CELERY'] and \
       app.config['LOGGING_SENTRY_CELERY_TRANSPORT']:
        parts = app.config['SENTRY_DSN'].split('+', 1)
        if parts[0] in ('eventlet', 'gevent', 'requests', 'sync',
                        'threaded', 'twisted', 'tornado'):
            app.config['SENTRY_DSN'] = "%s+%s" % (
                app.config['LOGGING_SENTRY_CELERY_TRANSPORT'],
                parts[1],
            )
        else:
            app.config['SENTRY_DSN'] = "%s+%s" % (
                app.config['LOGGING_SENTRY_CELERY_TRANSPORT'],
                "+".join(parts),
            )


def add_handler(logger, app):
    """Add handler to logger if not already added."""
    for h in logger.handlers:
        if type(h) == SentryHandler:
            return

    logger.addHandler(
        SentryHandler(
            app.extensions['sentry'].client,
            level=app.config['LOGGING_SENTRY_LEVEL']
        )
    )


def setup_app(app):
    """Setup Sentry extension."""
    app.config.setdefault('SENTRY_DSN', None)
    # Sanitize data more
    app.config.setdefault('SENTRY_PROCESSORS', (
        'raven.processors.SanitizePasswordsProcessor',
        'invenio.ext.logging.backends.sentry.InvenioSanitizeProcessor',
    ))
    # When a user is logged in, also include the user info in the log message.
    app.config.setdefault('SENTRY_USER_ATTRS', ['info', ])
    # Defaults to only reporting errors and warnings.
    app.config.setdefault('LOGGING_SENTRY_LEVEL', 'WARNING')
    # Send warnings to Sentry?
    app.config.setdefault('LOGGING_SENTRY_INCLUDE_WARNINGS', True)
    # Send Celery log messages to Sentry?
    app.config.setdefault('LOGGING_SENTRY_CELERY', True)
    # Transport mechanism for Celery. Defaults to synchronous transport.
    # See http://raven.readthedocs.org/en/latest/transports/index.html
    app.config.setdefault('LOGGING_SENTRY_CELERY_TRANSPORT', 'sync')

    if app.config['SENTRY_DSN']:
        # Detect Invenio requirements and add to Sentry include paths so
        # version information about them is added to the log message.
        app.config.setdefault('SENTRY_INCLUDE_PATHS', sentry_include_paths())

        # Fix-up known version problems getting version information
        # Patch submitted to raven-python, if accepted the following lines
        # can be removed:
        # https://github.com/getsentry/raven-python/pull/452
        from raven.utils import _VERSION_CACHE
        import numpy
        import webassets
        import setuptools
        _VERSION_CACHE['invenio'] = invenio.__version__
        _VERSION_CACHE['numpy'] = numpy.__version__
        _VERSION_CACHE['webassets'] = webassets.__version__
        _VERSION_CACHE['setuptools'] = setuptools.__version__

        # Modify Sentry transport for Celery - must be called prior to client
        # creation.
        celery_dsn_fix(app)

        # Installs sentry in app.extensions['sentry']
        s = Sentry(
            app,
            logging=True,
            level=getattr(logging, app.config['LOGGING_SENTRY_LEVEL'])
        )

        # Replace method with more robust version
        s.add_sentry_id_header = add_sentry_id_header

        # Add extra tags information to sentry.
        s.client.extra_context({'version': invenio.__version__})

        # Capture warnings from warnings module
        if app.config['LOGGING_SENTRY_INCLUDE_WARNINGS']:
            setup_warnings(s)

        # Setup Celery logging to Sentry
        if app.config['LOGGING_SENTRY_CELERY']:
            # Setup Celery loggers
            after_setup_task_logger.connect(
                partial(celery_logger_setup, app=app),
                weak=False
            )
            after_setup_logger.connect(
                partial(celery_logger_setup, app=app),
                weak=False
            )

        # Werkzeug only adds a stream handler if there's no other handlers
        # defined, so when Sentry adds a log handler no output is
        # received from Werkzeug unless we install a console handler here on
        # the werkzeug logger.
        if app.debug:
            logger = logging.getLogger('werkzeug')
            logger.setLevel(logging.INFO)
            handler = logging.StreamHandler()
            logger.addHandler(handler)


sentry = LocalProxy(lambda: current_app.extensions['sentry'])
"""Proxy object to sentry instance."""
