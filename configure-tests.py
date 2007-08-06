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

"""
Test the suitability of Python core and the availability of various
Python modules for running CDS Invenio.  Warn the user if there are
eventual troubles.  Exit status: 0 if okay, 1 if not okay.  Useful for
running from configure.ac.
"""

__revision__ = "$Id$"

## minimally recommended/required versions:
cfg_min_python_version = "2.3"
cfg_min_mysqldb_version = "0.9.2"

## 0) import modules needed for this testing:
import string
import sys
import getpass

def wait_for_user(msg):
    try:
        raw_input(msg)
    except KeyboardInterrupt:
        print "\n\nInstallation aborted."
        sys.exit(1)
    except EOFError:
        print " (continuing in batch mode)"
        return

## 1) check Python version:
if sys.version < cfg_min_python_version:
    print """
    *******************************************************
    ** ERROR: OLD PYTHON DETECTED: %s
    *******************************************************
    ** You seem to be using an old version of Python.    **
    ** You must use at least Python %s.                 **
    **                                                   **
    ** Note that if you have more than one Python        **
    ** installed on your system, you can specify the     **
    ** --with-python configuration option to choose      **
    ** a specific (e.g. non system wide) Python binary.  **
    **                                                   **
    ** Please upgrade your Python before continuing.     **
    *******************************************************
    """ % (string.replace(sys.version, "\n", ""), cfg_min_python_version)
    sys.exit(1)

## 2) check for required modules:
try:
    import MySQLdb
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
    ** IMPORT ERROR %s
    *************************************************
    ** Perhaps you forgot to install some of the   **
    ** prerequisite Python modules?  Please look   **
    ** at our INSTALL file for more details and    **
    ** fix the problem before continuing!          **
    *************************************************
    """ % e
    sys.exit(1)

try:
    import Cython
except ImportError, e1:
    try:
        import Pyrex
    except ImportError, e2:
        print """
        *************************************************
        ** IMPORT ERROR %s %s
        *************************************************
        ** As of CDS Invenio v0.93, the Pyrex and/or   **
        ** Cython module is required.  Please look     **
        ** at our INSTALL file for more details and    **
        ** fix the problem before continuing!          **
        *************************************************
        """ % (e1, e2)
        sys.exit(1)

## 3) check for recommended modules:
try:
    import psyco
except ImportError, e:
    print """
    *****************************************************
    ** IMPORT WARNING %s
    *****************************************************
    ** Note that Psyco is not really required but we   **
    ** recommend it for faster CDS Invenio operation.  **
    **                                                 **
    ** You can safely continue installing CDS Invenio  **
    ** now, and add this module anytime later.  (I.e.  **
    ** even after your CDS Invenio installation is put **
    ** into production.)                               **
    *****************************************************
    """ % e

    wait_for_user("Press ENTER to continue the installation...")

try:
    import rdflib
except ImportError, e:
    print """
    *****************************************************
    ** IMPORT WARNING %s
    *****************************************************
    ** Note that rdflib is needed only if you plan     **
    ** to work with the automatic classification of    **
    ** documents based on RDF-based taxonomies.        **
    **                                                 **
    ** You can safely continue installing CDS Invenio  **
    ** now, and add this module anytime later.  (I.e.  **
    ** even after your CDS Invenio installation is put **
    ** into production.)                               **
    *****************************************************
    """ % e
    wait_for_user("Press ENTER to continue the installation...")

try:
    import pyRXP
except ImportError, e:
    print """
    *****************************************************
    ** IMPORT WARNING %s
    *****************************************************
    ** Note that PyRXP is not really required but      **
    ** we recommend it for fast XML MARC parsing.      **
    **                                                 **
    ** You can safely continue installing CDS Invenio  **
    ** now, and add this module anytime later.  (I.e.  **
    ** even after your CDS Invenio installation is put **
    ** into production.)                               **
    *****************************************************
    """ % e
    wait_for_user("Press ENTER to continue the installation...")

try:
    import libxml2
except ImportError, e:
    print """
    *****************************************************
    ** IMPORT WARNING %s
    *****************************************************
    ** Note that libxml2 is not really required but    **
    ** we recommend it for XML metadata conversions    **
    ** and for fast XML parsing.                       **
    **                                                 **
    ** You can safely continue installing CDS Invenio  **
    ** now, and add this module anytime later.  (I.e.  **
    ** even after your CDS Invenio installation is put **
    ** into production.)                               **
    *****************************************************
    """ % e
    wait_for_user("Press ENTER to continue the installation...")

try:
    import libxslt
except ImportError, e:
    print """
    *****************************************************
    ** IMPORT WARNING %s
    *****************************************************
    ** Note that libxslt is not really required but    **
    ** we recommend it for XML metadata conversions.   **
    **                                                 **
    ** You can safely continue installing CDS Invenio  **
    ** now, and add this module anytime later.  (I.e.  **
    ** even after your CDS Invenio installation is put **
    ** into production.)                               **
    *****************************************************
    """ % e
    wait_for_user("Press ENTER to continue the installation...")

try:
    import Gnuplot
except ImportError, e:
    print """
    *****************************************************
    ** IMPORT WARNING %s
    *****************************************************
    ** Note that Gnuplot.py is not really required but **
    ** we recommend it in order to have nice download  **
    ** and citation history graphs on Detailed record  **
    ** pages.                                          **
    **                                                 **
    ** You can safely continue installing CDS Invenio  **
    ** now, and add this module anytime later.  (I.e.  **
    ** even after your CDS Invenio installation is put **
    ** into production.)                               **
    *****************************************************
    """ % e
    wait_for_user("Press ENTER to continue the installation...")

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

    wait_for_user("Press ENTER to continue the installation anyhow...")

