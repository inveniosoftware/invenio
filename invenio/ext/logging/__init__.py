# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012, 2013, 2014 CERN.
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
invenio.ext.logging
-------------------

Extension for logging and registering errors.

Short version - use the Flask application logger (``current_app.logger``). Do
not create log files manually.

To run the examples below in a shell, be sure to first create the Flask
application:

>>> from flask import current_app
>>> from invenio.base.factory import create_app
>>> app = create_app()

Handling errors
^^^^^^^^^^^^^^^

>>> from invenio.ext.logging import register_exception
>>> with app.app_context():
        try:
            raise Exception("This is an exception")
        except Exception as e:
            register_exception()


Logging
^^^^^^^
Please use the logger defined on the Flask application (``current_app.logger``)
to log any message.

>>> from flask import current_app
>>> with app.app_context():
...     current_app.logger.debug("My message")
...     current_app.logger.info("My message")
...     current_app.logger.warning("My message")
...     current_app.logger.error("My message")

You may also add extra data, which a log handler such as Sentry may decide to
include in the logged message:

>>> with app.app_context():
...     current_app.logger.error("My message", extra={'key': 'value'})


In case you do not have access to the current application, you may
*exceptionally* use the standard Python logging
(https://docs.python.org/2/library/logging.html). In case you do so, please
allow configurable logging handlers, so that an administrator can decide where
log records should be sent to.

In all cases, avoid creating log files manually and writing to them. It
prevents configuring e.g. sending emails or logging to sentry instead of
writing to files.

Log handlers
^^^^^^^^^^^^
Log messages written to  the Flask application logger can be handled by many
different backends, which is configurable by the an administrator. By default
Invenio ships with following log handlers:

* ``invenio.ext.logging.backends.fs`` - Rotating file system handler.
* ``invenio.ext.logging.backends.legacy`` - Error email reporting and logging
  to database. Default logging behaviour of Invenio 1.x.
* ``invenio.ext.logging.backends.sentry`` - Logging to Sentry service (see
  https://pypi.python.org/pypi/sentry and https://getsentry.com/)

Please see documentation in each backend for further configuration options.
"""

from .wrappers import register_exception, wrap_warn, get_pretty_traceback


def setup_app(app):
    """
    Nothing to setup. All is currently done in the specific backends.
    """
    pass


__all__ = [
    'register_exception', 'wrap_warn', 'get_pretty_traceback'
]
