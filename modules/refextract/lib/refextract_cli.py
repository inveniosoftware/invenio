# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011 CERN.
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

"""Refextract command line interface.
   Handles dependability, and starting the refextract daemon
"""
import sys


def main():
    """Main function to interface with bibsched"""

    ## Cannot check for standalone args here, since this is being called
    ## with the task id of the process, when ran inside Bibsched

    ## Run as standalone, if the user is specifying directories
    ## to fulltext documents
    run_as_standalone = filter(lambda arg: \
                               arg in ('-f', '--fulltext'), sys.argv[1:])
    if run_as_standalone:
        try:
            from invenio.refextract import main as refextract_standalone
        except ImportError, err:
            sys.stderr.write("Error: %s\n" % err)
            sys.stderr.flush()
            sys.exit(1)
        ## Run refextract in the usual standalone fashion
        refextract_standalone()
    else:
        try:
            from invenio.refextract_daemon import refextract_daemon
        except ImportError, err:
            sys.stderr.write("Error: %s\n" % err)
            sys.stderr.flush()
            sys.exit(1)
        ## Start Refextract as a Bibsched compliant daemon
        refextract_daemon()
