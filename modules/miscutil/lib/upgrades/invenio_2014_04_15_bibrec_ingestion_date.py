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

import warnings
from invenio.dbquery import run_sql

depends_on = ['invenio_release_1_1_0']


def info():
    return "Add new ingestion_date column to bibrec table"


def do_upgrade():
    """ Implement your upgrades here  """
    create_statement = run_sql('SHOW CREATE TABLE bibrec')[0][1]
    if "`ingestion_date` datetime NOT NULL DEFAULT '0000-00-00 00:00:00'" not in create_statement:
        run_sql("ALTER TABLE bibrec ADD COLUMN `ingestion_date` datetime NOT NULL DEFAULT '0000-00-00 00:00:00'")
        run_sql("UPDATE bibrec SET ingestion_date=creation_date")


def estimate():
    """  Estimate running time of upgrade in seconds (optional). """
    return run_sql("SELECT COUNT(1) FROM bibrec")[0][0] / 10000


def pre_upgrade():
    """  Run pre-upgrade checks (optional). """
    pass


def post_upgrade():
    """  Run post-upgrade checks (optional). """
    pass
