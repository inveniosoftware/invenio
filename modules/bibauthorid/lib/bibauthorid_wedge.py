# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011, 2012, 2013 CERN.
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

from invenio.legacy.bibauthorid import config as bconfig
from itertools import izip, starmap
from operator import mul
from invenio.bibauthorid_backinterface import Bib_matrix
from invenio.legacy.bibauthorid.general_utils import update_status \
                                    , update_status_final \
                                    , bibauthor_print \
                                    , wedge_print
from invenio.bibauthorid_prob_matrix import ProbabilityMatrix
import numpy
#mport cPickle as SER
import msgpack as SER

import gc

SP_NUMBERS = Bib_matrix.special_numbers
SP_SYMBOLS = Bib_matrix.special_symbols
SP_CONFIRM = Bib_matrix.special_symbols['+']
SP_QUARREL = Bib_matrix.special_symbols['-']

eps = 0.01
edge_cut_prob = ''
wedge_thrsh = ''

import os
PID = lambda : str(os.getpid())

def wedge(cluster_set, report_cluster_status=False, force_wedge_thrsh=False):
    # The lower bound of the edges being processed by the wedge algorithm.
    global edge_cut_prob
    global wedge_thrsh

    if not force_wedge_thrsh:
        edge_cut_prob = bconfig.WEDGE_THRESHOLD / 3.
        wedge_thrsh = bconfig.WEDGE_THRESHOLD
    else:
        edge_cut_prob = force_wedge_thrsh / 3.
        wedge_thrsh = force_wedge_thrsh

    matr = ProbabilityMatrix()
    matr.load(cluster_set.last_name)

    convert_cluster_set(cluster_set, matr)
    del matr # be sure that this is the last reference!

    do_wedge(cluster_set)

    report = []
    if bconfig.DEBUG_WEDGE_PRINT_FINAL_CLUSTER_COMPATIBILITIES or report_cluster_status:
        msg = []
        for cl1 in cluster_set.clusters:
            for cl2 in cluster_set.clusters:
                if cl2 > cl1:
                    id1 = cluster_set.clusters.index(cl1)
                    id2 = cluster_set.clusters.index(cl2)
                    c12 = _compare_to(cl1,cl2)
                    c21 = _compare_to(cl2,cl1)
                    report.append((id1,id2,c12+c21))
                    msg.append( ' %s vs %s : %s + %s = %s -- %s' %  (id1, id2, c12, c21, c12+c21, cl1.hates(cl2)))
        msg = 'Wedge final clusters for %s: \n' % str(wedge_thrsh) + '\n'.join(msg)
        if not bconfig.DEBUG_WEDGE_OUTPUT and bconfig.DEBUG_WEDGE_PRINT_FINAL_CLUSTER_COMPATIBILITIES:
            print
            print msg
            print
        wedge_print(msg)


    restore_cluster_set(cluster_set)

    if bconfig.DEBUG_CHECKS:
        assert cluster_set._debug_test_hate_relation()
        assert cluster_set._debug_duplicated_recs()

    if report_cluster_status:
        destfile = '/tmp/baistats/cluster_status_report_pid_%s_lastname_%s_thrsh_%s' % (str(PID()),str(cluster_set.last_name),str(wedge_thrsh))
        f = open(destfile, 'w')
        SER.dump([wedge_thrsh,cluster_set.last_name,report,cluster_set.num_all_bibs],f)
        f.close()
    gc.collect()

def _decide(cl1, cl2):
    score1 = _compare_to(cl1, cl2)
    score2 = _compare_to(cl2, cl1)
    s = score1 + score2
    wedge_print("Wedge: _decide (%f+%f) = %f cmp to %f" % (score1,score2,s,wedge_thrsh))
    return s > wedge_thrsh, s

def _compare_to(cl1, cl2):
    pointers = [cl1.out_edges[v] for v in cl2.bibs]

    assert pointers, PID()+"Wedge: no edges between clusters!"
    vals, probs = zip(*pointers)

    wedge_print("Wedge: _compare_to: vals = %s, probs = %s" % (str(vals), str(probs)))

    if SP_QUARREL in vals:
        ret = 0.
        wedge_print('Wedge: _compare_to: - edge present, returning 0')

    elif SP_CONFIRM in vals:
        ret = 0.5
        wedge_print('Wedge: _compare_to: + edge present, returning 0.5')

    else:

        avg = sum(vals) / len(vals)
        if avg > eps:
            nvals = [(val / avg) ** prob for val, prob in pointers]
        else:
            wedge_print("Wedge: _compare_to: vals too low to compare, skipping")
            return 0

        coeff = _gini(nvals)

        weight = sum(starmap(mul, pointers)) / sum(probs)

        ret = (coeff * weight) / 2.

        assert ret <= 0.5, PID()+'COMPARE_TO big value returned ret %s coeff %s weight %s nvals %s vals %s prob %s' % (ret, coeff, weight, nvals, vals, probs)

        wedge_print("Wedge: _compare_to: coeff = %f, weight = %f, retval = %f" % (coeff, weight, ret))

    return ret

