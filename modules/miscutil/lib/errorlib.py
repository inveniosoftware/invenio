# -*- coding: utf-8 -*-
## $Id$
## Comments and reviews for records.
                                                                                                                                                                                                     
## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002, 2003, 2004, 2005 CERN.
##
## The CDSware is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## The CDSware is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDSware; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
                                                                                                                                                                                                     
__lastupdated__ = """FIXME: last updated"""

from config import *
from webcomment import wash_url_argument

import time
import string
import traceback
import sys
import urllib

def get_client_info(req):
    """
    Returns a dictionary with client information
    @param req: mod_python request
    """
    try:
        return \
        {   'host'      : req.hostname,
            'url'       : req.unparsed_uri,
            'time'      : time.strftime("%Y-%m-%d %H:%M:%S"),
            'browser'   : req.headers_in.has_key('User-Agent') and req.headers_in['User-Agent'] or "NA",
            'client_ip' : req.connection.remote_ip
        }
    except:
        return {}

def get_tracestack():
    """
    If an exception has been caught, return the system tracestack or else return tracestack of what is currently in the stack 
    """
    if traceback.format_tb(sys.exc_info()[2]):
        tracestack_pretty = "Traceback: \n%s" % string.join(traceback.format_tb(sys.exc_info()[2]),"\n")
    else:
        tracestack = traceback.extract_stack()[:-1] #force traceback except for this call
        tracestack_pretty = "%sForced traceback (most recent call last)" % (' '*4,)
        for trace_tuple in tracestack:
            tracestack_pretty += '''
    File "%(file)s", line %(line)s, in %(function)s
        %(text)s''' % \
                {   'file'      : trace_tuple[0],
                    'line'      : trace_tuple[1],
                    'function'  : trace_tuple[2],
                    'text'      : trace_tuple[3] is None and "" or "%s" % trace_tuple[3]     
                }
    return tracestack_pretty

                                                                                                                                                                                                     
def register_errors(errors_or_warnings_list, file, req=None):
    """
    log errors to cdsware.err and warnings to cdsware.log
    errors will be logged with client information (if req is given) and a tracestack
    warnings will be logged with just the warning message
    @param errors_or_warnings_list: list of tuples (err_name, err_msg)
    err_name = ERR_ + %(module_directory_name)s + _ + %(error_name)s #ALL CAPS
    err_name must be stored in file:  module_directory_name + _config.py
             as the key for dict with name:  cfg_ + %(module_directory_name)s + _error_messages
    example:
        webcomment_config.py contains
            cfg_webcomment_error_messages = 
            {   'ERR_WEBCOMMENT_INVALID_RECID' : "The record id %s is invalid. Record ids must be %s", ...  }
        errors_or_warnings_list = [('ERR_WEBCOMMENT_INVALID_RECID', "The record id -3 is invalid. Record ids must be greater than zero"), ....]
        use get_msgs_for_code_list to produce the wanted errors_or_warnings_list from the dictionary values

    For warnings, same thing except:
        err_name can begin with either 'ERR' or 'WRN'
        dict name ends with _warning_messages

    @param req = mod_python request
    @return tuple integer 1 if successfully wrote to file, integer 0 if not
            will append another error to errors_list if unsuccessful
    """
    client_info_dict = ""
    if file == "error":
        # call the stack trace now
        tracestack_pretty = get_tracestack()

        ## if req is given, get client info
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
    file = wash_url_argument(file, 'str')
    for etuple in errors_or_warnings_list:
        etuple = wash_url_argument(etuple, 'tuple')
                                     
    # check file arg, if error default to warnings file + add error
    if file == 'error':
        file = 'err'
    elif file == 'warning':
        file = 'log'
    else:
        file = 'log'
        errors_or_warnings_list.append(('ERR_MISCUTIL_BAD_FILE_ARGUMENT_PASSED', "Invalid argument %s was passed") % file)
                                                                                                                                                                
    ## update log_errors
    file_pwd = logdir + '/cdsware.' + file
    errors = ''
    for etuple in errors_or_warnings_list:
        try: 
            errors += "%s%s : %s \n " % (' '*4*7+' ', etuple[0], etuple[1])
        except:
            errors += "%s%s \n " % (' '*4*7+' ', etuple)
    if errors:
        errors = errors[(4*7+1):-3] # get rid of begining spaces and last '\n'
    msg = '''
%(time)s --> %(errors)s%(error_file)s''' % \
    {   'time'          : client_info_dict and client_info_dict['time'] or time.strftime("%Y-%m-%d %H:%M:%S"),
        'errors'        : errors,
        'error_file'    : file=='err' and "\n%s%s\n%s\n" % (' '*4, client_info, tracestack_pretty) or ""
    }
    try:
        file_to_write = open(file_pwd, 'a+')
        file_to_write.writelines(msg)
        file_to_write.close()
        return_value = 1
    except :
        errors_or_warnings_list.append(('ERR_MISCUTIL_WRITE_FAILED', "Unable to write to file '%s'\n" % file_pwd))
        return_value = 0
    return return_value

