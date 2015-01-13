# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from itertools import chain, groupby, izip, cycle
from operator import itemgetter
from invenio.bibauthorid_matrix_optimization import maximized_mapping
from invenio.bibauthorid_backinterface import save_cluster
from invenio.bibauthorid_backinterface import get_confirmed_papers_of_authors
from invenio.bibauthorid_backinterface import get_bib10x, get_bib70x
from invenio.bibauthorid_backinterface import get_author_to_confirmed_names_mapping
from invenio.bibauthorid_backinterface import get_signatures_from_bibrefs
from invenio.bibauthorid_name_utils import generate_last_name_cluster_str
from invenio.bibauthorid_logutils import Logger

logger = Logger("cluster_set")


class Blob(object):

    def __init__(self, personid_records):
        '''
        @param personid_records:
            A list of tuples: (personid, bibrefrec, flag).
            Notice that all bibrefrecs should be the same
            since the Blob represents only one bibrefrec.
        '''
        self.bib = personid_records[0][1]
        assert all(p[1] == self.bib for p in personid_records), \
            "All cluster sets should share the bibrefrec"
        self.claimed = set()
        self.assigned = set()
        self.rejected = set()
        for pid, _, flag in personid_records:
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
    all_bibs = get_confirmed_papers_of_authors(pids)
    all_bibs = ((x[0], (int(x[1]), x[2], x[3]), x[4]) for x in all_bibs)
    bibs_dict = groupby(sorted(all_bibs, key=itemgetter(1)), key=itemgetter(1))
    blobs = [Blob(list(bibs)) for _, bibs in bibs_dict]

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
        assert len(blob.claimed) + len(blob.assigned) == 1, \
            "Each blob must have exactly one associated signature"
        if len(blob.claimed) > 0:
            union.append((blob.bib, list(blob.claimed)[0]))
        else:
            independent.append((blob.bib, list(blob.assigned)[0], list(blob.rejected)))

    return (union, independent)


class ClusterSet(object):

    class Cluster(object):

        def __init__(self, bibs, hate=None):
            # hate is a symetrical relation
            self.bibs = set(bibs)
            if hate:
                self.hate = set(hate)
            else:
                self.hate = set(list())
            self.personid = None

        def hates(self, other):
            return other in self.hate

        def quarrel(self, cl2):
            self.hate.add(cl2)
            cl2.hate.add(self)

        def _debug_test_hate_relation(self):
            for cl2 in self.hate:
                if not self.hates(cl2) or not cl2.hates(self):
                    return False
            return True

    def __init__(self):
        self.clusters = []
        self.num_all_bibs = None
        self.last_name = None

    def update_bibs(self):
        '''Updates the number of bibrefrecs held by this clusterset'''
        self.num_all_bibs = sum(len(cl.bibs) for cl in self.clusters)

    def all_bibs(self):
        '''Chain all bibs contained in this clusterset'''
        return chain.from_iterable(cl.bibs for cl in self.clusters)

    def create_skeleton(self, personids, last_name):
        blobs = create_blobs_by_pids(personids)
        self.last_name = last_name

        union, independent = group_blobs(blobs)

        union_clusters = {}
        for uni in union:
            union_clusters[uni[1]] = union_clusters.get(uni[1], []) + [uni[0]]

        cluster_dict = dict((personid, self.Cluster(bibs)) for personid, bibs in union_clusters.items())
        self.clusters = cluster_dict.values()

        for i, cl in enumerate(self.clusters):
            cl.hate = set(chain(self.clusters[:i], self.clusters[i + 1:]))

        for ind in independent:
            bad_clusters = [cluster_dict[i] for i in ind[2] if i in cluster_dict]
            cl = self.Cluster([ind[0]], bad_clusters)
            for bcl in bad_clusters:
                bcl.hate.add(cl)
            self.clusters.append(cl)

        self.update_bibs()
        return self

    # Creates a cluster set, ignoring the claims and the
    # rejected papers.
    def create_pure(self, personids, last_name):
        blobs = create_blobs_by_pids(personids)
        self.last_name = last_name

        self.clusters = [self.Cluster((blob.bib,)) for blob in blobs]
        self.update_bibs()
        return self

    def create_from_mark(self, bibrefs, last_name):
        bibrecrefs = get_signatures_from_bibrefs(bibrefs)
        self.clusters = [ClusterSet.Cluster([bib]) for bib in bibrecrefs]
        self.last_name = last_name
        self.update_bibs()
        return self

    # a *very* slow fucntion checking when the hate relation is no longer symetrical
    def _debug_test_hate_relation(self):
        for cl1 in self.clusters:
            if not cl1._debug_test_hate_relation():
                return False
        return True

    # similar to the function above
    def _debug_duplicated_recs(self, mapping=None):
        for cl in self.clusters:
            if mapping:
                setty = set(mapping[x][2] for x in cl.bibs)
            else:
                setty = set(x[2] for x in cl.bibs)

            if len(cl.bibs) != len(setty):
                return False
        return True

    # No longer used but it might be handy.
    @staticmethod
    def match_cluster_sets(cs1, cs2):
        """
        This functions tries to generate the best matching
        between cs1 and cs2 acoarding to the shared bibrefrecs.
        It returns a dictionary with keys, clsuters in cs1,
        and values, clusters in cs2.
        @param and type of cs1 and cs2: cluster_set
        @return: dictionary with the matching clusters.
        @return type: { cluster : cluster }
        """

        matr = [[len(cl1.bibs & cl2.bibs) for cl2 in cs2.clusters] for cl1 in cs1.clusters]
        mapping = maximized_mapping(matr)
        return dict((cs1.clusters[mappy[0]], cs2.clusters[mappy[1]]) for mappy in mapping)

    def store(self):
        '''
        Stores the cluster set in a special table.
        This is used to store the results of
        tortoise/wedge in a table and later merge them
        with personid.
        '''
        named_clusters = (("%s.%d" % (self.last_name, idx), cl) for idx, cl in enumerate(self.clusters))
        map(save_cluster, named_clusters)


