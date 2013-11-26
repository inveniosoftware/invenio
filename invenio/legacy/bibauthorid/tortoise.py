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

from invenio.legacy.bibauthorid import config as bconfig
from datetime import datetime
import os
#import cPickle as SER
import msgpack as SER

import gc
import matplotlib.pyplot as plt
import numpy as np

#This is supposed to defeat a bit of the python vm performance losses:
import sys
sys.setcheckinterval(1000000)

try:
    from collections import defaultdict
except:
    from invenio.utils.container import defaultdict

from itertools import groupby, chain, repeat
from invenio.legacy.bibauthorid.general_utils import update_status, update_status_final, override_stdout_config

from invenio.legacy.bibauthorid.cluster_set import delayed_cluster_sets_from_marktables
from invenio.legacy.bibauthorid.cluster_set import delayed_cluster_sets_from_personid
from invenio.legacy.bibauthorid.wedge import wedge
from invenio.legacy.bibauthorid.name_utils import generate_last_name_cluster_str
from invenio.legacy.bibauthorid.backinterface import empty_results_table
from invenio.legacy.bibauthorid.backinterface import remove_result_cluster
from invenio.legacy.bibauthorid.general_utils import bibauthor_print
from invenio.legacy.bibauthorid.prob_matrix import prepare_matirx
from invenio.legacy.bibauthorid.scheduler import schedule, matrix_coefs
from invenio.legacy.bibauthorid.least_squares import to_function as create_approx_func
from math import isnan

import multiprocessing as mp

#python2.4 compatibility
from invenio.legacy.bibauthorid.general_utils import bai_all as all

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
    cluster_set = cluster()
    bibauthor_print("Found, %s(%s). Total number of bibs: %d." % (name, lname, size))
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

    wedge(cluster_set, True, coeff)
    remove_result_cluster(cluster_set.last_name)

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

def tortoise_tweak_coefficient(lastnames, min_coef, max_coef, stepping, create_matrix=True):
    bibauthor_print('Coefficient tweaking!')
    bibauthor_print('Cluster sets from mark...')

    lnames = set([generate_last_name_cluster_str(n) for n in lastnames])
    coefficients = [x/100. for x in range(int(min_coef*100),int(max_coef*100),int(stepping*100))]

    pool = mp.Pool()

    if create_matrix:
        pool.map(_create_matrix, lnames)
    pool.map(_collect_statistics_lname_coeff, ((x,y) for x in lnames for y in coefficients ))


def _gen_plot(data, filename):
    plt.clf()
    ax = plt.subplot(111)
    ax.grid(visible=True)
    x = sorted(data.keys())

    w = [data[k][0] for k in x]
    try:
        wscf = max(w)
    except:
        wscf = 0
    w = [float(i)/wscf for i in w]
    y = [data[k][1] for k in x]
    maxi = [data[k][3] for k in x]
    mini = [data[k][2] for k in x]

    lengs = [data[k][4] for k in x]
    try:
        ml = float(max(lengs))
    except:
        ml = 1
    lengs = [k/ml for k in lengs]

    normalengs = [data[k][5] for k in x]

    ax.plot(x,y,'-o',label='avg')
    ax.plot(x,maxi,'-o', label='max')
    ax.plot(x,mini,'-o', label='min')
    ax.plot(x,w, '-x', label='norm %s' % str(wscf))
    ax.plot(x,lengs,'-o',label='acl %s' % str(int(ml)))
    ax.plot(x,normalengs, '-o', label='ncl')
    plt.ylim(ymax = 1., ymin = -0.01)
    plt.xlim(xmax = 1., xmin = -0.01)
    ax.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,ncol=6, mode="expand", borderaxespad=0.)
    plt.savefig(filename)



