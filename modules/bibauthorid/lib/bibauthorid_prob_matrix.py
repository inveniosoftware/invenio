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
from bibauthorid_comparison import compare_bibrefrecs
from bibauthorid_comparison import clear_all_caches as clear_comparison_caches
from bibauthorid_backinterface import Bib_matrix
from bibauthorid_backinterface import filter_modified_record_ids
from bibauthorid_general_utils import bibauthor_print \
                                    , update_status \
                                    , update_status_final \
                                    , is_eq

if bconfig.DEBUG_CHECKS:
    def _debug_is_eq_v(vl1, vl2):
        if isinstance(vl1, str) and isinstance(vl2, str):
            return vl1 == vl2

        if isinstance(vl1, tuple) and isinstance(vl2, tuple):
            return is_eq(vl1[0], vl2[0]) and is_eq(vl1[1], vl2[1])

        return False


class ProbabilityMatrix(object):
    '''
    This class contains and maintains the comparison
    between all virtual authors. It is able to write
    and read from the database and update the results.
    '''
    def __init__(self):
        self._bib_matrix = Bib_matrix()

    def load(self, lname, load_map=True, load_matrix=True):
        update_status(0., "Loading probability matrix...")
        self._bib_matrix.load(lname, load_map, load_matrix)
        update_status_final("Probability matrix loaded.")

    def store(self, name):
        update_status(0., "Saving probability matrix...")
        self._bib_matrix.store(name)
        update_status_final("Probability matrix saved.")

    def __getitem__(self, bibs):
        return self._bib_matrix[bibs[0], bibs[1]]


    def __get_up_to_date_bibs(self):
        return frozenset(filter_modified_record_ids(
                         self._bib_matrix.get_keys(),
                         self._bib_matrix.creation_time))

    def is_up_to_date(self, cluster_set):
        return self.__get_up_to_date_bibs() >= frozenset(cluster_set.all_bibs())

    def recalculate(self, cluster_set):
        '''
        Constructs probability matrix. If use_cache is true, it will
        try to load old computations from the database. If save cache
        is true it will save the current results into the database.
        @param cluster_set: A cluster set object, used to initialize
        the matrix.
        '''
        def check_for_cleaning(cur_calc):
            if cur_calc % 10000000 == 0:
                clear_comparison_caches()

        old_matrix = self._bib_matrix
        cached_bibs = self.__get_up_to_date_bibs()
        self._bib_matrix = Bib_matrix(cluster_set)

        ncl = cluster_set.num_all_bibs
        expected = ((ncl * (ncl - 1)) / 2)
        if expected == 0:
            expected = 1

        cur_calc, opti = 0, 0
        for cl1 in cluster_set.clusters:
            update_status((float(opti) + cur_calc) / expected, "Prob matrix: calc %d, opti %d." % (cur_calc, opti))
            for cl2 in cluster_set.clusters:
                if id(cl1) < id(cl2) and not cl1.hates(cl2):
                    for bib1 in cl1.bibs:
                        for bib2 in cl2.bibs:
                            if bib1 in cached_bibs and bib2 in cached_bibs:
                                val = old_matrix[bib1, bib2]
                                if not val:
                                    cur_calc += 1
                                    check_for_cleaning(cur_calc)
                                    val = compare_bibrefrecs(bib1, bib2)
                                else:
                                    opti += 1
                                    if bconfig.DEBUG_CHECKS:
                                        assert _debug_is_eq_v(val, compare_bibrefrecs(bib1, bib2))
                            else:
                                cur_calc += 1
                                check_for_cleaning(cur_calc)
                                val = compare_bibrefrecs(bib1, bib2)

                            self._bib_matrix[bib1, bib2] = val

        clear_comparison_caches()
        update_status_final("Matrix done. %d calc, %d opt." % (cur_calc, opti))


def prepare_matirx(cluster_set, force):
    if bconfig.DEBUG_CHECKS:
        assert cluster_set._debug_test_hate_relation()
        assert cluster_set._debug_duplicated_recs()

    matr = ProbabilityMatrix()
    matr.load(cluster_set.last_name, load_map=True, load_matrix=False)
    if not force and matr.is_up_to_date(cluster_set):
        bibauthor_print("Cluster %s is up-to-date and therefore will not be computed."
            % cluster_set.last_name)
        # nothing to do
        return False

    matr.load(cluster_set.last_name, load_map=False, load_matrix=True)
    matr.recalculate(cluster_set)
    matr.store(cluster_set.last_name)
    return True
