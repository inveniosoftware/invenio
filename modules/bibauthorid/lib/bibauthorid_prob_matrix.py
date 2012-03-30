import time

import bibauthorid_config as bconfig
from bibauthorid_comparison import compare_bibrefrecs
from bibauthorid_comparison import clear_all_caches as clear_comparison_caches
from bibauthorid_backinterface import bib_matrix
from bibauthorid_general_utils import update_status

if bconfig.TABLES_UTILS_DEBUG:
    def _debug_is_eq(v1, v2):
        eps = 1e-6
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

    def __init__(self, cluster_set, last_name="", cached=[],
                 use_cache=False, save_cache=False):
        '''
        Constructs probability matrix. If use_cache is true, it will
        try to load old computations from the database. If save cache
        is true it will save the current results into the database.
        @param cluster_set: A cluster set object, used to initialize
        the matrix.
        @param last_name: A string which defines the current cluster
        of names. It is used only if use_cache or save_cache is true.
        @param cached: A list with the bibs, which are not touched
        since last save.
        '''
        self._bib_matrix = bib_matrix(cluster_set)

        old_matrix = bib_matrix()
        successful_load = False
        if use_cache:
            successful_load = old_matrix.load(last_name)
        else:
            assert not cached

        ncl = sum([len(cl.bibs) for cl in cluster_set.clusters])
        expected = ((ncl * (ncl - 1)) / 2)
        print "maximum number of comparisons: %d" % expected
        if expected == 0:
            expected = 1

        save_interval = 10 ** 8
        self.cur_calc = 0
        self.save_calc = save_interval
        self.opti = 0
        self.last_save = None

        def taka_a_break():
            clear_comparison_caches()

            if save_cache:
                update_status(self.percent, "saving...")
                t = time.time()
                self._bib_matrix.store(last_name)
                self.last_save = int(time.time() - t)

        def calculate_value(bib1, bib2):
            if self.cur_calc == self.save_calc:
                taka_a_break()
                self.save_calc += save_interval
            self.cur_calc += 1

            return compare_bibrefrecs(bib1, bib2)

        def update_current_status():
            if self.last_save != None:
                save_str = "last save: %d sec" % self.last_save
            else:
                save_str = ""
            update_status(self.percent, save_str)

        print "Building the probability matrix..."
        for cl1 in cluster_set.clusters:
            self.percent = (float(self.opti) + float(self.cur_calc)) / expected
            update_current_status()
            for cl2 in cluster_set.clusters:
                if id(cl1) != id(cl2) and not cl1.hates(cl2):
                    for bib1 in cl1.bibs:
                        for bib2 in cl2.bibs:
                            if bib1 < bib2:
                                if bib1 in cached and bib2 in cached and successful_load:
                                    val = old_matrix[bib1, bib2]
                                    if not val:
                                        val = calculate_value(bib1, bib2)
                                    else:
                                        self.opti += 1
                                        if bconfig.TABLES_UTILS_DEBUG:
                                            assert _debug_is_eq_v(val, compare_bibrefrecs(bib1, bib2))
                                else:
                                    val = calculate_value(bib1, bib2)

                                self._bib_matrix[bib1, bib2] = val

        self.percent = 1
        taka_a_break()
        update_current_status()
        print "\nDone. %d calculations, %d optimized." % (self.cur_calc, self.opti)

    def __getitem__(self, bibs):
        return self._bib_matrix[bibs[0], bibs[1]]

