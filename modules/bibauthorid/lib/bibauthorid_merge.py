# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011, 2012 CERN.
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
from itertools import groupby, chain, imap, izip

from bibauthorid_general_utils import update_status \
                                    , update_status_final
from bibauthorid_matrix_optimization import maximized_mapping
from bibauthorid_backinterface import update_personID_canonical_names
from bibauthorid_backinterface import get_existing_result_clusters
from bibauthorid_backinterface import get_lastname_results
from bibauthorid_backinterface import personid_name_from_signature
from bibauthorid_backinterface import personid_from_signature
from bibauthorid_backinterface import move_signature
from bibauthorid_backinterface import get_claimed_papers
from bibauthorid_backinterface import get_new_personid
from bibauthorid_backinterface import find_conflicts
from bibauthorid_backinterface import get_free_pids
from bibauthorid_backinterface import get_signature_info
from bibauthorid_dbinterface import delete_empty_persons
from bibauthorid_dbinterface import get_bibrefrec_to_pid_flag_mapping

def merge_static():
    '''
        This function merges aidPERSONIDPAPERS with aidRESULTS.
        Use it after tortoise.
        This function is static: if aid* tables are changed while it's running,
        probably everything will crash and a black hole will open, eating all your data.
    '''
    class Sig(object):
        def __init__(self, bibrefrec, pid_flag):
            self.rejected = dict(filter(lambda p:                p[1] <= -2, pid_flag))
            self.assigned =      filter(lambda p: -2 <  p[1] and p[1] <   2, pid_flag)
            self.claimed =       filter(lambda p:  2 <= p[1],                pid_flag)
            self.bibrefrec = bibrefrec

            assert self.invariant()

        def invariant(self):
            return len(self.assigned) + len(self.claimed) <= 1

        def empty(self):
            return not self.isclaimed and not self.isassigned

        def isclaimed(self):
            return len(self.claimed) == 1

        def get_claimed(self):
            return self.claimed[0][0]

        def get_assigned(self):
            return self.assigned[0][0]

        def isassigned(self):
            return len(self.assigned) == 1

        def isrejected(self, pid):
            return pid in self.rejected

        def change_pid(self, pid):
            assert self.invariant()
            assert self.isassigned()
            self.assigned = [(pid, 0)]
            move_signature(self.bibrefrec, pid)

    class Cluster(object):
        def __init__(self, pid, sigs):
            self.pid = pid

            self.sigs = dict((sig.bibrefrec[2], sig) for sig in sigs if not sig.empty())

        def send_sig(self, other, sig):
            paper = sig.bibrefrec[2]
            assert paper in self.sigs and paper not in other.sigs

            del self.sigs[paper]
            other.sigs[paper] = sig

            if sig.isassigned():
                sig.change_pid(other.pid)

    last_names = frozenset(name[0].split('.')[0] for name in get_existing_result_clusters())

    personid = get_bibrefrec_to_pid_flag_mapping()
    free_pids = get_free_pids()

    for idx, last in enumerate(last_names):
        update_status(float(idx) / len(last_names), "Merging, %d/%d current: %s" % (idx, len(last_names), last))

        results = ((int(row[0].split(".")[1]), row[1:4]) for row in get_lastname_results(last))

        # [(last name number, [bibrefrecs])]
        results = [(k, map(itemgetter(1), d)) for k, d in groupby(sorted(results, key=itemgetter(0)), key=itemgetter(0))]

        # List of dictionaries.
        # [{new_pid -> N}]
        matr = []

        # Set of all old pids.
        old_pids = set()

        for k, ds in results:
            pids = []
            for d in ds:
                pid_flag = filter(lambda x: x[1] > -2, personid.get(d, []))
                if pid_flag:
                    assert len(pid_flag) == 1
                    pid = pid_flag[0][0]
                    pids.append(pid)
                    old_pids.add(pid)

            matr.append(dict((k, len(list(d))) for k, d in groupby(sorted(pids))))

        old_pids = list(old_pids)
        best_match = maximized_mapping([[row.get(old, 0) for old in old_pids] for row in matr])

        # [[bibrefrecs] -> pid]
        matched_clusters = [(results[new_idx][1], old_pids[old_idx]) for new_idx, old_idx, unused in best_match]
        not_matched_clusters = frozenset(xrange(len(results))) - frozenset(imap(itemgetter(0), best_match))
        not_matched_clusters = izip((results[i][1] for i in not_matched_clusters), free_pids)

        # pid -> Cluster
        clusters = dict((pid, Cluster(pid, [Sig(bib, personid.get(bib, [])) for bib in sigs]))
                        for sigs, pid in chain(matched_clusters, not_matched_clusters))

        todo = clusters.items()
        for pid, clus in todo:
            assert clus.pid == pid

            for paper, sig in clus.sigs.items():
                if sig.isclaimed():
                    if sig.get_claimed() != pid:
                        target_clus = clusters[sig.get_claimed()]

                        if paper in target_clus.sigs:
                            new_clus = Cluster(free_pids.next(), [])
                            target_clus.send_sig(new_clus, target_clus[paper])
                            todo.append(new_clus)
                            clusters[new_clus.pid] = new_clus

                        assert paper not in target_clus.sigs
                        clus.send_sig(target_clus, sig)
                elif sig.get_assigned() != pid:
                    if not sig.isrejected(pid):
                        move_signature(sig.bibrefrec, pid)
                    else:
                        move_signature(sig.bibrefrec, free_pids.next())
                else:
                    assert not sig.isrejected(pid)

    update_status_final("Merging done.")

    update_status_final()
    delete_empty_persons()
    update_personID_canonical_names()

