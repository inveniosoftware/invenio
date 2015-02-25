# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2013 CERN.
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

# global switch - if 0, remote_debugger is not loaded at all and
# no remote debugging is available, if you run the debugger for the Invenio
# site, make sure also your config contains the same directive

# Remote debugging is enabled via CFG_DEVEL_TOOLS (note, invenio.wsgi will not
# import the remote debugger if not set).
CFG_REMOTE_DEBUGGER_ENABLED = 0  # by default, we don't want to enable debugger

CFG_REMOTE_DEBUGGER_TYPE = ''
CFG_REMOTE_DEBUGGER_NAME = ''

try:
    from invenio.config import CFG_DEVEL_TOOLS
    if 'winpdb-local' in CFG_DEVEL_TOOLS:
        CFG_REMOTE_DEBUGGER_TYPE = 'winpdb'
        CFG_REMOTE_DEBUGGER_NAME = 'winpdb-local'
        CFG_REMOTE_DEBUGGER_ENABLED = 1
    elif 'winpdb-remote' in CFG_DEVEL_TOOLS:
        CFG_REMOTE_DEBUGGER_TYPE = 'winpdb'
        CFG_REMOTE_DEBUGGER_NAME = 'winpdb-remote'
        CFG_REMOTE_DEBUGGER_ENABLED = 1
    elif 'pydev' in CFG_DEVEL_TOOLS:
        CFG_REMOTE_DEBUGGER_TYPE = 'pydev'
        CFG_REMOTE_DEBUGGER_NAME = 'pydev'
        CFG_REMOTE_DEBUGGER_ENABLED = 1
except ImportError:
    pass

# Start debugger on WSGI application loading (i.e loading of invenio.wsgi).
# Default is only to start debugger on per request basis and not on application
# loading.
try:
    from invenio.config import CFG_REMOTE_DEBUGGER_WSGI_LOADING
except ImportError:
    CFG_REMOTE_DEBUGGER_WSGI_LOADING = False


# Modules that should be imported during initialization
# the structure is: 'debugger name': { 'module_path' : 'name', ... }, ...
#
# So, 'pydev.pydevd': 'pydev' means: "import pydev.pydevd as pydev"
# WARNING! The name of the module is quite important, as the functions
# are calling them without checking if they were imported or not. That is
# not a bug, that is a feature! You shall know what you are doing when
# changing default names.
#
# You can uncomment some lines if you know you are not going to use these
# modules for debugging.

CFG_REMOTE_DEBUGGER_IMPORT = {
    '': {},  # no debugger specified
    'winpdb': {
        'rpdb2': 'rpdb2',  # windpb debugging
    },
    'pydev': {
        'pydev.pydevd': 'pydevd',  # eclipse/pydev
        'pydev.pydevd_file_utils': 'putils',  # eclipse/pydev
    },
}

# -----------------------------------------------------------------------------
# configuration options for winpdb debugging
try:
    from invenio.config import CFG_REMOTE_DEBUGGER_WINPDB_PASSWORD
except ImportError:
    CFG_REMOTE_DEBUGGER_WINPDB_PASSWORD = 'Change1Me'


# -----------------------------------------------------------------------------
# configuration options for Eclipse/Pydev

# Remote debugging with Eclipse Pydev - Apache does not need to be configured
# as a single-worker. But you do the following:
#
# 1. find pydevd.py inside your Eclipse/Pydev installation
#    (on my computer it is in: c:\dev\eclipse342\plugins\org.python.pydev.debug_1.5.0.1251989166\pysrc)
# 2. copy the pysrc folder into the remote machine (eg. inside: /usr/lib/python2.5/site-packages
# 3. rename the pysrc into pydev
# 4. put __init__.py inside pydev (if you don't do that, pydev is not recognized as a package)
#
# Then, in your Eclipse, change perspective to the debug mode, start Pydev remote
# debug server, set some breakpoint and reload a webpage with url param debug=3
# eg. http://invenio-vm/?debug=3
#
# I repeat, you must be in the Debug perspective to catch the breakpoints!
#
# This is where your (local) Eclipse is listening for communication, this IP address
# can be anything that Invenio can access (ie. the machine that is running Invenio
# must have access to the IP)

CFG_REMOTE_DEBUGGER_PYDEV_REMOTE_IP = '127.0.0.1'  #'192.168.0.1'
CFG_REMOTE_DEBUGGER_PYDEV_REMOTE_PORT = 5678


# When you hit a breakpoing, Eclipse needs to know which file to display. For instance:
# you are developing inside a virtual machine (Linux) where Invenio code lives at
# /opt/cds-invenio/lib/python/invenio. Your environment is Windows (yes, why not? ;-))
# and you have access to the invenio folder through samba as:
#
# \\invenio-vm\root\opt\cds-invenio\lib\python\invenio
#
# (or perhaps you don't have samba but you have a local copy of the codebase somewhere else)
#
# You must set a mapping: local Eclipse path <--> remote Linux path
# in this way:
#
# CFG_REMOTE_DEBUGGER_PYDEV_PATHS = [('\\\\invenio-vm\\root\\opt\\cds-invenio\\lib\\python\\invenio',
#                                     '/opt/cds-invenio/lib/python/invenio')]
#
# what I (rca) do is to map a whole drive through samba:
# CFG_REMOTE_DEBUGGER_PYDEV_PATHS = [('\\\\invenio-vm\\root\\',
#                                     '/')]
# and I also recommend using (back)slashes at the end, ie. /opt/ and not /opt

CFG_REMOTE_DEBUGGER_PYDEV_PATHS = [
    #('/opt/cds-invenio/lib/python/invenio/', '/usr/local/lib/python2.5/site-packages/invenio/'),
    #('U:\\opt\\', '/opt/'),
    #('\\\\Invenio-ubu\\root\\', '/'),
    #('U:\\usr\\', '/usr/'),

    #('\\\\invenio-ubu\\root\\usr\\', '/usr/'),
    #('\\\\invenio-ubu\\root\\opt\\', '/opt/')
    ]

# Shall we monitor changes and restart daemon threads when you change source code?
# Put here list of glob patters (files) to monitor. The paths are relative to the
# Invenio root dir.
CFG_REMOTE_DEBUGGER_WSGI_RELOAD = ['lib/python/invenio/*.py']


# For debugging of a debugger ;)

CFG_PYDEV_DEBUG = False
