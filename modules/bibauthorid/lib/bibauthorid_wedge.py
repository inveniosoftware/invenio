# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2013 CERN.
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

from invenio import bibauthorid_config as bconfig
from itertools import izip, starmap
from operator import mul
from multiprocessing import Process
from invenio.bibauthorid_general_utils import sortFileInPlace
from invenio.bibauthorid_logutils import Logger

from invenio.bibauthorid_prob_matrix import ProbabilityMatrix, Bib_matrix
import numpy
# mport cPickle as SER
import msgpack as SER

import gzip as filehandler
import h5py

import gc

import cPickle

SP_NUMBERS = Bib_matrix.special_numbers
SP_SYMBOLS = Bib_matrix.special_symbols
SP_CONFIRM = Bib_matrix.special_symbols['+']
SP_QUARREL = Bib_matrix.special_symbols['-']

eps = 0.01
edge_cut_prob = ''
wedge_thrsh = ''
h5file = None


logger = Logger("wedge", verbose=bconfig.DEBUG_WEDGE_OUTPUT)

import os
PID = lambda: str(os.getpid())

import pyximport
pyximport.install()
from invenio.bibauthorid_meld_edges import meld_edges


def wedge(cluster_set, report_cluster_status=False, force_wedge_thrsh=False):
    # The lower bound of the edges being processed by the wedge algorithm.
    global edge_cut_prob
    global wedge_thrsh

    if not force_wedge_thrsh:
        edge_cut_prob = bconfig.WEDGE_THRESHOLD / 4.
        wedge_thrsh = bconfig.WEDGE_THRESHOLD
    else:
        edge_cut_prob = force_wedge_thrsh / 4.
        wedge_thrsh = force_wedge_thrsh

    matr = ProbabilityMatrix(cluster_set.last_name)
    matr.load()

    global h5file
    h5filepath = bconfig.TORTOISE_FILES_PATH + 'wedge_cache_' + str(PID())
    h5file = h5py.File(h5filepath)

    convert_cluster_set(cluster_set, matr)
    del matr  # be sure that this is the last reference!

    do_wedge(cluster_set)

    report = []
    if report_cluster_status:
        msg = []
        for cl1 in cluster_set.clusters:
            for cl2 in cluster_set.clusters:
                if cl2 > cl1:
                    id1 = cluster_set.clusters.index(cl1)
                    id2 = cluster_set.clusters.index(cl2)
                    c12 = _compare_to(cl1, cl2)
                    c21 = _compare_to(cl2, cl1)
                    report.append((id1, id2, c12 + c21))
                    msg.append(' %s vs %s : %s + %s = %s -- %s' % (id1, id2, c12, c21, c12 + c21, cl1.hates(cl2)))
        msg = 'Wedge final clusters for %s: \n' % str(wedge_thrsh) + '\n'.join(msg)
        logger.log(msg)

    restore_cluster_set(cluster_set)

    if bconfig.DEBUG_CHECKS:
        assert cluster_set._debug_test_hate_relation()
        assert cluster_set._debug_duplicated_recs()

    if report_cluster_status:
        destfile = '/tmp/baistats/cluster_status_report_pid_%s_lastname_%s_thrsh_%s' % (
            str(PID()), str(cluster_set.last_name), str(wedge_thrsh))
        f = filehandler.open(destfile, 'w')
        SER.dump([wedge_thrsh, cluster_set.last_name, report, cluster_set.num_all_bibs], f)
        f.close()
    gc.collect()

    h5file.close()
    os.remove(h5filepath)


def _decide(cl1, cl2):
    score1 = _compare_to(cl1, cl2)
    score2 = _compare_to(cl2, cl1)
    s = score1 + score2
    logger.log("Wedge: _decide (%f+%f) = %f cmp to %f" % (score1, score2, s, wedge_thrsh))
    return s > wedge_thrsh, s


def _compare_to(cl1, cl2):
    cl1_out_edges = h5file[str(id(cl1))]
    pointers = [cl1_out_edges[v] for v in cl2.bibs]

    assert pointers, PID() + "Wedge: no edges between clusters!"
    vals, probs = zip(*pointers)

    logger.log("Wedge: _compare_to: vals = %s, probs = %s" % (str(vals), str(probs)))

    if SP_QUARREL in vals:
        ret = 0.
        logger.log('Wedge: _compare_to: - edge present, returning 0')

    elif SP_CONFIRM in vals:
        ret = 0.5
        logger.log('Wedge: _compare_to: + edge present, returning 0.5')

    else:

        avg = sum(vals) / len(vals)
        if avg > eps:
            nvals = [(val / avg) ** prob for val, prob in pointers]
        else:
            logger.log("Wedge: _compare_to: vals too low to compare, skipping")
            return 0

        coeff = _gini(nvals)

        weight = sum(starmap(mul, pointers)) / sum(probs)

        ret = (coeff * weight) / 2.

        assert ret <= 0.5, PID() + 'COMPARE_TO big value returned ret %s coeff %s weight %s nvals %s vals %s prob %s' % (
            ret, coeff, weight, nvals, vals, probs)

        logger.log("Wedge: _compare_to: coeff = %f, weight = %f, retval = %f" % (coeff, weight, ret))

    return ret


