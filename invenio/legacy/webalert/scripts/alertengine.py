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

"""Alert engine command line interface"""

__revision__ = "$Id$"

from invenio.base.factory import with_app_context


def usage():
    from invenio.config import CFG_SITE_SUPPORT_EMAIL
    print("""Usage: alertengine [OPTION]
Run the alert engine.

  -h, --help          display this help and exit
  -V, --version       output version information and exit

  -d  --date="YEAR-MONTH-DAY" run the alertengine as if we were the
                              specified day, for test purposes (today)

Report bugs to <%s>""" % CFG_SITE_SUPPORT_EMAIL)

@with_app_context()
def main():
    import datetime
    import sys
    import getopt
    from invenio.legacy.webalert.alert_engine import run_alerts
    # from time import time

    date = datetime.date.today()

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hVd:",
                                   ["help", "version", "date="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        if o in ("-V", "--version"):
            print(__revision__)
            sys.exit(0)
        if o in ("-d", "--date"):
            year, month, day = map(int, a.split('-'))
            date = datetime.date(year, month, day)


    run_alerts(date)

# if __name__ == "__main__":
#     t0 = time()
#     main()
#     t1 = time()
#     print 'Alert engine finished in %.2f seconds' % (t1 - t0)
