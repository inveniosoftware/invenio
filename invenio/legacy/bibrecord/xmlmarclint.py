# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2013, 2014 CERN.
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

"""
XML MARC lint - check your XML MARC files.
"""

from __future__ import print_function

import getopt
import string

from invenio.legacy.bibrecord import (
    create_records,
    print_recs
)


def main():
    """Execute script."""
    import sys

    cmdusage = """Usage: %s [options] <marcxmlfile>
    General options:
      -h, --help            Print this help.
      -v, --verbose=LEVEL   Verbose level (from 0 to 9, default 0).
    Description: checks the validity of MARCXML file.
    """ % (sys.argv[0])

    verbose = 0
    badrecords = []
    listofrecs = []

    try:
        opts, args = getopt.getopt(
            sys.argv[1:], "hv:", ["help", "verbose="])
    except getopt.GetoptError:
        print(cmdusage)
        sys.exit(2)

    for opt in opts:
        if opt[0] in ("-h", "--help"):
            sys.stderr.write(cmdusage)
            sys.exit(0)
        elif opt[0] in ("-v", "--verbose"):
            try:
                verbose = string.atoi(opt[1])
            except ValueError:
                print("[ERROR] verbose must be an integer.")
                sys.exit(2)

    try:
        xmlfile = args[0]
    except IndexError:
        sys.stderr.write(cmdusage)
        sys.exit(0)

    try:
        xmltext = open(xmlfile, 'r').read()
    except IOError:
        print("[ERROR] File %s not found." % xmlfile)
        import sys
        sys.exit(1)

    listofrecs = create_records(xmltext, 0, 1)
    badr = filter((lambda x: x[1] == 0), listofrecs)
    badrecords = map((lambda x: x[0]), badr)

    s = ''
    errors = []

    if xmltext and not listofrecs:
        print("[ERROR] No valid record detected.")
        sys.exit(1)

    if verbose:
        if verbose <= 3:
            errors.extend(map((lambda x: x[2]), listofrecs))
        else:
            s = print_recs(badrecords)
            errors.extend(map((lambda x: x[2]), listofrecs))
    else:
        if badrecords:
            print(
                "[ERROR] Bad records detected.  For more information, increase verbosity.")
            print("\n[INFO] You may also want to run `xmllint %s' to help "
                  "localise errors in the input file." % xmlfile)
            sys.exit(1)

    errors = [error for error in errors if error]

    if s or errors:
        if s:
            print(s)
        for error in errors:
            print("[ERROR]", error)
        print("[INFO] You may also want to run `xmllint %s' to help "
              "localise errors in the input file." % xmlfile)
        sys.exit(1)
