from itertools import chain
from operator import itemgetter
from bibauthorid_matrix_optimization import maximized_mapping
from bibauthorid_backinterface import group_blobs, save_cluster
from bibauthorid_backinterface import get_bib10x, get_bib70x
from bibauthorid_backinterface import get_all_valid_bibrecs
from bibauthorid_backinterface import get_bibrefrec_subset
from bibauthorid_name_utils import generate_last_name_cluster_str

class cluster_set:
    class cluster:
        def __init__(self, bibs, hate = []):
            # hate is a symetrical relation
            self.bibs = set(bibs)
            self.hate = set(hate)

        def hates(self, other):
            return other in self.hate

        def quarrel(self, cl2):
            self.hate.add(cl2)
            cl2.hate.add(self)

        def _debug_test_hate_relation(self):
            for cl2 in self.hate:
                if not self.hates(cl2) or not cl2.hates(self):
                    return False
            return True

    def __init__(self):
        self.clusters = []

    def create_skeleton(self, blobs):
        union, independent = group_blobs(blobs)

        union_clusters = {}
        for uni in union:
            union_clusters[uni[1]] = union_clusters.get(uni[1], []) + [uni[0]]

        cluster_dict = dict((personid, self.cluster(bibs)) for personid, bibs in union_clusters.items())
        self.clusters = cluster_dict.values()

        for i, cl in enumerate(self.clusters):
            cl.hate = set(self.clusters[:i] + self.clusters[i+1:])

        for ind in independent:
            bad_clusters = [cluster_dict[i] for i in ind[2] if i in cluster_dict]
            cl = self.cluster([ind[0]], bad_clusters)
            for bcl in bad_clusters:
                bcl.hate.add(cl)
            self.clusters.append(cl)

    def create_body(self, blobs):
        union, independent = group_blobs(blobs)

        arranged_clusters = {}
        flying = []
        for uni in union:
            arranged_clusters[uni[1]] = arranged_clusters.get(uni[1], []) + [uni[0]]

        for ind in independent:
            if ind[1]:
                arranged_clusters[ind[1]] = arranged_clusters.get(ind[1], []) + [ind[0]]
            else:
                flying.append(ind[0])

        for pid, bibs in arranged_clusters.items():
            cl = self.cluster(bibs)
            cl.personid = pid
            self.clusters.append(cl)

        for bib in flying:
            cl = self.cluster([bib])
            cl.personid = None
            self.clusters.append(cl)

    # a *very* slow fucntion checking when the hate relation is no longer symetrical
    def _debug_test_hate_relation(self):
        for cl1 in self.clusters:
            if not cl1._debug_test_hate_relation():
                return False
        return True

    @staticmethod
    def match_cluster_sets(cs1, cs2):
        """
        This functions tries to generate the best matching
        between cs1 and cs2 acoarding to the shared bibrefrecs.
        It returns a dictionary with keys, clsuters in cs1,
        and values, clusters in cs2.
        @param and type of cs1 and cs2: cluster_set
        @return: dictionary with the matching clusters.
        @return type: { cluster : cluster }
        """

        matr = [[-len(cl1.bibs & cl2.bibs) for cl2 in cs2.clusters] for cl1 in cs1.clusters]
        mapping = maximized_mapping(matr)
        return dict((cs1.clusters[mappy[0]], cs2.clusters[mappy[1]]) for mappy in mapping)


    def store(self, name):
        '''
        Stores the cluster set in a special table.
        This is used to store the results of
        tortoise/wedge in a table and later merge them
        with personid.
        '''
        named_clusters = (("%s.%d" % (name, idx), cl) for idx, cl in enumerate(self.clusters))
        map(save_cluster, named_clusters)


def cluster_sets_from_marktables():
    # { (100, 123) -> name }
    ref100 = get_bib10x()
    ref700 = get_bib70x()
    bibref_2_name = dict([((100, ref), generate_last_name_cluster_str(name)) for ref, name in ref100] +
                         [((700, ref), generate_last_name_cluster_str(name)) for ref, name in ref700])

    all_recs = get_all_valid_bibrecs()

    all_bibrefrecs = chain(((100, ref, rec) for rec, ref in get_bibrefrec_subset(100, all_recs, map(itemgetter(0), ref100))),
                           ((700, ref, rec) for rec, ref in get_bibrefrec_subset(700, all_recs, map(itemgetter(0), ref700))))

    last_name_2_bibs = {}
    for bibrefrec in all_bibrefrecs:
        table, ref, unused = bibrefrec
        name = bibref_2_name[(table, ref)]
        last_name_2_bibs[name] = last_name_2_bibs.get(name, []) + [bibrefrec]

    cluster_sets = []
    for name, bibrecrefs in last_name_2_bibs.items():
        new_cluster_set = cluster_set()
        new_cluster_set.clusters = [cluster_set.cluster([bib]) for bib in bibrecrefs]
        cluster_sets.append((new_cluster_set, name))

    return cluster_sets

