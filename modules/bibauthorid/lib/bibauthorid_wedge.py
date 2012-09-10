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

import bibauthorid_config as bconfig
from itertools import izip, starmap
from operator import mul
from bibauthorid_backinterface import Bib_matrix
from bibauthorid_general_utils import update_status \
                                    , update_status_final \
                                    , bibauthor_print \
                                    , wedge_print
from bibauthorid_prob_matrix import ProbabilityMatrix
import numpy

eps = 0.001

# The lower bound of the edges being processed by the wedge algorithm.
edge_cut_prob = bconfig.WEDGE_THRESHOLD / 2

def wedge(cluster_set):
    matr = ProbabilityMatrix()
    matr.load(cluster_set.last_name)

    convert_cluster_set(cluster_set, matr)
    del matr # be sure that this is the last reference!

    do_wedge(cluster_set)

    restore_cluster_set(cluster_set)

    if bconfig.DEBUG_CHECKS:
        assert cluster_set._debug_test_hate_relation()
        assert cluster_set._debug_duplicated_recs()


def do_wedge(cluster_set, deep_debug=False):
    '''
    Rearranges the cluster_set acoarding to be values in the probability_matrix.
    The deep debug option will produce a lot of output. Avoid using it with more
    than 20 bibs in the cluster set.
    '''

    def decide(cl1, cl2):
        score1 = compare_to(cl1, cl2)
        score2 = compare_to(cl2, cl1)

        return compare_to_final_bounds(score1, score2)

    def compare_to(cl1, cl2):
        pointers = [cl1.out_edges[v] for v in cl2.bibs]

        assert pointers, "Wedge: no edges between clusters!"
        vals, probs = zip(*pointers)

        avg = sum(vals) / len(vals)
        if avg > eps:
            nvals = ((val / avg) ** prob for val, prob in pointers)
        else:
            return 0

        coeff = gini(nvals)

        weight = sum(starmap(mul, pointers)) / sum(probs)

        wedge_print("Wedge: Decide: vals = %s, probs = %s" % (str(vals), str(probs)))
        wedge_print("Wedge: Decide: coeff = %f, weight = %f" % (coeff, weight))

        return coeff * weight

    def gini(arr):
        arr = sorted(arr, reverse=True)
        dividend = sum(starmap(mul, izip(arr, xrange(1, 2 * len(arr), 2))))
        divisor = len(arr) * sum(arr)
        return float(dividend) / divisor

    def compare_to_final_bounds(score1, score2):
        return score1 + score2 > bconfig.WEDGE_THRESHOLD

    def edge_sorting(edge):
        '''
        probability + certainty / 10
        '''
        return edge[2][0] + edge[2][1] / 10.

    bib_map = create_bib_2_cluster_dict(cluster_set)

    plus_edges, minus_edges, edges = group_edges(cluster_set)

    for i, (bib1, bib2) in enumerate(plus_edges):
        update_status(float(i) / len(plus_edges), "Agglomerating obvious clusters...")
        cl1 = bib_map[bib1]
        cl2 = bib_map[bib2]
        if cl1 != cl2 and not cl1.hates(cl2):
            join(cl1, cl2)
            cluster_set.clusters.remove(cl2)
            for v in cl2.bibs:
                bib_map[v] = cl1
    update_status_final("Agglomerating obvious clusters done.")

    for i, (bib1, bib2) in enumerate(minus_edges):
        update_status(float(i) / len(minus_edges), "Dividing obvious clusters...")
        cl1 = bib_map[bib1]
        cl2 = bib_map[bib2]
        if cl1 != cl2 and not cl1.hates(cl2):
            cl1.quarrel(cl2)
    update_status_final("Dividing obvious clusters done.")

    bibauthor_print("Sorting the value edges.")
    edges = sorted(edges, key=edge_sorting, reverse=True)

    interval = 1000
    wedge_print("Wedge: New wedge, %d edges." % len(edges))
    for current, (v1, v2, unused) in enumerate(edges):
        if (current % interval) == 0:
            update_status(float(current) / len(edges), "Wedge...")

        assert unused != '+' and unused != '-', "Signed edge after filter!"
        wedge_print("Wedge: poped new edge: Verts = %s, %s Value = (%f, %f)" % (v1, v2, unused[0], unused[1]))
        cl1 = bib_map[v1]
        cl2 = bib_map[v2]
        if cl1 != cl2 and not cl1.hates(cl2):
            if deep_debug:
                export_to_dot(cluster_set, "/tmp/%s%d.dot" % (cluster_set.last_name, current), cluster_set.mapping, (v1, v2, unused))

            if decide(cl1, cl2):
                wedge_print("Wedge: Joined!")
                join(cl1, cl2)
                cluster_set.clusters.remove(cl2)
                for v in cl2.bibs:
                    bib_map[v] = cl1
            else:
                wedge_print("Wedge: Quarreled!")
                cl1.quarrel(cl2)
        elif cl1 == cl2:
            wedge_print("Wedge: Clusters already joined!")
        else:
            wedge_print("Wedge: Clusters hate each other!")

    update_status_final("Wedge done.")
    bibauthor_print("")

    if deep_debug:
        export_to_dot(cluster_set, "/tmp/%sfinal.dot" % cluster_set.last_name, cluster_set.mapping)

