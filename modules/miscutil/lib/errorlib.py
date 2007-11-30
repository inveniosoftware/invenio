# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

""" Error handling library """

__revision__ = "$Id$"

import traceback
import sys
import time

from invenio.config import cdslang, logdir, alertengineemail, adminemail, supportemail, cdsname
from invenio.miscutil_config import CFG_MISCUTIL_ERROR_MESSAGES
from invenio.urlutils import wash_url_argument
from invenio.messages import wash_language, gettext_set_language
from invenio.dateutils import convert_datestruct_to_datetext

def get_client_info(req):
    """
    Returns a dictionary with client information
    @param req: mod_python request
    """
    try:
        return \
        {   'host'      : req.hostname,
            'url'       : req.unparsed_uri,
            'time'      : convert_datestruct_to_datetext(time.localtime()),
            'browser'   : req.headers_in.has_key('User-Agent') and req.headers_in['User-Agent'] or "N/A",
            'client_ip' : req.connection.remote_ip
        }
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
            ret += fmt % (key, user_info[key])
        return ret
    else:
        return "No client information available"

def get_tracestack():
    """
    If an exception has been caught, return the system tracestack or else return tracestack of what is currently in the stack
    """
    if traceback.format_tb(sys.exc_info()[2]):
        delimiter = "\n"
        tracestack_pretty = "Traceback: \n%s" % delimiter.join(traceback.format_tb(sys.exc_info()[2]))
    else:
        tracestack = traceback.extract_stack()[:-1] #force traceback except for this call
        tracestack_pretty = "%sForced traceback (most recent call last)" % (' '*4,)
        for trace_tuple in tracestack:
            tracestack_pretty += """
    File "%(file)s", line %(line)s, in %(function)s
        %(text)s""" % \
                {   'file'      : trace_tuple[0],
                    'line'      : trace_tuple[1],
                    'function'  : trace_tuple[2],
                    'text'      : trace_tuple[3] is not None and str(trace_tuple[3]) or ""
                }
    return tracestack_pretty

def register_exception(force_stack=False, stream='error', req=None, prefix='', suffix=''):
    """
    log error exception to invenio.err and warning exception to invenio.log
    errors will be logged with client information (if req is given)

    @param force_stack: when True stack is always printed, while when False,
    stack is printed only whenever the Exception type is not containing the
    word Invenio

    @param stream: 'error' or 'warning'

    @param req = mod_python request

    @param prefix a message to be printed before the exception in
    the log

    @param suffix a message to be printed before the exception in
    the log

    @return 1 if successfully wrote to stream, 0 if not
    """
    try:
        exc_info =  sys.exc_info()
        if exc_info[0]:
            if stream=='error':
                stream='err'
            else:
                stream='log'
            stream_to_write = open(logdir + '/invenio.' + stream, 'a')
            # <type 'exceptions.StandardError'> -> exceptions.StandardError
            exc_name = str(exc_info[0])[7:-2]
            # exceptions.StandardError -> StandardError
            exc_name = exc_name.split('.')[-1]
            exc_value = str(exc_info[1])
            print >> stream_to_write, "%(time)s -> %(name)s %(value)s" % {
                'time' : time.strftime("%Y-%m-%d %H:%M:%S"),
                'name' : exc_name,
                'value' : exc_value
            }
            if prefix:
                print >> stream_to_write, prefix
            print >> stream_to_write, get_pretty_wide_client_info(req)
            if not exc_name.startswith('Invenio') or force_stack:
                tracestack = traceback.extract_stack()[-5:-2] #force traceback except for this call
                tracestack_pretty = "%sForced traceback (most recent call last)" % (' '*4,)
                for trace_tuple in tracestack:
                    tracestack_pretty += """
  File "%(file)s", line %(line)s, in %(function)s
    %(text)s""" % \
                        {   'file'      : trace_tuple[0],
                            'line'      : trace_tuple[1],
                            'function'  : trace_tuple[2],
                            'text'      : trace_tuple[3] is not None and str(trace_tuple[3]) or ""
                        }
            print >> stream_to_write, tracestack_pretty
            traceback.print_exception(exc_info[0], exc_info[1], exc_info[2], None, stream_to_write)
            if suffix:
                print >> stream_to_write, suffix
            print >> stream_to_write, '\n'
            stream_to_write.close()
            return 1
        else:
            return 0
    except Exception, e:
        print >> sys.stderr, "Error in registering exception to '%s': '%s'" % (logdir + '/invenio.' + stream, e)
        return 0