def get_msg_associated_to_code(code, file):
    """
    Returns formated string of code
    @param code: error or warning code
    @param file: 'error' or 'warning'
    @return tuple (code, formated_message)
    """
    module_directory_name = code.split('_')[1].lower()
    module_config = module_directory_name + '_config'
    module_dict = "cfg_" + module_directory_name + "_%s_messages" % file
    module_dict_call = "cdsware." + module_config + '.' + module_dict
    try:
        import cdsware
        err_msg = eval(module_dict_call)[code]
    except:
        err_msg = "### Error retrieval failure: could not retrieve error msg because of programming error - could not retrieve %s in errors.py/get_msg_associated_to_code" % (module_dict_call + "['" + code + "']")
    return (code, err_msg) 

def get_msgs_for_code_list(code_list, file):
    """
    @param code_list: list of tuples  [(err_name, arg1, ..., argN), ...]
    
    err_name = ERR_ + %(module_directory_name)s + _ + %(error_name)s #ALL CAPS
    err_name must be stored in file:  module_directory_name + _config.py
             as the key for dict with name:  cfg_ + %(module_directory_name)s + _error_messages
    example:
        webcomment_config.py contains
            cfg_webcomment_error_messages = 
            {   'ERR_WEBCOMMENT_INVALID_RECID' : "The record id %s is invalid. Record ids must be %s", ...  }
        errors_or_warnings_list = [('ERR_WEBCOMMENT_INVALID_RECID', "The record id -3 is invalid. Record ids must be greater than zero"), ....]
        use get_msgs_for_code_list to produce the wanted errors_or_warnings_list from the dictionary values

    For warnings, same thing except:
        err_name can begin with either 'ERR' or 'WRN'
        dict name ends with _warning_messages

    @return list of tuples of length 2 [('ERR_...', err_msg), ...]
            if code_list empty, will return None.
            if errors retrieving error messages, will append an error to the list
    """
    out = []
    if type(code_list) is None:
        return None
    code_list = wash_url_argument(code_list, 'list')
    file = wash_url_argument(file, 'str')
    for code_tuple in code_list:
        code_tuple = wash_url_argument(code_tuple, 'tuple')
        nb_tuple_args = len(code_tuple) - 1
        err_code = code_tuple[0]
        if file=='error' and not err_code.startswith('ERR'):
            out.append(('ERR_MISCUTIL_PROGRAMMING_ERROR', "Trying to write a non error message to cdsware.err log"))
            continue
        elif file=='warning' and not err_code.startswith('ERR') and not err_code.startswith('WRN'):
            out.append(('ERR_MISCUTIL_PROGRAMMING_ERROR', "Trying to write a non error message or non warning message to cdsware.log log"))
            continue
        err_msg  = get_msg_associated_to_code(err_code, file)[1]
        nb_msg_args = err_msg.count('%s')
        parsing_error = ""
        if err_msg.startswith('###') or nb_msg_args==0: #if error or no %s in err_msg
            out.append((err_code, err_msg))
            continue
        if nb_msg_args == nb_tuple_args:
            err_msg = err_msg % code_tuple[1:]
        elif nb_msg_args < nb_tuple_args:
            err_msg = err_msg % code_tuple[1:nb_msg_args+1]
            parsing_error = " Programming error: Too many arguments given for error %s " % code_tuple[0]
        elif nb_msg_args > nb_tuple_args:
            code_tuple = list(code_tuple)
            for i in range(nb_msg_args - nb_tuple_args):
                code_tuple.append('???')
            code_tuple = tuple(code_tuple)
            err_msg = err_msg % code_tuple[1:]
            parsing_error = " Programming error: Too few arguments given for error %s " % code_tuple[0]
        out.append((err_code, err_msg))
        if parsing_error:
            out.append(('ERR_MISUTIL_PROGRAMMING_ERROR', parsing_error))
    if not out:
        out = None
    return out

def send_error_report_to_admin(header, url, time, browser, client, error, sys_error, traceback):
    """
    Sends an email to the admin with client info and tracestack
    """
    from_addr =  'CDS Alert Engine <%s>' % alertengineemail
    to_addr = adminemail 

    body = '''
The following error was seen by a user and sent to you.
%(contact)s

%(header)s

%(url)s
%(time)s
%(broser)s
%(client)s
%(error)s
%(sys_error)s
%(traceback)s

Please see the %(logdir)s/errors.log for traceback details.                                                                                                                                                                                                     
    ''' % \
        {   'header'    : header,
            'url'       : url,
            'time'      : time,
            'broser'    : browser,
            'client'    : client,
            'error'     : error,
            'sys_error' : sys_error,
            'traceback' : traceback,
            'logdir'    : logdir,
            'contact'   : "Please contact %s quoting the following information:"  % (supportemail,) #! is support email always cds?
        }

    from alert_engine import send_email
    send_email(from_addr, to_addr, body)

