# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2013 CERN.
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

""" Error handling library """

__revision__ = "$Id$"

import traceback
import os
import sys
import time
import datetime
import re
import inspect
from cStringIO import StringIO

from invenio.config import CFG_SITE_LANG, CFG_LOGDIR, \
    CFG_WEBALERT_ALERT_ENGINE_EMAIL, CFG_SITE_ADMIN_EMAIL, \
    CFG_SITE_SUPPORT_EMAIL, CFG_SITE_NAME, CFG_SITE_URL, \
    CFG_SITE_EMERGENCY_EMAIL_ADDRESSES, \
    CFG_SITE_ADMIN_EMAIL_EXCEPTIONS, \
    CFG_ERRORLIB_RESET_EXCEPTION_NOTIFICATION_COUNTER_AFTER, \
    CFG_PROPAGATE_EXCEPTIONS, \
    CFG_ERRORLIB_SENTRY_URI
from invenio.urlutils import wash_url_argument
from invenio.messages import wash_language, gettext_set_language
from invenio.dateutils import convert_datestruct_to_datetext
from invenio.dbquery import run_sql


## Regular expression to match possible password related variable that should
## be disclosed in frame analysis.
RE_PWD = re.compile(r"pwd|pass|p_pw", re.I)


def get_client_info(req):
    """
    Returns a dictionary with client information
    @param req: mod_python request
    """
    try:
        return {
            'host': req.hostname,
            'url': req.unparsed_uri,
            'time': convert_datestruct_to_datetext(time.localtime()),
            'browser': 'User-Agent' in req.headers_in and \
                          req.headers_in['User-Agent'] or "N/A",
            'client_ip': req.remote_ip}
    except:
        return {}


def get_pretty_wide_client_info(req):
    """Return in a pretty way all the avilable information about the current
    user/client"""
    if req:
        from invenio.webuser import collect_user_info
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


def get_tracestack():
    """
    If an exception has been caught, return the system tracestack or else
    return tracestack of what is currently in the stack
    """
    if traceback.format_tb(sys.exc_info()[2]):
        delimiter = "\n"
        tracestack_pretty = "Traceback: \n%s" % \
            delimiter.join(traceback.format_tb(sys.exc_info()[2]))
    else:
        ## force traceback except for this call
        tracestack = traceback.extract_stack()[:-1]
        tracestack_pretty = "%sForced traceback (most recent call last)" % \
                            (' '*4, )
        for trace_tuple in tracestack:
            tracestack_pretty += """
    File "%(file)s", line %(line)s, in %(function)s
        %(text)s""" % {
            'file': trace_tuple[0],
            'line': trace_tuple[1],
            'function': trace_tuple[2],
            'text': trace_tuple[3] is not None and \
                    str(trace_tuple[3]) or ""}
    return tracestack_pretty

def register_emergency(msg, recipients=None):
    """Launch an emergency. This means to send email messages to each
    address in 'recipients'. By default recipients will be obtained via
    get_emergency_recipients() which loads settings from
    CFG_SITE_EMERGENCY_EMAIL_ADDRESSES
    """
    from invenio.mailutils import send_email
    from socket import gethostname
    if not recipients:
        recipients = get_emergency_recipients()
    recipients = set(recipients)
    recipients.add(CFG_SITE_ADMIN_EMAIL)
    mail_subject = "Emergency notification from " + gethostname() + " at " + CFG_SITE_URL
    sms_subject = "ALERT"
    for address_str in recipients:
        if "sms" in address_str:
            # Probably an SMS, lets reduce things!
            subject = sms_subject
        else:
            subject = mail_subject
        send_email(CFG_SITE_SUPPORT_EMAIL, address_str, subject, msg)

def get_emergency_recipients(recipient_cfg=CFG_SITE_EMERGENCY_EMAIL_ADDRESSES, now=None):
    """Parse a list of appropriate emergency email recipients from
    CFG_SITE_EMERGENCY_EMAIL_ADDRESSES, or from a provided dictionary
    comprised of 'time constraint' => 'comma separated list of addresses'

    CFG_SITE_EMERGENCY_EMAIL_ADDRESSES format example:

    CFG_SITE_EMERGENCY_EMAIL_ADDRESSES = {
        'Sunday 22:00-06:00': '0041761111111@email2sms.foo.com',
        '06:00-18:00': 'team-in-europe@foo.com,0041762222222@email2sms.foo.com',
        '18:00-06:00': 'team-in-usa@foo.com',
        '*': 'john.doe.phone@foo.com'}
    """

    from invenio.dateutils import parse_runtime_limit

    if now is None:
        now = datetime.datetime.now()

    recipients = set()
    for time_condition, address_str in recipient_cfg.items():
        if time_condition and time_condition is not '*':
            current_range, dummy_range = parse_runtime_limit(time_condition,
                                                             now=now)
            if not current_range[0] <= now <= current_range[1]:
                continue

        recipients.add(address_str)
    return list(recipients)

