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

import bibauthorid_config as bconfig
from bibauthorid_general_utils import update_status
import numpy

# The lower bound of the edges being processed by the wedge algorithm.
lower_power = .5
higher_power = 4.
final_coeff = .8
edge_cut_prob = final_coeff / 2.

wedge_log = 40

special_items = ((None, -3.), ('+', -2.), ('-', -1.))
special_symbols = dict((x[0], x[1]) for x in special_items)
special_numbers = dict((x[1], x[0]) for x in special_items)

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

    print "Converting the cluster set"
    new2old = convert_cluster_set(cluster_set, prob_matrix)

    assert cluster_set._debug_test_hate_relation()
    bib_map = create_bib_2_cluster_dict(cluster_set)

    print "Grouping all edges"
    plus_edges, minus_edges, edges = group_edges(cluster_set)

    print "Aglumerating obvious clusters"
    for bib1, bib2 in plus_edges:
        cl1 = bib_map[bib1]
        cl2 = bib_map[bib2]
        if cl1 != cl2 and not cl1.hates(cl2):
            join(cl1, cl2)
            cluster_set.clusters.remove(cl2)
            for v in cl2.bibs:
                bib_map[v] = cl1

    print "Dividing obvious clusters"
    for bib1, bib2 in minus_edges:
        cl1 = bib_map[bib1]
        cl2 = bib_map[bib2]
        if cl1 != cl2 and not cl1.hates(cl2):
            cl1.quarrel(cl2)

    print "Sorting the value edges"
    edges = sorted(edges, key=edge_sorting, reverse=True)

    interval = 1000
    print "Starting wedge: %d edges..." % len(edges)
    for current, (v1, v2, unused) in enumerate(edges):
        if (current % interval) == 0:
            update_status(float(current) / len(edges))

        assert cluster_set._debug_test_hate_relation()
        assert unused != '+' and unused != '-'

        bconfig.LOGGER.log(wedge_log, "Wedge: poped new edge: Verts = %s, %s Value = (%f, %f)" % (v1, v2, unused[0], unused[1]))
        cl1 = bib_map[v1]
        cl2 = bib_map[v2]
        if cl1 != cl2 and not cl1.hates(cl2):
            bconfig.LOGGER.log(wedge_log, "Wedge: First cluster: verts = %s" % str(cl1.bibs))
            bconfig.LOGGER.log(wedge_log, "Wedge: First cluster: hate = %s" % str([x.bibs for x in cl1.hate]))
            bconfig.LOGGER.log(wedge_log, "Wedge: Second cluster: verts = %s" % str(cl2.bibs))
            bconfig.LOGGER.log(wedge_log, "Wedge: Second cluster: hate = %s" % str([x.bibs for x in cl2.hate]))
            if decide(cl1, cl2):
                bconfig.LOGGER.log(wedge_log, "Wedge: Joined!")
                join(cl1, cl2)
                cluster_set.clusters.remove(cl2)
                for v in cl2.bibs:
                    bib_map[v] = cl1
            else:
                bconfig.LOGGER.log(wedge_log, "Wedge: Quarreled!")
                cl1.quarrel(cl2)
    update_status(1)
    print ""

    restore_cluster_set(cluster_set, new2old)

def meld_edges(p1, p2):
    '''
    Creates one out_edges set from two.
    The operation is associative and commutative.
    The objects are: (out_edges for in a cluster, number of vertices in the same cluster)
    '''
    out_edges1, verts1 = p1
    out_edges2, verts2 = p2

    def median(e1, e2):
        if e1[0] in special_numbers:
            return e1

        if e2[0] in special_numbers:
            return e2

        inter_cert = e1[1] * verts1 + e2[1] * verts2
        inter_prob = e1[0] * e1[1] * verts1 + e2[0] * e2[1] * verts2
        return (inter_prob / inter_cert, inter_cert / (verts1 + verts2))

    assert len(out_edges1) == len(out_edges2)
    size = len(out_edges1)

    result = numpy.ndarray(shape=(size, 2), dtype=float, order='C')
    for i in xrange(size):
        result[i] = median(out_edges1[i], out_edges2[i])

    return (result, verts1 + verts2)

def convert_cluster_set(cs, prob_matr):
    '''
    Convertes a normal cluster set to a wedge clsuter set.
    @param cs: a cluster set to be converted
    @param type: cluster set
    @return: a mapping from a number to a bibrefrec.
    '''

    # step 1:
    #    + Assign a number to each bibrefrec.
    #    + Replace the arrays of bibrefrecs with arrays of numbers.
    #    + Store the result and prepare it to be returned.

    result_mapping = []
    for clus in cs.clusters:
        result_mapping += list(clus.bibs)
        clus.bibs = range(len(result_mapping))[-len(clus.bibs):]

    assert len(result_mapping) == len(set(result_mapping))

    # step 2:
    #    + Using the prob matrix create a vector values to all other bibs.
    #    + Meld those vectors into one for each cluster.

    for current, c1 in enumerate(cs.clusters):
        update_status(float(current) / len(cs.clusters))

        assert len(c1.bibs) > 0
        pointers = []

        for v1 in c1.bibs:
            pointer = numpy.ndarray(shape=(len(result_mapping), 2), dtype=float, order='C')
            pointer.fill(special_symbols[None])
            for c2 in cs.clusters:
                if c1 != c2 and not c1.hates(c2):
                    for v2 in c2.bibs:
                        val = prob_matr[result_mapping[v1], result_mapping[v2]]
                        if val in special_symbols:
                            numb = special_symbols[val]
                            val = (numb, numb)
                        assert len(val) == 2
                        pointer[v2] = val
            pointers.append((pointer, 1))

        c1.out_edges = reduce(meld_edges, pointers)[0]

    update_status(1)
    print ""

    return result_mapping

def restore_cluster_set(cs, new2old):
    for cl in cs.clusters:
        cl.bibs = set(new2old[b] for b in cl.bibs)
        del cl.out_edges
        del cl.hate

def create_bib_2_cluster_dict(cs):
    '''
    Creates and returns a dictionary bibrefrec -> cluster.
    The cluster set must be converted!
    '''
    size = sum([len(cl.bibs) for cl in cs.clusters])
    ret = range(size)
    for cl in cs.clusters:
        for bib in cl.bibs:
            ret[bib] = cl
    return ret

def group_edges(cs):
    plus = []
    minus = []
    pairs = []

    for current, cl1 in enumerate(cs.clusters):
        update_status(float(current) / len(cs.clusters))

        bib1 = tuple(cl1.bibs)[0]
        pointers = cl1.out_edges
        for bib2 in xrange(len(cl1.out_edges)):
            val = pointers[bib2]
            if val[0] not in special_numbers:
                if val[0] > edge_cut_prob:
                    pairs.append((bib1, bib2, val))
            elif val[0] == special_symbols['+']:
                plus.append((bib1, bib2))
            elif val[0] == special_symbols['-']:
                minus.append((bib1, bib2))
            else:
                assert val[0] == special_symbols[None]

    update_status(1)
    print ""
    return plus, minus, pairs

def join(cl1, cl2):
    '''
    Joins two clusters from a cluster set in the first.
    '''
    cl1.out_edges = meld_edges((cl1.out_edges, len(cl1.bibs)),
                               (cl2.out_edges, len(cl2.bibs)))[0]
    cl1.bibs += cl2.bibs

    assert not cl1.hates(cl1)
    assert not cl2.hates(cl2)

    cl1.hate |= cl2.hate
    for cl in cl2.hate:
        cl.hate.remove(cl2)
        cl.hate.add(cl1)

