## -*- coding: utf-8 -*-
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
BibEdit Cache tool

Usage: bibeditcache record_id user_id [options]

A tool reading bibedit cache files and displaying their content

Options:
  --list-undo-handlers         Prints all the undo handlers stored in the cache file
  --list-redo-handlers         Prints all the undo handlers stored in the cache file
"""

import sys
from invenio.bibedit_utils import get_cache_file_contents
from pprint import pprint

def usage():
    """ Print the usafe information"""
    print __doc__

def print_ur_list(ur_list):
    """Prints nicely formated undo/redo list"""
    pprint(ur_list, indent=0, width=50)

def main():
    """ The main function providing the functionalityu of the BibEdit cache tool
    """
    if len(sys.argv) < 3:
        usage()
        exit(1)

    recid = sys.argv[1]
    uid = sys.argv[2]
    cache_content = get_cache_file_contents(recid, uid)

    if len(sys.argv) == 3:
        print str(cache_content)

    if '--list-undo-handlers' in sys.argv:
        print "Undo handlers:"
        print_ur_list(cache_content[5])

    if '--list-redo-handlers' in sys.argv:
        print "Undo handlers:"
        print_ur_list(cache_content[6])
