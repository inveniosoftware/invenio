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

import re
import bibauthorid_config as bconfig
from itertools import starmap
from operator import mul
from bibauthorid_name_utils import compare_names
from bibauthorid_dbinterface import get_name_by_bibrecref
from bibauthorid_dbinterface import get_grouped_records
from bibauthorid_dbinterface import get_all_authors
from bibauthorid_dbinterface import get_collaboration
from bibauthorid_dbinterface import resolve_affiliation
from bibauthorid_backinterface import get_key_words
from bibrank_citation_searcher import get_citation_dict
from bibauthorid_general_utils import metadata_comparison_print


# This module is not thread safe!
# Be sure to use processes instead of
# threads if you need parallel
# computation!

# FIXME: hack for Python-2.4; switch to itemgetter() once Python-2.6 is default
# use_refrec = itemgetter(slice(None))
# use_ref = itemgetter(0, 1)
# use_rec = itemgetter(2)
use_refrec = lambda x: x
use_ref = lambda x: x[0:2]
use_rec = lambda x: x[2]

# At first glance this may look silly.
# However, if we load the dictionaries
# uncoditionally there will be only
# one instance of them in the memory after
# fork

cit_dict = get_citation_dict("citationdict")
recit_dict = get_citation_dict("reversedict")

caches = []
def create_new_cache():
    ret = {}
    caches.append(ret)
    return ret


def clear_all_caches():
    for c in caches:
        c.clear()


_replacer = re.compile("[^a-zA-Z]")
def canonical_str(string):
    return _replacer.sub('', string).lower()


def jaccard(set1, set2):
    '''
    This is no longer jaccard distance.
    '''
    metadata_comparison_print("Jaccard: Found %d items in the first set." % len(set1))
    metadata_comparison_print("Jaccard: Found %d items in the second set." % len(set2))

    if not set1 or not set2:
        return '?'

    match = len(set1 & set2)
    ret = float(match) / float(len(set1) + len(set2) - match)

    metadata_comparison_print("Jaccard: %d common items." % match)
    metadata_comparison_print("Jaccard: returning %f." % ret)
    return ret


def cached_sym(reducing):
    '''
    Memoizes a pure function with two symmetrical arguments.
    '''
    def deco(func):
        cache = create_new_cache()
        def ret(a, b):
            ra, rb = reducing(a), reducing(b)

            if ra < rb:
                ra, rb = (ra, rb)
            else:
                ra, rb = (rb, ra)

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
    papers = _compare_papers(bibref1, bibref2)
    if papers != '?':
        return papers

    if bconfig.CFG_INSPIRE_SITE:
        insp_ids = _compare_inspireid(bibref1, bibref2)
        if insp_ids != '?':
            return insp_ids, 1.

    # unfortunately, we have to do all comparisons
    if bconfig.CFG_INSPIRE_SITE:
        func_weight = (
                   (_compare_affiliations, 1.),
                   (_compare_names, 5.),
                   (_compare_citations, .5),
                   (_compare_citations_by, .5),
                   (_compare_key_words, 2.),
                  )
    elif bconfig.CFG_ADS_SITE:
        func_weight = (
            (_compare_email, 3.),
            (_compare_unified_affiliations, 2.),
            (_compare_names, 5.),
    #        register(_compare_citations, .5)
    #        register(_compare_citations_by, .5)
            (_compare_key_words, 2.)
                       )

    else:
        func_weight = ((_compare_names, 5.),)

    results = [(func(bibref1, bibref2), weight) for func, weight in func_weight]


    coll = _compare_collaboration(bibref1, bibref2)
    if coll == '?':
        coll = _compare_coauthors(bibref1, bibref2)

    results.append((coll, 3.))
    total_weights = sum(res[1] for res in results)
    metadata_comparison_print("Final vector: %s." % str(results))
    results = filter(lambda x: x[0] != '?', results)

    if not results:
        return 0, 0

    cert = sum(starmap(mul, results))
    prob = sum(res[1] for res in results)
    return cert / prob, prob / total_weights


@cached_arg(use_refrec)
def _find_affiliation(bib):
    aff = get_grouped_records(bib, str(bib[0]) + '__u').values()[0]
    return set(canonical_str(a) for a in aff)


def _compare_affiliations(bib1, bib2):
    metadata_comparison_print("Comparing affiliations.")

    aff1 = _find_affiliation(bib1)
    aff2 = _find_affiliation(bib2)

    ret = jaccard(aff1, aff2)
    return ret


@cached_arg(use_refrec)
def _find_unified_affiliation(bib):
    aff = get_grouped_records(bib, str(bib[0]) + '__u').values()[0]
    return set(x for x in list(canonical_str(resolve_affiliation(a)) for a in aff) if not x == "None")


