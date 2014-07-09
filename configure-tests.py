## This file is part of Invenio.
## Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013 CERN.
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

from __future__ import print_function

"""
Test the suitability of Python core and the availability of various
Python modules for running Invenio.  Warn the user if there are
eventual troubles.  Exit status: 0 if okay, 1 if not okay.  Useful for
running from configure.ac.
"""

## minimally recommended/required versions:
CFG_MIN_PYTHON_VERSION = (2, 6)
CFG_MAX_PYTHON_VERSION = (2, 9, 9999)
CFG_MIN_MYSQLDB_VERSION = "1.2.1_p2"

## 0) import modules needed for this testing:
import string
import sys
import getpass
import subprocess
import re

error_messages = []
warning_messages = []

def wait_for_user(msg):
    """Print MSG and prompt user for confirmation."""
    try:
        raw_input(msg)
    except KeyboardInterrupt:
        print("\n\nInstallation aborted.")
        sys.exit(1)
    except EOFError:
        print(" (continuing in batch mode)")
        return

## 1) check Python version:
if sys.version_info < CFG_MIN_PYTHON_VERSION:
    error_messages.append(
    """
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
    """ % (string.replace(sys.version, "\n", ""),
           '.'.join(CFG_MIN_PYTHON_VERSION))
    )

if sys.version_info > CFG_MAX_PYTHON_VERSION:
    error_messages.append(
    """
    *******************************************************
    ** ERROR: TOO NEW PYTHON DETECTED: %s
    *******************************************************
    ** You seem to be using a too new version of Python. **
    ** You must use at most Python %s.             **
    **                                                   **
    ** Perhaps you have downloaded and are installing an **
    ** old Invenio version?  Please look for more recent **
    ** Invenio version or please contact the development **
    ** team at <info@invenio-software.org> about this    **
    ** problem.                                          **
    **                                                   **
    ** Installation aborted.                             **
    *******************************************************
    """ % (string.replace(sys.version, "\n", ""),
           '.'.join(CFG_MAX_PYTHON_VERSION))
    )

## 2) check for required modules:
try:
    import MySQLdb
    import base64
    from six.moves import cPickle
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
    import pyparsing
    import signal
    import tempfile
    import time
    import traceback
    import unicodedata
    import urllib
    import zlib
    import wsgiref
    import sqlalchemy
    import werkzeug
    import jinja2
    import flask
    import fixture
    import flask.ext.assets
    import flask.ext.cache
    import flask.ext.sqlalchemy
    import flask.ext.testing
    import wtforms
    import flask.ext.wtf
    import flask.ext.admin

    ## Check Werkzeug version
    werkzeug_ver = werkzeug.__version__.split(".")
    if werkzeug_ver[0] == "0" and int(werkzeug_ver[1]) < 8:
        error_messages.append(
    """
    *****************************************************
    ** Werkzeug version %s detected
    *****************************************************
    ** Your are using an outdated version of Werkzeug  **
    ** with known problems. Please upgrade Werkzeug to **
    ** at least v0.8 by running e.g.:                  **
    **   pip install Werkzeug --upgrade                **
    *****************************************************
    """ % werkzeug.__version__
        )
except ImportError as msg:
    error_messages.append("""
    *************************************************
    ** IMPORT ERROR %s
    *************************************************
    ** Perhaps you forgot to install some of the   **
    ** prerequisite Python modules?  Please look   **
    ** at our INSTALL file for more details and    **
    ** fix the problem before continuing!          **
    *************************************************
    """ % msg
    )


## 3) check for recommended modules:
try:
    import rdflib
except ImportError as msg:
    warning_messages.append(
    """
    *****************************************************
    ** IMPORT WARNING %s
    *****************************************************
    ** Note that rdflib is needed only if you plan     **
    ** to work with the automatic classification of    **
    ** documents based on RDF-based taxonomies.        **
    **                                                 **
    ** You can safely continue installing Invenio      **
    ** now, and add this module anytime later.  (I.e.  **
    ** even after your Invenio installation is put     **
    ** into production.)                               **
    *****************************************************
    """ % msg
    )

try:
    import pyRXP
except ImportError as msg:
    warning_messages.append("""
    *****************************************************
    ** IMPORT WARNING %s
    *****************************************************
    ** Note that PyRXP is not really required but      **
    ** we recommend it for fast XML MARC parsing.      **
    **                                                 **
    ** You can safely continue installing Invenio      **
    ** now, and add this module anytime later.  (I.e.  **
    ** even after your Invenio installation is put     **
    ** into production.)                               **
    *****************************************************
    """ % msg
    )

try:
    import dateutil
