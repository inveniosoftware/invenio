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

from bibauthorid_cluster_set import delayed_cluster_sets_from_marktables
from bibauthorid_cluster_set import delayed_cluster_sets_from_personid
from bibauthorid_wedge import wedge
from bibauthorid_name_utils import generate_last_name_cluster_str
from bibauthorid_backinterface import empty_results_table
from bibauthorid_backinterface import remove_result_cluster
from bibauthorid_general_utils import bibauthor_print
from bibauthorid_prob_matrix import prepare_matirx
from bibauthorid_scheduler import schedule \
                                  , Estimator \
                                  , matrix_coefs \
                                  , wedge_coefs
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
    cluster_sets, lnames, sizes = delayed_cluster_sets_from_marktables()
    bibauthor_print("Building all matrices.")
    exit_statuses = schedule_create_matrix(
        cluster_sets,
        sizes,
        force=True)
    assert len(exit_statuses) == len(cluster_sets)

    empty_results_table()

    bibauthor_print("Preparing cluster sets.")
    cluster_sets, lnames, sizes = delayed_cluster_sets_from_marktables()
    bibauthor_print("Starting disambiguation.")
    exit_statuses = schedule_wedge_and_store(
        cluster_sets,
        sizes)
    assert len(exit_statuses) == len(cluster_sets)


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
        clusters, lnames, sizes = delayed_cluster_sets_from_personid(pure, last_run)
        bibauthor_print("Building all matrices.")
        exit_statuses = schedule_create_matrix(
            clusters,
            sizes,
            force=force_matrix_creation)
        assert len(exit_statuses) == len(clusters)

    bibauthor_print("Preparing cluster sets.")
    clusters, lnames, sizes = delayed_cluster_sets_from_personid(pure, last_run)
    bibauthor_print("Starting disambiguation.")
    exit_statuses = schedule_wedge_and_store(
        clusters,
        sizes)
    assert len(exit_statuses) == len(clusters)


def tortoise_last_name(name, from_mark=False, pure=False):
    assert not(from_mark and pure)

    lname = generate_last_name_cluster_str(name)

    if from_mark:
        clusters, lnames, sizes = delayed_cluster_sets_from_marktables()
    else:
        clusters, lnames, sizes = delayed_cluster_sets_from_personid(pure)

    try:
        idx = lnames.index(lname)
        cluster = clusters[idx]
        size = sizes[idx]
        bibauthor_print("Found, %s(%s). Total number of bibs: %d." % (name, lname, size))
        cluster_set = cluster()
        create_matrix(cluster_set, True)
        wedge_and_store(cluster_set)
    except IndexError:
        bibauthor_print("Sorry, %s(%s) not found in the last name clusters" % (name, lname))


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
                    Estimator(matrix_coefs),
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
                    Estimator(wedge_coefs),
                    memfile_path)
