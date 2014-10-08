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

from invenio.dbquery import run_sql
from invenio.bibauthorid_logutils import Logger

depends_on = ['invenio_2014_01_23_bibauthorid_rabbit_matchable_name_column']

Logger.override_verbosity(True)


def info():
    return "Remove duplicates in aidPERSONIDPAPERS."


def do_upgrade():

    logger = Logger("aidPERSONIDPAPERS_duplicates")

    logger.log('Removing duplicate entries in aidPERSONIDPAPERS...')
    duplicates = 0

    while True:  # Needed because there may be >1 duplicates.
        duplicate_entries = run_sql('select * '
                                    'from aidPERSONIDPAPERS   '
                                    'group by personid, bibref_table, '
                                    'bibref_value, bibrec, flag, '
                                    'lcul, last_updated '
                                    'having count(*) > 1')

        if not duplicate_entries:
            break

        for entry in duplicate_entries:
            run_sql('delete from aidPERSONIDPAPERS '
                    'where personid = %s and '
                    'bibref_table = %s and '
                    'bibref_value = %s and '
                    'bibrec = %s and '
                    'name = %s and '
                    'm_name = %s and '
                    'flag = %s and '
                    'lcul = %s and '
                    'last_updated = %s '
                    'limit 1',
                    entry)

            duplicates += len(duplicate_entries)

logger.log("""%s duplicate entries removed in
              aidPERSONIDPAPERS.""" % duplicates)


def estimate():
    return 1