except ImportError as msg:
    warning_messages.append("""
    *****************************************************
    ** IMPORT WARNING %s
    *****************************************************
    ** Note that dateutil is not really required but   **
    ** we recommend it for user-friendly date          **
    ** parsing.                                        **
    **                                                 **
    ** You can safely continue installing Invenio      **
    ** now, and add this module anytime later.  (I.e.  **
    ** even after your Invenio installation is put     **
    ** into production.)                               **
    *****************************************************
    """ % msg
    )

try:
    import libxml2
except ImportError as msg:
    warning_messages.append("""
    *****************************************************
    ** IMPORT WARNING %s
    *****************************************************
    ** Note that libxml2 is not really required but    **
    ** we recommend it for XML metadata conversions    **
    ** and for fast XML parsing.                       **
    **                                                 **
    ** You can safely continue installing Invenio      **
    ** now, and add this module anytime later.  (I.e.  **
    ** even after your Invenio installation is put     **
    ** into production.)                               **
    *****************************************************
    """ % msg
    )

try:
    import libxslt
except ImportError as msg:
    warning_messages.append(
    """
    *****************************************************
    ** IMPORT WARNING %s
    *****************************************************
    ** Note that libxslt is not really required but    **
    ** we recommend it for XML metadata conversions.   **
    **                                                 **
    ** You can safely continue installing Invenio      **
    ** now, and add this module anytime later.  (I.e.  **
    ** even after your Invenio installation is put     **
    ** into production.)                               **
    *****************************************************
    """ % msg
    )

try:
    import Gnuplot
except ImportError as msg:
    warning_messages.append(
    """
    *****************************************************
    ** IMPORT WARNING %s
    *****************************************************
    ** Note that Gnuplot.py is not really required but **
    ** we recommend it in order to have nice download  **
    ** and citation history graphs on Detailed record  **
    ** pages.                                          **
    **                                                 **
    ** You can safely continue installing Invenio      **
    ** now, and add this module anytime later.  (I.e.  **
    ** even after your Invenio installation is put     **
    ** into production.)                               **
    *****************************************************
    """ % msg
    )

try:
    import rauth
except ImportError as msg:
    warning_messages.append(
    """
    *****************************************************
    ** IMPORT WARNING %s
    *****************************************************
    ** Note that python-rauth is not really required   **
    ** but we recommend it in order to enable oauth    **
    ** based authentication.                           **
    **                                                 **
    ** You can safely continue installing Invenio      **
    ** now, and add this module anytime later.  (I.e.  **
    ** even after your Invenio installation is put     **
    ** into production.)                               **
    *****************************************************
    """ % msg
    )

try:
    import openid
except ImportError as msg:
    warning_messages.append(
    """
    *****************************************************
    ** IMPORT WARNING %s
    *****************************************************
    ** Note that python-openid is not really required  **
    ** but we recommend it in order to enable OpenID   **
    ** based authentication.                           **
    **                                                 **
    ** You can safely continue installing Invenio      **
    ** now, and add this module anytime later.  (I.e.  **
    ** even after your Invenio installation is put     **
    ** into production.)                               **
    *****************************************************
    """ % msg
    )

try:
    import magic
    if not hasattr(magic, "open"):
        raise StandardError
except ImportError as msg:
    warning_messages.append(
    """
    *****************************************************
    ** IMPORT WARNING %s
    *****************************************************
    ** Note that magic module is not really required   **
    ** but we recommend it in order to have detailed   **
    ** content information about fulltext files.       **
    **                                                 **
    ** You can safely continue installing Invenio      **
    ** now, and add this module anytime later.  (I.e.  **
    ** even after your Invenio installation is put     **
    ** into production.)                               **
    *****************************************************
    """ % msg
    )
except StandardError:
    warning_messages.append(
    """
    *****************************************************
    ** IMPORT WARNING python-magic
    *****************************************************
    ** The python-magic package you installed is not   **
    ** the one supported by Invenio. Please refer to   **
    ** the INSTALL file for more details.              **
    **                                                 **
    ** You can safely continue installing Invenio      **
    ** now, and add this module anytime later.  (I.e.  **
    ** even after your Invenio installation is put     **
    ** into production.)                               **
    *****************************************************
    """
    )

try:
    import reportlab
except ImportError as msg:
    warning_messages.append(
    """
    *****************************************************
    ** IMPORT WARNING %s
    *****************************************************
    ** Note that reportlab module is not really        **
    ** required, but we recommend it you want to       **
    ** enrich PDF with OCR information.                **
    **                                                 **
    ** You can safely continue installing Invenio      **
    ** now, and add this module anytime later.  (I.e.  **
    ** even after your Invenio installation is put     **
    ** into production.)                               **
    *****************************************************
    """ % msg
    )

try:
    try:
        import PyPDF2
    except ImportError:
        import pyPdf
