# This file is part of Invenio.
# Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011,
# 2012, 2013, 2014 CERN.
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

__revision__ = "$Id$"

import getopt
import sys

from invenio.base.helpers import with_app_context

def usage(exitcode=1, msg=""):
    """Prints usage info."""
    if msg:
        print("Error: %s." % msg, file=sys.stderr)
        print(file=sys.stderr)
    print("""Usage: %s [options]

General options:
  -h, --help\t\tprint this help
  -V, --version\t\tprint version number

Authentication options:
  -u, --user=USER\tUser name needed to perform the administrative task

Option to administrate authorizations:
  -a, --add\t\tadd default authorization settings
  -c, --compile\t\tcompile firewall like role definitions (FireRole)
  -r, --reset\t\treset to default settings
  -D, --demo\t\tto be used with -a or -r in order to consider demo site authorizations
""" % sys.argv[0], file=sys.stderr)
    sys.exit(exitcode)


@with_app_context()
def main():
    """Main function that analyzes command line input and calls whatever
    is appropriate. """

    from invenio.modules.access.firerole import repair_role_definitions
    from invenio.modules.access.control import (acc_add_default_settings,
                                                acc_reset_default_settings)
    from invenio.base.globals import cfg
    from invenio.legacy.bibsched.bibtask import authenticate

    DEF_DEMO_USER_ROLES = cfg.get('DEF_DEMO_USER_ROLES', tuple())
    DEF_DEMO_ROLES = cfg.get('DEF_DEMO_ROLES', tuple())
    DEF_DEMO_AUTHS = cfg.get('DEF_DEMO_AUTHS', tuple())

    ## parse command line:
    # set user-defined options:
    options = {'user' : '', 'reset' : 0, 'compile' : 0, 'add' : 0, 'demo' : 0}
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hVu:racD",
                                    ["help", "version", "user=",
                                    "reset", "add", "compile", "demo"])
    except getopt.GetoptError as err:
        usage(1, err)
    try:
        for opt in opts:
            if opt[0] in ("-h", "--help"):
                usage(0)
            elif opt[0] in ("-V", "--version"):
                print(__revision__)
                sys.exit(0)
            elif opt[0] in ("-u", "--user"):
                options["user"] = opt[1]
            elif opt[0] in ("-r", "--reset"):
                options["reset"] = 1
            elif opt[0] in ("-a", "--add"):
                options["add"] = 1
            elif opt[0] in ("-c", "--compile"):
                options["compile"] = 1
            elif opt[0] in ("-D", "--demo"):
                options["demo"] = 1
            else:
                usage(1)
        if options['add'] or options['reset'] or options['compile']:
            #if acca.acc_get_action_id('cfgwebaccess'):
            #    # Action exists hence authentication works :-)
            #    options['user'] = authenticate(options['user'],
            #        authorization_msg="WebAccess Administration",
            #        authorization_action="cfgwebaccess")
            if options['reset'] and options['demo']:
                acc_reset_default_settings(
                    [cfg['CFG_SITE_ADMIN_EMAIL']], DEF_DEMO_USER_ROLES,
                    DEF_DEMO_ROLES, DEF_DEMO_AUTHS)
                print("Reset default demo site settings.")
            elif options['reset']:
                acc_reset_default_settings([cfg['CFG_SITE_ADMIN_EMAIL']])
                print("Reset default settings.")
            elif options['add'] and options['demo']:
                acc_add_default_settings(
                    [cfg['CFG_SITE_ADMIN_EMAIL']], DEF_DEMO_USER_ROLES,
                    DEF_DEMO_ROLES, DEF_DEMO_AUTHS)
                print("Added default demo site settings.")
            elif options['add']:
                acc_add_default_settings([cfg['CFG_SITE_ADMIN_EMAIL']])
                print("Added default settings.")
            if options['compile']:
                repair_role_definitions()
                print("Compiled firewall like role definitions.")
        else:
            usage(1, "You must specify at least one command")
    except StandardError as e:
        from invenio.ext.logging import register_exception
        register_exception()
        usage(e)
    return

### okay, here we go:
if __name__ == '__main__':
    main()


