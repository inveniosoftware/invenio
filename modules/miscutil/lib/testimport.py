## $Id$
##
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
Test importing the CDS Invenio module.  The program expects the prefix
directory to be passed as an argument.  Warn the user to create a
symlink in case of troubles during import.  Exit status: 0 if
okay, 1 if not okay.  Useful for running during make install.
"""

__revision__ = "$Id$"

import sys

def deduce_site_packages_location():
    """Return the most probable location of site-packages directory
       deduced from the sys variable.  Otherwise return example
       directory.  Suitable to advise people how to create Python
       invenio module symlink."""
    out = "/usr/lib/python2.3/site-packages" # example directory
    for path in sys.path:
        if path.endswith("site-package"):
            out = path # put proper directory instead of the example one
            break
    return out

try:
    PREFIX = sys.argv[1]
except IndexError:
    print "Error: no argument passed."
    print "Usage: %s <prefix>" % sys.argv[0]
    sys.exit(1)
    
try:
    import invenio
    DUMMY = invenio # to make checkers happy
except ImportError, e:
    print """
    ******************************************************
    ** IMPORT ERROR: %s
    ******************************************************
    ** Perhaps you need to create a symbolic link       **
    ** from your system-wide Python module directory    **
    ** to your CDS Invenio installation directory?      **
    **                                                  **
    ** If yes, then please create it via:               **
    **                                                  
    **    $ sudo ln -s %s/lib/python/invenio %s/invenio
    **                                                  
    ** and continue with the 'make install' afterwards. **
    **                                                  **
    ** If not, then please inspect the above error      **
    ** message and fix the problem before continuing.   **
    ******************************************************
    """ % (e,
           PREFIX,
           deduce_site_packages_location())
    sys.exit(1)
