# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011, 2013 CERN.
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
BibIndex bibliographic data, reference and fulltext indexing utility.

Usage: bibindex %s [options]
Examples:
       bibindex -a -i 234-250,293,300-500 -u admin@localhost
       bibindex -a -w author,fulltext -M 8192 -v3
       bibindex -d -m +4d -A on --flush=10000

 Indexing options:
 -a,  --add                add or update words for selected records
 -d,  --del                delete words for selected records
 -i,  --id=low[-high]      select according to record recID.
 -m,  --modified=from[,to] select according to modification date
 -c,  --collection=c1[,c2] select according to collection

 Repairing options:
 -k,  --check              check consistency for all records in the table(s)
 -r,  --repair             try to repair all records in the table(s)

 Specific options:
 -w,  --windex=w1[,w2]     word/phrase indexes to consider (all)
 -M,  --maxmem=XXX         maximum memory usage in kB (no limit)
 -f,  --flush=NNN          full consistent table flush after NNN records (10000)

 Scheduling options:
 -u,  --user=USER          user name to store task, password needed
 -s,  --sleeptime=SLEEP    time after which to repeat task (no)
                           e.g.: 1s, 30m, 24h, 7d
 -t,  --time=TIME          moment for the task to be active (now)
                           e.g.: +15s, 5m, 3h, 2002-10-27 13:57:26

 General options:
 -h,  --help               print this help and exit
 -V,  --version            print version and exit
 -v,  --verbose=LEVEL      verbose level (from 0 to 9, default 1)
"""

from invenio.base.factory import with_app_context


@with_app_context()
def main():
    from invenio.legacy.bibindex.engine import main as bibindex_main
    return bibindex_main()
