"""
Test the suitability of Python core and the availability of various
Python modules for running CDSware.  Warn the user if there are
eventual troubles.  Exit status: 0 if okay, 1 if not okay.  Useful for
running from configure.ac.
"""

## $Id$
## Tests availability of Python modules and their versions.

## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002 CERN.
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

__version__ = "$Id$"

## minimally recommended/required versions:
cfg_min_python_version = "2.3"
cfg_min_mysqldb_version = "0.9.2"
cfg_min_numeric_version = "21.0"

## 0) import modules needed for this testing:
import string
import sys
import getpass

## 1) check Python version:
if sys.version < cfg_min_python_version:
    print """
    *******************************************************
    ** WARNING: OLD PYTHON DETECTED: %s 
    *******************************************************
    ** You seem to be using an old version of Python.    **
    **                                                   **
    ** Note that if you have more than one Python        **
    ** installed on your system, you can specify the     **
    ** --with-python configuration option to choose      **
    ** a specific (e.g. non system wide) Python binary.  **
    **                                                   **
    ** We strongly recommend you to run CDSware with     **
    ** at least Python %s.  Some older versions    ** 
    ** were known to be problematic with respect to      **
    ** encodings and mod_python, see for example         **
    ** <http://www.modpython.org/pipermail/mod_python/2002-October/002607.html>.
    **                                                   **
    ** Note that some operating systems (such as Debian) **
    ** may backport important bugfixes to older Python   **
    ** releases, so your concrete Python installation    **
    ** may be immune to these problems already.          **  
    ** If you are not sure, you may continue the CDSware **
    ** installation now and recall that in case of       **
    ** problems you may need to upgrade Python and       **
    ** reinstall CDSware from scratch.                   **
    *******************************************************
    """ % (string.replace(sys.version, "\n", ""), cfg_min_python_version) 
    getpass.getpass("Press ENTER to continue the installation anyhow...")

## 2) check for required modules:
try:
    import MySQLdb
    import Numeric
    import base64
    import cPickle
    import cStringIO
    import cgi
    import copy
    import fileinput
    import getopt
    import marshal
    import md5
    import os
    import signal
    import sre
    import string
    import tempfile
    import time
    import traceback
    import unicodedata
    import urllib
    import zlib
except ImportError, e:
    print """
    *************************************************
    ** ERROR: PYTHON IMPORT FAILURE %s
    *************************************************
    ** Perhaps you forgot to install some of the   **
    ** prerequisite Python modules?  Please look   **
    ** at our INSTALL file for more details and    **
    ** fix the problem before continuing!          **
    *************************************************
    """ % e
    sys.exit(1)

## 3) check for recommended modules:
try:
    import psyco
except ImportError, e:
    print """
    *****************************************************
    ** WARNING: PYTHON IMPORT WARNING %s
    *****************************************************
    ** Note that this module is not required but we    **
    ** recommend it for faster CDSware operation.      **
    ** You can safely continue installing CDSware now, **
    ** and add the recommended Python module anytime   **
    ** later. (for example, even after your CDSware    **
    ** installation is put into full production)       **
    *****************************************************
    """ % e
    getpass.getpass("Press ENTER to continue the installation...")

## 4) check for versions of some important modules:
if MySQLdb.__version__ < cfg_min_mysqldb_version:
    print """
    *****************************************************
    ** WARNING: PYTHON MODULE MYSQLDB %s DETECTED
    *****************************************************
    ** We strongly recommend you to upgrade `MySQLdb'  **
    ** to at least version %s.  See the INSTALL     **
    ** file for more details.                          **
    *****************************************************
    """ % (MySQLdb.__version__, cfg_min_mysqldb_version)
    getpass.getpass("Press ENTER to continue the installation anyhow...")

if Numeric.__version__ < cfg_min_numeric_version:
    print """
    *****************************************************
    ** WARNING: PYTHON MODULE NUMERIC %s DETECTED
    *****************************************************
    ** We strongly recommend you to upgrade `Numeric'  **
    ** to at least version %s.  See the INSTALL      **
    ** file for more details.                          **
    *****************************************************
    """ % (Numeric.__version__, cfg_min_numeric_version)
    getpass.getpass("Press ENTER to continue the installation anyhow...")
