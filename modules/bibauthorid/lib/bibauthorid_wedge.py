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
bibauthorid_tables_utils
    Bibauthorid's DB handler
'''

import bibauthorid_config as bconfig

# The lower bound of the edges being processed by the wedge algorithm.
edge_cut_prob = 0.5
lower_power = 0.5
higher_power = 4.
final_coeff = 1.

wedge_log = 40

def wedge(cluster_set, prob_matrix):
    '''
    Rearranges the cluster_set acoarding to be values in the probability_matrix.
    '''

    def decide(cl1, cl2):
        score1 = compare_to(cl1, cl2)
	score2 = compare_to(cl2, cl1)

        return compare_to_final_bounds(score1, score2)

    def compare_to(cl1, cl2):
        pointers = [cl1.out_edges[v] for v in cl2.bibs]

        vals = [p[0] for p in pointers]
        probs = [p[1] for p in pointers]

        avg = sum(vals) / len(vals)
        nvals = [(vals[i] / avg) ** probs[i] for i in range(len(vals))]

        nvag = sum(nvals) / len(nvals)
        nvals = [n / nvag for n in nvals]

        coeff = max(1 / _d(nvals, higher_power),
                        _d(nvals, lower_power))

        weight = sum([vals[i] * probs[i] for i in range(len(vals))]) / sum(probs)

        bconfig.LOGGER.log(wedge_log, "Wedge: Decide: vals = %s, probs = %s" % (str(vals), str(probs)))
        bconfig.LOGGER.log(wedge_log, "Wedge: Decide: coeff = %f, weight = %f" % (coeff, weight))

        return coeff * weight

    def _d(array, power):
        return (sum([vi ** power for vi in array]) / len(array)) ** (1. / power)

    def compare_to_final_bounds(score1, score2):
        return score1 + score2 > final_coeff

    def edge_sorting(edge):
        '''
        probability + certainty / 10
        '''
        return edge[2][0] + edge[2][1] / 10.

    convert_cluster_set(cluster_set, prob_matrix)

    if not cluster_set._debug_test_hate_relation():
        raise AssertionError

    bib_map = create_bib_2_cluster_dict(cluster_set)

    edges = sorted(get_all_edges_above_bound(cluster_set), key = edge_sorting, reverse = True)

    for v1, v2, unused in edges:
        if not cluster_set._debug_test_hate_relation():
            raise AssertionError
        bconfig.LOGGER.log(wedge_log, "Wedge: poped new edge: Verts = %s, %s Value = (%f, %f)" % (v1, v2, unused[0], unused[1]))
        cl1 = bib_map[v1]
        cl2 = bib_map[v2]
        if cl1 != cl2 and not cl1.hates(cl2):
            if len(cl1.bibs & cl2.bibs) != 0:
                raise AssertionError

            if (len(cl1.bibs & frozenset(cl2.out_edges.keys())) != len(cl1.bibs) or
                len(cl2.bibs & frozenset(cl1.out_edges.keys())) != len(cl2.bibs)):
                raise AssertionError

            bconfig.LOGGER.log(wedge_log, "Wedge: First cluster: verts = %s" % str(cl1.bibs))
            bconfig.LOGGER.log(wedge_log, "Wedge: First cluster: hate = %s" % str([x.bibs for x in cl1.hate]))
            bconfig.LOGGER.log(wedge_log, "Wedge: Second cluster: verts = %s" % str(cl2.bibs))
            bconfig.LOGGER.log(wedge_log, "Wedge: Second cluster: hate = %s" % str([x.bibs for x in cl2.hate]))
            if decide(cl1, cl2):
                bconfig.LOGGER.log(wedge_log, "Wedge: Joined!")
                if not cluster_set._debug_test_hate_relation():
                    raise AssertionError
                join(cl1, cl2)
                cluster_set.clusters.remove(cl2)
                if not cluster_set._debug_test_hate_relation():
                    import pdb; pdb.set_trace()
                    raise AssertionError
                for v in cl2.bibs:
                    bib_map[v] = cl1
            else:
                bconfig.LOGGER.log(wedge_log, "Wedge: Quarreled!")
                cl1.quarrel(cl2)
                if not cluster_set._debug_test_hate_relation():
                    raise AssertionError

def get_first_elem(set_obj):
    if len(set_obj) < 1:
        raise AssertionError

    return iter(set_obj).next()

def meld_edges(p1, p2):
    '''
    Creates one out_edges set from two.
    The operation is associative and commutative.
    The objects are: (out_edges for in a cluster, number of vertices in the same cluster)
    '''
    out_edges1 = p1[0]
    verts1 = p1[1]
    out_edges2 = p2[0]
    verts2 = p2[1]

    def median(e1, e2):
        inter_cert = e1[1] * verts1 + e2[1] * verts2
        inter_prob = e1[0] * e1[1] * verts1 + e2[0] * e2[1] * verts2
        return (inter_prob / inter_cert, inter_cert / (verts1 + verts2))

    result = {}
    keys = [k for k in out_edges1 if k in out_edges2]
    return (dict((k, median(out_edges1[k], out_edges2[k])) for k in keys), verts1 + verts2)

def convert_cluster_set(cs, prob_matr):
    '''
    Convertes a normal cluster set to a wedge clsuter set.
    @param cs: a cluster set to be converted
    @param type: cluster set
    '''
    for c1 in cs.clusters:
        if len(c1.bibs) < 1:
            raise AssertionError("Empty clusters are not valid")
        matching_verts = [v for c2 in cs.clusters if c1 != c2 and not c1.hates(c2) for v in c2.bibs]
        pointers = [(dict((bib2, prob_matr[bib1, bib2]) for bib2 in matching_verts), 1) for bib1 in c1.bibs]
        c1.out_edges = reduce(meld_edges, pointers)[0]

def create_bib_2_cluster_dict(cs):
    '''
    Creates and returns a dictionary bibrefrec -> cluster.
    '''
    return dict((bib, cl) for cl in cs.clusters for bib in cl.bibs)

def get_all_edges_above_bound(cs):
    '''
    Returns an array with elemets of the type: [bibref, bibref, score],
    where the elemets are all pairs of bibres in the cluster_set above
    the edge_cut threshold.
    '''
    return [(get_first_elem(cl1.bibs), bib2, val)
                for cl1 in cs.clusters
                    for bib2, val in cl1.out_edges.items()
                        if get_first_elem(cl1.bibs) < bib2
                            if edge_cut_prob < val[0]]

def join(cl1, cl2):
    '''
    Joins two clusters from a cluster set in the first.
    '''
    if cl1.hates(cl2):
        raise AssertionError("You cannot join hating clusters")

    cl1.out_edges = meld_edges((cl1.out_edges, len(cl1.bibs)),
                               (cl2.out_edges, len(cl2.bibs)))[0]
    cl1.bibs |= cl2.bibs

    if (not cl1._debug_test_hate_relation() or
        not cl2._debug_test_hate_relation()):
        raise AssertionError

    if cl1.hates(cl1) or cl2.hates(cl2):
        raise AssertionError

    cl1.hate |= cl2.hate
    for cl in cl2.hate:
        cl.hate.remove(cl2)
        cl.hate.add(cl1)

    if not cl1._debug_test_hate_relation():
        raise AssertionError

