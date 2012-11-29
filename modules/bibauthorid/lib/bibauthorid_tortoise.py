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
from datetime import datetime
import os
import cPickle

from itertools import groupby, chain
from invenio.bibauthorid_general_utils import update_status, update_status_final

from invenio.bibauthorid_cluster_set import delayed_cluster_sets_from_marktables
from invenio.bibauthorid_cluster_set import delayed_cluster_sets_from_personid
from invenio.bibauthorid_wedge import wedge
from invenio.bibauthorid_name_utils import generate_last_name_cluster_str
from invenio.bibauthorid_backinterface import empty_results_table
from invenio.bibauthorid_backinterface import remove_result_cluster
from invenio.bibauthorid_general_utils import bibauthor_print
from invenio.bibauthorid_prob_matrix import prepare_matirx
from invenio.bibauthorid_scheduler import schedule, matrix_coefs
from invenio.bibauthorid_least_squares import to_function as create_approx_func
from math import isnan

import multiprocessing as mp

#python2.4 compatibility
from invenio.bibauthorid_general_utils import bai_all as all

'''
    There are three main entry points to tortoise

    i) tortoise
        Performs disambiguation iteration.
        The arguemnt pure indicates whether to use
        the claims and the rejections or not.
        Use pure=True only to test the accuracy of tortoise.

    ii) tortoise_from_scratch
        NOT RECOMMENDED!
        Use this function only if you have just
        installed invenio and this is your first
        disambiguation or if personid is broken.

    iii) tortoise_last_name
        Computes the clusters for only one last name
        group. Is is primary used for testing. It
        may also be used to fix a broken last name
        cluster. It does not involve multiprocessing
        so it is convinient to debug with pdb.
'''

# Exit codes:
# The standard ones are not well documented
# so we are using random numbers.

def tortoise_from_scratch():
    bibauthor_print("Preparing cluster sets.")
    cluster_sets, _lnames, sizes = delayed_cluster_sets_from_marktables()
    bibauthor_print("Building all matrices.")
    exit_statuses = schedule_create_matrix(
        cluster_sets,
        sizes,
        force=True)
    assert len(exit_statuses) == len(cluster_sets)
    assert all(stat == os.EX_OK for stat in exit_statuses)

    empty_results_table()

    bibauthor_print("Preparing cluster sets.")
    cluster_sets, _lnames, sizes = delayed_cluster_sets_from_marktables()
    bibauthor_print("Starting disambiguation.")
    exit_statuses = schedule_wedge_and_store(
        cluster_sets,
        sizes)
    assert len(exit_statuses) == len(cluster_sets)
    assert all(stat == os.EX_OK for stat in exit_statuses)


def tortoise(pure=False,
             force_matrix_creation=False,
             skip_matrix_creation=False,
             last_run=None):
    assert not force_matrix_creation or not skip_matrix_creation
    # The computation must be forced in case we want
    # to compute pure results
    force_matrix_creation = force_matrix_creation or pure

    if not skip_matrix_creation:
        bibauthor_print("Preparing cluster sets.")
        clusters, _lnames, sizes = delayed_cluster_sets_from_personid(pure, last_run)
        bibauthor_print("Building all matrices.")
        exit_statuses = schedule_create_matrix(
            clusters,
            sizes,
            force=force_matrix_creation)
        assert len(exit_statuses) == len(clusters)
        assert all(stat == os.EX_OK for stat in exit_statuses)

    bibauthor_print("Preparing cluster sets.")
    clusters, _lnames, sizes = delayed_cluster_sets_from_personid(pure, last_run)
    bibauthor_print("Starting disambiguation.")
    exit_statuses = schedule_wedge_and_store(
        clusters,
        sizes)
    assert len(exit_statuses) == len(clusters)
    assert all(stat == os.EX_OK for stat in exit_statuses)


