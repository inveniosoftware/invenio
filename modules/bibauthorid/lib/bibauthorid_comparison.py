# TODO: add the GNU licensecanonical_str

import re
import bibauthorid_config as bconfig
from bibauthorid_name_utils import compare_names
from bibauthorid_dbinterface import get_name_by_bibrecref
from bibauthorid_dbinterface import get_grouped_records
from bibauthorid_dbinterface import get_all_authors
from bibauthorid_dbinterface import get_collaboration
from bibrank_citation_searcher import get_citation_dict

# All fuctions below receive two argumets, both lists of bibrefrecs
# Each bibrefrec is a tuple of 3 integers:
# 1: the number of the table (usually 100 or 700)
# 2: bibxxx in this table
# 3: bibrec


if bconfig.TABLES_UTILS_DEBUG:
    def comparison_log(msg):
        print msg
else:
    def comparison_log(msg):
        pass


_replacer = re.compile("[^a-zA-Z]")
def canonical_str(string):
    return _replacer.sub('', string).lower()


def jaccard(set1, set2):
    comparison_log("Jaccard: Found %d items in the first set." % len(set1))
    comparison_log("Jaccard: Found %d items in the second set." % len(set2))
    total = len(set1) + len(set2)
    if total == 0:
        return '?'

    match = len(set1 & set2)
    union = total - match
    ret = float(match) / float(union)

    comparison_log("Jaccard: %d common items." % match)
    comparison_log("Jaccard: %d different items." % union)
    comparison_log("Jaccard: returning %f." % ret)
    return ret


# The main function of this module
def compare_bibrefrecs(bibref1, bibref2):
    # try first the metrics, which might return + or -

    insp_ids = _compare_inspireid(bibref1, bibref2)
    if insp_ids != '?':
        return insp_ids

    papers = _compare_papers(bibref1, bibref2)
    if papers != '?':
        return papers

    # unfortunately, we have to do all comparisons
    results = []
    def register(func, weight):
        results.append((func(bibref1, bibref2), weight))

    register(_compare_affiliations, .1)
    register(_compare_names, .6)
    register(_compare_citations, .05)
    register(_compare_citations_by, .05)

    coll = _compare_collaboration(bibref1, bibref2)
    if coll == '?':
        coll = _compare_coauthors(bibref1, bibref2)

    register(lambda x, y: coll, .2)

    # sums the results multiplied by the weights and also sums the weights
    def reducer(acum, i):
        if i[0] == '?':
            return acum
        else:
            return (acum[0] + i[0] * i[1], acum[1] + i[1])

    comparison_log("Final vector: %s." % str(results))
    final = reduce(reducer, results, (0, 0))

    # devide the final probability by the sum of the weights
    ret = (final[0] / final[1], final[1])
    
    #comparison_log("Returning %s." % str(ret))
    print "Returning %s." % str(ret)
    # the returned value should be considered as a pair of (probability, cerntainty)
    return ret


# O(n + m)
def _compare_affiliations(bibs1, bibs2):
    comparison_log("Comparing affiliations.")
    def _find_affiliation(bibs):
        affs = [get_grouped_records(bib, str(bib[0]) + '__u').values()[0] for bib in bibs]
        return set(canonical_str(a) for aff in affs for a in aff)

    aff1 = _find_affiliation(bibs1)
    aff2 = _find_affiliation(bibs2)

    ret = jaccard(aff1, aff2)
    return ret


# O(n + m)
def _compare_inspireid(bibs1, bibs2):
    comparison_log("Comparing inspire ids.")
    def _find_inspireid(bibs):
        iids = [get_grouped_records(bib, str(bib[0]) + '__i').values()[0] for bib in bibs]
        return set(i for ids in iids for i in ids)

    iids1 = _find_inspireid(bibs1)
    iids2 = _find_inspireid(bibs2)

    comparison_log("Found %d, %d different inspire ids for the two sets." % (len(iids1), len(iids2)))
    if (len(iids1) != 1 or
        len(iids2) != 1):
        # This is a strange situation. If one of the sets is empty
        # than we cannot do anything. However, if one of the sets
        # has move than 1 element, the data is corrupt and we also
        # cannot do anything.
        return '?'

    elif iids1 == iids2:
        comparison_log("The ids are the same.")
        return '+'
    else:
        comparison_log("The ids are different.")
        return '-'


# O(n + m)
def _compare_papers(bibs1, bibs2):
    comparison_log("Checking if the two bib refs are in the same paper.")
    def _find_papers(bibs):
        return set(bib[2] for bib in bibs)

    pprs1 = _find_papers(bibs1)
    pprs2 = _find_papers(bibs2)

    if pprs1 & pprs2:
        comparison_log("Yes.")
        return '-'
    else:
        comparison_log("No.")
        return '?'


# O(n * m)
# This is the only comparison which is O(m*n),
# which makes it *VERY* slow.
# Use it only if n or m in 1(preferebly both)
def _compare_names(bibs1, bibs2):
    comparison_log("Comparing names.")
    def _find_names(bibs):
        return [get_name_by_bibrecref(bib) for bib in bibs]

    names1 = _find_names(bibs1)
    names2 = _find_names(bibs2)

    all_pairs = [compare_names(n1, n2) for n1 in names1 for n2 in names2]
    comparison_log("Total pairs: %d." % len(all_pairs))

    if all_pairs:
        comparison_log("Result vector: %s." % all_pairs[0:50])
        return sum(all_pairs) / len(all_pairs)
    else:
        return '?'


# O(n + m)
def _compare_collaboration(bibs1, bibs2):
    comparison_log("Comparing collaboration.")
    def _find_collaboration(bibs):
        colls = [c for bib in bibs for c in get_collaboration(bib[2])]
        return set(canonical_str(coll) for coll in colls)

    colls1 = _find_collaboration(bibs1)
    colls2 = _find_collaboration(bibs2)

    comparison_log("Found %d, %d different collaborations for the two sets." % (len(colls1), len(colls2)))
    if (len(colls1) != 1 or
        len(colls2) != 1):
        return '?'
    elif colls1 == colls2:
        return 1.
    else:
        return 0.


# O(n + m)
def _compare_coauthors(bibs1, bibs2):
    comparison_log("Comparing authors.")
    def _find_coauthors(bibs):
       return set(canonical_str(a) for bib in bibs for a in get_all_authors(bib[2]))

    aths1 = _find_coauthors(bibs1)
    aths2 = _find_coauthors(bibs2)

    return jaccard(aths1, aths2)


# O(n + m)
def _compare_citations(bibs1, bibs2):
    comparison_log("Comparing citations.")
    def _extract_cites(bibrec):
        cit_dict = get_citation_dict("citationdict")
        return cit_dict.get(bibrec, ())

    def _find_citations(bibs):
        return set(c for bib in bibs for c in _extract_cites(bib[2]))

    cites1 = _find_citations(bibs1)
    cites2 = _find_citations(bibs2)

    return jaccard(cites1, cites2)


# O(n + m)
def _compare_citations_by(bibs1, bibs2):
    comparison_log("Comparing citations by.")
    def _extract_cites_by(bibrec):
        cit_dict =  get_citation_dict("reversedict")
        return cit_dict.get(bibrec, ())

    def _find_citations_by(bibs):
        return set(c for bib in bibs for c in _extract_cites_by(bib[2]))

    cites1 = _find_citations_by(bibs1)
    cites2 = _find_citations_by(bibs2)

    return jaccard(cites1, cites2)

