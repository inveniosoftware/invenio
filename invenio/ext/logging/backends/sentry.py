# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
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
invenio.ext.logging.backends.sentry
-----------------------------------

Integration of Sentry for application error logging. Configuration options:

SENTRY_DSN = "https://...:...@app.getsentry.com/..."
SENTRY_INCLUDE_PATHS = [..]  # List all modules you want version information
                             # for.
LOGGING_SENTRY_LEVEL = 'ERROR' # log level (maps to logging.ERROR)

Note, Sentry also supports logging JavaScript errors. This is however not yet
supported.
"""

import logging
import pkg_resources

from werkzeug.local import LocalProxy
from flask import current_app
from raven.contrib.flask import Sentry
import invenio


def sentry_include_paths():
    try:
        dist = pkg_resources.get_distribution('invenio')
        return map(lambda req: req.key, dist.requires())
    except pkg_resources.DistributionNotFound:
        pass


def setup_app(app):
    """
    Setup Sentry extension
    """
    app.config.setdefault('SENTRY_DSN', None)
    # When a user is logged in, also include the user info in the log message.
    app.config.setdefault('SENTRY_USER_ATTRS', ['info', ])
    # Defaults to only reporting errors and warnings.
    app.config.setdefault('LOGGING_SENTRY_LEVEL', 'WARNING')

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

        # Installs sentry in app.extensions['sentry']
        s = Sentry(
            app,
            logging=True,
            level=getattr(logging, app.config['LOGGING_SENTRY_LEVEL'])
        )

        # Add extra tags information to sentry.
        s.client.extra_context({'version': invenio.__version__})

        # Werkzeug only adds a stream handler if there's no other handlers
        # defined, so when Sentry adds a log handler no output is
        # received from Werkzeug unless we install a console handler here on
        # the werkzeug logger.
        if app.debug:
            logger = logging.getLogger('werkzeug')
            logger.setLevel(logging.INFO)
            handler = logging.StreamHandler()
            logger.addHandler(handler)


sentry = LocalProxy(lambda: current_app.extension['sentry'])
"""
Proxy object to sentry instance
"""