def _gini(arr):
    arr = sorted(arr, reverse=True)
    dividend = sum(starmap(mul, izip(arr, xrange(1, 2 * len(arr), 2))))
    divisor = len(arr) * sum(arr)
    return float(dividend) / divisor

def _compare_to_final_bounds(score1, score2):
    return score1 + score2 > bconfig.WEDGE_THRESHOLD

def _edge_sorting(edge):
    '''
    probability + certainty / 10
    '''
    return edge[2][0] + edge[2][1] / 10.

def do_wedge(cluster_set, deep_debug=False):
    '''
    Rearranges the cluster_set acoarding to be values in the probability_matrix.
    The deep debug option will produce a lot of output. Avoid using it with more
    than 20 bibs in the cluster set.
    '''

    bib_map = create_bib_2_cluster_dict(cluster_set)

    plus_edges, minus_edges, edges = group_edges(cluster_set)

    interval = 1000
    for i, (bib1, bib2) in enumerate(plus_edges):
        if (i % interval) == 0:
            update_status(float(i) / len(plus_edges), "Agglomerating obvious clusters...")
        cl1 = bib_map[bib1]
        cl2 = bib_map[bib2]
        if cl1 != cl2 and not cl1.hates(cl2):
            join(cl1, cl2)
            cluster_set.clusters.remove(cl2)
            for v in cl2.bibs:
                bib_map[v] = cl1
    update_status_final("Agglomerating obvious clusters done.")

    interval = 1000
    for i, (bib1, bib2) in enumerate(minus_edges):
        if (i % interval) == 0:
            update_status(float(i) / len(minus_edges), "Dividing obvious clusters...")
        cl1 = bib_map[bib1]
        cl2 = bib_map[bib2]
        if cl1 != cl2 and not cl1.hates(cl2):
            cl1.quarrel(cl2)
    update_status_final("Dividing obvious clusters done.")

    bibauthor_print("Sorting the value edges.")
    edges = sorted(edges, key=_edge_sorting, reverse=True)

    interval = 500000
    wedge_print("Wedge: New wedge, %d edges." % len(edges))
    for current, (v1, v2, unused) in enumerate(edges):
        if (current % interval) == 0:
            update_status(float(current) / len(edges), "Wedge...")

        assert unused != '+' and unused != '-', PID()+"Signed edge after filter!"
        cl1 = bib_map[v1]
        cl2 = bib_map[v2]
        idcl1 = cluster_set.clusters.index(cl1)
        idcl2 = cluster_set.clusters.index(cl2)

        #keep the ids low!
        if idcl1 > idcl2:
            idcl1, idcl2 = idcl2, idcl1
            cl1, cl2 = cl2, cl1

        wedge_print("Wedge: popped new edge: Verts = (%s,%s) from (%s, %s) Value = (%f, %f)" % (idcl1, idcl2, v1, v2, unused[0], unused[1]))

        if cl1 != cl2 and not cl1.hates(cl2):
            if deep_debug:
                export_to_dot(cluster_set, "/tmp/%s%d.dot" % (cluster_set.last_name, current), bib_map, (v1, v2, unused))

            decision, value = _decide(cl1, cl2)
            if decision:
                wedge_print("Wedge: Joined %s to %s with %s"% (idcl1, idcl2, value))
                join(cl1, cl2)
                cluster_set.clusters.remove(cl2)
                for v in cl2.bibs:
                    bib_map[v] = cl1
            else:
                wedge_print("Wedge: Quarreled %s from %s with %s " %  (idcl1, idcl2, value))
                cl1.quarrel(cl2)
        elif cl1 == cl2:
            wedge_print("Wedge: Clusters already joined! (%s,%s)" % (idcl1, idcl2))
        else:
            wedge_print("Wedge: Clusters hate each other! (%s,%s)" % (idcl1, idcl2))

    update_status_final("Wedge done.")
    bibauthor_print("")

    if deep_debug:
        export_to_dot(cluster_set, "/tmp/%sfinal.dot" % cluster_set.last_name, bib_map)

