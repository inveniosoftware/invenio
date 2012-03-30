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

from itertools import groupby
from operator import itemgetter

from bibauthorid_dbinterface import get_recently_modified_record_ids as get_papers_recently_modified #emitting
from bibauthorid_dbinterface import get_user_log                         #emitting
from bibauthorid_dbinterface import insert_user_log                      #emitting
from bibauthorid_dbinterface import get_all_names_from_personid          #emitting
from bibauthorid_dbinterface import filter_newer_bibs                    #emitting
from bibauthorid_dbinterface import get_key_words                        #emitting
from bibauthorid_dbinterface import bib_matrix                           #emitting
from bibauthorid_dbinterface import get_name_by_bibrecref                #emitting
from bibauthorid_dbinterface import get_new_pesonid                      #emitting
from bibauthorid_dbinterface import get_deleted_papers                   #emitting
from bibauthorid_dbinterface import get_authors_from_paper               #emitting
from bibauthorid_dbinterface import get_coauthors_from_paper             #emitting
from bibauthorid_dbinterface import delete_paper_from_personid           #emitting
from bibauthorid_dbinterface import get_signatures_from_rec              #emitting
from bibauthorid_dbinterface import modify_signature                     #emitting
from bibauthorid_dbinterface import remove_sigs                          #emitting
from bibauthorid_dbinterface import find_pids_by_name                    #emitting
from bibauthorid_dbinterface import new_person_from_signature            #emitting
from bibauthorid_dbinterface import add_signature                        #emitting
from bibauthorid_dbinterface import copy_personids                       #emitting
from bibauthorid_dbinterface import get_all_bibrecs                      #emitting
from bibauthorid_dbinterface import remove_all_bibrecs                   #emitting
from bibauthorid_dbinterface import save_cluster                         #emitting
from bibauthorid_dbinterface import empty_results_table                  #emitting
from bibauthorid_dbinterface import check_personid_papers                #emitting
from bibauthorid_dbinterface import get_bib10x, get_bib70x               #emitting
from bibauthorid_dbinterface import get_bibrefrec_subset                 #emitting
from bibauthorid_dbinterface import update_personID_canonical_names      #emitting
from bibauthorid_dbinterface import get_full_personid_papers             #emitting
from bibauthorid_dbinterface import get_full_results                     #emitting
from bibauthorid_dbinterface import personid_get_recids_affected_since   #emitting
from bibauthorid_dbinterface import get_existing_personids               #emitting
from bibauthorid_dbinterface import get_lastname_results                 #emitting
from bibauthorid_dbinterface import personid_name_from_signature         #emitting
from bibauthorid_dbinterface import get_existing_result_clusters         #emitting
from bibauthorid_dbinterface import remove_personid_papers               #emitting
from bibauthorid_dbinterface import repair_personid                      #emitting
from bibauthorid_dbinterface import get_sql_time                         #emitting

from search_engine import perform_request_search
import bibauthorid_dbinterface as dbinter


class blob:
    def __init__(self, personid_records):
        '''
        @param personid_records:
            A list of tuples: (personid, bibrefrec, flag).
            Notice that all bibrefrecs should be the same
            since the blob represents only one bibrefrec.
        '''
        self.bib = personid_records[0][1]
        assert all(p[1] == self.bib for p in personid_records)
        self.claimed = set()
        self.assigned = set()
        self.rejected = set()
        for pid, unused, flag in personid_records:
            if flag > 1:
                self.claimed.add(pid)
            elif flag >= -1:
                self.assigned.add(pid)
            else:
                self.rejected.add(pid)


def create_blobs_by_pids(pids):
    '''
    Returs a list of blobs by a given set of personids.
    Blob is an object which describes all information
    for a bibrefrec in the personid table.
    @type pids: iterable of integers
    '''
    all_bibs = dbinter.get_all_papers_of_pids(pids)
    all_bibs = ((x[0], (int(x[1]), x[2], x[3]), x[4]) for x in all_bibs)
    bibs_dict = groupby(sorted(all_bibs, key=itemgetter(1)), key=itemgetter(1))
    blobs = [blob(list(bibs)) for unused, bibs in bibs_dict]

    return blobs


