# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012 CERN.
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


import gc
import invenio.bibauthorid_config as bconfig
from invenio.bibauthorid_comparison import compare_bibrefrecs
from invenio.bibauthorid_comparison import clear_all_caches as clear_comparison_caches
from invenio.bibauthorid_backinterface import get_modified_papers_before
from invenio.bibauthorid_logutils import Logger
from invenio.bibauthorid_general_utils import is_eq

# import pyximport; pyximport.install()
from invenio.bibauthorid_bib_matrix import Bib_matrix

if bconfig.DEBUG_CHECKS:
    def _debug_is_eq_v(vl1, vl2):
        if isinstance(vl1, str) and isinstance(vl2, str):
            return vl1 == vl2

        if isinstance(vl1, tuple) and isinstance(vl2, tuple):
            return is_eq(vl1[0], vl2[0]) and is_eq(vl1[1], vl2[1])

        return False

logger = Logger("prob_matrix")


class ProbabilityMatrix(object):

    '''
    This class contains and maintains the comparison
    between all virtual authors. It is able to write
    and read from the database and update the results.
    '''

    def __init__(self, name):
        self._bib_matrix = Bib_matrix(name)

    def load(self, load_map=True, load_matrix=True):
        logger.update_status(0., "Loading probability matrix...")
        self._bib_matrix.load()
        logger.update_status_final("Probability matrix loaded.")

    def store(self):
        logger.update_status(0., "Saving probability matrix...")
        self._bib_matrix.store()
        logger.update_status_final("Probability matrix saved.")

    def __getitem__(self, bibs):
        return self._bib_matrix[bibs[0], bibs[1]]

    def getitem_numeric(self, bibs):
        return self._bib_matrix.getitem_numeric(bibs)

    def __get_up_to_date_bibs(self, bib_matrix):
        return frozenset(get_modified_papers_before(
                         bib_matrix.get_keys(),
                         bib_matrix.creation_time))

    def is_up_to_date(self, cluster_set):
        return self.__get_up_to_date_bibs(self._bib_matrix) >= frozenset(cluster_set.all_bibs())

    def recalculate(self, cluster_set):
        '''
        Constructs probability matrix. If use_cache is true, it will
        try to load old computations from the database. If save cache
        is true it will save the current results into the database.
        @param cluster_set: A cluster set object, used to initialize
        the matrix.
        '''
        last_cleaned = 0
        self._bib_matrix.store()
        try:
            old_matrix = Bib_matrix(self._bib_matrix.name + 'copy')
            old_matrix.duplicate_existing(self._bib_matrix.name, self._bib_matrix.name + 'copy')
            old_matrix.load()
            cached_bibs = self.__get_up_to_date_bibs(old_matrix)
            have_cached_bibs = bool(cached_bibs)
        except IOError:
            old_matrix.destroy()
            cached_bibs = None
            have_cached_bibs = False

        self._bib_matrix.destroy()
        self._bib_matrix = Bib_matrix(cluster_set.last_name, cluster_set=cluster_set)

        ncl = cluster_set.num_all_bibs
        expected = ((ncl * (ncl - 1)) / 2)
        if expected == 0:
            expected = 1

        try:
            cur_calc, opti, prints_counter = 0, 0, 0
            for cl1 in cluster_set.clusters:

                if cur_calc + opti - prints_counter > 100000 or cur_calc == 0:
                    logger.update_status(
                        (float(opti) + cur_calc) / expected, "Prob matrix: calc %d, opti %d." %
                        (cur_calc, opti))
                    prints_counter = cur_calc + opti

    # clean caches
                if cur_calc - last_cleaned > 20000000:
                    gc.collect()
    #                clear_comparison_caches()
                    last_cleaned = cur_calc

                for cl2 in cluster_set.clusters:
                    if id(cl1) < id(cl2) and not cl1.hates(cl2):
                        for bib1 in cl1.bibs:
                            for bib2 in cl2.bibs:
                                if have_cached_bibs:
                                    try:
                                        val = old_matrix[bib1, bib2]
                                        opti += 1
                                        if bconfig.DEBUG_CHECKS:
                                            assert _debug_is_eq_v(val, compare_bibrefrecs(bib1, bib2))
                                    except KeyError:
                                        cur_calc += 1
                                        val = compare_bibrefrecs(bib1, bib2)
                                    if val is None:
                                        cur_calc += 1
                                        val = compare_bibrefrecs(bib1, bib2)
                                else:
                                    cur_calc += 1
                                    val = compare_bibrefrecs(bib1, bib2)
                                self._bib_matrix[bib1, bib2] = val

        except Exception as e:
            raise Exception("""Error happened in prob_matrix.recalculate
            original_exception: %s
            """ % (str(e)))

        clear_comparison_caches()
        logger.update_status_final("Matrix done. %d calc, %d opt." % (cur_calc, opti))


def prepare_matrix(cluster_set, force):
    if bconfig.DEBUG_CHECKS:
        assert cluster_set._debug_test_hate_relation()
        assert cluster_set._debug_duplicated_recs()

    matr = ProbabilityMatrix(cluster_set.last_name)
    matr.load(load_map=True, load_matrix=False)
    if not force and matr.is_up_to_date(cluster_set):
        logger.log("Cluster %s is up-to-date and therefore will not be computed."
                   % cluster_set.last_name)
        return False

    matr.load(load_map=False, load_matrix=True)
    matr.recalculate(cluster_set)
    matr.store()
    return True
