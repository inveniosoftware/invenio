#!@PYTHON@
# -*- mode: python; coding: utf-8; -*-
#
# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011 CERN.
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

from __future__ import print_function

import sys
import getopt

from invenio.base.factory import with_app_context


def usage(exitcode=1, msg=""):
    """Prints usage info."""
    if msg:
        sys.stderr.write("Error: %s.\n" % msg)
    sys.stderr.write("Usage: %s [options]\n" % sys.argv[0])
    sys.stderr.write("General options:\n")
    sys.stderr.write("  -h, --help      \t\t Print this help.\n")
    sys.stderr.write("  -V, --version   \t\t Print version information.\n")
    sys.stderr.write("""Description: read specially-formatted email message from stdin
and upload the records it contains to the system.\n""")
    sys.exit(exitcode)


@with_app_context()
def main():
    import invenio.legacy.elmsubmit.api as elmsubmit

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hV", ["help", "version"])
    except getopt.GetoptError as err:
        usage(1, err)
    try:
        for opt in opts:
            if opt[0] in ["-h", "--help"]:
                usage(0)
            elif opt[0] in ["-V", "--version"]:
                print(elmsubmit.__revision__)
                sys.exit(0)
    except StandardError as e:
        usage(e)
    return elmsubmit.process_email(sys.stdin.read())
