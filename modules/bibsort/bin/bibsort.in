#!@PYTHON@
## -*- mode: python; coding: utf-8; -*-
##
## This file is part of Invenio.
## Copyright (C) 2010, 2011, 2012 CERN.
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
Usage: bibsort [options]

BibSort tool

Options:
  -h, --help            show this help message and exit
  -l, --load-config     Loads the configuration from bibsort.conf into the
                        database
  -d, --dump-config     Outputs a database dump in form of a config file
  -p, --print-sorting-methods
                        Prints the available sorting methods
  -B, --rebalance       Runs the sorting methods given in '--metods'and
                        rebalances all the buckets.
                        If no method is specified, the rebalance will be done
                        for all the methods in the config file.
  -S, --update-sorting  Runs the sorting methods given in '--methods' for the
                        recids given in '--recids'.
                        If no method is specified, the update will be done for
                        all the methods in the config file.
                        If no recids are specified, the update will be done
                        for all the records that have been
                        modified/inserted from the last run of the sorting.
                        If you want to run the sorting for all records, you
                        should use the '-B' option
  -M, --methods=METHODS Specify the sorting methods for which the
                        update_sorting or rebalancing will run
                        (ex: --methods=method1,method2,method3).
  -R, --recids=RECIDS   Specify the records for which the update_sorting will
                        run (ex: --recids=1,2-56,72)
"""

try:
    from invenio.bibsort_daemon import main
except ImportError, e:
    print "Error: %s" % e
    import sys
    sys.exit(1)

main()