def merge_static_oldstyle():
    '''
        This function merges aidPERSONIDPAPERS with aidRESULTS.
        Use it after tortoise.
        This function is static: if aid* tables are changed while it's running,
        probably everything will crash and a black hole will open, eating all your data.
    '''
    last_names = frozenset(name[0].split('.')[0] for name in get_existing_result_clusters())

    def get_free_pids():
        while True:
            yield get_new_personid()

    free_pids = get_free_pids()

    current_mapping = get_bibrefrec_to_pid_flag_mapping()

    def move_sig_and_update_mapping(sig, old_pid_flag, new_pid_flag):
        move_signature(sig, new_pid_flag[0])
        current_mapping[sig].remove(old_pid_flag)
        current_mapping[sig].append(new_pid_flag)

    def try_move_signature(sig, target_pid):
        """
        """
        paps = current_mapping[sig]
        rejected = filter(lambda p: p[1] <= -2, paps)
        assigned = filter(lambda p:-2 < p[1] and p[1] < 2, paps)
        claimed = filter(lambda p: 2 <= p[1] and p[0] == target_pid, paps)

        if claimed or not assigned or assigned[0] == target_pid:
            return

        assert len(assigned) == 1

        if rejected:
            newpid = free_pids.next()
            move_sig_and_update_mapping(sig, assigned[0], (newpid, assigned[0][1]))
        else:
            conflicts = find_conflicts(sig, target_pid)
            if not conflicts:
                move_sig_and_update_mapping(sig, assigned[0], (target_pid, assigned[0][1]))
            else:
                assert len(conflicts) == 1
                if conflicts[0][3] == 2:
                    newpid = free_pids.next()
                    move_sig_and_update_mapping(sig, assigned[0], (newpid, assigned[0][1]))
                else:
                    newpid = free_pids.next()
                    csig = tuple(conflicts[0][:3])
                    move_sig_and_update_mapping(csig, (target_pid, conflicts[0][3]), (newpid, conflicts[0][3]))
                    move_sig_and_update_mapping(sig, assigned[0], (target_pid, assigned[0][1]))

    for idx, last in enumerate(last_names):
        update_status(float(idx) / len(last_names), "%d/%d current: %s" % (idx, len(last_names), last))

        results = ((int(row[0].split(".")[1]), row[1:4]) for row in get_lastname_results(last))

        # [(last name number, [bibrefrecs])]
        results = [(k, map(itemgetter(1), d)) for k, d in groupby(sorted(results, key=itemgetter(0)), key=itemgetter(0))]

        # List of dictionaries.
        # [{new_pid -> N}]
        matr = []

        # Set of all old pids.
        old_pids = set()

        for k, ds in results:
            pids = []
            claim = []
            for d in ds:
                pid_flag = current_mapping.get(d, [])
                if pid_flag:
                    pid, flag = pid_flag[0]
                    pids.append(pid)
                    old_pids.add(pid)
                    if flag > 1:
                        claim.append((d, pid))

            matr.append(dict((k, len(list(d))) for k, d in groupby(sorted(pids))))

        # We cast it to list in order to ensure the order persistence.
        old_pids = list(old_pids)
        best_match = maximized_mapping([[row.get(old, 0) for old in old_pids] for row in matr])

        matched_clusters = [(results[new_idx][1], old_pids[old_idx]) for new_idx, old_idx, unused in best_match]
        not_matched_clusters = frozenset(xrange(len(results))) - frozenset(imap(itemgetter(0), best_match))
        not_matched_clusters = izip((results[i][1] for i in not_matched_clusters), free_pids)

        for sigs, pid in chain(matched_clusters, not_matched_clusters):
            for sig in sigs:
                if sig in current_mapping:
                    if not pid in map(itemgetter(0), filter(lambda x: x[1] > -2, current_mapping[sig])):
                        try_move_signature(sig, pid)

    update_status_final()
    delete_empty_persons()
    update_personID_canonical_names()

