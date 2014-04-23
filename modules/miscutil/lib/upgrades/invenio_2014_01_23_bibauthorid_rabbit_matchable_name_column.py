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
from invenio.bibauthorid_logutils import Logger
from invenio.bibauthorid_dbinterface import get_name_by_bibref, create_matchable_name
from invenio.bibauthorid_rabbit import rabbit

depends_on = ['invenio_2013_11_28_bibauthorid_search_engine_column_changes']

def info():
    return "Updates the columns of aidPERSONIDPAPERS, adds the rabbit matchable name, assigns default value to columns."

def do_upgrade():

    logger = Logger("Rabbit m_name upgrade script")

    warnings.filterwarnings('ignore')
    run_sql("alter table aidPERSONIDPAPERS add `m_name` VARCHAR(256) not null after name")

    run_sql("alter table aidPERSONIDPAPERS add INDEX `m_name-b` (`m_name`)")

    present_bibrefs = set(run_sql("select bibref_table, bibref_value from aidPERSONIDPAPERS"))

    total_updates = len(present_bibrefs)


    records_for_rabbit = set()
    for i,bibref in enumerate(present_bibrefs):
        logger.update_status(float(i)/total_updates, '%s out of %s (%s)' % (str(i), str(total_updates), str(bibref)))
        try:
            name = get_name_by_bibref(bibref)
        except AssertionError, error:
            if "A bibref must have exactly one name" in error.message:
                records_for_rabbit.add(bibref[1])
            else:
                raise error
        else:
            m_name = create_matchable_name(name)
            run_sql("update aidPERSONIDPAPERS set name=%s, m_name=%s where bibref_table=%s "
                    "and bibref_value=%s ", (name, m_name, bibref[0], bibref[1]))
    if records_for_rabbit:
        rabbit(records_for_rabbit)
    logger.update_status(1., 'Finished')

    run_sql("alter table aidPERSONIDDATA modify  data varchar(256) not null default '' ")

def estimate():
    """
    Let's assume 2ms per sql query in a standard production environment, with some safety margin.
    """
    n = run_sql("select count(*) from aidPERSONIDPAPERS")[0][0]
    queries = n*2
    return 0.002 * queries

