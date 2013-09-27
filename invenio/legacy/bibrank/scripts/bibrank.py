# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
BibRank ranking daemon.

Usage: %s [options]
     Ranking examples:
       %s -wjif -a --id=0-30000,30001-860000 --verbose=9
       %s -wjif -d --modified='2002-10-27 13:57:26'
       %s -wwrd --rebalance --collection=Articles
       %s -wwrd -a -i 234-250,293,300-500 -u admin

 Ranking options:
 -w, --run=r1[,r2]         runs each rank method in the order given

 -c, --collection=c1[,c2]  select according to collection
 -i, --id=low[-high]       select according to doc recID
 -m, --modified=from[,to]  select according to modification date
 -l, --lastupdate          select according to last update

 -a, --add                 add or update words for selected records
 -d, --del                 delete words for selected records
 -S, --stat                show statistics for a method

 -R, --recalculate         recalculate weigth data, used by word frequency method
                           should be used if ca 1% of the document has been changed
                           since last time -R was used

 -E, --extcites=NUM        print the top entries of the external cites table.
                           These are entries that should be entered in
                           your collection, since they have been cited
                           by NUM or more other records present in the
                           system.  Useful for cataloguers to input
                           external papers manually.

 Repairing options:
 -k,  --check              check consistency for all records in the table(s)
                           check if update of ranking data is necessary
 -r, --repair              try to repair all records in the table(s)
 Scheduling options:
 -u, --user=USER           user name to store task, password needed
 -s, --sleeptime=SLEEP     time after which to repeat tasks (no)
                            e.g.: 1s, 30m, 24h, 7d
 -t, --time=TIME           moment for the task to be active (now)
                            e.g.: +15s, 5m, 3h , 2002-10-27 13:57:26
 General options:
 -h, --help                print this help and exit
 -V, --version             print version and exit
 -v, --verbose=LEVEL       verbose level (from 0 to 9, default 1)
"""

__revision__ = "$Id$"

from invenio.base.factory import with_app_context


@with_app_context()
def main():
    from invenio.bibrank import main as bibrank_main
    return bibrank_main()
