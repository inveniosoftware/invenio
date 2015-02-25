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

"""
Usage: bibrankgkb %s [options]
     Examples:
       bibrankgkb --input=bibrankgkb.cfg --output=test.kb
       bibrankgkb -otest.kb -v9
       bibrankgkb -v9

 Generate options:
 -i,  --input=file          input file, default from /etc/bibrank/bibrankgkb.cfg
 -o,  --output=file         output file, will be placed in current folder
 General options:
 -h,  --help                print this help and exit
 -V,  --version             print version and exit
 -v,  --verbose=LEVEL       verbose level (from 0 to 9, default 1)
"""
__revision__ = "$Id$"

from invenio.base.factory import with_app_context


@with_app_context()
def main():
    from invenio.legacy.bibrank.gkb import main as gkb_main
    return gkb_main()