def tortoise_last_name(name, from_mark=False, pure=False):
    bibauthor_print('Start working on %s' % name)
    assert not(from_mark and pure)

    lname = generate_last_name_cluster_str(name)

    if from_mark:
        bibauthor_print(' ... from mark!')
        clusters, lnames, sizes = delayed_cluster_sets_from_marktables([lname])
        bibauthor_print(' ... delayed done')
    else:
        bibauthor_print(' ... from pid, pure')
        clusters, lnames, sizes = delayed_cluster_sets_from_personid(pure)
        bibauthor_print(' ... delayed pure done!')

#    try:
    idx = lnames.index(lname)
    cluster = clusters[idx]
    size = sizes[idx]
    bibauthor_print("Found, %s(%s). Total number of bibs: %d." % (name, lname, size))
    cluster_set = cluster()
    create_matrix(cluster_set, True)
    wedge_and_store(cluster_set)
#    except IndexError:
#        bibauthor_print("Sorry, %s(%s) not found in the last name clusters" % (name, lname))

def _collect_statistics_lname_coeff(params):
    lname = params[0]
    coeff = params[1]

    clusters, lnames, sizes = delayed_cluster_sets_from_marktables([lname])
    idx = lnames.index(lname)
    cluster = clusters[idx]
    size = sizes[idx]
    bibauthor_print("Found, %s. Total number of bibs: %d." % (lname, size))
    cluster_set = cluster()
    create_matrix(cluster_set, False)

    bibs = cluster_set.num_all_bibs
    expected = bibs * (bibs - 1) / 2
    bibauthor_print("Start working on %s. Total number of bibs: %d, "
                    "maximum number of comparisons: %d"
                    % (cluster_set.last_name, bibs, expected))

    result = wedge(cluster_set, True, coeff)
    remove_result_cluster(cluster_set.last_name)
    return (coeff, lname, result)

def _create_matrix(lname):

    clusters, lnames, sizes = delayed_cluster_sets_from_marktables([lname])
    idx = lnames.index(lname)
    cluster = clusters[idx]
    size = sizes[idx]
    bibauthor_print("Found, %s. Total number of bibs: %d." % (lname, size))
    cluster_set = cluster()
    create_matrix(cluster_set, True)

    bibs = cluster_set.num_all_bibs
    expected = bibs * (bibs - 1) / 2
    bibauthor_print("Start working on %s. Total number of bibs: %d, "
                    "maximum number of comparisons: %d"
                    % (cluster_set.last_name, bibs, expected))
    cluster_set.store()

def tortoise_tweak_coefficient(lastnames, min_coef, max_coef, stepping, destfile):
    bibauthor_print('Coefficient tweaking!')
    bibauthor_print('Cluster sets from mark...')

    lnames = set([generate_last_name_cluster_str(n) for n in lastnames])
    coefficients = [x/100. for x in range(int(min_coef*100),int(max_coef*100),int(stepping*100))]

    pool = mp.Pool()

    pool.map(_create_matrix, lnames)
    ress = pool.map(_collect_statistics_lname_coeff, ((x,y) for x in lnames for y in coefficients))

    f = open(destfile, 'w')
    cPickle.dump(ress,f)
    f.close()

