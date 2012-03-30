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

import os

from operator import itemgetter
from itertools import groupby, chain

from bibauthorid_cluster_set import cluster_set
from bibauthorid_cluster_set import cluster_sets_from_marktables
from bibauthorid_prob_matrix import probability_matrix
from bibauthorid_wedge import wedge
from bibauthorid_name_utils import generate_last_name_cluster_str
from bibauthorid_backinterface import get_all_names_from_personid
from bibauthorid_backinterface import create_blobs_by_pids
from bibauthorid_backinterface import filter_newer_bibs
from bibauthorid_backinterface import empty_results_table

def create_lastname_list_from_personid():
    '''
    This function generates a dictionary from a last name
    to list of personids which have this lastname.
    '''
    # ((personid, [full Name1]) ... )
    all_names = get_all_names_from_personid()

    # ((personid, last_name) ... )
    all_names = ((row[0], generate_last_name_cluster_str(row[1][0]))
                  for row in all_names)

    # { (last_name : [personid ... ]) ... }
    all_names = groupby(sorted(all_names, key=itemgetter(1)), key=itemgetter(1))
    all_names = ((key, map(itemgetter(0), data)) for key, data in all_names)

    return all_names


def disambiguate_last_name(personids, last_name, last_run):
    '''
    Creates a cluster_set from personid and calls disambiguate.
    '''
    cs = cluster_set()
    cs.create_skeleton(create_blobs_by_pids(personids))
    disambiguate(cs, last_name, last_run)


def disambiguate(cluster_set, last_name, last_run):
    '''
    Updates personid from a list of personids, sharing common
    last name, and this last name.
    '''
    print "Total number of bibs: %d" % len(cluster_set.clusters)
    print "Number of bibs which hate something: %s" % len([c for c in cluster_set.clusters if c.hate])
    print "Total sum of hate links: %s" % sum([len(c.hate) for c in cluster_set.clusters])

    all_bibs = chain(*(c.bibs for c in cluster_set.clusters))
    clean_records = set(filter_newer_bibs(all_bibs, last_run))

    matr = probability_matrix(cluster_set, last_name, clean_records, True, True)

    wedge(cluster_set, matr)
    del(matr)

    cluster_set.store(last_name)


def tortoise_from_scratch():
    cluster_sets = cluster_sets_from_marktables()
    cluster_sets = sorted(cluster_sets, key=lambda x: len(x[0].clusters))
    cluster_sets = [(x[0], x[1], "2000-11-07 17:15:00") for x in cluster_sets]

    empty_results_table()
    start_workers(disambiguate, cluster_sets, 6)


def tortoise():
    names = create_lastname_list_from_personid()
    names = sorted(names, key=lambda x: len(x[1]))
    names = [(x[1], x[0], "2000-11-07 17:15:00") for x in names]

    empty_results_table()
    start_workers(disambiguate_last_name, names, 6)


def start_workers(job, arr_args, workers_n):
    all_jobs = []

     # [(number of clusters, number of workers)...]
    if workers_n == 12:
     # those numbers are optimized for 12 cores
        tasks = [(len(arr_args) - 3410, 8),
                 (2000, 1),
                 (1000, 1),
                 (400, 1),
                 (10, 1),
                ]
    else:
        tasks = [(len(arr_args), workers_n),
                ]

    start = 0
    for lenght, workers in tasks:
        if lenght > 0:
            end = start + lenght
            all_jobs.append((start, end, workers))
            start = end

    if all_jobs:
        assert all_jobs[0][0] == 0, all_jobs
        for i in range(len(all_jobs) - 1):
            assert all_jobs[i][0] < all_jobs[i][1], all_jobs
            assert all_jobs[i][2] > 0, all_jobs
            assert all_jobs[i][1] == all_jobs[i + 1][0], all_jobs
        assert all_jobs[-1][0] < all_jobs[-1][1], all_jobs
        assert all_jobs[-1][1] == len(arr_args), all_jobs
        assert sum([t[2] for t in all_jobs]) == workers_n, all_jobs

    wrkrs_cnt = 0
    for start, end, workers in all_jobs:
        for number in range(workers):
            wrkrs_cnt += 1
            if os.fork() == 0:
                i = start + number
                while i < end:
                    job(*arr_args[i])
                    i += workers
                print "worker done: %d %d %d" % (start, end, workers)
                os._exit(0)

    for unused in xrange(wrkrs_cnt):
        os.wait()