def tortoise_coefficient_statistics(pickle_output=None, generate_graphs=True):
    override_stdout_config(stdout=True)

    files = ['/tmp/baistats/'+x for x in os.listdir('/tmp/baistats/') if x.startswith('cluster_status_report_pid')]
    fnum = float(len(files))
    quanta = .1/fnum


    total_stats = 0
    used_coeffs = set()
    used_clusters = set()

    #av_counter, avg, min, max, nclus, normalized_avg
    cluster_stats = defaultdict(lambda : defaultdict(lambda : [0.,0.,0.,0.,0.,0.]))
    coeff_stats = defaultdict(lambda : [0.,0.,0.,0.,0.,0.])


    def gen_graphs(only_synthetic=False):
        update_status(0, 'Generating coefficients graph...')
        _gen_plot(coeff_stats, '/tmp/graphs/AAAAA-coefficients.svg')
        if not only_synthetic:
            cn = cluster_stats.keys()
            l = float(len(cn))
            for i,c in enumerate(cn):
                update_status(i/l, 'Generating name graphs... %s' % str(c))
                _gen_plot(cluster_stats[c], '/tmp/graphs/CS-%s.png' % str(c))

    for i,fi in enumerate(files):
        if generate_graphs:
            if i%1000 ==0:
                gen_graphs(True)

        f = open(fi,'r')
        status = i/fnum
        update_status(status, 'Loading '+ fi[fi.find('lastname')+9:])
        contents = SER.load(f)
        f.close()

        cur_coef = contents[0]
        cur_clust = contents[1]

        cur_maxlen = float(contents[3])

        if cur_coef:
            total_stats += 1
            used_coeffs.add(cur_coef)
            used_clusters.add(cur_clust)

            update_status(status+0.2*quanta, '  Computing averages...')

            cur_clen = len(contents[2])
            cur_coeffs = [x[2] for x in contents[2]]
            cur_clustnumber = float(len(set([x[0] for x in contents[2]])))

            assert cur_clustnumber > 0 and cur_clustnumber < cur_maxlen, "Error, found log with strange clustnumber! %s %s %s %s" % (str(cur_clust), str(cur_coef), str(cur_maxlen),
                                                                                                                          str(cur_clustnumber))

            if cur_coeffs:

                assert len(cur_coeffs) == cur_clen and cur_coeffs, "Error, there is a cluster witohut stuff? %s %s %s"% (str(cur_clust), str(cur_coef), str(cur_coeffs))
                assert all([x >= 0 and x <= 1 for x in cur_coeffs]), "Error, a coefficient is wrong here! Check me! %s %s %s" % (str(cur_clust), str(cur_coef), str(cur_coeffs))

                cur_min = min(cur_coeffs)
                cur_max = max(cur_coeffs)
                cur_avg = sum(cur_coeffs)/cur_clen

                update_status(status+0.4*quanta, '  comulative per coeff...')

                avi = coeff_stats[cur_coef][0]
                #number of points
                coeff_stats[cur_coef][0] = avi+1
                #average of coefficients
                coeff_stats[cur_coef][1] = (coeff_stats[cur_coef][1]*avi + cur_avg)/(avi+1)
                #min coeff
                coeff_stats[cur_coef][2] = min(coeff_stats[cur_coef][2], cur_min)
                #max coeff
                coeff_stats[cur_coef][3] = max(coeff_stats[cur_coef][3], cur_max)
                #avg number of clusters
                coeff_stats[cur_coef][4] = (coeff_stats[cur_coef][4]*avi + cur_clustnumber)/(avi+1)
                #normalized avg number of clusters
                coeff_stats[cur_coef][5] = (coeff_stats[cur_coef][5]*avi + cur_clustnumber/cur_maxlen)/(avi+1)


                update_status(status+0.6*quanta, '  comulative per cluster per coeff...')

                avi = cluster_stats[cur_clust][cur_coef][0]
                cluster_stats[cur_clust][cur_coef][0] = avi+1
                cluster_stats[cur_clust][cur_coef][1] = (cluster_stats[cur_clust][cur_coef][1]*avi + cur_avg)/(avi+1)
                cluster_stats[cur_clust][cur_coef][2] = min(cluster_stats[cur_clust][cur_coef][2], cur_min)
                cluster_stats[cur_clust][cur_coef][3] = max(cluster_stats[cur_clust][cur_coef][3], cur_max)
                cluster_stats[cur_clust][cur_coef][4] = (cluster_stats[cur_clust][cur_coef][4]*avi + cur_clustnumber)/(avi+1)
                cluster_stats[cur_clust][cur_coef][5] = (cluster_stats[cur_clust][cur_coef][5]*avi + cur_clustnumber/cur_maxlen)/(avi+1)

    update_status_final('Done!')

    if generate_graphs:
        gen_graphs()


    if pickle_output:
        update_status(0,'Dumping to file...')
        f = open(pickle_output,'w')
        SER.dump({'cluster_stats':dict((x,dict(cluster_stats[x])) for x in cluster_stats.iterkeys()), 'coeff_stats':dict((coeff_stats))}, f)
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
