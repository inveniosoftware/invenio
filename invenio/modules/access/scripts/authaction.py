#!@PYTHON@
# -*- mode: python; coding: utf-8; -*-
#
# This file is part of Invenio.
# Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2010, 2011 CERN.
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

"""authaction -- CLI interface to Access Control Engine"""

__revision__ = "$Id$"

import sys

from invenio.base.helpers import with_app_context


def usage(code, msg=''):
    """Print usage info."""
    if msg:
        sys.stderr.write("Error: %s.\n" % msg)
    sys.stderr.write("authaction -- CLI interface to Access Control Engine\n")
    sys.stderr.write("Usage: %s [options] <id_user> <name_action> [keyword1] [value1] [keyword2] [value2] ...\n" % sys.argv[0])
    sys.stderr.write("Command options:\n")
    sys.stderr.write("  <id_user> = ID of the user\n")
    sys.stderr.write("  <name_action> = action name\n")
    sys.stderr.write("  [keyword1] = optional first keyword argument\n")
    sys.stderr.write("  [value1] = its value\n")
    sys.stderr.write("  [keyword2] = optional second keyword argument\n")
    sys.stderr.write("  [value2] = its value\n")
    sys.stderr.write("  ... = et caetera\n")
    sys.stderr.write("General options:\n")
    sys.stderr.write("  -h, --help      \t\t Print this help.\n")
    sys.stderr.write("  -V, --version   \t\t Print version information.\n")
    sys.exit(code)


@with_app_context()
def main():
    """CLI to acc_authorize_action. The function finds the needed
    arguments in sys.argv.
    If the number of arguments is wrong it prints help.
    Return 0 on success, 9 or higher on failure. """

    from invenio.modules.access.engine import acc_authorize_action
    from invenio.modules.access.local_config import CFG_WEBACCESS_WARNING_MSGS

    alen, auth = len(sys.argv), 0

    # return ``not permitted'' if wrong arguments
    if alen > 1 and sys.argv[1] in ["-h", "--help"]:
        usage(0)
    elif alen > 1 and sys.argv[1] in ["-V", "--version"]:
        sys.stderr.write("%s\n" % __revision__)
        sys.exit(0)
    if alen < 3 or alen % 2 == 0:
        print("7 - %s" % CFG_WEBACCESS_WARNING_MSGS[7])
        return "7 - %s" % CFG_WEBACCESS_WARNING_MSGS[7]

    # try to authorize
    else:
        # get values
        id_user = int(sys.argv[1])
        name_action = sys.argv[2]

        kwargs = {}
        for i in range(3, alen, 2):
            kwargs[sys.argv[i]] = sys.argv[i + 1]

        # run ace-function
        (auth_code, auth_message) = acc_authorize_action(id_user, name_action,
                                                         **kwargs)

    # print and return
    print("%s - %s" % (auth_code, auth_message))
    return "%s - %s" % (auth_code, auth_message)
