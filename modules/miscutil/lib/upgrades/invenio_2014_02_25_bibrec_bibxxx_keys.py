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
from invenio.dbquery import run_sql, IntegrityError
from invenio.textutils import wait_for_user

depends_on = ['invenio_release_1_1_0']


def info():
    return "Amends primary key definition for bibrec_bibxxx tables"


def do_upgrade():
    """ Implement your upgrades here  """
    for tag in range(100):
        table_name = "bibrec_bib%02dx" % tag
        alter_query = "ALTER TABLE %s DROP KEY id_bibrec, ADD PRIMARY KEY (id_bibrec, id_bibxxx, field_number)" % table_name
        try:
            run_sql(alter_query)
        except IntegrityError:
            warnings.warn("Table %s is going to be fixed" % table_name)
            _fix_table(table_name)
            run_sql(alter_query)


def _fix_table(table_name):
    run_sql("CREATE TEMPORARY TABLE tmp_%s LIKE %s" % (table_name, table_name))
    run_sql("INSERT INTO tmp_%s SELECT DISTINCT * FROM %s" % (table_name, table_name))
    run_sql("TRUNCATE %s" % table_name)
    run_sql("INSERT INTO %s SELECT * FROM tmp_%s" % (table_name, table_name))
    run_sql("DROP TABLE tmp_%s" % table_name)


def estimate():
    """  Estimate running time of upgrade in seconds (optional). """
    return run_sql("SELECT COUNT(1) FROM bibrec")[0][0]/1500

