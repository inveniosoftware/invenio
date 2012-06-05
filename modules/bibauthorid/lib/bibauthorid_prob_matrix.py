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
from bibauthorid_backinterface import bib_matrix
from bibauthorid_backinterface import get_sql_time
from bibauthorid_backinterface import filter_modified_record_ids
from bibauthorid_general_utils import update_status \
                                    , update_status_final

if bconfig.DEBUG_CHECKS:
    def _debug_is_eq(v1, v2):
        eps = 1e-2
        return v1 + eps > v2 and v2 + eps > v1

    def _debug_is_eq_v(vl1, vl2):
        if isinstance(vl1, str) and isinstance(vl2, str):
            return vl1 == vl2

        if isinstance(vl1, tuple) and isinstance(vl2, tuple):
            return _debug_is_eq(vl1[0], vl2[0]) and _debug_is_eq(vl1[1], vl2[1])

        return False

class probability_matrix:
    '''
    This class contains and maintains the comparison
    between all virtual authors. It is able to write
    and read from the database and update the results.
    '''

    def __init__(self, cluster_set, use_cache=False, save_cache=False):
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

        self._bib_matrix = bib_matrix(cluster_set)

        old_matrix = bib_matrix()

        ncl = sum(len(cl.bibs) for cl in cluster_set.clusters)
        expected = ((ncl * (ncl - 1)) / 2)
        if expected == 0:
            expected = 1

        if use_cache and old_matrix.load(cluster_set.last_name):
            cached_bibs = set(filter_modified_record_ids(
                                  old_matrix.get_keys(),
                                  old_matrix.creation_time))
        else:
            cached_bibs = set()

        if save_cache:
            creation_time = get_sql_time()

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

        if save_cache:
            update_status(1., "saving...")
            self._bib_matrix.store(cluster_set.last_name, creation_time)

        update_status_final("Matrix done. %d calc, %d opt." % (cur_calc, opti))

    def __getitem__(self, bibs):
        return self._bib_matrix[bibs[0], bibs[1]]