def _gini(arr):
    arr.sort(reverse=True)
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


def _pack_vals(v):
    return str(v[0]) + ';' + str(v[1]) + ';' + str(v[2][0]) + ';' + str(v[2][1]) + '\n'


def _unpack_vals(s):
    v = s.strip().split(';')
    return int(v[0]), int(v[1]), (float(v[2]), float(v[3]))


def do_wedge(cluster_set, deep_debug=False):
    '''
    Rearranges the cluster_set acoarding to be values in the probability_matrix.
    The deep debug option will produce a lot of output. Avoid using it with more
    than 20 bibs in the cluster set.
    '''

    bib_map = create_bib_2_cluster_dict(cluster_set)
    original_process_id = PID()
    # remember to close the files!
    # plus_edges_fp, len_plus, minus_edges_fp, len_minus, edges_fp, len_edges = group_sort_edges(cluster_set)

    p = Process(target=group_sort_edges, args=(cluster_set, original_process_id))
    p.start()
    p.join()

    plus_edges_fp = open(bconfig.TORTOISE_FILES_PATH + '/wedge_edges_cache_p_' + str(original_process_id), 'r')
    minus_edges_fp = open(bconfig.TORTOISE_FILES_PATH + '/wedge_edges_cache_m_' + str(original_process_id), 'r')
    edges_fp = open(bconfig.TORTOISE_FILES_PATH + '/wedge_edges_cache_e_' + str(original_process_id), 'r')
    data_fp = open(bconfig.TORTOISE_FILES_PATH + '/wedge_edges_cache_data_' + str(original_process_id), 'r')

    len_plus, len_minus, len_edges = cPickle.load(data_fp)
    data_fp.close()

    interval = 1000
    for i, s in enumerate(plus_edges_fp):
        bib1, bib2, unused = _unpack_vals(s)
        if (i % interval) == 0:
            logger.update_status(float(i) / len_plus, "Agglomerating obvious clusters...")
        cl1 = bib_map[bib1]
        cl2 = bib_map[bib2]
        if cl1 != cl2 and not cl1.hates(cl2):
            join(cl1, cl2)
            cluster_set.clusters.remove(cl2)
            for v in cl2.bibs:
                bib_map[v] = cl1
    logger.update_status_final("Agglomerating obvious clusters done.")

    interval = 1000
    for i, s in enumerate(minus_edges_fp):
        bib1, bib2, unused = _unpack_vals(s)
        if (i % interval) == 0:
            logger.update_status(float(i) / len_minus, "Dividing obvious clusters...")
        cl1 = bib_map[bib1]
        cl2 = bib_map[bib2]
        if cl1 != cl2 and not cl1.hates(cl2):
            cl1.quarrel(cl2)
    logger.update_status_final("Dividing obvious clusters done.")

    interval = 50000
    logger.log("Wedge: New wedge, %d edges." % len_edges)
    current = -1
    for s in edges_fp:
        v1, v2, unused = _unpack_vals(s)
        current += 1
        if (current % interval) == 0:
            logger.update_status(float(current) / len_edges, "Wedge...")

        assert unused != '+' and unused != '-', PID() + "Signed edge after filter!"
        cl1 = bib_map[v1]
        cl2 = bib_map[v2]
        # try using object ids instead of index to boost performances
        # idcl1 = cluster_set.clusters.index(cl1)
        # idcl2 = cluster_set.clusters.index(cl2)
        idcl1 = id(cl1)
        idcl2 = id(cl2)

        # keep the ids low!
        if idcl1 > idcl2:
            idcl1, idcl2 = idcl2, idcl1
            cl1, cl2 = cl2, cl1

        logger.log(
            "Wedge: popped new edge: Verts = (%s,%s) from (%s, %s) Value = (%f, %f)" %
            (idcl1, idcl2, v1, v2, unused[0], unused[1]))

        if cl1 != cl2 and not cl1.hates(cl2):
            if deep_debug:
                export_to_dot(
                    cluster_set, "/tmp/%s%d.dot" %
                    (cluster_set.last_name, current), bib_map, (v1, v2, unused))

            decision, value = _decide(cl1, cl2)
            if decision:
                logger.log("Wedge: Joined %s to %s with %s" % (idcl1, idcl2, value))
                join(cl1, cl2)
                cluster_set.clusters.remove(cl2)
                for v in cl2.bibs:
                    bib_map[v] = cl1
            else:
                logger.log("Wedge: Quarreled %s from %s with %s " % (idcl1, idcl2, value))
                cl1.quarrel(cl2)
        elif cl1 == cl2:
            logger.log("Wedge: Clusters already joined! (%s,%s)" % (idcl1, idcl2))
        else:
            logger.log("Wedge: Clusters hate each other! (%s,%s)" % (idcl1, idcl2))

    logger.update_status_final("Wedge done.")
    logger.log("")

    if deep_debug:
        export_to_dot(cluster_set, "/tmp/%sfinal.dot" % cluster_set.last_name, bib_map)

    plus_edges_fp.close()
    minus_edges_fp.close()
    edges_fp.close()
    data_fp.close()

    try:
        os.remove(bconfig.TORTOISE_FILES_PATH + '/wedge_edges_cache_p_' + str(original_process_id))
        os.remove(bconfig.TORTOISE_FILES_PATH + '/wedge_edges_cache_m_' + str(original_process_id))
        os.remove(bconfig.TORTOISE_FILES_PATH + '/wedge_edges_cache_e_' + str(original_process_id))
        os.remove(bconfig.TORTOISE_FILES_PATH + '/wedge_edges_cache_data_' + str(original_process_id))
    except:
        pass


