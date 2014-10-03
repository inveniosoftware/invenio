# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
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

"""An upgrade for creating ORCID token table."""

from invenio.dbquery import run_sql

depends_on = ['invenio_release_1_1_0']


def info():
    """Info about new ORCID tokens table."""
    return "New bibauthorid ORCID tokens table"


def do_upgrade():
    """Create the ORCID token table."""
    run_sql("""CREATE TABLE IF NOT EXISTS `aidTOKEN` (
      `personid` BIGINT( 16 ) UNSIGNED PRIMARY
      KEY NOT NULL, `token` VARCHAR( 255 ) NOT NULL,
      `was_changed` SMALLINT( 6 ) NOT NULL
    ) ENGINE=MyISAM""")


def estimate():
    """  Estimate running time of upgrade in seconds (optional). """
    return 1
