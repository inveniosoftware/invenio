# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2013, 2014 CERN.
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

from __future__ import print_function, absolute_import

""" Error handling library """

import traceback
import warnings
import os
import sys
import time
import re
import inspect
from flask import current_app
from six import iteritems, StringIO

from invenio.base.globals import cfg


# Regular expression to match possible password related variable that should
# be disclosed in frame analysis.
RE_PWD = re.compile(r"pwd|pass|p_pw", re.I)


def get_pretty_wide_client_info(req):
    """Return (in a pretty way) all the available information about the current
    user/client"""
    if req:
        from invenio.legacy.webuser import collect_user_info
        user_info = collect_user_info(req)
        keys = user_info.keys()
        keys.sort()
        max_key = max([len(key) for key in keys])
        ret = ""
        fmt = "%% %is: %%s\n" % max_key
        for key in keys:
            if RE_PWD.search(key):
                continue
            if key in ('uri', 'referer'):
                ret += fmt % (key, "<%s>" % user_info[key])
            else:
                ret += fmt % (key, user_info[key])
        if ret.endswith('\n'):
            return ret[:-1]
        else:
            return ret
    else:
        return "No client information available"


def get_traceback():
    """
    If an exception has been caught, return the system stack trace or else
    return stack trace of what is currently in the stack
    """
    if traceback.format_tb(sys.exc_info()[2]):
        delimiter = "\n"
        traceback_pretty = "Traceback: \n%s" % \
            delimiter.join(traceback.format_tb(sys.exc_info()[2]))
    else:
        ## force traceback except for this call
        stack = traceback.extract_stack()[:-1]
        traceback_pretty = "%sForced traceback (most recent call last)" % \
            (' '*4, )
        for trace_tuple in stack:
            traceback_pretty += """
    File "%(file)s", line %(line)s, in %(function)s
        %(text)s""" % {
                'file': trace_tuple[0],
                'line': trace_tuple[1],
                'function': trace_tuple[2],
                'text': trace_tuple[3] is not None
                and str(trace_tuple[3]) or ""
            }
    return traceback_pretty


def find_all_values_to_hide(local_variables, analyzed_stack=None):
    """Return all the potential password to hide."""
    ## Let's add at least the DB password.
    if analyzed_stack is None:
        ret = set([cfg['CFG_DATABASE_PASS']])
        analyzed_stack = set()
    else:
        ret = set()
    for key, value in iteritems(local_variables):
        if id(value) in analyzed_stack:
            ## Let's avoid loops
            continue
        analyzed_stack.add(id(value))
        if RE_PWD.search(key):
            ret.add(str(value))
        if isinstance(value, dict):
            ret |= find_all_values_to_hide(value, analyzed_stack)
    if '' in ret:
        ## Let's discard the empty string in case there is an empty password,
        ## or otherwise anything will be separated by '<*****>' in the output
        ## :-)
        ret.remove('')
    return ret


