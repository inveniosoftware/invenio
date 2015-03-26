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

"""Implement various utils.

Utilities that could potentially exist in separate packages should be placed in
this file.
"""

import sys
import warnings

from collections import namedtuple
from six import StringIO
import logging
import shlex
import six
from flask import has_app_context, current_app
from functools import partial
from werkzeug.utils import import_string, find_modules


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


# Python 2.6 implementation of logging.captureWarnings introduced in Python 2.7
# Copy/pasted from logging/__init__.py. Can be removed as soon as dependency on
# Python 2.6 is removed.


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


def run_py_func(manager_run, command_line, passthrough=False):
    """Runs a function of a python function with given sys.argv.

    Typically used to run the `main` function of an executable that provides no
    pythonic API.

    :param command_line: arguments to inject to sys.argv
    :type command_line: str (parsed with shlex) or iterable (passed verbatim)

    :param manager_run: function to run
    :type manager_run: function

    :param passthrough: allow stdout and and stderr to be printed to the terminal
    :type passthrough: bool

    :return: namedtuple(out, err, exit_code)
    """
    sys_stderr_orig = sys.stderr
    sys_stdout_orig = sys.stdout
    sys.stdout = StringIO()
    sys.stderr = StringIO()
    sys_argv_orig = sys.argv

    formatter = logging.Formatter('%(message)s', '')

    # Log to StringIO
    log_to_new_stdout = logging.getLogger('run_py_func_new_stdout')
    log_handler_stdout = logging.StreamHandler(sys.stdout)
    log_handler_stdout.setFormatter(formatter)
    log_to_new_stdout.addHandler(log_handler_stdout)

    log_to_new_stderr = logging.getLogger('run_py_func_new_stderr')
    long_handler_new_stderr = logging.StreamHandler(sys.stderr)
    long_handler_new_stderr.setFormatter(formatter)
    log_to_new_stderr.addHandler(long_handler_new_stderr)

    # Also log to original stdout and stderr
    if passthrough:
        log_to_stderr_orig = logging.getLogger('run_py_func_stderr_orig')
        log_handler_stdout_orig = logging.StreamHandler(sys_stdout_orig)
        log_handler_stdout_orig.setFormatter(formatter)
        log_to_stderr_orig.addHandler(log_handler_stdout_orig)

        log_to_stderr_orig = logging.getLogger('run_py_func_stderr_orig')
        log_handler_stderr_orig = logging.StreamHandler(sys_stderr_orig)
        log_handler_stderr_orig.setFormatter(formatter)
        log_to_stderr_orig.addHandler(log_handler_stderr_orig)

    # Figure out how to handle `command_line`
    if isinstance(command_line, six.string_types):
        if sys.version_info < (2, 7, 3):
            # Work around non-unicode-capable versions of shlex.split
            sys.argv =  map(lambda s: s.decode('utf8'),
                            shlex.split(command_line.encode('utf8')))
        else:
            sys.argv = shlex.split(command_line)
    else:
        sys.argv = command_line

    exit_code = None
    try:
        manager_run()
    except SystemExit as e:
        exit_code = e.code
    finally:
        out = sys.stdout.getvalue()
        err = sys.stderr.getvalue()
        # clear the standard output buffer
        sys.stdout.truncate(0)
        assert len(sys.stdout.getvalue()) == 0
        sys.stderr.truncate(0)
        assert len(sys.stderr.getvalue()) == 0
        sys.stderr = sys_stderr_orig
        sys.stdout = sys_stdout_orig
        sys.argv = sys_argv_orig

    return namedtuple('Res', ('out', 'err', 'exit_code'))(out, err, exit_code)
