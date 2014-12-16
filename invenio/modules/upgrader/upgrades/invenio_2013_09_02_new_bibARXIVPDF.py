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
from invenio.legacy.dbquery import run_sql
from invenio.utils.text import wait_for_user

depends_on = ['invenio_release_1_1_0']

def info():
    return "New pdfchecker (bibARXIVPDF) table"

def do_upgrade():
    """ Implement your upgrades here  """
    run_sql("""CREATE TABLE IF NOT EXISTS bibARXIVPDF (
  id_bibrec mediumint(8) unsigned NOT NULL,
  status ENUM('ok', 'missing') NOT NULL,
  date_harvested datetime NOT NULL,
  version tinyint(2) NOT NULL,
  PRIMARY KEY (id_bibrec),
  KEY status (status)
) ENGINE=MyISAM""")

def estimate():
    """  Estimate running time of upgrade in seconds (optional). """
    return 1