def get_pretty_traceback(req=None, exc_info=None, skip_frames=0):
    """
    Given an optional request object and an optional exc_info,
    returns a text string representing many details about an exception.
    """
    if exc_info is None:
        exc_info = sys.exc_info()
    if exc_info[0]:
        ## We found an exception.

        ## We want to extract the name of the Exception
        exc_name = exc_info[0].__name__
        exc_value = str(exc_info[1])
        filename, line_no, function_name = _get_filename_and_line(exc_info)

        ## Let's record when and where and what
        www_data = (
            "%(time)s -> %(name)s: %(value)s (%(file)s:%(line)s:%(function)s)"
            % {
                'time': time.strftime("%Y-%m-%d %H:%M:%S"),
                'name': exc_name,
                'value': exc_value,
                'file': filename,
                'line': line_no,
                'function': function_name
            }
        )

        ## Let's retrieve contextual user related info, if any
        try:
            client_data = get_pretty_wide_client_info(req)
        except Exception as err:
            client_data = "Error in retrieving " \
                "contextual information: %s" % err

        ## Let's extract the traceback:
        traceback_data_stream = StringIO()
        print("\n** Traceback details \n", file=traceback_data_stream)
        traceback.print_exc(file=traceback_data_stream)
        stack = [frame[0] for frame in inspect.trace()]
        try:
            stack.reverse()
            print("\n** Stack frame details", file=traceback_data_stream)
            values_to_hide = set()
            for frame in stack:
                try:
                    print(file=traceback_data_stream)
                    print("Frame %s in %s at line %s" % (
                        frame.f_code.co_name,
                        frame.f_code.co_filename,
                        frame.f_lineno), file=traceback_data_stream)
                    ## Dereferencing f_locals
                    ## See: http://utcc.utoronto.ca/~cks/space/blog/python/
                    ##      FLocalsAndTraceFunctions
                    local_values = frame.f_locals
                    try:
                        values_to_hide |= find_all_values_to_hide(local_values)

                        code = open(frame.f_code.co_filename).readlines()
                        first_line = max(1, frame.f_lineno-3)
                        last_line = min(len(code), frame.f_lineno+3)
                        print("-" * 79, file=traceback_data_stream)
                        for line in xrange(first_line, last_line+1):
                            code_line = code[line-1].rstrip()
                            if line == frame.f_lineno:
                                print(
                                    "----> %4i %s" % (line, code_line),
                                    file=traceback_data_stream
                                )
                            else:
                                print(
                                    "      %4i %s" % (line, code_line),
                                    file=traceback_data_stream
                                )
                        print("-" * 79, file=traceback_data_stream)
                    except:
                        pass
                    for key, value in local_values.items():
                        print(
                            "\t%20s = " % key, end=' ',
                            file=traceback_data_stream
                        )
                        try:
                            value = repr(value)
                        except Exception as err:
                            ## We shall gracefully accept errors when repr() of
                            ## a value fails (e.g. when we are trying to repr()
                            ## a variable that was not fully initialized as the
                            ## exception was raised during its __init__ call).
                            value = "ERROR: when representing the value: %s" \
                                    % (err)
                        try:
                            print(
                                _truncate_dynamic_string(value),
                                file=traceback_data_stream
                            )
                        except:
                            print(
                                "<ERROR WHILE PRINTING VALUE>",
                                file=traceback_data_stream
                            )
                finally:
                    del frame
        finally:
            del stack
        traceback_data = traceback_data_stream.getvalue()
        for to_hide in values_to_hide:
            ## Let's hide passwords
            traceback_data = traceback_data.replace(to_hide, '<*****>')

        ## Okay, start printing:
        output = StringIO()

        print("* %s" % www_data, file=output)
        print("\n** User details", file=output)
        print(client_data, file=output)

        if traceback_data:
            print(traceback_data, file=output)
        return output.getvalue()
    else:
        return ""


def register_exception(stream='error',
                       req=None,
                       prefix='',
                       suffix='',
                       alert_admin=False,
                       subject=''):
    """
    Log error exception to invenio.err and warning exception to invenio.log.
    Errors will be logged together with client information (if req is
    given).

    Note:   For sanity reasons, dynamic params such as PREFIX, SUFFIX and
            local stack variables are checked for length, and only first 500
            chars of their values are printed.

    :param stream: 'critical', 'error', 'warning', 'info', 'debug'

    :param req: mod_python request

    :param prefix: a message to be printed before the exception in
    the log

    :param suffix: a message to be printed before the exception in
    the log

    :param alert_admin: whether to send the exception to the administrator via
        email. Note this parameter is bypassed when
        CFG_SITE_ADMIN_EMAIL_EXCEPTIONS is set to a value different than 1
    :param subject: overrides the email subject

    :return: 1 if successfully wrote to stream, 0 if not
    """
    if stream == 'error':
        logger = current_app.logger.error
    elif stream == 'warning':
        logger = current_app.logger.warning
    elif stream == 'info':
        logger = current_app.logger.info
    elif stream == 'debug':
        logger = current_app.logger.debug
    elif stream == 'critical':
        logger = current_app.logger.critical
    else:
        # Legacy - Invenio 1.x defaults to log level warning when stream was
        # undefined.
        warnings.warn(
            "register_exception() called without 'stream' defined",
            DeprecationWarning
        )
        logger = current_app.logger.warning

    extra = dict(
        invenio_register_exception=dict(
            stream=stream,
            req=req,
            prefix=prefix,
            suffix=suffix,
            alert_admin=alert_admin,
            subject=subject,
        )
    )

    try:
        logger(
            subject,
            exc_info=sys.exc_info(),
            extra=extra
        )
        return 1
    except Exception as err:
        print("Error in registering exception '%s'" % err, file=sys.stderr)
        return 0


def _get_filename_and_line(exc_info):
    """Return the filename, the line and the function_name where
    the exception happened."""
    tb = exc_info[2]
    exception_info = traceback.extract_tb(tb)[-1]
    filename = os.path.basename(exception_info[0])
    line_no = exception_info[1]
    function_name = exception_info[2]
    return filename, line_no, function_name


def _truncate_dynamic_string(val, maxlength=500):
    """
    Return at most MAXLENGTH characters of VAL.  Useful for
    sanitizing dynamic variable values in the output.
    """
    out = repr(val)
    if len(out) > maxlength:
        out = out[:maxlength] + ' [...]'
    return out
