# TODO: add the GNU licensecanonical_str

import re
import bibauthorid_config as bconfig
from bibauthorid_name_utils import compare_names
from bibauthorid_dbinterface import get_name_by_bibrecref
from bibauthorid_dbinterface import get_grouped_records
from bibauthorid_dbinterface import get_all_authors
from bibauthorid_dbinterface import get_collaboration
from bibauthorid_backinterface import get_key_words
from bibrank_citation_searcher import get_citation_dict

# This module is not thread safe!
# Be sure to use processes instead of
# threads if you need parallel
# computation!

caches = []
def create_new_cache():
    ret = {}
    caches.append(ret)
    return ret


def clear_all_caches():
    for c in caches:
        c.clear()


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
    '''
    This is no longer jaccard distance.
    '''
    comparison_log("Jaccard: Found %d items in the first set." % len(set1))
    comparison_log("Jaccard: Found %d items in the second set." % len(set2))
    maxx = max(len(set1), len(set2))
    if maxx == 0:
        return '?'

    match = len(set1 & set2)
    ret = float(match) / float(maxx)

    comparison_log("Jaccard: %d common items." % match)
    comparison_log("Jaccard: returning %f." % ret)
    return ret


def cached_sym(reducing):
    '''
    Memoizes a pure function with two symmetrical arguments.
    '''
    def deco(func):
        cache = create_new_cache()
        def ret(a, b):
            ra, rb = reducing(a), reducing(b)
            ra, rb = min(ra, rb), max(ra, rb)
            if (ra, rb) not in cache:
                cache[(ra, rb)] = func(a, b)
            return cache[(ra, rb)]
        return ret
    return deco


def cached_arg(reducing):
    '''
    Memoizes a pure function.
    '''
    def deco(func):
        cache = create_new_cache()
        def ret(a):
            ra = reducing(a)
            if ra not in cache:
                cache[ra] = func(a)
            return cache[ra]
        return ret
    return deco


# The main function of this module
def compare_bibrefrecs(bibref1, bibref2):
    '''
    This function compares two bibrefrecs (100:123,456) using all metadata
    and returns:
        * a pair with two numbers in [0, 1] - the probability that the two belong
            together and the ratio of the metadata functions used to the number of
            all metadata functions.
        * '+' - the metadata showed us that the two belong together for sure.
        * '-' - the metadata showed us that the two do not belong together for sure.

        Example:
            '(0.7, 0.4)' - 2 out of 5 functions managed to compare the bibrefrecs and
                using their computations the average value of 0.7 is returned.
            '-' - the two bibrefres are in the same paper, so they dont belong together
                for sure.
            '(1, 0)' There was insufficient metadata to compare the bibrefrecs. (The
                first values in ignored).
    '''

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

    register(_compare_affiliations, 1.)
    register(_compare_names, 5.)
    register(_compare_citations, .5)
    register(_compare_citations_by, .5)
    register(_compare_key_words, 2.)

    coll = _compare_collaboration(bibref1, bibref2)
    if coll == '?':
        coll = _compare_coauthors(bibref1, bibref2)

    register(lambda x, y: coll, 3.)

    # sums the results multiplied by the weights and also sums the weights
    def reducer(acum, i):
        if i[0] == '?':
            return acum
        else:
            return (acum[0] + i[0] * i[1], acum[1] + i[1])

    comparison_log("Final vector: %s." % str(results))
    final = reduce(reducer, results, (0, 0))
    weights_sum = sum(res[1] for res in results)

    # devide the final probability by the sum of the weights
    ret = (final[0] / final[1], final[1] / weights_sum)

    #comparison_log("Returning %s." % str(ret))
    #print "%s, %s comparison score is %s." % (str(bibref1), str(bibref2), str(ret))
    # the returned value should be considered as a pair of (probability, cerntainty)
    return ret


@cached_arg(lambda x: x)
def _find_affiliation(bib):
    aff = get_grouped_records(bib, str(bib[0]) + '__u').values()[0]
    return set(canonical_str(a) for a in aff)