def find_all_values_to_hide(local_variables, analyzed_stack=None):
    """Return all the potential password to hyde."""
    ## Let's add at least the DB password.
    if analyzed_stack is None:
        from invenio.dbquery import CFG_DATABASE_PASS
        ret = set([CFG_DATABASE_PASS])
        analyzed_stack = set()
    else:
        ret = set()
    for key, value in local_variables.iteritems():
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
        www_data = "%(time)s -> %(name)s: %(value)s (%(file)s:%(line)s:%(function)s)" % {
            'time': time.strftime("%Y-%m-%d %H:%M:%S"),
            'name': exc_name,
            'value': exc_value,
            'file': filename,
            'line': line_no,
            'function': function_name }

        ## Let's retrieve contextual user related info, if any
        try:
            client_data = get_pretty_wide_client_info(req)
        except Exception, err:
            client_data = "Error in retrieving " \
                "contextual information: %s" % err

        ## Let's extract the traceback:
        tracestack_data_stream = StringIO()
        print >> tracestack_data_stream, \
                "\n** Traceback details \n"
        traceback.print_exc(file=tracestack_data_stream)
        stack = [frame[0:4] for frame in inspect.trace()]
        #stack = [frame[0] for frame in inspect.getouterframes(exc_info[2])][skip_frames:]
        try:
            stack.reverse()
            print >> tracestack_data_stream, \
                    "\n** Stack frame details"
            values_to_hide = set()
            for frame, frame_filename, frame_line, frame_name in stack:
                try:
                    print >> tracestack_data_stream
                    print >> tracestack_data_stream, \
                            "Frame %s in %s at line %s" % (
                                frame_name,
                                frame_filename,
                                frame_line)
                    ## Dereferencing f_locals
                    ## See: http://utcc.utoronto.ca/~cks/space/blog/python/FLocalsAndTraceFunctions
                    local_values = frame.f_locals
                    try:
                        values_to_hide |= find_all_values_to_hide(local_values)

                        code = open(frame_filename).readlines()
                        first_line = max(1, frame_line-3)
                        last_line = min(len(code), frame_line+3)
                        print >> tracestack_data_stream, "-" * 79
                        for line in xrange(first_line, last_line+1):
                            code_line = code[line-1].rstrip()
                            if line == frame_line:
                                print >> tracestack_data_stream, \
                                    "----> %4i %s" % (line, code_line)
                            else:
                                print >> tracestack_data_stream, \
                                    "      %4i %s" % (line, code_line)
                        print >> tracestack_data_stream, "-" * 79
                    except:
                        pass
                    for key, value in local_values.items():
                        print >> tracestack_data_stream, "\t%20s = " % key,
                        try:
                            value = repr(value)
                        except Exception, err:
                            ## We shall gracefully accept errors when repr() of
                            ## a value fails (e.g. when we are trying to repr() a
                            ## variable that was not fully initialized as the
                            ## exception was raised during its __init__ call).
                            value = "ERROR: when representing the value: %s" % (err)
                        try:
                            print >> tracestack_data_stream, \
                                _truncate_dynamic_string(value)
                        except:
                            print >> tracestack_data_stream, \
                                "<ERROR WHILE PRINTING VALUE>"
                finally:
                    del frame
        finally:
            del stack
        tracestack_data = tracestack_data_stream.getvalue()
        for to_hide in values_to_hide:
            ## Let's hide passwords
            tracestack_data = tracestack_data.replace(to_hide, '<*****>')

        ## Okay, start printing:
        output = StringIO()

        print >> output, "* %s" % www_data
        print >> output, "\n** User details"
        print >> output, client_data

        if tracestack_data:
            print >> output, tracestack_data
        return output.getvalue()
    else:
        return ""

def _is_pow_of_2(n):
    """
    Return True if n is a power of 2
    """
    while n > 1:
        if n % 2:
            return False
        n = n / 2
    return True

