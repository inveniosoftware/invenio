# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011 CERN.
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
'''
    bibauthorid_frontinterface
    This file aims to filter and modify the interface given by
    bibauthorid_bdinterface in order to make it usable by the 
    backend so to keep it as clean as possible.
'''

from bibauthorid_dbinterface import get_recently_modified_record_ids as get_papers_recently_modified #emitting
from bibauthorid_dbinterface import authornames_tables_gc                #emitting
from bibauthorid_dbinterface import get_user_log                         #emitting
from bibauthorid_dbinterface import insert_user_log                      #emitting
from bibauthorid_dbinterface import update_authornames_tables_from_paper #emitting
from bibauthorid_dbinterface import save_bibmap_and_matrix_to_db         #emitting
from bibauthorid_dbinterface import load_bibmap_and_matrix_from_db       #emitting
from bibauthorid_dbinterface import get_all_names_from_personid          #emitting
from bibauthorid_dbinterface import get_person_data                      #emitting
from bibauthorid_dbinterface import create_probability_table             #emitting

import bibauthorid_config as bconfig
import bibauthorid_dbinterface as dbinter

def probability_table_exists():
    '''
    Returns true if the table aidPROBCHECK exists in the database.
    '''
    rows = len(dbinter.check_table("aidPROBCACHE"))
    if (rows != 1 and rows != 0):
        raise AssertionError
    return rows == 1

def get_papers_by_pids(pids):
    '''
    By a given set of personids returs a dict: {personid : [(bibrefrec, flag)]}
    @type pids: iterable of integers
    '''
    all_bibs = dbinter.get_all_papers_of_pids(pids)

    ret = {}

    # The results are sorted by bibrefrec and now we have to filter them.
    # We use the fact that after sorting the collisions are one next to
    # another
    head = 0
    tail = 1
    limit = len(all_bibs)
    while tail <= limit:
        while (tail < limit
               and all_bibs[head][1] == all_bibs[tail][1]):
            tail = tail + 1
            bconfig.LOGGER.log(45, "Warning! Duplicated %d %s %d" % all_bibs[tail])
        # investigate [head, tail - 1]

        personid, bibrefrec, flag = all_bibs[head]
        head = head + 1
        while head < tail:
            if all_bibs[head][2] < -1:
                bconfig.LOGGER.log(45, "Warning! Duplicated rejected paper, ignoring (%d %s %d)." % all_bibs[head])
                continue
            elif all_bibs[head][2] <= 1:
                if flag <= 1:
                    bconfig.LOGGER.log(45, "Warning! Selecting new representative paper (%d %s %d)." % all_bibs[head])
                    personid, bibrefrec, flag = all_bibs[head]
            else:
                bconfig.LOGGER.log(45, "Warning! Selecting new representative paper (%d %s %d)." % all_bibs[head])
                personid, bibrefrec, flag = all_bibs[head]
                if 1 < flag:
                    bconfig.LOGGER.log(45, "Warning! More than one duplicated claimed paper.")
                    flag = flag + 1
        tail = tail + 1

        if flag > 2:
            flag = 0

        ret[personid] = ret.get(personid, []) + [(bibrefrec, flag)]\

    return ret