def merge_dynamic():
    '''
        This function merges aidPERSONIDPAPERS with aidRESULTS.
        Use it after tortoise.
        This function is dynamic: it allows aid* tables to be changed while it is still running,
        hence the claiming faciity for example can stay online during the merge. This comfort 
        however is paid off in term of speed.
    '''
    last_names = frozenset(name[0].split('.')[0] for name in get_existing_result_clusters())

    def get_free_pids():
        while True:
            yield get_new_personid()

    free_pids = get_free_pids()

    def try_move_signature(sig, target_pid):
        """
        """
        paps = get_signature_info(sig)
        rejected = filter(lambda p: p[1] <= -2, paps)
        assigned = filter(lambda p:-2 < p[1] and p[1] < 2, paps)
        claimed = filter(lambda p: 2 <= p[1] and p[0] == target_pid, paps)

        if claimed or not assigned or assigned[0] == target_pid:
            return

        assert len(assigned) == 1

        if rejected:
            move_signature(sig, free_pids.next())
        else:
            conflicts = find_conflicts(sig, target_pid)
            if not conflicts:
                move_signature(sig, target_pid)
            else:
                assert len(conflicts) == 1
                if conflicts[0][3] == 2:
                    move_signature(sig, free_pids.next())
                else:
                    move_signature(conflicts[0][:3], free_pids.next())
                    move_signature(sig, target_pid)

    for idx, last in enumerate(last_names):
        update_status(float(idx) / len(last_names), "%d/%d current: %s" % (idx, len(last_names), last))

        results = ((int(row[0].split(".")[1]), row[1:4]) for row in get_lastname_results(last))

        # [(last name number, [bibrefrecs])]
        results = [(k, map(itemgetter(1), d)) for k, d in groupby(sorted(results, key=itemgetter(0)), key=itemgetter(0))]

        # List of dictionaries.
        # [{new_pid -> N}]
        matr = []

        # Set of all old pids.
        old_pids = set()

        for k, ds in results:
            pids = []
            claim = []
            for d in ds:
                pid_flag = personid_from_signature(d)
                if pid_flag:
                    pid, flag = pid_flag[0]
                    pids.append(pid)
                    old_pids.add(pid)
                    if flag > 1:
                        claim.append((d, pid))

            matr.append(dict((k, len(list(d))) for k, d in groupby(sorted(pids))))

        # We cast it to list in order to ensure the order persistence.
        old_pids = list(old_pids)
        best_match = maximized_mapping([[row.get(old, 0) for old in old_pids] for row in matr])

        matched_clusters = [(results[new_idx][1], old_pids[old_idx]) for new_idx, old_idx, unused in best_match]
        not_matched_clusters = frozenset(xrange(len(results))) - frozenset(imap(itemgetter(0), best_match))
        not_matched_clusters = izip((results[i][1] for i in not_matched_clusters), free_pids)

        for sigs, pid in chain(matched_clusters, not_matched_clusters):
            for sig in sigs:
                try_move_signature(sig, pid)

    update_status_final()
    delete_empty_persons()
    update_personID_canonical_names()

def matched_claims(inspect=None):
    '''
        Checks how many claims are violated in aidRESULTS.
        Returs the number of preserved and the total number of claims.
    '''
    last_names = frozenset(name[0].split('.')[0] for name in get_existing_result_clusters())
    r_match = 0
    r_total = 0

    for lname in last_names:
        if inspect and lname != inspect:
            continue

        results_dict = dict(((row[1], row[2], row[3]), int(row[0].split(".")[1]))
                        for row in get_lastname_results(lname))

        results_clusters = max(results_dict.values()) + 1
        assert frozenset(results_dict.values()) == frozenset(range(results_clusters))

        pids = frozenset(x[0] for x in chain.from_iterable(personid_name_from_signature(r) for r in results_dict.keys()))

        matr = ((results_dict[x] for x in get_claimed_papers(pid) if x in results_dict) for pid in pids)
        matr = (dict((k, len(list(d))) for k, d in groupby(sorted(row))) for row in matr)
        matr = [[row.get(i, 0) for i in xrange(results_clusters)] for row in matr]

        r_match += sum(m[2] for m in maximized_mapping(matr))
        r_total += sum(sum(row) for row in matr)

    return r_match, r_total

