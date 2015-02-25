# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2005, 2006, 2007, 2008, 2010, 2011, 2013 CERN.
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

"""WebMessage Admin -- clean messages"""

__revision__ = "$Id$"

import getpass
import readline
import sys

from invenio.base.factory import with_app_context


def usage(code, msg=''):
    """Print usage info."""
    if msg:
        sys.stderr.write("Error: %s.\n" % msg)
    sys.stderr.write("WebMessage Admin -- cleans forgotten messages")
    sys.stderr.write("Usage: %s [options] <command>\n" % sys.argv[0])
    sys.stderr.write("Command options:\n")
    sys.stderr.write("  <command> = clean\n")
    sys.stderr.write("General options:\n")
    sys.stderr.write("  -h, --help      \t\t Print this help.\n")
    sys.stderr.write("  -V, --version   \t\t Print version information.\n")
    sys.exit(code)


@with_app_context()
def main():
    """CLI to clean_messages. The function finds the needed
    arguments in sys.argv.
    If the number of arguments is wrong it prints help.
    Return 1 on success, 0 on failure. """
    from invenio.config import CFG_SITE_SUPPORT_EMAIL
    from invenio.modules.messages.dblayer import clean_messages
    from invenio.legacy.dbquery import run_sql

    alen = len(sys.argv)
    action = ''

    # print help if wrong arguments
    if alen > 1 and sys.argv[1] in ["-h", "--help"]:
        usage(0)
    elif alen > 1 and sys.argv[1] in ["-V", "--version"]:
        print(__revision__)
        sys.exit(0)
    if alen != 2 or sys.argv[1] not in ['clean']:
        usage(1)

    # getting input from user
    print('User:    ', end=' ')
    user = raw_input()
    password = getpass.getpass()

    # validating input
    perform = 0

    # check password
    if user == CFG_SITE_SUPPORT_EMAIL:
        perform = run_sql("""select * from user where email = '%s' and password = '%s' """ % (CFG_SITE_SUPPORT_EMAIL, password)) and 1 or 0

    if not perform:
        # wrong password or user not recognized
        print('User not authorized')
        return perform

    # perform chosen action
    if sys.argv[1] == 'clean':
        cleaned = clean_messages()
        print('Database cleaned. %i suppressed messages' % int(cleaned))

    return perform