def _compare_affiliations(bib1, bib2):
    comparison_log("Comparing affiliations.")

    aff1 = _find_affiliation(bib1)
    aff2 = _find_affiliation(bib2)

    ret = jaccard(aff1, aff2)
    return ret


@cached_arg(lambda x: x)
def _find_inspireid(bib):
    ids = get_grouped_records(bib, str(bib[0]) + '__i').values()[0]
    return set(ids)


def _compare_inspireid(bib1, bib2):
    comparison_log("Comparing inspire ids.")

    iids1 = _find_inspireid(bib1)
    iids2 = _find_inspireid(bib2)

    comparison_log("Found %d, %d different inspire ids for the two sets." % (len(iids1), len(iids2)))
    if (len(iids1) != 1 or
        len(iids2) != 1):
        return '?'
    elif iids1 == iids2:
        comparison_log("The ids are the same.")
        return '+'
    else:
        comparison_log("The ids are different.")
        return '-'


def _compare_papers(bib1, bib2):
    comparison_log("Checking if the two bib refs are in the same paper.")
    if bib1[2] == bib2[2]:
        return '-'
    return '?'


get_name_by_bibrecref = cached_arg(lambda x: (x[0], x[1]))(get_name_by_bibrecref)

@cached_sym(lambda x: (x[0], x[1]))
def _compare_names(bib1, bib2):
    comparison_log("Comparing names.")

    name1 = get_name_by_bibrecref(bib1)
    name2 = get_name_by_bibrecref(bib2)

    if name1 and name2:
        return compare_names(name1, name2, False)
    return '?'


@cached_arg(lambda x: x[2])
def _find_key_words(bib):
    words = get_key_words(bib[2])
    return set(canonical_str(word) for word in words)


@cached_sym(lambda x: x[2])
def _compare_key_words(bib1, bib2):
    comparison_log("Comparing key words.")
    words1 = _find_key_words(bib1)
    words2 = _find_key_words(bib2)

    return jaccard(words1, words2)

@cached_arg(lambda x: x[2])
def _find_collaboration(bib):
    colls = get_collaboration(bib[2])
    return set(canonical_str(coll) for coll in colls)


@cached_sym(lambda x: x[2])
def _compare_collaboration(bib1, bib2):
    comparison_log("Comparing collaboration.")

    colls1 = _find_collaboration(bib1)
    colls2 = _find_collaboration(bib2)

    comparison_log("Found %d, %d different collaborations for the two sets." % (len(colls1), len(colls2)))
    if (len(colls1) != 1 or
        len(colls2) != 1):
        return '?'
    elif colls1 == colls2:
        return 1.
    else:
        return 0.


@cached_arg(lambda x: x[2])
def _find_coauthors(bib):
    return set(canonical_str(a) for a in get_all_authors(bib[2]))


@cached_sym(lambda x: x[2])
def _compare_coauthors(bib1, bib2):
    comparison_log("Comparing authors.")

    aths1 = _find_coauthors(bib1)
    aths2 = _find_coauthors(bib2)

    return jaccard(aths1, aths2)


def _extract_cites(bibrec):
    cit_dict = get_citation_dict("citationdict")
    return cit_dict.get(bibrec, ())


@cached_arg(lambda x: x[2])
def _find_citations(bib):
    return set(c for c in _extract_cites(bib[2]))


@cached_sym(lambda x: x[2])
def _compare_citations(bib1, bib2):
    comparison_log("Comparing citations.")

    cites1 = _find_citations(bib1)
    cites2 = _find_citations(bib2)

    return jaccard(cites1, cites2)


def _extract_cites_by(bibrec):
    cit_dict = get_citation_dict("reversedict")
    return cit_dict.get(bibrec, ())


@cached_arg(lambda x: x[2])
def _find_citations_by(bib):
    return set(c for c in _extract_cites_by(bib[2]))


@cached_sym(lambda x: x[2])
def _compare_citations_by(bib1, bib2):
    comparison_log("Comparing citations by.")

    cites1 = _find_citations_by(bib1)
    cites2 = _find_citations_by(bib2)

    return jaccard(cites1, cites2)