def group_blobs(blobs):
    '''
    Separates the blobs into two groups
    of objects - those with claims and
    those without.
    '''

    # created from blobs, which are claimed
    # [(bibrefrec, personid)]
    union = []

    # created from blobs, which are not claimed
    # [(bibrefrec, personid/None, [personid])]
    independent = []

    for blob in blobs:
        if len(blob.claimed) > 0:
            assert len(blob.claimed) == 1
            union.append((blob.bib, list(blob.claimed)[0]))
        elif len(blob.assigned) > 0:
            assert len(blob.assigned) == 1
            independent.append((blob.bib, list(blob.assigned)[0], list(blob.rejected)))
        else:
            assert len(blob.assigned) == 0
            independent.append((blob.bib, None, list(blob.rejected)))

    return (union, independent)


def group_personid(papers_table="aidPERSONID_PAPERS", data_table="aidPERSONID_DATA"):
    '''
    Extracts, groups and returns the whole personid.
    '''
    papers = dbinter.get_full_personid_papers(papers_table)
    data = dbinter.get_full_personid_data(data_table)

    group = lambda x: groupby(sorted(x, key=itemgetter(0)), key=itemgetter(0))
    to_dict = lambda x: dict((pid, map(itemgetter(slice(1, None)), data)) for pid, data in x)

    return (to_dict(group(papers)), to_dict(group(data)))


def compare_personid_tables(personIDold_papers, personIDold_data,
                            personIDnew_papers, personIDnew_data, fp):
    """
    Compares how personIDnew is different to personIDold.
    The two arguments must be generated with group_personid.
    fp must be a valid file object.
    """
    header_new = "+++ "
#    header_old = "    "
    header_removed = "--- "

    def write_new_personid(pid):
        fp.write("            Personid %d\n" % pid)

    def write_end_personid():
        fp.write("\n")

    def write_paper(row, header):
        fp.write("%s[PAPER] %s, signature %s %d %d, flag: %d, lcul: %d\n" % (header, row[3], row[0], row[1], row[2], row[4], row[5]))

    def write_data(row, header):
        tag = "[%s]" % row[0].upper()
        fp.write("%s%s %s, opt: (%s %s %s)\n" % (header, tag, row[1], row[2], row[3], row[4]))

    all_pids = (frozenset(personIDold_data.keys())
               | frozenset(personIDnew_data.keys())
               | frozenset(personIDold_papers.keys())
               | frozenset(personIDnew_papers.keys()))

    for pid in all_pids:
        data_old = frozenset(personIDold_data.get(pid, frozenset()))
        data_new = frozenset(personIDnew_data.get(pid, frozenset()))
#        old_data = data_new & data_old
        new_data = data_new - data_old
        del_data = data_old - data_new

        papers_old = frozenset(personIDold_papers.get(pid, frozenset()))
        papers_new = frozenset(personIDnew_papers.get(pid, frozenset()))
#        old_papers = papers_new & papers_old
        new_papers = papers_new - papers_old
        del_papers = papers_old - papers_new

        if new_data or del_data or new_papers or del_papers:
            write_new_personid(pid)

            for arr, header in zip([new_data, del_data],
                                   [header_new, header_removed]):
                for row in arr:
                    write_data(row, header)

            for arr, header in zip([new_papers, del_papers],
                                   [header_new, header_removed]):
                for row in arr:
                    write_paper(row, header)

            write_end_personid()

def filter_bibrecs_outside(all_papers):
    all_bibrecs = get_all_bibrecs()

    to_remove = list(frozenset(all_bibrecs) - frozenset(all_papers))
    chunk = 1000
    separated = [to_remove[i: i + chunk] for i in range(0, len(to_remove), chunk)]

    for sep in separated:
        remove_all_bibrecs(sep)

def get_all_valid_bibrecs():
    return perform_request_search(p="")

