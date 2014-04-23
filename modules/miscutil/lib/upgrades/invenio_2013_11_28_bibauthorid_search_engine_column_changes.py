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

import warnings
from invenio.dbquery import run_sql

depends_on = ['invenio_release_1_1_0']

def info():
    return "Updates the columns of the bibauthorid search engine tables"

def do_upgrade():
    warnings.filterwarnings('ignore')
    run_sql("""TRUNCATE TABLE aidINVERTEDLISTS""")
    run_sql("""DROP TABLE aidDENSEINDEX""")
    run_sql("""CREATE TABLE IF NOT EXISTS `aidDENSEINDEX` (
                 `id` BIGINT( 16 ) NULL DEFAULT NULL,
                 `indexable_string` VARCHAR( 256 ) NULL DEFAULT NULL,
                 `personids` LONGBLOB NULL DEFAULT NULL,
                 `flag` SMALLINT( 2 ) NOT NULL,
                 `indexable_surname` VARCHAR( 256 ) NULL DEFAULT NULL,
                  PRIMARY KEY  (`id`, `flag`),
                  INDEX `nameid-b` (`id`)
               ) ENGINE=MyISAM""")

def estimate():
    return 1