def register_errors(errors_or_warnings_list, stream, req=None):
    """
    log errors to invenio.err and warnings to invenio.log
    errors will be logged with client information (if req is given) and a tracestack
    warnings will be logged with just the warning message

    @param errors_or_warnings_list: list of tuples (err_name, err_msg)

    err_name = ERR_ + %(module_directory_name)s + _ + %(error_name)s #ALL CAPS
    err_name must be stored in file:  module_directory_name + _config.py
    as the key for dict with name:  CFG_ + %(module_directory_name)s + _ERROR_MESSAGES

    @param stream: 'error' or 'warning'

    @param req = mod_python request
    @return tuple integer 1 if successfully wrote to stream, integer 0 if not
            will append another error to errors_list if unsuccessful
    """
    client_info_dict = ""
    if stream == "error":
        # call the stack trace now
        tracestack_pretty = get_tracestack()
        # if req is given, get client info
        if req:
            client_info_dict = get_client_info(req)
            if client_info_dict:
                client_info = \
'''URL: http://%(host)s%(url)s
    Browser: %(browser)s
    Client: %(client_ip)s''' % client_info_dict
            else:
                client_info = "No client information available"
        else:
            client_info = "No client information available"
    # check arguments
    errors_or_warnings_list = wash_url_argument(errors_or_warnings_list, 'list')
    stream = wash_url_argument(stream, 'str')
    for etuple in errors_or_warnings_list:
        etuple = wash_url_argument(etuple, 'tuple')
    # check stream arg for presence of [error,warning]; when none, add error and default to warning
    if stream == 'error':
        stream = 'err'
    elif stream == 'warning':
        stream = 'log'
    else:
        stream = 'log'
        error = 'ERR_MISCUTIL_BAD_FILE_ARGUMENT_PASSED'
        errors_or_warnings_list.append((error, eval(CFG_MISCUTIL_ERROR_MESSAGES[error])% stream))
    # update log_errors
    stream_location = logdir + '/invenio.' + stream
    errors = ''
    for etuple in errors_or_warnings_list:
        try:
            errors += "%s%s : %s \n " % (' '*4*7+' ', etuple[0], etuple[1])
        except:
            errors += "%s%s \n " % (' '*4*7+' ', etuple)
    if errors:
        errors = errors[(4*7+1):-3] # get rid of begining spaces and last '\n'
    msg = """
%(time)s --> %(errors)s%(error_file)s""" % \
    {   'time'          : client_info_dict and client_info_dict['time'] or time.strftime("%Y-%m-%d %H:%M:%S"),
        'errors'        : errors,
        'error_file'    : stream=='err' and "\n%s%s\n%s\n" % (' '*4, client_info, tracestack_pretty) or ""
    }
    try:
        stream_to_write = open(stream_location, 'a+')
        stream_to_write.writelines(msg)
        stream_to_write.close()
        return_value = 1
    except :
        error = 'ERR_MISCUTIL_WRITE_FAILED'
        errors_or_warnings_list.append((error, CFG_MISCUTIL_ERROR_MESSAGES[error] % stream_location))
        return_value = 0
    return return_value

def get_msg_associated_to_code(err_code, stream='error'):
    """
    Returns string of code
    @param code: error or warning code
    @param stream: 'error' or 'warning'
    @return tuple (err_code, formatted_message)
    """
    err_code = wash_url_argument(err_code, 'str')
    stream = wash_url_argument(stream, 'str')
    try:
        module_directory_name = err_code.split('_')[1].lower()
        module_config = module_directory_name + '_config'
        module_dict_name = "CFG_" + module_directory_name.upper() + "_%s_MESSAGES" % stream.upper()
        module = __import__(module_config, globals(), locals(), [module_dict_name])
        module_dict = getattr(module, module_dict_name)
        err_msg = module_dict[err_code]
    except ImportError:
        error = 'ERR_MISCUTIL_IMPORT_ERROR'
        err_msg = CFG_MISCUTIL_ERROR_MESSAGES[error] % (err_code,
                                                        module_config)
        err_code = error
    except AttributeError:
        error = 'ERR_MISCUTIL_NO_DICT'
        err_msg = CFG_MISCUTIL_ERROR_MESSAGES[error] % (err_code,
                                                        module_config,
                                                        module_dict_name)
        err_code = error
    except KeyError:
        error = 'ERR_MISCUTIL_NO_MESSAGE_IN_DICT'
        err_msg = CFG_MISCUTIL_ERROR_MESSAGES[error] % (err_code,
                                                        module_config + '.' + module_dict_name)
        err_code = error
    except:
        error = 'ERR_MISCUTIL_UNDEFINED_ERROR'
        err_msg = CFG_MISCUTIL_ERROR_MESSAGES[error] % err_code
        err_code = error
    return (err_code, err_msg)