def _compare_unified_affiliations(bib1, bib2):
    metadata_comparison_print("Comparing affiliations.")

    aff1 = _find_affiliation(bib1)
    aff2 = _find_affiliation(bib2)

    ret = jaccard(aff1, aff2)
    return ret


@cached_arg(use_refrec)
def _find_inspireid(bib):
    ids = get_grouped_records(bib, str(bib[0]) + '__i').values()[0]
    return set(ids)


def _compare_inspireid(bib1, bib2):
    metadata_comparison_print("Comparing inspire ids.")

    iids1 = _find_inspireid(bib1)
    iids2 = _find_inspireid(bib2)

    metadata_comparison_print("Found %d, %d different inspire ids for the two sets." % (len(iids1), len(iids2)))
    if (len(iids1) != 1 or
        len(iids2) != 1):
        return '?'
    elif iids1 == iids2:
        metadata_comparison_print("The ids are the same.")
        return 1.
    else:
        metadata_comparison_print("The ids are different.")
        return 0.


@cached_arg(use_refrec)
def _find_email(bib):
    ids = get_grouped_records(bib, str(bib[0]) + '__m').values()[0]
    return set(ids)


def _compare_email(bib1, bib2):
    metadata_comparison_print("Comparing email addresses.")

    iids1 = _find_email(bib1)
    iids2 = _find_email(bib2)

    metadata_comparison_print("Found %d, %d different email addresses for the two sets."
                   % (len(iids1), len(iids2)))
    if (len(iids1) != 1 or
        len(iids2) != 1):
        return '?'
    elif iids1 == iids2:
        metadata_comparison_print("The addresses are the same.")
        return 1.0
    else:
        metadata_comparison_print("The addresses are there, but different.")
        return 0.3


def _compare_papers(bib1, bib2):
    metadata_comparison_print("Checking if the two bib refs are in the same paper.")
    if bib1[2] == bib2[2]:
        return '-'
    return '?'


get_name_by_bibrecref = cached_arg(use_ref)(get_name_by_bibrecref)

@cached_sym(use_ref)
def _compare_names(bib1, bib2):
    metadata_comparison_print("Comparing names.")

    name1 = get_name_by_bibrecref(bib1)
    name2 = get_name_by_bibrecref(bib2)

    if name1 and name2:
        return compare_names(name1, name2, False)
    return '?'


@cached_arg(use_rec)
def _find_key_words(bib):
    words = get_key_words(bib[2])
    return set(canonical_str(word) for word in words)


@cached_sym(use_rec)
def _compare_key_words(bib1, bib2):
    metadata_comparison_print("Comparing key words.")
    words1 = _find_key_words(bib1)
    words2 = _find_key_words(bib2)

    return jaccard(words1, words2)

@cached_arg(use_rec)
def _find_collaboration(bib):
    colls = get_collaboration(bib[2])
    return set(canonical_str(coll) for coll in colls)


@cached_sym(use_rec)
def _compare_collaboration(bib1, bib2):
    metadata_comparison_print("Comparing collaboration.")

    colls1 = _find_collaboration(bib1)
    colls2 = _find_collaboration(bib2)

    metadata_comparison_print("Found %d, %d different collaborations for the two sets." % (len(colls1), len(colls2)))
    if (len(colls1) != 1 or
        len(colls2) != 1):
        return '?'
    elif colls1 == colls2:
        return 1.
    else:
        return 0.


@cached_arg(use_rec)
def _find_coauthors(bib):
    return set(canonical_str(a) for a in get_all_authors(bib[2]))


@cached_sym(use_rec)
def _compare_coauthors(bib1, bib2):
    metadata_comparison_print("Comparing authors.")

    aths1 = _find_coauthors(bib1)
    aths2 = _find_coauthors(bib2)

    return jaccard(aths1, aths2)


@cached_arg(use_rec)
def _find_citations(bib):
    return set(cit_dict.get(bib[2], ()))


@cached_sym(use_rec)
def _compare_citations(bib1, bib2):
    metadata_comparison_print("Comparing citations.")

    cites1 = _find_citations(bib1)
    cites2 = _find_citations(bib2)

    return jaccard(cites1, cites2)


@cached_arg(use_rec)
def _find_citations_by(bib):
    return set(recit_dict.get(bib[2], ()))


@cached_sym(use_rec)
def _compare_citations_by(bib1, bib2):
    metadata_comparison_print("Comparing citations by.")

    cites1 = _find_citations_by(bib1)
    cites2 = _find_citations_by(bib2)

    return jaccard(cites1, cites2)