def exception_should_be_notified(name, filename, line):
    """
    Return True if the exception should be notified to the admin.
    This actually depends on several considerations, e.g. wethever
    it has passed some since the last time this exception has been notified.
    """
    try:
        exc_log = run_sql("SELECT id,last_notified,counter,total FROM hstEXCEPTION WHERE name=%s AND filename=%s AND line=%s", (name, filename, line))
        if exc_log:
            exc_id, last_notified, counter, total = exc_log[0]
            delta = datetime.datetime.now() - last_notified
            counter += 1
            total += 1
            if (delta.seconds + delta.days * 86400) >= CFG_ERRORLIB_RESET_EXCEPTION_NOTIFICATION_COUNTER_AFTER:
                run_sql("UPDATE hstEXCEPTION SET last_seen=NOW(), last_notified=NOW(), counter=1, total=%s WHERE id=%s", (total, exc_id))
                return True
            else:
                run_sql("UPDATE hstEXCEPTION SET last_seen=NOW(), counter=%s, total=%s WHERE id=%s", (counter, total, exc_id))
                return _is_pow_of_2(counter)
        else:
            run_sql("INSERT INTO hstEXCEPTION(name, filename, line, last_seen, last_notified, counter, total) VALUES(%s, %s, %s, NOW(), NOW(), 1, 1)", (name, filename, line))
            return True
    except:
        raise
        return True

def get_pretty_notification_info(name, filename, line):
    """
    Return a sentence describing when this exception was already seen.
    """
    exc_log = run_sql("SELECT last_notified,last_seen,total FROM hstEXCEPTION WHERE name=%s AND filename=%s AND line=%s", (name, filename, line))
    if exc_log:
        last_notified, last_seen, total = exc_log[0]
        return "This exception has already been seen %s times\n    last time it was seen: %s\n    last time it was notified: %s\n" % (total, last_seen.strftime("%Y-%m-%d %H:%M:%S"), last_notified.strftime("%Y-%m-%d %H:%M:%S"))
    else:
        return "It is the first time this exception has been seen.\n"

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

    @param stream: 'error' or 'warning'

    @param req: mod_python request

    @param prefix: a message to be printed before the exception in
    the log

    @param suffix: a message to be printed before the exception in
    the log

    @param alert_admin: wethever to send the exception to the administrator via
        email. Note this parameter is bypassed when
                CFG_SITE_ADMIN_EMAIL_EXCEPTIONS is set to a value different than 1
    @param subject: overrides the email subject

    @return: 1 if successfully wrote to stream, 0 if not
    """

    if CFG_ERRORLIB_SENTRY_URI:
        from raven import Client
        client = Client(CFG_ERRORLIB_SENTRY_URI)
        client.captureException()

    from invenio.webinterface_handler import ClientDisconnected

    if CFG_PROPAGATE_EXCEPTIONS:
        raise

    try:
        ## Let's extract exception information
        exc_info = sys.exc_info()
        exc_name = exc_info[0].__name__

        if exc_info[0] in (ClientDisconnected, KeyboardInterrupt):
            raise

        output = get_pretty_traceback(
            req=req, exc_info=exc_info, skip_frames=2)
        if output:
            ## Okay, start printing:
            log_stream = StringIO()
            email_stream = StringIO()

            print >> email_stream, '\n',

            ## If a prefix was requested let's print it
            if prefix:
                #prefix = _truncate_dynamic_string(prefix)
                print >> log_stream, prefix + '\n'
                print >> email_stream, prefix + '\n'

            print >> log_stream, output
            print >> email_stream, output

            ## If a suffix was requested let's print it
            if suffix:
                #suffix = _truncate_dynamic_string(suffix)
                print >> log_stream, suffix
                print >> email_stream, suffix

            log_text = log_stream.getvalue()
            email_text = email_stream.getvalue()

            if email_text.endswith('\n'):
                email_text = email_text[:-1]

            ## Preparing the exception dump
            stream = stream=='error' and 'err' or 'log'

            ## We now have the whole trace
            written_to_log = False
            try:
                ## Let's try to write into the log.
                open(os.path.join(CFG_LOGDIR, 'invenio.' + stream), 'a').write(
                    log_text)
                written_to_log = True
            except:
                written_to_log = False
            filename, line_no, function_name = _get_filename_and_line(exc_info)

            ## let's log the exception and see whether we should report it.
            pretty_notification_info = get_pretty_notification_info(exc_name, filename, line_no)
            #dont report KeyboardInterrupt exceptions
            if exc_name == "KeyboardInterrupt":
                return 1
            elif exception_should_be_notified(exc_name, filename, line_no) and (CFG_SITE_ADMIN_EMAIL_EXCEPTIONS > 1 or
                (alert_admin and CFG_SITE_ADMIN_EMAIL_EXCEPTIONS > 0) or
                not written_to_log):
                ## If requested or if it's impossible to write in the log
                from invenio.mailutils import send_email
                if not subject:
                    subject = 'Exception (%s:%s:%s)' % (filename, line_no, function_name)
                subject = '%s at %s' % (subject, CFG_SITE_URL)
                email_text = "\n%s\n%s" % (pretty_notification_info, email_text)
                if not written_to_log:
                    email_text += """\
