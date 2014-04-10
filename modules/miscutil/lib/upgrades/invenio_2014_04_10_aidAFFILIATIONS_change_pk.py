# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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

from invenio.dbquery import run_sql

depends_on = ['invenio_2014_04_01_new_aidAFFILIATIONS']

def info():
    return "aidAFFILIATIONS allows multiple affiliations per personid"

def do_upgrade():
    """ Implement your upgrades here  """
    run_sql("""ALTER TABLE `aidAFFILIATIONS`
               DROP PRIMARY KEY,
               ADD PRIMARY KEY(`personid`, `affiliation`),
               ADD INDEX `last_recid` (`last_recid`)""")

def estimate():
    """  Estimate running time of upgrade in seconds (optional). """
    return 1
