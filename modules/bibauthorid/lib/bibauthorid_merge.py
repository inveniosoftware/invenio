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

from operator import itemgetter
from itertools import count, ifilter, groupby, chain, imap, izip

from bibauthorid_backinterface import get_name_by_bibrecref
from bibauthorid_name_utils import create_normalized_name
from bibauthorid_name_utils import split_name_parts
from bibauthorid_general_utils import update_status
from bibauthorid_matrix_optimization import maximized_mapping
from bibauthorid_backinterface import get_existing_result_clusters
from bibauthorid_backinterface import get_existing_personids
from bibauthorid_backinterface import get_lastname_results
from bibauthorid_backinterface import personid_name_from_signature
from bibauthorid_backinterface import remove_personid_papers
from bibauthorid_backinterface import add_signature

def merge():
    '''
    This function merges aidPERSONIDPAPERS with aidRESULTS.
    Use it after tortoise.
    '''
    def name_from_sig(sig):
        sig = sig[:-1]
        if sig not in ref_2_name:
            name = get_name_by_bibrecref(sig)
            nice_name = create_normalized_name(split_name_parts(name))
            ref_2_name[sig] = nice_name
            return nice_name
        else:
            return ref_2_name[sig]

    last_names = frozenset(name[0].split('.')[0] for name in get_existing_result_clusters())

    used_pids = get_existing_personids()
    free_pids = ifilter(lambda x: x not in used_pids, count())

    for idx, last in enumerate(last_names):
        update_status(float(idx) / len(last_names), "%d/%d current: %s" % (idx, len(last_names), last))

        results = ((int(row[0].split(".")[1]), (row[1], row[2], row[3]))
                        for row in get_lastname_results(last))
        results = [(k, map(itemgetter(1), d)) for k, d in groupby(sorted(results, key=itemgetter(0)), key=itemgetter(0))]

        # a dictionary from bibrefs (table, value) to names (string)
        ref_2_name = {}
        # initially a list of dictionaries, later list of list with values.
        matr = []
        # initially a set of all old pids
        old_pids = set()

        for k, ds in results:
            pids = []
            for d in ds:
                pid_name = personid_name_from_signature(d)
                if pid_name:
                    pid = map(itemgetter(0), pid_name)
                    name = pid_name[0][1]
                    pids += pid
                    old_pids |= set(pid)
                    ref_2_name[d[:-1]] = name

            matr.append(dict((k, len(list(d))) for k, d in groupby(sorted(pids))))

        old_pids = list(old_pids)
        best_match = maximized_mapping([[row.get(old, 0) for old in old_pids] for row in matr])

        # lets mark the unused personids as free
        free_pids = chain(frozenset(xrange(len(old_pids))) - frozenset(imap(itemgetter(1), best_match)), free_pids)

        matched_clusters = [(results[new_idx][1], old_pids[old_idx]) for new_idx, old_idx, unused in best_match]
        not_matched_clusters = frozenset(xrange(len(results))) - frozenset(imap(itemgetter(0), best_match))
        not_matched_clusters = izip((results[i][1] for i in not_matched_clusters), free_pids)

        remove_personid_papers(old_pids)

        for sig, pid in chain(matched_clusters, not_matched_clusters):
            for s in sig:
                add_signature(s, name_from_sig(s), pid)

    update_status(1)
    print

 
