## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 CERN.
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
Test importing the Invenio module.  The program expects the prefix
directory to be passed as an argument.  Warn the user to create
symlink(s) in case of troubles during import.  Exit status: 0 if
okay, 1 if not okay.  Useful for running during make install.
"""

__revision__ = "$Id$"

import os
import sys

def deduce_site_packages_locations():
    """Return a list of locations of Python site-packages directories
       deduced from the sys variable.  Otherwise return example
       directory.  Suitable to advise people how to create Python
       invenio module symlink."""
    out = []
    for path in sys.path:
        if path.endswith("site-packages"):
            out.append(path)
        if path.endswith("dist-packages"):
            out.append(path)
    if out:
        return out
    else:
        # nothing detected, return example directory
        return ["/usr/lib/python2.3/site-packages",]

try:
    PREFIX = sys.argv[1]
except IndexError:
    print "Error: no argument passed."
    print "Usage: %s <prefix>" % sys.argv[0]
    sys.exit(1)

## Firstly, check importing invenio:
try:
    import invenio
    DUMMY = invenio # to make checkers happy
except ImportError, e:
    print """
    ******************************************************
    ** IMPORT ERROR: %s
    ******************************************************
    ** Perhaps you need to create symbolic link(s)      **
    ** from your system-wide Python site-packages       **
    ** directory(ies) to your Invenio installation  **
    ** directory?                                       **
    **                                                  **
    ** If yes, then please create symlink(s) via:       **
    **""" % e
    for adir in deduce_site_packages_locations():
        print """\
    **    $ sudo ln -s %s/lib/python/invenio %s/invenio""" % (PREFIX, adir)
    print """\
    **
    ** and continue with the 'make install' afterward.  **
    **                                                  **
    ** If not, then please inspect the above error      **
    ** message and fix the problem before continuing.   **
    ******************************************************
    """
    sys.exit(1)

## Secondly, check nested symlink problem that people sometimes do on
## some OS-es when they overdo the symbolic linking:
if os.path.exists(PREFIX + '/lib/python/invenio/invenio'):
    print """
    ******************************************************
    ** NESTED SYMLINK PROBLEM?
    ******************************************************
    ** It seems that the following object exists:       **
    **   %s    **
    ** Perhaps you have made some nested symlinks in    **
    ** the previous installation step?  Please check    **
    ** and delete the above object.                     **
    ******************************************************
    """ % (PREFIX + '/lib/python/invenio/invenio')
    sys.exit(1)