def meld_edges(p1, p2):
    '''
    Creates one out_edges set from two.
    The operation is associative and commutative.
    The objects are: (out_edges for in a cluster, number of vertices in the same cluster)
    '''
    out_edges1, verts1 = p1
    out_edges2, verts2 = p2
    assert verts1 > 0 and verts2 > 0, PID()+'MELD_EDGES: verts problem %s %s ' % (str(verts1), str(verts2))
    vsum = verts1 + verts2
    invsum = 1. / vsum

    special_numbers = Bib_matrix.special_numbers #local reference optimization

    def median(e1, e2):

    #dirty optimization, should check if value is in dictionary instead
    # if e1[0] in special_numbers: return e1
    # if e2[0] in special_numbers: return e2
        if e1[0] < 0:
            assert e1[0] in special_numbers, "MELD_EDGES: wrong value for median? %s" % str(e1)
            return e1
        if e2[0] < 0:
            assert e2[0] in special_numbers, "MELD_EDGES: wrong value for median? %s" % str(e2)
            return e2

        i1 = e1[1] * verts1
        i2 = e2[1] * verts2
        inter_cert = i1 + i2
        inter_prob = e1[0] * i1 + e2[0] * i2
        return (inter_prob / inter_cert, inter_cert * invsum)

    assert len(out_edges1) == len(out_edges2), "Invalid arguments for meld edges"
    size = len(out_edges1)

    result = numpy.ndarray(shape=(size, 2), dtype=float, order='C')
    for i in xrange(size):
        result[i] = median(out_edges1[i], out_edges2[i])
        assert (result[i][0] >= 0 and result[i][0] <= 1) or result[i][0] in Bib_matrix.special_numbers, PID()+'MELD_EDGES: value %s' % result[i]
        assert (result[i][1] >= 0 and result[i][1] <= 1) or result[i][1] in Bib_matrix.special_numbers, PID()+'MELD_EDGES: compat %s' % result[i]

    return (result, vsum)

def convert_cluster_set(cs, prob_matr):
    '''
    Convertes a normal cluster set to a wedge clsuter set.
    @param cs: a cluster set to be converted
    @param type: cluster set
    @return: a mapping from a number to a bibrefrec.
    '''
    gc.disable()

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

    assert len(result_mapping) == len(set(result_mapping)), PID()+"Cluster set conversion failed"
    assert len(result_mapping) == cs.num_all_bibs, PID()+"Cluster set conversion failed"

    cs.new2old = result_mapping

    # step 2:
    #    + Using the prob matrix create a vector values to all other bibs.
    #    + Meld those vectors into one for each cluster.

    special_symbols = Bib_matrix.special_symbols #locality optimization

    interval = 10000
    for current, c1 in enumerate(cs.clusters):
        if (current % interval) == 0:
            update_status(float(current) / len(cs.clusters), "Converting the cluster set...")

        assert len(c1.bibs) > 0, PID()+"Empty cluster send to wedge"
        pointers = []

        for v1 in c1.bibs:
            pointer = numpy.ndarray(shape=(len(result_mapping), 2), dtype=float, order='C')
            pointer.fill(special_symbols[None])
            rm = result_mapping[v1] #locality optimization
            for c2 in cs.clusters:
                if c1 != c2 and not c1.hates(c2):
                    for v2 in c2.bibs:
                        val = prob_matr[rm, result_mapping[v2]]
                        try:
                            numb = special_symbols[val]
                            val = (numb, numb)
                        except KeyError:
                            pass
                        assert len(val) == 2, "Edge coding failed"
                        pointer[v2] = val
            pointers.append((pointer, 1))
        c1.out_edges = reduce(meld_edges, pointers)[0]

    update_status_final("Converting the cluster set done.")
    gc.enable()

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
    gc.disable()
    interval = 1000
    for current, cl1 in enumerate(cs.clusters):
        if (current % interval) == 0:
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
    gc.enable()
    return plus, minus, pairs


def join(cl1, cl2):
    '''
    Joins two clusters from a cluster set in the first.
    '''
    cl1.out_edges = meld_edges((cl1.out_edges, len(cl1.bibs)),
                               (cl2.out_edges, len(cl2.bibs)))[0]
    cl1.bibs += cl2.bibs

    assert not cl1.hates(cl1), PID()+"Joining hateful clusters"
    assert not cl2.hates(cl2), PID()+"Joining hateful clusters2"

    cl1.hate |= cl2.hate
    for cl in cl2.hate:
        cl.hate.remove(cl2)
        cl.hate.add(cl1)


def export_to_dot(cs, fname, graph_info, extra_edge=None):
    from invenio.legacy.bibauthorid.dbinterface import get_name_by_bibrecref

    fptr = open(fname, "w")
    fptr.write("graph wedgy {\n")
    fptr.write("    overlap=prism\n")

    for idx, bib in enumerate(graph_info):
        fptr.write('    %d [color=black label="%s"];\n' % (idx, get_name_by_bibrecref(idx)))

    if extra_edge:
        v1, v2, (prob, cert) = extra_edge
        fptr.write('    %d -- %d [color=green label="p: %.2f, c: %.2f"];\n' % (v1, v2, prob, cert))

    for clus in cs.clusters:
        fptr.write("    %s [color=blue];\n" % " -- ".join(str(x) for x in clus.bibs))

        fptr.write("".join("    %d -- %d [color=red]\n" % (b1, b2)
                      for b1 in clus.bibs for h in clus.hate for b2 in h.bibs))

    fptr.write("}")
