# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2013, 2014 CERN.
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

"""Implement various utils.

Utilities that could potentially exist in separate packages should be placed in
this file.
"""

from flask import has_app_context, current_app
from werkzeug.utils import import_string, find_modules
from functools import partial


def import_module_from_packages(name, app=None, packages=None, silent=False):
    """Import modules from packages."""
    warnings.warn("Use of import_module_from_packages has been deprecated."
                  " Please use Flask-Registry instead.",  DeprecationWarning)

    if app is None and has_app_context():
        app = current_app
    if app is None:
        raise Exception(
            'Working outside application context or provide app'
        )

    if packages is None:
        packages = app.config.get('PACKAGES', [])

    for package in packages:
        if package.endswith('.*'):
            for module in find_modules(package[:-2], include_packages=True):
                try:
                    yield import_string(module + '.' + name, silent)
                except ImportError:
                    pass
                except Exception:
                    app.logger.exception("could not import %s.%s",
                                         package, name)
            continue
        try:
            yield import_string(package + '.' + name, silent)
        except ImportError:
            pass
        except Exception:
            app.logger.exception("could not import %s.%s", package, name)

autodiscover_user_settings = partial(import_module_from_packages,
                                     'user_settings')
autodiscover_managers = partial(import_module_from_packages, 'manage')


def try_to_eval(string, context={}, **general_context):
    """Take care of evaluating the python expression.

    If an exception happens, it tries to import the needed module.

    @param string: String to evaluate
    @param context: Context needed, in some cases, to evaluate the string

    @return: The value of the expression inside string
    """
    if not string:
        return None

    res = None
    imports = []
    general_context.update(context)
    simple = False
    while True:
        try:
            # kwalitee: disable=eval
            res = eval(string, globals().update(general_context), locals())
        except NameError as err:
            #Try first to import using werkzeug import_string
            try:
                from werkzeug.utils import import_string
                if "." in string:
                    part = string.split('.')[0]
                    import_string(part)
                    for i in string.split('.')[1:]:
                        part += '.' + i
                        import_string(part)
                    continue
                else:
                    simple = True
            except:
                pass

            import_name = str(err).split("'")[1]
            if import_name not in imports:
                if import_name in context:
                    globals()[import_name] = context[import_name]
                else:
                    globals()[import_name] = __import__(import_name)
                    imports.append(import_name)
                continue
            elif simple:
                import_name = str(err).split("'")[0]
                if import_name in context:
                    globals()[import_name] = context[import_name]
                else:
                    globals()[import_name] = __import__(import_name)
                    imports.append(import_name)
                continue

            raise ImportError("Can't import the needed module to evaluate %s"
                              (string, ))
        import os
        if isinstance(res, type(os)):
            raise ImportError
        return res


#
# Python 2.6 implementation of logging.captureWarnings introduced in Python 2.7
# Copy/pasted from logging/__init__.py. Can be removed as soon as dependency on
# Python 2.6 is removed.
import logging
import warnings
import sys


class NullHandler(logging.Handler):

    """This handler does nothing.

    It's intended to be used to avoid the
    "No handlers could be found for logger XXX" one-off warning. This is
    important for library code, which may contain code to log events. If a user
    of the library does not configure logging, the one-off warning might be
    produced; to avoid this, the library developer simply needs to instantiate
    a NullHandler and add it to the top-level logger of the library module or
    package.
    """

    def handle(self, record):
        """Handle."""
        pass

    def emit(self, record):
        """Emit."""
        pass

    def createLock(self):
        """Lock."""
        self.lock = None


_warnings_showwarning = None


def _showwarning(message, category, filename, lineno, file=None, line=None):
    """Implementation of showwarnings which redirects to logging.

    It will first check to see if the file parameter is None.
    If a file is specified, it will
    delegate to the original warnings implementation of showwarning. Otherwise,
    it will call warnings.formatwarning and will log the resulting string to a
    warnings logger named "py.warnings" with level logging.WARNING.
    """
    if sys.hexversion >= 0x2070000:
        raise RuntimeError("_showwarning() should not be used on Python 2.7+")

    if file is not None:
        if _warnings_showwarning is not None:
            _warnings_showwarning(message, category, filename, lineno, file,
                                  line)
    else:
        s = warnings.formatwarning(message, category, filename, lineno, line)
        logger = logging.getLogger("py.warnings")
        if not logger.handlers:
            logger.addHandler(NullHandler())
        logger.warning("%s", s)


def _captureWarnings(capture):
    """If capture is true, redirect all warnings to the logging package.

    If capture is False, ensure that warnings are not redirected to logging
    but to their original destinations.
    """
    if sys.hexversion >= 0x2070000:
        raise RuntimeError(
            "_captureWarnings() should not be used on Python 2.7+"
        )

    global _warnings_showwarning
    if capture:
        if _warnings_showwarning is None:
            _warnings_showwarning = warnings.showwarning
            warnings.showwarning = _showwarning
    else:
        if _warnings_showwarning is not None:
            warnings.showwarning = _warnings_showwarning
            _warnings_showwarning = None

if sys.hexversion >= 0x2070000:
    captureWarnings = logging.captureWarnings
else:
    captureWarnings = _captureWarnings

# https://mail.python.org/pipermail/python-ideas/2011-January/008958.html
class staticproperty(object):

    """Property decorator for static methods."""

    def __init__(self, function):
        self._function = function

    def __get__(self, instance, owner):
        return self._function()


class classproperty(object):

    """Property decorator for class methods."""

    def __init__(self, function):
        self._function = function

    def __get__(self, instance, owner):
        return self._function(owner)