def meld_edges(p1, p2):
    '''
    Creates one out_edges set from two.
    The operation is associative and commutative.
    The objects are: (out_edges for in a cluster, number of vertices in the same cluster)
    '''
    out_edges1, verts1 = p1
    out_edges2, verts2 = p2

    def median(e1, e2):
        if e1[0] in Bib_matrix.special_numbers:
            return e1

        if e2[0] in Bib_matrix.special_numbers:
            return e2

        inter_cert = e1[1] * verts1 + e2[1] * verts2
        inter_prob = e1[0] * e1[1] * verts1 + e2[0] * e2[1] * verts2
        return (inter_prob / inter_cert, inter_cert / (verts1 + verts2))

    assert len(out_edges1) == len(out_edges2), "Invalid arguments for meld edges"
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
        start = len(result_mapping)
        result_mapping += list(clus.bibs)
        end = len(result_mapping)
        clus.bibs = range(start, end)

    assert len(result_mapping) == len(set(result_mapping)), "Cluster set conversion failed"
    assert len(result_mapping) == cs.num_all_bibs, "Cluster set conversion failed"

    cs.new2old = result_mapping

    # step 2:
    #    + Using the prob matrix create a vector values to all other bibs.
    #    + Meld those vectors into one for each cluster.

    for current, c1 in enumerate(cs.clusters):
        update_status(float(current) / len(cs.clusters), "Converting the cluster set...")

        assert len(c1.bibs) > 0, "Empty cluster send to wedge"
        pointers = []

        for v1 in c1.bibs:
            pointer = numpy.ndarray(shape=(len(result_mapping), 2), dtype=float, order='C')
            pointer.fill(Bib_matrix.special_symbols[None])
            for c2 in cs.clusters:
                if c1 != c2 and not c1.hates(c2):
                    for v2 in c2.bibs:
                        val = prob_matr[result_mapping[v1], result_mapping[v2]]
                        if val in Bib_matrix.special_symbols:
                            numb = Bib_matrix.special_symbols[val]
                            val = (numb, numb)
                        assert len(val) == 2, "Edge coding failed"
                        pointer[v2] = val
            pointers.append((pointer, 1))

        c1.out_edges = reduce(meld_edges, pointers)[0]

    update_status_final("Converting the cluster set done.")

def restore_cluster_set(cs):
    for cl in cs.clusters:
        cl.bibs = set(cs.new2old[b] for b in cl.bibs)
        del cl.out_edges
    cs.update_bibs()

def create_bib_2_cluster_dict(cs):
    '''
    Creates and returns a dictionary bibrefrec -> cluster.
    The cluster set must be converted!
    '''
    size = sum(len(cl.bibs) for cl in cs.clusters)
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
        update_status(float(current) / len(cs.clusters), "Grouping all edges...")

        bib1 = tuple(cl1.bibs)[0]
        pointers = cl1.out_edges
        for bib2 in xrange(len(cl1.out_edges)):
            val = pointers[bib2]
            if val[0] not in Bib_matrix.special_numbers:
                if val[0] > edge_cut_prob:
                    pairs.append((bib1, bib2, val))
            elif val[0] == Bib_matrix.special_symbols['+']:
                plus.append((bib1, bib2))
            elif val[0] == Bib_matrix.special_symbols['-']:
                minus.append((bib1, bib2))
            else:
                assert val[0] == Bib_matrix.special_symbols[None], "Invalid Edge"

    update_status_final("Finished with the edge grouping.")

    bibauthor_print("Positive edges: %d, Negative edges: %d, Value edges: %d."
                     % (len(plus), len(minus), len(pairs)))
    return plus, minus, pairs


def join(cl1, cl2):
    '''
    Joins two clusters from a cluster set in the first.
    '''
    cl1.out_edges = meld_edges((cl1.out_edges, len(cl1.bibs)),
                               (cl2.out_edges, len(cl2.bibs)))[0]
    cl1.bibs += cl2.bibs

    assert not cl1.hates(cl1), "Joining hateful clusters"
    assert not cl2.hates(cl2), "Joining hateful clusters"

    cl1.hate |= cl2.hate
    for cl in cl2.hate:
        cl.hate.remove(cl2)
        cl.hate.add(cl1)


def export_to_dot(cs, fname, graph_info, extra_edge=None):
    from bibauthorid_dbinterface import get_name_by_bibrecref

    fptr = open(fname, "w")
    fptr.write("graph wedgy {\n")
    fptr.write("    overlap=prism\n")

    for idx, bib in enumerate(graph_info):
        fptr.write('    %d [color=black label="%s"];\n' % (idx, get_name_by_bibrecref(bib)))

    if extra_edge:
        v1, v2, (prob, cert) = extra_edge
        fptr.write('    %d -- %d [color=green label="p: %.2f, c: %.2f"];\n' % (v1, v2, prob, cert))

    for clus in cs.clusters:
        fptr.write("    %s [color=blue];\n" % " -- ".join(str(x) for x in clus.bibs))

        fptr.write("".join("    %d -- %d [color=red]\n" % (b1, b2)
                      for b1 in clus.bibs for h in clus.hate for b2 in h.bibs))

    fptr.write("}")
