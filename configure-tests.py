## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
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

## minimally recommended/required versions:
cfg_min_python_version = "2.4"
cfg_max_python_version = "2.9.9999"
cfg_min_mysqldb_version = "1.2.1_p2"

## 0) import modules needed for this testing:
import string
import sys
import getpass

def wait_for_user(msg):
    """Print MSG and prompt user for confirmation."""
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
    ** ERROR: TOO OLD PYTHON DETECTED: %s
    *******************************************************
    ** You seem to be using a too old version of Python. **
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
if sys.version > cfg_max_python_version:
    print """
    *******************************************************
    ** ERROR: TOO NEW PYTHON DETECTED: %s
    *******************************************************
    ** You seem to be using a too new version of Python. **
    ** You must use at most Python %s.             **
    **                                                   **
    ** Perhaps you have downloaded and are installing an **
    ** old Invenio version?  Please look for more recent **
    ** Invenio version or please contact the development **
    ** team at <cds.support@cern.ch> about this problem. **
    **                                                   **
    ** Installation aborted.                             **
    *******************************************************
    """ % (string.replace(sys.version, "\n", ""), cfg_max_python_version)
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
    import sys
    if sys.hexversion < 0x2060000:
        import md5
    else:
        import hashlib
    import marshal
    import os
    import signal
    import tempfile
    import time
    import traceback
    import unicodedata
    import urllib
    import zlib
    import wsgiref
except ImportError, msg:
    print """
    *************************************************
    ** IMPORT ERROR %s
    *************************************************
    ** Perhaps you forgot to install some of the   **
    ** prerequisite Python modules?  Please look   **
    ** at our INSTALL file for more details and    **
    ** fix the problem before continuing!          **
    *************************************************
    """ % msg
    sys.exit(1)

## 3) check for recommended modules:
try:
    if (2**31 - 1) == sys.maxint:
        # check for Psyco since we seem to run in 32-bit environment
        import psyco
    else:
        # no need to advise on Psyco on 64-bit systems
        pass
except ImportError, msg:
    print """
    *****************************************************
    ** IMPORT WARNING %s
    *****************************************************
    ** Note that Psyco is not really required but we   **
    ** recommend it for faster CDS Invenio operation   **
    ** if you are running in 32-bit operating system.  **
    **                                                 **
    ** You can safely continue installing CDS Invenio  **
    ** now, and add this module anytime later.  (I.e.  **
    ** even after your CDS Invenio installation is put **
    ** into production.)                               **
    *****************************************************
    """ % msg

    wait_for_user("Press ENTER to continue the installation...")

try:
    import rdflib
except ImportError, msg:
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
    """ % msg
    wait_for_user("Press ENTER to continue the installation...")

try:
    import pyRXP
except ImportError, msg:
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
    """ % msg
    wait_for_user("Press ENTER to continue the installation...")

try:
    import libxml2
except ImportError, msg:
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
    """ % msg
    wait_for_user("Press ENTER to continue the installation...")

try:
    import libxslt
except ImportError, msg:
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
    """ % msg
    wait_for_user("Press ENTER to continue the installation...")

try:
    import Gnuplot
except ImportError, msg:
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
    """ % msg
    wait_for_user("Press ENTER to continue the installation...")

try:
    import magic
    if not hasattr(magic, "open"):
        raise StandardError
except ImportError, msg:
    print """
    *****************************************************
    ** IMPORT WARNING %s
    *****************************************************
    ** Note that magic module is not really required   **
    ** but we recommend it in order to have detailed   **
    ** content information about fulltext files.       **
    **                                                 **
    ** You can safely continue installing CDS Invenio  **
    ** now, and add this module anytime later.  (I.e.  **
    ** even after your CDS Invenio installation is put **
    ** into production.)                               **
    *****************************************************
    """ % msg
except StandardError:
    print """
    *****************************************************
    ** IMPORT WARNING python-magic
    *****************************************************
    ** The python-magic package you installed is not   **
    ** the one supported by Invenio. Please refer to   **
    ** the INSTALL file for more details.              **
    **                                                 **
    ** You can safely continue installing CDS Invenio  **
    ** now, and add this module anytime later.  (I.e.  **
    ** even after your CDS Invenio installation is put **
    ** into production.)                               **
    *****************************************************
    """

try:
    import reportlab
except ImportError, msg:
    print """
    *****************************************************
    ** IMPORT WARNING %s
    *****************************************************
    ** Note that reportlab module is not really        **
    ** required, but we recommend it you want to       **
    ** enrich PDF with OCR information.                **
    **                                                 **
    ** You can safely continue installing CDS Invenio  **
    ** now, and add this module anytime later.  (I.e.  **
    ** even after your CDS Invenio installation is put **
    ** into production.)                               **
    *****************************************************
    """ % msg
    wait_for_user("Press ENTER to continue the installation...")

## 4) check for versions of some important modules:
if MySQLdb.__version__ < cfg_min_mysqldb_version:
    print """
    *****************************************************
    ** ERROR: PYTHON MODULE MYSQLDB %s DETECTED
    *****************************************************
    ** You have to upgrade your MySQLdb to at least    **
    ** version %s.  You must fix this problem    **
    ** before continuing.  Please see the INSTALL file **
    ** for more details.                               **
    *****************************************************
    """ % (MySQLdb.__version__, cfg_min_mysqldb_version)
    sys.exit(1)

try:
    import Stemmer
    try:
        from Stemmer import algorithms
    except ImportError, msg:
        print """
        *****************************************************
        ** ERROR: STEMMER MODULE PROBLEM %s
        *****************************************************
        ** Perhaps you are using an old Stemmer version?   **
        ** You must either remove your old Stemmer or else **
        ** upgrade to Snowball Stemmer
        **   <http://snowball.tartarus.org/wrappers/PyStemmer-1.0.1.tar.gz>
        ** before continuing.  Please see the INSTALL file **
        ** for more details.                               **
        *****************************************************
        """ % (msg)
        sys.exit(1)
except ImportError:
    pass # no prob, Stemmer is optional

## 5) check for Python.h (needed for intbitset):
try:
    from distutils.sysconfig import get_python_inc
    path_to_python_h = get_python_inc() + os.sep + 'Python.h'
    if not os.path.exists(path_to_python_h):
        raise StandardError, "Cannot find %s" % path_to_python_h
except StandardError, msg:
    print """
    *****************************************************
    ** ERROR: PYTHON HEADER FILE ERROR %s
    *****************************************************
    ** You do not seem to have Python developer files  **
    ** installed (such as Python.h).  Some operating   **
    ** systems provide these in a separate Python      **
    ** package called python-dev or python-devel.      **
    ** You must install such a package before          **
    ** continuing the installation process.            **
    *****************************************************
    """ % (msg)
    sys.exit(1)
