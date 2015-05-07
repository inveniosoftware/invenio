# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2014, 2015 CERN.
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

"""Extension for logging and registering errors.

In short, use the Flask application logger (``current_app.logger``). Do
not create log files manually.

To run the examples below in a shell, be sure to first create the Flask
application:

>>> from flask import current_app
>>> from invenio.base.factory import create_app
>>> app = create_app()

Logging errors
--------------
The preferred way to log errors is by using the Flask application logger:

>>> with app.app_context():
...     try:
...         raise Exception("This is an exception")
...     except Exception:
...         current_app.logger.exception("My message")

``logger.exception()`` will automatically include the exception stacktrace in
the log record, which each log handler may decide to include or not.

You may also manually include exception information in the logger using the
``exc_info`` keyword argument:

>>> import sys
>>> with app.app_context():
...     try:
...         raise Exception("This is an exception")
...     except Exception:
...         current_app.logger.critical("My message", exc_info=1)


Naturally, other log levels may also be used:

>>> app.logger.info("This is an info message")
>>> app.logger.warning("This is a warning message")
>>> app.logger.debug("This is a debug message")

Log handlers
------------
Log messages written to the Flask application logger can be handled by many
different backends, which is configurable by the an administrator. By default
Invenio ships with following log handlers:

* ``invenio.ext.logging.backends.fs`` - Rotating file system handler.
* ``invenio.ext.logging.backends.legacy`` - Error email reporting and logging
  to database. Default logging behaviour of Invenio 1.x.
* ``invenio.ext.logging.backends.sentry`` - Logging to Sentry service (see
  https://pypi.python.org/pypi/sentry and https://getsentry.com/)

Installing one or more of the logging backends is a simple as including
them in your configuration variable ``EXTENSIONS``::

    EXTENSIONS = [
        # ...
        'invenio.ext.logging',
        'invenio.ext.logging.backends.fs',
        'invenio.ext.logging.backends.legacy',
        'invenio.ext.logging.backends.sentry',
        # ...
    ]

Note that each backend may require additional configuration. Please see
:ref:`ext_logging_backends` for specific details.

Additionally if you plan to write your own backend, you may wish to consult
Python's logging documentation for how to create handlers, formatters
and filters: https://docs.python.org/2/library/logging.html

Legacy handling of errors
-------------------------
Invenio 1.x used a method ``register_exception`` to log errors. This method may
still be used, but may be deprecated in the future:

>>> from invenio.ext.logging import register_exception
>>> with app.app_context():
...     try:
...         raise Exception("This is an exception")
...     except Exception as e:
...         register_exception()


The method ``register_exception`` is in fact just a small wrapper around the
application logger.

Error handling do's and don'ts
------------------------------

**Always use ``except Exception:`` (or preferably more specific exceptions)
over ``except:``**, unless you explicitly want to catch the following built-in
exceptions (``SystemExit``, ``KeyboardInterrupt``, ``GeneratorExit``).

See https://docs.python.org/2/library/exceptions.html#exception-hierarchy

**Reraise**. To gracefully handle errors, you may often catch
exceptions to perform some cleanup or e.g. convert a low-level library
exception into a more high-level application exception. This may however often
discard the initial exception and its traceback, making it hard to track
down the root cause. To preserve the traceback, simply reraise the caught
exception using a ``raise`` with no arguments:

>>> with app.app_context():
...     try:
...         try:
...             0 / 0
...         except ZeroDivisionError as e:
...             # Do clean-up
...             raise
...     except Exception as e:
...         current_app.logger.exception("Something bad happened")

If you like to convert the exception, it can be done like this:

>>> import six
>>> class AppError(Exception):
...     pass
>>> with app.app_context():
...     try:
...         try:
...             0 / 0
...         except ZeroDivisionError as e:
...             six.reraise(MyAppError, "Custom message", sys.exc_info()[2])
...     except AppError as e:
...         current_app.logger.exception("Something bad happened")

Warnings
^^^^^^^^
Warnings are useful to alert developers and system administrators about
possible problems, e.g. usage of obsolete modules, deprecated APIs etc.

Please follow Invenio :ref:`deprecationpolicy` section.
"""

from __future__ import absolute_import

import logging

from .wrappers import get_pretty_traceback, register_exception


def setup_app(app):
    """Setup logging extesions."""
    # Output deprecation warnings in debug mode
    if app.debug:
        logger = logging.getLogger('py.warnings')
        logger.addHandler(logging.StreamHandler())
        logger.setLevel(logging.WARNING)
