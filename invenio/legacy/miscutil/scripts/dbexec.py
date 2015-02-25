# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2010, 2011, 2012, 2013 CERN.
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

import subprocess
import sys

from invenio.base.globals import cfg
from invenio.ext.script import Manager

manager = Manager(usage="Runs SQL commands")


@manager.option('-V', '--version', dest='version', action='store_true',
                default=False,  help="Print version information.")
@manager.option('-i', '--interactive', dest='interactive', action='store_true',
                default=False, help="Bring inteactive SQL REPL. (default=batch-execute)")
def dbexec(version=False, interactive=False):
    """Runs SQL commands."""
    MYSQL = cfg.get('MYSQL', 'mysql')
    ## is version called?
    if version:
        print(__revision__)
        return 0

    params = [
        '--default-character-set=utf8',
        '--max_allowed_packet=1G',
        '--host=%s' % (cfg['CFG_DATABASE_HOST'], ),
        '--port=%s' % (cfg['CFG_DATABASE_PORT'], ),
        '--user=%s' % (cfg['CFG_DATABASE_USER'], ),
        '--password=%s' % (cfg['CFG_DATABASE_PASS'], ),
        cfg['CFG_DATABASE_NAME']
        ]

    ## interactive mode asked for?
    if not interactive:
        params.insert(0, '-B')

    return subprocess.call([MYSQL] + params)


def main():
    from invenio.base.factory import create_app
    app = create_app()
    manager.app = app
    if len(sys.argv) < 2 or sys.argv[1] != 'dbexec':
        sys.argv.insert(1, 'dbexec')
    manager.run()

if __name__ == '__main__':
    main()
