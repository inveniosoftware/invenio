from bibauthorid_backinterface import get_papers_by_pids

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

    def create_by_personid(self, personid_list):
        '''
        @param personid_list: A list of personids which share common last name.
        @type: example: [481882, 481877, 481878, 481884]
        '''
        all_unions = []

        all_bibs = get_papers_by_pids(personid_list)

        if frozenset(all_bibs.keys()) != frozenset(personid_list):
            raise AssertionError("get_papers_by_pids scred up")

        for bibs in all_bibs.values():
            # united: A cluster with all claimed papers. Hates all rejected papers.
            confirmed = set(bib[0] for bib in bibs if 1 < bib[1])
            if confirmed:
                united = [self.cluster(confirmed)]
            else:
                united = []

            # haters: A cluster per each rejected paper. Hates the united cluster.
            haters = [self.cluster(set([bib[0]]), set(united)) for bib in bibs if bib[1] < -1]
            if united:
                united[0].hate = set(haters)

            # neutral: A cluster per each other paper. Hates nothing.
            neutral = [self.cluster(set([bib[0]])) for bib in bibs if -1 <= bib[1] and bib[1] <= 1]

            all_unions += united
            self.clusters += united + haters + neutral

        # make all unions hate each other
        for i in range(len(all_unions)):
            all_unions[i].hate |= (set(all_unions[:i] + all_unions[i+1:]))

    def create_by_bibtables(self):
       pass

    # a *very* slow fucntion checking when the hate relation is no longer symetrical
    def _debug_test_hate_relation(self):
        for cl1 in self.clusters:
            if not cl1._debug_test_hate_relation():
                return False
        return True