def get_msgs_for_code_list(code_list, stream='error', ln=cdslang):
    """
    @param code_list: list of tuples  [(err_name, arg1, ..., argN), ...]

    err_name = ERR_ + %(module_directory_name)s + _ + %(error_name)s #ALL CAPS
    err_name must be stored in file:  module_directory_name + _config.py
    as the key for dict with name:  CFG_ + %(module_directory_name)s + _ERROR_MESSAGES
    For warnings, same thing except:
        err_name can begin with either 'ERR' or 'WRN'
        dict name ends with _warning_messages

    @param stream: 'error' or 'warning'

    @return list of tuples of length 2 [('ERR_...', err_msg), ...]
            if code_list empty, will return None.
            if errors retrieving error messages, will append an error to the list
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    out = []
    if type(code_list) is None:
        return None
    code_list = wash_url_argument(code_list, 'list')
    stream = wash_url_argument(stream, 'str')
    for code_tuple in code_list:
        if not(type(code_tuple) is tuple):
            code_tuple = (code_tuple,)
        nb_tuple_args = len(code_tuple) - 1
        err_code = code_tuple[0]
        if stream == 'error' and not err_code.startswith('ERR'):
            error = 'ERR_MISCUTIL_NO_ERROR_MESSAGE'
            out.append((error, eval(CFG_MISCUTIL_ERROR_MESSAGES[error])))
            continue
        elif stream == 'warning' and not (err_code.startswith('ERR') or err_code.startswith('WRN')):
            error = 'ERR_MISCUTIL_NO_WARNING_MESSAGE'
            out.append((error, eval(CFG_MISCUTIL_ERROR_MESSAGES[error])))
            continue
        (new_err_code, err_msg) = get_msg_associated_to_code(err_code, stream)
        if err_msg[:2] == '_(' and err_msg[-1] == ')':
            # err_msg is internationalized
            err_msg = eval(err_msg)
        nb_msg_args = err_msg.count('%') - err_msg.count('%%')
        parsing_error = ""
        if new_err_code != err_code or nb_msg_args == 0:
            # undefined_error or immediately displayable error
            out.append((new_err_code, err_msg))
            continue
        try:
            if nb_msg_args == nb_tuple_args:
                err_msg = err_msg % code_tuple[1:]
            elif nb_msg_args < nb_tuple_args:
                err_msg = err_msg % code_tuple[1:nb_msg_args+1]
                parsing_error =  'ERR_MISCUTIL_TOO_MANY_ARGUMENT'
                parsing_error_message = eval(CFG_MISCUTIL_ERROR_MESSAGES[parsing_error])
                parsing_error_message %= code_tuple[0]
            elif nb_msg_args > nb_tuple_args:
                code_tuple = list(code_tuple)
                for dummy in range(nb_msg_args - nb_tuple_args):
                    code_tuple.append('???')
                    code_tuple = tuple(code_tuple)
                err_msg = err_msg % code_tuple[1:]
                parsing_error = 'ERR_MISCUTIL_TOO_FEW_ARGUMENT'
                parsing_error_message = eval(CFG_MISCUTIL_ERROR_MESSAGES[parsing_error])
                parsing_error_message %= code_tuple[0]
        except:
            parsing_error = 'ERR_MISCUTIL_BAD_ARGUMENT_TYPE'
            parsing_error_message = eval(CFG_MISCUTIL_ERROR_MESSAGES[parsing_error])
            parsing_error_message %= code_tuple[0]
        out.append((err_code, err_msg))
        if parsing_error:
            out.append((parsing_error, parsing_error_message))
    if not(out):
        out = None
    return out

def send_error_report_to_admin(header, url, time_msg,
                               browser, client, error,
                               sys_error, traceback_msg):
    """
    Sends an email to the admin with client info and tracestack
    """
    from_addr =  '%s Alert Engine <%s>' % (cdsname, alertengineemail)
    to_addr = adminemail
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

Please see the %(logdir)s/invenio.err for traceback details.""" % \
        {   'header'    : header,
            'url'       : url,
            'time'      : time_msg,
            'browser'    : browser,
            'client'    : client,
            'error'     : error,
            'sys_error' : sys_error,
            'traceback' : traceback_msg,
            'logdir'    : logdir,
            'contact'   : "Please contact %s quoting the following information:"  % (supportemail,) #! is support email always cds?
        }
    from invenio.mailutils import send_email
    send_email(from_addr, to_addr, content=body)