def delayed_create_from_mark(bibrefs, last_name):
    def ret():
        return ClusterSet().create_from_mark(bibrefs, last_name)
    return ret


def delayed_cluster_sets_from_marktables(limit_to_surnames=False):
    # { name -> [(table, bibref)] }
    logger.log('Delayed_cluster_set_from_marktables limited to %s' % str(limit_to_surnames))

    name_buket = {}
    if limit_to_surnames:
        limit_to_surnames = set([generate_last_name_cluster_str(s) for s in limit_to_surnames])

    for tab, ref, name in chain(izip(cycle((100,)), *izip(*get_bib10x())),
                                izip(cycle((700,)), *izip(*get_bib70x()))):
        name = generate_last_name_cluster_str(name)
        if limit_to_surnames and not name in limit_to_surnames:
            continue
        name_buket[name] = name_buket.get(name, []) + [(tab, ref)]

    logger.log('Delayed_cluster_set_from_marktables going to get %s  signatures....' % str(len(name_buket)))

    all_refs = ((name, refs, len(list(get_signatures_from_bibrefs(refs))))
                for name, refs in name_buket.items())
    all_refs = sorted(all_refs, key=itemgetter(2))
    return ([delayed_create_from_mark(set(refs), name) for name, refs, _ in all_refs],
            map(itemgetter(0), all_refs),
            map(itemgetter(2), all_refs))


def create_lastname_list_from_personid(last_modification):
    '''
    This function generates a dictionary from a last name
    to list of personids which have this lastname.
    '''
    # ((personid, [full Name1], Nbibs) ... )
    all_names = get_author_to_confirmed_names_mapping(last_modification)

    # ((personid, last_name, Nbibs) ... )
    all_names = ((row[0], generate_last_name_cluster_str(iter(row[1]).next()), row[2])
                 for row in all_names)

    # { (last_name, [(personid)... ], Nbibs) ... }
    all_names = groupby(sorted(all_names, key=itemgetter(1)), key=itemgetter(1))
    all_names = ((key, list(data)) for key, data in all_names)
    all_names = ((key, map(itemgetter(0), data), sum(x[2] for x in data)) for key, data in all_names)

    return all_names


def delayed_create(create_f, pids, lname):
    def ret():
        return create_f(ClusterSet(), pids, lname)
    return ret


def delayed_cluster_sets_from_personid(pure, last_modification=None):
    names = create_lastname_list_from_personid(last_modification)
    names = sorted(names, key=itemgetter(2))
    if pure:
        create = ClusterSet.create_pure
    else:
        create = ClusterSet.create_skeleton
    return ([delayed_create(create, name[1], name[0]) for name in names],
            map(itemgetter(0), names),
            map(itemgetter(2), names))