def tortoise_coefficient_statistics(statfile, parsed_output=None):
    f = open(statfile,'r')
    stats = cPickle.load(f)
    f.close()

    # general statistics: number of tests, different coefficients, different clusters
    total_tests = len(stats)
    used_coeffs = set(x[0] for x in stats)
    user_clusters = set(x[1] for x in stats)
    assert total_tests == len(used_coeffs) * len(user_clusters)

    update_status(0, 'Creating grouped stats...')
    grouped_stats = groupby(sorted(stats), lambda x: x[0])
    update_status_final('Done creating grouped stats')
    update_status(0, 'Creating cluster sizes per coefficient...')
    cluster_sizes_per_coeff = [ (g[0], [len(k[2]) for k in g[1]] ) for g in grouped_stats]
    update_status_final('Done creating cluster sizes per coefficient')
    # average number of clusters per coefficient
    update_status(0, 'Creating avg clusters per coeff...')
    avg_clusters_per_coeff = [ (k[0], sum(k[1])/len(k[1])) for k in cluster_sizes_per_coeff ]
    update_status_final('Done creating avg clusters per coeff')

    edges_min_max_avg_per_coeff = []
    maxlen = float(len(used_coeffs))
    grouped_stats = groupby(sorted(stats), lambda x: x[0])
    for i,coeff in enumerate(grouped_stats):
        update_status(i/maxlen, 'Computing adv stats...')
        edgeslist =  [ [x[2] for x in cluster[2]] for cluster in coeff[1] ]
        minedges = [min(x) for x in edgeslist if x]
        maxedges = [max(x) for x in edgeslist if x]
        avgs = [sum([p for p in x if not isnan(p)])/float(len(x))  for x in edgeslist if x]

        minedge = min(minedges)
        maxedge = max(maxedges)
        av = float(len(avgs))
        avg = sum(avg/av for avg in avgs)

        edges_min_max_avg_per_coeff.append((coeff[0],minedge,maxedge,avg))


    print "Total tests: ", total_tests
    print "Used coefficients: ", used_coeffs
    print "Used clusters: ", len(user_clusters)
    print "Average clusters per coefficient: "
    for x in sorted(avg_clusters_per_coeff, key=lambda x: x[0]):
        print '  - ', x
    print "Edges stats per coefficient: "
    for x in edges_min_max_avg_per_coeff:
        print ' - ', 'Coeff: ', x[0], 'Min: ', x[1], " Max: ", x[2], " Avg: ", x[3]

    if parsed_output:
        f = open(parsed_output, 'w')
        d = {'edges_coeff_min_max_avg':edges_min_max_avg_per_coeff, 'avg_clust_per_coeff':avg_clusters_per_coeff}
        cPickle.dump(d, f)
        f.close()

def create_matrix(cluster_set, force):
    bibs = cluster_set.num_all_bibs
    expected = bibs * (bibs - 1) / 2
    bibauthor_print("Start building matrix for %s. Total number of bibs: %d, "
                    "maximum number of comparisons: %d"
                    % (cluster_set.last_name, bibs, expected))

    return prepare_matirx(cluster_set, force)


def force_create_matrix(cluster_set, force):
    bibauthor_print("Building a cluster set.")
    return create_matrix(cluster_set(), force)


def wedge_and_store(cluster_set):
    bibs = cluster_set.num_all_bibs
    expected = bibs * (bibs - 1) / 2
    bibauthor_print("Start working on %s. Total number of bibs: %d, "
                    "maximum number of comparisons: %d"
                    % (cluster_set.last_name, bibs, expected))

    wedge(cluster_set)
    remove_result_cluster(cluster_set.last_name)
    cluster_set.store()
    return True


def force_wedge_and_store(cluster_set):
    bibauthor_print("Building a cluster set.")
    return wedge_and_store(cluster_set())


def schedule_create_matrix(cluster_sets, sizes, force):
    def create_job(cluster):
        def ret():
            return force_create_matrix(cluster, force)
        return ret

    memfile_path = None
    if bconfig.DEBUG_PROCESS_PEAK_MEMORY:
        tt = datetime.now()
        tt = (tt.hour, tt.minute, tt.day, tt.month, tt.year)
        memfile_path = ('%smatrix_memory_%d:%d_%d-%d-%d.log' %
                        ((bconfig.TORTOISE_FILES_PATH,) + tt))

    return schedule(map(create_job, cluster_sets),
                    sizes,
                    create_approx_func(matrix_coefs),
                    memfile_path)


def schedule_wedge_and_store(cluster_sets, sizes):
    def create_job(cluster):
        def ret():
            return force_wedge_and_store(cluster)
        return ret

    memfile_path = None
    if bconfig.DEBUG_PROCESS_PEAK_MEMORY:
        tt = datetime.now()
        tt = (tt.hour, tt.minute, tt.day, tt.month, tt.year)
        memfile_path = ('%swedge_memory_%d:%d_%d-%d-%d.log' %
                        ((bconfig.TORTOISE_FILES_PATH,) + tt))

    return schedule(map(create_job, cluster_sets),
                    sizes,
                    create_approx_func(matrix_coefs),
                    memfile_path)