def convert_cluster_set(cs, prob_matr):
    '''
    Convertes a normal cluster set to a wedge cluster set.
    @param cs: a cluster set to be converted
    @param type: cluster set
    @return: a mapping from a number to a bibrefrec.
    '''
    # gc.disable()

    # step 1:
    #    + Assign a number to each bibrefrec.
    #    + Replace the arrays of bibrefrecs with arrays of numbers.
    #    + Store the result and prepare it to be returned.
    result_mapping = list()
    for clus in cs.clusters:
        start = len(result_mapping)
        result_mapping += list(clus.bibs)
        end = len(result_mapping)
        clus.bibs = range(start, end)

    assert len(result_mapping) == len(set(result_mapping)), PID() + "Cluster set conversion failed"
    assert len(result_mapping) == cs.num_all_bibs, PID() + "Cluster set conversion failed"

    cs.new2old = result_mapping

    # step 2:
    #    + Using the prob matrix create a vector values to all other bibs.
    #    + Meld those vectors into one for each cluster.

    special_symbols = Bib_matrix.special_symbols  # locality optimization
    pb_getitem_numeric = prob_matr.getitem_numeric

    interval = 100
    gc.set_threshold(100, 100, 100)
    current = -1
    real_pointer = None
    try:
        for c1 in cs.clusters:
            gc.collect()
            current += 1
            if (current % interval) == 0:
                logger.update_status(float(current) / len(cs.clusters), "Converting the cluster set...")

            assert len(c1.bibs) > 0, PID() + "Empty cluster send to wedge"
            pointers = list()

            for v1 in c1.bibs:
                pointer = list()
                index = list()
                rm = result_mapping[v1]  # locality optimization
                for c2 in cs.clusters:
                    if c1 != c2 and not c1.hates(c2):
                        pointer += [pb_getitem_numeric((rm, result_mapping[v2])) for v2 in c2.bibs]
                        index += c2.bibs
                if index and pointer:
                    real_pointer = numpy.ndarray(shape=(len(result_mapping), 2), dtype=float, order='C')
                    real_pointer.fill(special_symbols[None])
                    real_pointer[index] = pointer
                    pointers.append((real_pointer, 1))

            if pointers:
                out_edges = reduce(meld_edges, pointers)[0]
                h5file.create_dataset(str(id(c1)), (len(out_edges), 2), 'f')
                dset = h5file[str(id(c1))]
                dset[:] = out_edges
            else:
                h5file.create_dataset(str(id(c1)), (len(cs.clusters), 2), 'f')

    except Exception as e:
        raise Exception("""Error happened in convert_cluster_set with
                        v1: %s,
                        real_pointer: %s,
                        pointer: %s,
                        pointers: %s,
                        result_mapping: %s, index: %s,
                        len(real_pointer): %s,
                        len(pointer): %s,
                        len(pointers):  %s,
                        original_exception: %s
                        """ % (str(v1), str(real_pointer), str(pointer), str(pointers),
                               str(result_mapping), str(index),
                        str(len(real_pointer)), str(len(pointer)),
                        str(len(pointers)), str(e)))

    logger.update_status_final("Converting the cluster set done.")
    # gc.enable()


def restore_cluster_set(cs):
    for cl in cs.clusters:
        cl.bibs = set(cs.new2old[b] for b in cl.bibs)
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


