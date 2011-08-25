from scipy.sparse import lil_matrix

from bibauthorid_backinterface import probability_table_exists
from bibauthorid_backinterface import create_probability_table
from bibauthorid_backinterface import save_bibmap_and_matrix_to_db
from bibauthorid_backinterface import load_bibmap_and_matrix_from_db
from bibauthorid_comparison import compare_bibrefrecs

class probability_matrix:
    '''
    This class contains and maintains the comparison
    between all virtual authors. It is able to write
    and read from the database and update the results.
    '''
    class bib_matrix:
        '''
        This small class contains the sparse matrix
        and encapsulates it.
        '''
        def __init__(self, cluster_set = None):
            if cluster_set:
                bibs = [bib for cl in cluster_set.clusters
                        for bib in cl.bibs]
                self._bibmap = dict((b[1], b[0]) for b in enumerate(bibs))
                width = len(bibs)
                size = ((width - 1) * width) / 2
                # create a linearized matrix
                self._matrix = [None for x in xrange(size)]

        def _resolve_entry(self, bibs):
            entry = sorted([self._bibmap[bib] for bib in bibs])
            if entry[0] >= entry[1]:
                raise AssertionError
            return entry[0] + ((entry[1] - 1) * entry[1]) / 2

        def __setitem__(self, bibs, val):
            entry = self._resolve_entry(bibs)
            self._matrix[entry] = val

        def __getitem__(self, bibs):
            entry = self._resolve_entry(bibs)
            return self._matrix[entry]

        def store(self, name):
            '''
            This method will store the matrix to the
            database.
            '''
            if not probability_table_exists():
                raise AssertionError

            save_bibmap_and_matrix_to_db(name, self._bibmap, self._matrix)

        def load(self, name):
            '''
            This method will load the matrix from the
            database.
            '''
            if not probability_table_exists():
                raise AssertionError

            self._bibmap, self._matrix = load_bibmap_and_matrix_from_db(name)

    def __init__(self, cluster_set, last_name="", cached = [],
                 use_cache = False, save_cache = False):
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
        self._bib_matrix = self.bib_matrix(cluster_set)

        old_matrix = self.bib_matrix()
        if use_cache and probability_table_exists():
            old_matrix.load(last_name)
        elif cached:
            raise AssertionError("You cannot have cached"
                                  "results and empty table!")

        for cl1 in cluster_set.clusters:
            for cl2 in cluster_set.clusters:
                if id(cl1) != id(cl2) and cl1.hates(cl2) == False:
                    for bib1 in cl1.bibs:
                        for bib2 in cl2.bibs:
                            if bib1 in cached and bib2 in cached:
                                val = old_matrix[bib1, bib2]
                                if val == None:
                                    val = compare_bibrefrecs(bib1, bib2)
                            else:
                                val = compare_bibrefrecs(bib1, bib2)
                            self._bib_matrix[bib1, bib2] = val

        if save_cache:
            if not probability_table_exists():
                create_probability_table()
            self._bib_matrix.store(last_name)

    def __getitem__(self, bibs):
        return self._bib_matrix[bibs[0], bibs[1]]

