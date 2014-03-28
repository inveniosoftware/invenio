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

depends_on = ['invenio_release_1_1_0']

def info():
    return "New bibauthorid affiliations (aidAFFILIATIONS) table"

def do_upgrade():
    """ Implement your upgrades here  """
    run_sql("""CREATE TABLE IF NOT EXISTS `aidAFFILIATIONS` (
  `personid` BIGINT( 16 ) UNSIGNED NOT NULL ,
  `affiliation` VARCHAR( 256 ) NOT NULL,
  `last_recid` MEDIUMINT( 8 ) UNSIGNED NOT NULL,
  `last_occurence` datetime NOT NULL
) ENGINE=MyISAM""")

def estimate():
    """  Estimate running time of upgrade in seconds (optional). """
    return 1
