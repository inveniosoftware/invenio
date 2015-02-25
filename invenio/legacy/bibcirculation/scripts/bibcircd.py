#!@PYTHON@
# -*- mode: python; coding: utf-8; -*-
#
# This file is part of Invenio.
# Copyright (C) 2008, 2009, 2010, 2011 CERN.
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


__revision__ = "$Id$"

# try:
#     from invenio.legacy.bibcirculation.daemon import main
# except ImportError as e:
#     print "Error: %s" % e
#     import sys
#     sys.exit(1)

from invenio.base.factory import with_app_context


@with_app_context()
def main():
    from invenio.legacy.bibcirculation.daemon import main as bibcirc_main
    bibcirc_main()