def group_sort_edges(cs, original_process_id):
    logger.log("group_sort_edges spowned by %s" % original_process_id)

    plus_fp = open(bconfig.TORTOISE_FILES_PATH + '/wedge_edges_cache_p_' + str(original_process_id), 'w')
    minus_fp = open(bconfig.TORTOISE_FILES_PATH + '/wedge_edges_cache_m_' + str(original_process_id), 'w')
    pairs_fp = open(bconfig.TORTOISE_FILES_PATH + '/wedge_temp_edges_cache_e_' + str(original_process_id), 'w')
    data_fp = open(bconfig.TORTOISE_FILES_PATH + '/wedge_edges_cache_data_' + str(original_process_id), 'w')

    plus_count = 0
    minus_count = 0
    pairs_count = 0

    default_val = [0., 0.]
    # gc.disable()
    interval = 1000
    current = -1
    for cl1 in cs.clusters:
        current += 1
        if (current % interval) == 0:
            logger.update_status(float(current) / len(cs.clusters), "Grouping all edges...")

        bib1 = tuple(cl1.bibs)[0]
        pointers = h5file[str(id(cl1))]
        for bib2 in xrange(len(h5file[str(id(cl1))])):
            val = pointers[bib2]
            # if val[0] not in Bib_matrix.special_numbers:
            # optimization: special numbers are assumed to be negative
            if val[0] >= 0:

                if val[0] > edge_cut_prob:
                    pairs_count += 1
                    pairs_fp.write(_pack_vals((bib1, bib2, val)))

            elif val[0] == Bib_matrix.special_symbols['+']:
                plus_count += 1
                plus_fp.write(_pack_vals((bib1, bib2, default_val)))

            elif val[0] == Bib_matrix.special_symbols['-']:
                minus_count += 1
                minus_fp.write(_pack_vals((bib1, bib2, default_val)))
            else:
                assert val[0] == Bib_matrix.special_symbols[None], "Invalid Edge"

    logger.update_status_final("Finished with the edge grouping.")

    plus_fp.close()
    minus_fp.close()
    pairs_fp.close()

    logger.log("Positive edges: %d, Negative edges: %d, Value edges: %d."
               % (plus_count, minus_count, pairs_count))
    # gc.enable()
    logger.log("Sorting in-file value edges.")
    sortFileInPlace(bconfig.TORTOISE_FILES_PATH + '/wedge_temp_edges_cache_e_' + str(original_process_id),
                    bconfig.TORTOISE_FILES_PATH + '/wedge_edges_cache_e_' + str(original_process_id),
                    lambda x: _edge_sorting(_unpack_vals(x)), reverse=True)

    os.remove(bconfig.TORTOISE_FILES_PATH + '/wedge_temp_edges_cache_e_' + str(original_process_id))

    logger.log("Dumping egdes data to file...")
    cPickle.dump((plus_count, minus_count, pairs_count), data_fp)
    logger.log("Grouping and sorting of edges is done!")
    data_fp.close()


def join(cl1, cl2):
    '''
    Joins two clusters from a cluster set in the first.
    '''
    cl1_out_edges = h5file[str(id(cl1))]
    cl2_out_edges = h5file[str(id(cl2))]
    cl1_out_edges[:] = meld_edges((cl1_out_edges, len(cl1.bibs)),
                                  (cl2_out_edges, len(cl2.bibs)))[0]
    cl1.bibs += cl2.bibs

    assert not cl1.hates(cl1), PID() + "Joining hateful clusters"
    assert not cl2.hates(cl2), PID() + "Joining hateful clusters2"

    cl1.hate |= cl2.hate
    for cl in cl2.hate:
        cl.hate.remove(cl2)
        cl.hate.add(cl1)


def export_to_dot(cs, fname, graph_info, extra_edge=None):
    from invenio.bibauthorid_dbinterface import get_name_by_bibref

    fptr = open(fname, "w")
    fptr.write("graph wedgy {\n")
    fptr.write("    overlap=prism\n")

    for idx, bib in enumerate(graph_info):
        fptr.write('    %d [color=black label="%s"];\n' % (idx, get_name_by_bibref(idx)))

    if extra_edge:
        v1, v2, (prob, cert) = extra_edge
        fptr.write('    %d -- %d [color=green label="p: %.2f, c: %.2f"];\n' % (v1, v2, prob, cert))

    for clus in cs.clusters:
        fptr.write("    %s [color=blue];\n" % " -- ".join(str(x) for x in clus.bibs))

        fptr.write("".join("    %d -- %d [color=red]\n" % (b1, b2)
                           for b1 in clus.bibs for h in clus.hate for b2 in h.bibs))

    fptr.write("}")