Note that this email was sent to you because it has been impossible to log
this exception into %s""" % os.path.join(CFG_LOGDIR, 'invenio.' + stream)
                send_email(
                    CFG_SITE_ADMIN_EMAIL,
                    CFG_SITE_ADMIN_EMAIL,
                    subject=subject,
                    content=email_text)
            return 1
        else:
            return 0
    except Exception, err:
        print >> sys.stderr, "Error in registering exception to '%s': '%s'" % (
            CFG_LOGDIR + '/invenio.' + stream, err)
        return 0


def raise_exception(exception_type=Exception,
                    msg='',
                    stream='error',
                    req=None,
                    prefix='',
                    suffix='',
                    alert_admin=False,
                    subject=''):
    """
    Log error exception to invenio.err and warning exception to invenio.log.
    Errors will be logged together with client information (if req is
    given).

    It does not require a previously risen exception.

    Note:   For sanity reasons, dynamic params such as PREFIX, SUFFIX and
            local stack variables are checked for length, and only first 500
            chars of their values are printed.

    @param exception_type: exception type to be used internally

    @param msg: error message

    @param stream: 'error' or 'warning'

    @param req: mod_python request

    @param prefix: a message to be printed before the exception in
    the log

    @param suffix: a message to be printed before the exception in
    the log

    @param alert_admin: wethever to send the exception to the administrator via
        email. Note this parameter is bypassed when
                CFG_SITE_ADMIN_EMAIL_EXCEPTIONS is set to a value different than 1
    @param subject: overrides the email subject

    @return: 1 if successfully wrote to stream, 0 if not
    """
    try:
        raise exception_type(msg)
    except:
        return register_exception(stream=stream,
                                  req=req,
                                  prefix=prefix,
                                  suffix=suffix,
                                  alert_admin=alert_admin,
                                  subject=subject)


def send_error_report_to_admin(header, url, time_msg,
                               browser, client, error,
                               sys_error, traceback_msg):
    """
    Sends an email to the admin with client info and tracestack
    """
    from_addr = '%s Alert Engine <%s>' % (
        CFG_SITE_NAME, CFG_WEBALERT_ALERT_ENGINE_EMAIL)
    to_addr = CFG_SITE_ADMIN_EMAIL
    body = """
The following error was seen by a user and sent to you.
%(contact)s

%(header)s

%(url)s
%(time)s
%(browser)s
%(client)s
%(error)s
%(sys_error)s
%(traceback)s

Please see the %(logdir)s/invenio.err for traceback details.""" % {
        'header': header,
        'url': url,
        'time': time_msg,
        'browser': browser,
        'client': client,
        'error': error,
        'sys_error': sys_error,
        'traceback': traceback_msg,
        'logdir': CFG_LOGDIR,
        'contact': "Please contact %s quoting the following information:" %
            (CFG_SITE_SUPPORT_EMAIL, )}
    from invenio.mailutils import send_email
    send_email(from_addr, to_addr, subject="Error notification", content=body)

def _get_filename_and_line(exc_info):
    """
    Return the filename, the line and the function_name where the exception happened.
    """
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


def wrap_warn():
    import warnings
    from functools import wraps

    def wrapper(showwarning):
        @wraps(showwarning)
        def new_showwarning(message=None, category=None, filename=None, lineno=None, file=None, line=None):
            invenio_err = open(os.path.join(CFG_LOGDIR, 'invenio.err'), "a")
            print >> invenio_err, "* %(time)s -> WARNING: %(category)s: %(message)s (%(file)s:%(line)s)\n" % {
            'time': time.strftime("%Y-%m-%d %H:%M:%S"),
            'category': category,
            'message': message,
            'file': filename,
            'line': lineno}
            print >> invenio_err, "** Traceback details\n"
            traceback.print_stack(file=invenio_err)
            print >> invenio_err, "\n"
        return new_showwarning

    warnings.showwarning = wrapper(warnings.showwarning)
