## This file is part of Invenio.
## Copyright (C) 2011, 2013 CERN.
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
Module for debugging mod_python && mod_wsgi applications that run inside
the Apache webserver (or any other webserver). This is a utility module
that makes remote debugging possible and easy.
"""



# Debug mode is activated by passing debug=[debugger_id] in the url, when
# you try to load a webpage using such url, the execution will stop (if
# breakpoints are set, or automatically depending on the debugger you are
# using). This module is only a helper utility, the actual debugging is
# done by others.
#
# Each debugger has its own number:
#
# local winpdb: debug=1
# remote winpdb: debug=2
# remote pydev: debug=3
#
# If the debug parameter is not present, the code is executed normally
# (without stopping).
#
#
# Each debugger has its own parameters that can be set via url parameters,
# you can also create your your own debugging functions, and assign a new
# number to them. Please see get_debugger() function for more information on
# how to create a new call, and see the individual debuggers for information
# what parameters they accept.
#
# Important: Remember to set WSGIDaemonProcess processes=1 threads=1 in Apache

# ----------------------------- CONFIGURATION -----------------------------------------

from .config import CFG_REMOTE_DEBUGGER_ENABLED, \
    CFG_REMOTE_DEBUGGER_IMPORT, CFG_REMOTE_DEBUGGER_WINPDB_PASSWORD, \
    CFG_REMOTE_DEBUGGER_PYDEV_REMOTE_IP, CFG_REMOTE_DEBUGGER_PYDEV_REMOTE_PORT, \
    CFG_REMOTE_DEBUGGER_PYDEV_PATHS, CFG_REMOTE_DEBUGGER_WSGI_RELOAD, \
    CFG_PYDEV_DEBUG, CFG_REMOTE_DEBUGGER_TYPE, CFG_REMOTE_DEBUGGER_NAME

# -------------------------------------------------------------------------------------
# --------------------------- no config past this point -------------------------------
# -------------------------------------------------------------------------------------
from invenio import config
import os
import glob
import traceback
import sys
from cStringIO import StringIO


def start_file_changes_monitor():
    from invenio.utils import remote_debugger_wsgi_reload as monitor
    monitor.start(interval=1.0)
    for pattern in CFG_REMOTE_DEBUGGER_WSGI_RELOAD:
        for f in glob.glob(os.path.join(config.CFG_PREFIX, pattern)):
            monitor.track(f)

# -------------------------------------------------------------------------------------
# -----------------------------     DEBUGGER PART LOADING    --------------------------
# -------------------------------------------------------------------------------------



normcase = os.path.normcase

# raise exception so that this module is not loaded (this modules is always imported
# in try...except manner)
if not CFG_REMOTE_DEBUGGER_ENABLED:
    raise Exception('Remote debugger is disabled')



# import modules that are configured for this debugger, at least for Eclipse, this
# MUST HAPPEN before other stuff gets loaded
for path, name in CFG_REMOTE_DEBUGGER_IMPORT.get(CFG_REMOTE_DEBUGGER_TYPE, {}).items():
    try:
        if '.' in path:
            globals()[name] = __import__(path, globals(), locals(), path.split('.'))
        else:
            globals()[name] = __import__(path)
    except Exception:
        traceback.print_exc()
        sys.stderr.write("Error in remote_debugger, import of the %s failed" % path)


def error_msg(debugger_args):
    """Error has been caught and we were given chance to report it"""

    debug_no, params = parse_args(debugger_args)

    if debug_no == '3':
        exc_info =  sys.exc_info()
        if exc_info[0]:
            exception_data = StringIO()
            traceback.print_exception(exc_info[0], exc_info[1], exc_info[2], None, exception_data)
            exception_data = exception_data.getvalue()
            if exception_data.endswith('\n'):
                    exception_data = exception_data[:-1]
            #pydev is truncating data (no help printing in loop)
            sys.stderr.write('\n\n...')
            sys.stderr.write(exception_data[-600:])
            sys.stderr.write('\n\n')


def start():
    """
    Switch into a debugger mode manualy - to be called fromt the command line scripts mostly
    @var debugger_args: string, eg. "3|ip:192.168.31.1|port:9999"
    """
    debug_starter = get_debugger()

    if debug_starter is None:
        raise Exception("Requested debugger not found or not initalized properly.")
    debug_starter()


def get_debugger():
    """
    Returns function that will initialize the debugger
    @var arg: arg passed from url parameter debug=xxx
    @return: function call
    """
    params = {}
    if 'winpdb-local' == CFG_REMOTE_DEBUGGER_NAME:
        func = start_embedded_winpdb_debugger
    elif 'winpdb-remote' == CFG_REMOTE_DEBUGGER_NAME:
        func = start_remote_winpdb_debugger
    elif 'pydev-remote' == CFG_REMOTE_DEBUGGER_NAME:
        func = start_remote_pydev_debugger
    else:
        return None

    # we could determine the function signature and check arguments
    # func.func_code.co_varnames[:func.func_code.co_argcount]
    # but I don't do that intentionally (to raise error if something wrong is
    # sumbmitted)


    #raise(str(params))

    return lambda: func(**params)

def parse_args(arg):
    """Parses arguments supplied through url param debug=xcxv
    @return: tuple of debuggper_no, additional_params
    """
    debug_no = ''
    params = {}
    # parse the passed-in arg
    if '|' in arg[0]:
        # it will raise error if something wrong happens
        a = arg[0].split('|')
        debug_no = a[0]
        for k, v in map(lambda x: x.split(':'), a[1:]):
            try:
                v = int(v)
            except:
                if v == 'False':
                    v = False
                elif v == 'True':
                    v = True
            params[k] = v
    else:
        debug_no = arg[0]

    return (debug_no, params)


def start_embedded_winpdb_debugger(passwd=None):
    """
    Winpdb debugger, rpdb2 must be enabled in the
    CFG_REMOTE_DEBUGGER_IMPORT

    Change the call to suit your needs
    """
    p = passwd or CFG_REMOTE_DEBUGGER_WINPDB_PASSWORD
    rpdb2.start_embedded_debugger(p)



def start_remote_winpdb_debugger(passwd=None):
    """
    Winpdb remote debugger, change the call to suit your needs
    """
    p = passwd or CFG_REMOTE_DEBUGGER_WINPDB_PASSWORD
    rpdb2.start_embedded_debugger(p, fAllowRemote=True)



def start_remote_pydev_debugger(ip=None, port=None, suspend=False, stderr=True, stdout=True, path=None):
    """
    remote eclipse/pydev debugger, pydev and putils module should be available
    in the CFG_REMOTE_DEBUGGER_IMPORT

    If you want to change behaviour of the debugger interactively, you can
    pass arguments encoded in the url, example:
    http://someurl/collection/X?debug=3|ip:192.168.31.1|port:9999|stderr:0

    @keyword ip: (str) the machine where the Pydev debugger is listening for incoming connections
    @keyword port: (str) the port of the remote machine
    @keyword suspend: (bool) whether to stop execution right after the debugger was activated
    @keyword stderr: (bool) redirect the stderr to the remote debugging machine console
    @keyword stdout: (bool) redirect the stdout to the remote debugging machine console
    @keyword path: (str) list of mappings of <source> -> <target> paths separated by '#'

    """

    # to see the translation
    if CFG_PYDEV_DEBUG:
        sys.stderr.write("We set the pydev to be verbose")
        putils.DEBUG_CLIENT_SERVER_TRANSLATION = True
        if hasattr(pydevd, "MYDEBUG"):
            pydevd.MYDEBUG = False

    i = ip or CFG_REMOTE_DEBUGGER_PYDEV_REMOTE_IP
    p = port or CFG_REMOTE_DEBUGGER_PYDEV_REMOTE_PORT

    _pydev_paths = None
    if hasattr(putils, 'PATHS_FROM_ECLIPSE_TO_PYTHON'): #never versions of Pydev
        _pydev_paths = getattr(putils, 'PATHS_FROM_ECLIPSE_TO_PYTHON')
    elif hasattr(putils, 'PATHS_FROM_CLIENT_TO_SERVER'): # pydev 1.5
        _pydev_paths = getattr(putils, 'PATHS_FROM_CLIENT_TO_SERVER')

    # Eclipse needs to know how to map the file from the remote server
    if CFG_REMOTE_DEBUGGER_PYDEV_PATHS:
        xpaths = map(lambda x: (normcase(x[0]), normcase(x[1])), CFG_REMOTE_DEBUGGER_PYDEV_PATHS)
        for couple in xpaths:
            if couple not in _pydev_paths:
                _pydev_paths.append(couple)

    # paths set through the url parameter
    if path:
        elements = path.split('#')
        if len(elements) % 2 == 1:
            elements.pop(-1)
        i = 0
        xpaths = []
        while len(elements):
            xpaths.append((normcase(elements.pop(0)), normcase(elements.pop(0))))
        for couple in xpaths:
            if couple not in _pydev_paths:
                _pydev_paths.append(couple)



    # the first argument is the IP of the (remote) machine where Eclipse Pydev
    # is listening, we send suspend=False to not bother with stopping the code executing when
    # pydev is initialized, set your own breakpoints inside Eclipse to stop execution


    # this is HACK!!! we basically try to reconnect to another IP as requested on url param
    # I dont know if it does not break pydev internals at some point
    if (ip is not None) and hasattr(pydevd, 'oldxxxip') and pydevd.oldxxxip != ip:
        pydevd.connected = False


    pydevd.settrace(i,
                    stdoutToServer=stdout,
                    stderrToServer=stderr,
                    port=p,
                    suspend=suspend)

    pydevd.oldxxxip = ip

    if CFG_PYDEV_DEBUG:
        sys.stderr.write("These are the mapping paths\n")
        sys.stderr.write(str(_pydev_paths) + "\n")