except ImportError as msg:
    warning_messages.append(
    """
    *****************************************************
    ** IMPORT WARNING %s
    *****************************************************
    ** Note that pyPdf or pyPdf2 module is not really  **
    ** required, but we recommend it you want to       **
    ** enrich PDF with OCR information.                **
    **                                                 **
    ** You can safely continue installing Invenio      **
    ** now, and add this module anytime later.  (I.e.  **
    ** even after your Invenio installation is put     **
    ** into production.)                               **
    *****************************************************
    """ % msg
    )

try:
    import unidecode
except ImportError, msg:
    warning_messages.append(
    """
    *****************************************************
    ** IMPORT WARNING %s
    *****************************************************
    ** Note that unidecode module is not really        **
    ** required, but we recommend it you want to       **
    ** introduce smarter author names matching.        **
    **                                                 **
    ** You can safely continue installing Invenio      **
    ** now, and add this module anytime later.  (I.e.  **
    ** even after your Invenio installation is put     **
    ** into production.)                               **
    *****************************************************
    """ % msg
    )

## 4) check for versions of some important modules:
if MySQLdb.__version__ < CFG_MIN_MYSQLDB_VERSION:
    error_messages.append(
    """
    *****************************************************
    ** ERROR: PYTHON MODULE MYSQLDB %s DETECTED
    *****************************************************
    ** You have to upgrade your MySQLdb to at least    **
    ** version %s.  You must fix this problem    **
    ** before continuing.  Please see the INSTALL file **
    ** for more details.                               **
    *****************************************************
    """ % (MySQLdb.__version__, CFG_MIN_MYSQLDB_VERSION)
    )

try:
    import Stemmer
    try:
        from Stemmer import algorithms
    except ImportError as msg:
        error_messages.append(
        """
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
        )
except ImportError:
    pass # no prob, Stemmer is optional

## 5) check for Python.h (needed for intbitset):
try:
    from distutils.sysconfig import get_python_inc
    path_to_python_h = get_python_inc() + os.sep + 'Python.h'
    if not os.path.exists(path_to_python_h):
        raise StandardError, "Cannot find %s" % path_to_python_h
except StandardError as msg:
    error_messages.append(
    """
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
    )

## 6) Check if ffmpeg is installed and if so, with the minimum configuration for bibencode
try:
    try:
        process = subprocess.Popen('ffprobe', stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    except OSError:
        raise StandardError, "FFMPEG/FFPROBE does not seem to be installed!"
    returncode = process.wait()
    output = process.communicate()[1]
    RE_CONFIGURATION = re.compile("(--enable-[a-z0-9\-]*)")
    CONFIGURATION_REQUIRED = (
                '--enable-gpl',
                '--enable-version3',
                '--enable-nonfree',
                '--enable-libtheora',
                '--enable-libvorbis',
                '--enable-libvpx',
                '--enable-libopenjpeg'
                )
    options = RE_CONFIGURATION.findall(output)
    if sys.version_info < (2, 6):
        import sets
        s = sets.Set(CONFIGURATION_REQUIRED)
        if not s.issubset(options):
            raise StandardError, options.difference(s)
    else:
        if not set(CONFIGURATION_REQUIRED).issubset(options):
            raise StandardError, set(CONFIGURATION_REQUIRED).difference(options)
except StandardError as msg:
    warning_messages.append(
    """
    *****************************************************
    ** WARNING: FFMPEG CONFIGURATION MISSING %s
    *****************************************************
    ** You do not seem to have FFmpeg configured with  **
    ** the minimum video codecs to run the demo site.  **
    ** Please install the necessary libraries and      **
    ** re-install FFmpeg according to the Invenio      **
    ** installation manual (INSTALL).                  **
    *****************************************************
    """ % (msg)
    )

if warning_messages:
    print("""
    ******************************************************
    ** WARNING MESSAGES                                 **
    ******************************************************
    """)
    for warning in warning_messages:
        print(warning)

if error_messages:
    print("""
    ******************************************************
    ** ERROR MESSAGES                                   **
    ******************************************************
    """)
    for error in error_messages:
        print(error)

if warning_messages and error_messages:
    print("""
    There were %(n_err)s error(s) found that you need to solve.
    Please see above, solve them, and re-run configure.
    Note that there are also %(n_wrn)s warnings you may want
    to look into.  Aborting the installation.
    """ % {'n_wrn': len(warning_messages),
           'n_err': len(error_messages)})

    sys.exit(1)
elif error_messages:
    print("""
    There were %(n_err)s error(s) found that you need to solve.
    Please see above, solve them, and re-run configure.
    Aborting the installation.
    """ % {'n_err': len(error_messages)})

    sys.exit(1)
elif warning_messages:
    print("""
    There were %(n_wrn)s warnings found that you may want to
    look into, solve, and re-run configure before you
    continue the installation.  However, you can also continue
    the installation now and solve these issues later, if you wish.
    """ % {'n_wrn': len(warning_messages)})
