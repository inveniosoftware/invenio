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

import re
from invenio import bibauthorid_config as bconfig
from itertools import starmap

from operator import mul, itemgetter
from invenio.bibauthorid_name_utils import compare_names
from invenio.bibauthorid_dbinterface import get_name_by_bibref
from invenio.bibauthorid_dbinterface import get_grouped_records
from invenio.bibauthorid_dbinterface import get_authors_of_paper
from invenio.bibauthorid_dbinterface import get_collaborations_for_paper
from invenio.bibauthorid_dbinterface import get_resolved_affiliation
from invenio.bibauthorid_backinterface import get_keywords_for_paper
from invenio.bibrank_citation_searcher import get_cited_by, get_refers_to
# metadat_comparison_print commented everywhere to increase performances,
# import and calls left here to make future debug easier.
from invenio.bibauthorid_logutils import Logger
import gc
import random

CFG_MEMOIZE_DICT_SIZE = 1000000

logger = Logger('metadata_comparison')
logger.verbose = bconfig.DEBUG_METADATA_COMPARISON_OUTPUT

# This module is not thread safe!
# Be sure to use processes instead of
# threads if you need parallel
# computation!

use_refrec = itemgetter(slice(None))
use_ref = itemgetter(0, 1)
use_rec = itemgetter(2)
use_string = lambda x: x


CACHES = list()


def create_new_cache():
    ret = dict()
    # global CACHES
    CACHES.append(ret)
    return ret


def clear_all_caches():
    # global CACHES
    for c in CACHES:
        c.clear()


_replacer = re.compile("[^a-zA-Z]")


def canonical_str(string):
    return _replacer.sub('', string).lower()


def jaccard(set1, set2):
    '''
    This is no longer jaccard distance.
    '''
    logger.log("Jaccard: Found %d items in the first set and %d in nthe second set" % (len(set1), len(set2)))

    if not set1 or not set2:
        return '?'

    match = len(set1 & set2)
    ret = match / float(len(set1) + len(set2) - match)

    logger.log("Jaccard: %d common items; returning %f" % (match, ret))
    return ret


def cached_sym(red):
    '''
    Memoizes a pure function with two symmetrical arguments.
    '''
    def deco(func):
        cache = create_new_cache()

        def ret(a, b):
            ra, rb = red(a), red(b)
            if ra > rb:
                ra, rb = rb, ra
            try:
                return cache[(ra, rb)]
            except KeyError:
                val = func(a, b)
                if len(cache) > CFG_MEMOIZE_DICT_SIZE:
                    keys = cache.keys()
                    random.shuffle(keys)
                    to_delete = keys[0:CFG_MEMOIZE_DICT_SIZE / 2]
                    map(cache.pop, to_delete)
                    gc.collect()
                cache[(ra, rb)] = val
                return val
        return ret
    return deco


def cached_arg(red):
    '''
    Memoizes a pure function.
    '''
    def deco(func):
        cache = create_new_cache()

        def ret(a):
            ra = red(a)
            try:
                return cache[ra]
            except KeyError:
                val = func(a)
                if len(cache) > CFG_MEMOIZE_DICT_SIZE:
                    keys = cache.keys()
                    random.shuffle(keys)
                    to_delete = keys[0:CFG_MEMOIZE_DICT_SIZE / 2]
                    map(cache.pop, to_delete)
                    gc.collect()
                cache[ra] = val
                return val
        return ret
    return deco


def check_comparison(fn):
    allowed = ['+', '-']

    def checked(a, b):
        val = fn(a, b)
        if isinstance(val, tuple):
            assert (val[0] >= 0 and val[0] <= 1), 'COMPARISON: Returned value not in range %s' % str(val)
            assert (val[1] >= 0 and val[1] <= 1), 'COMPARISON: Returned compatibility not in range %s' % str(val)
        else:
            assert val in allowed, 'COMPARISON: returned not tuple value not in range %s' % str(val)
        return val
    return checked

# The main function of this module


@check_comparison
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

    logger.log("")
    logger.log("Started comparing %s vs %s" % (str(bibref1), str(bibref2)))
    # try first the metrics, which might return + or -
    papers = _compare_papers(bibref1, bibref2)
    if papers != '?':
        return papers

#    if bconfig.CFG_INSPIRE_SITE:
#        insp_ids = _compare_inspireid(bibref1, bibref2)
#        if insp_ids != '?':
#            return insp_ids

    results = list()
    for func, weight, fname in cbrr_func_weight:
        r = func(bibref1, bibref2)
        assert r == '?' or (r <= 1 and r >= 0), 'COMPARISON %s returned %s for %s' % (fname, str(r), str(len(results)))
        results.append((r, weight))

    total_weights = sum(res[1] for res in results)

    logger.log("Final comparison vector: %s." % str(results))

    results = filter(lambda x: x[0] != '?', results)

    if not results:
        logger.log("Final result: Skipped all tests, returning 0,0")
        return (0, 0)

    cert = sum(starmap(mul, results))
    prob = sum(res[1] for res in results)
    vals = cert / prob, prob / total_weights
    assert vals[0] >= 0 and vals[0] <= 1, 'COMPARISON: RETURNING VAL out of range'
    assert vals[1] >= 0 and vals[1] <= 1, 'COMPARISON: RETURNING PROB out of range'

    logger.log("Final result: %s" % str(vals))

    return vals


@cached_arg(use_refrec)
def _find_affiliation(bib):
    aff = get_grouped_records(bib, str(bib[0]) + '__u').values()[0]
    return set(canonical_str(a) for a in aff)


def _compare_affiliations(bib1, bib2):
    logger.log("Comparing affiliations.")

    aff1 = _find_affiliation(bib1)
    aff2 = _find_affiliation(bib2)

    ret = jaccard(aff1, aff2)

    logger.log("Affiliations: %s %s %s", (str(aff1), str(aff2), str(ret)))
    return ret


@cached_arg(use_refrec)
def _find_unified_affiliation(bib):
    aff = get_grouped_records(bib, str(bib[0]) + '__u').values()[0]
    return set(x for x in list(canonical_str(get_resolved_affiliation(a)) for a in aff) if not x == "None")


def _compare_unified_affiliations(bib1, bib2):
    logger.log("Comparing unified affiliations.")

    aff1 = _find_affiliation(bib1)
    aff2 = _find_affiliation(bib2)

    ret = jaccard(aff1, aff2)

    logger.log("Affiliations: %s %s %s", (str(aff1), str(aff2), str(ret)))
    return ret


@cached_arg(use_refrec)
def _find_inspireid(bib):
    ids = get_grouped_records(bib, str(bib[0]) + '__i').values()[0]
    return set(ids)


def _compare_inspireid(bib1, bib2):
    logger.log("Comparing inspire ids.")

    iids1 = _find_inspireid(bib1)
    iids2 = _find_inspireid(bib2)

    logger.log("Found %d, %d different inspire ids for the two sets." % (len(iids1), len(iids2)))
    if (len(iids1) != 1 or
            len(iids2) != 1):
        return '?'

    elif iids1 == iids2:
        logger.log("The ids are the same.")
        return 1
    else:
        logger.log("The ids are different.")
        return 0


@cached_arg(use_refrec)
def _find_email(bib):
    ids = get_grouped_records(bib, str(bib[0]) + '__m').values()[0]
    return set(ids)


def _compare_email(bib1, bib2):
    logger.log("Comparing email addresses.")

    iids1 = _find_email(bib1)
    iids2 = _find_email(bib2)

    logger.log("Found %d, %d different email addresses for the two sets." % (len(iids1), len(iids2)))
    if (len(iids1) != 1 or
            len(iids2) != 1):
        return '?'
    elif iids1 == iids2:
        logger.log("The addresses are the same.")
        return 1.0
    else:
        logger.log("The addresses are there, but different.")
        return 0.3


def _compare_papers(bib1, bib2):
    logger.log("Checking if the two bib refs are in the same paper...")
    if bib1[2] == bib2[2]:
        logger.log("  ... Yes they are! Are you crazy, man?")
        return '-'
    return '?'


cached_get_name_by_bibrecref = cached_arg(use_ref)(get_name_by_bibref)
cached_compare_names = cached_sym(use_string)(compare_names)


@cached_sym(use_ref)
def _compare_names(bib1, bib2):
    logger.log("Comparing names.")

    name1 = cached_get_name_by_bibrecref(bib1)
    name2 = cached_get_name_by_bibrecref(bib2)

    logger.log(" Found %s and %s" % (name1, name2))
    if name1 and name2:
        cmpv = cached_compare_names(name1, name2)
        logger.log(" cmp(%s,%s) = %s" % (name1, name2, str(cmpv)))
        return cmpv
    return '?'


@cached_arg(use_rec)
def _find_key_words(bib):
    words = get_keywords_for_paper(bib[2])
    return set(canonical_str(word) for word in words)


@cached_sym(use_rec)
def _compare_key_words(bib1, bib2):
    logger.log("Comparing key words.")
    words1 = _find_key_words(bib1)
    words2 = _find_key_words(bib2)
    cmpv = jaccard(words1, words2)
    logger.log(" key words got (%s vs %s) for %s" % (words1, words2, cmpv))
    return cmpv


@cached_arg(use_rec)
def _find_collaboration(bib):
    colls = get_collaborations_for_paper(bib[2])
    return set(canonical_str(coll) for coll in colls)


@cached_sym(use_rec)
def _compare_collaboration(bib1, bib2):
    logger.log("Comparing collaboration.")

    colls1 = _find_collaboration(bib1)
    colls2 = _find_collaboration(bib2)

    logger.log("Found %d, %d different collaborations for the two sets." % (len(colls1), len(colls2)))
    if (len(colls1) != 1 or
            len(colls2) != 1):
        return '?'
    elif colls1 == colls2:
        return 1.
    else:
        return 0.


@cached_arg(use_rec)
def _find_coauthors(bib):
    return set(canonical_str(a) for a in get_authors_of_paper(bib[2]))


@cached_sym(use_rec)
def _compare_coauthors(bib1, bib2):
    logger.log("Comparing authors.")

    aths1 = _find_coauthors(bib1)
    aths2 = _find_coauthors(bib2)

    cmpv = jaccard(aths1, aths2)
    logger.log("   coauthors lists as %s" % (cmpv))
    return cmpv


@cached_arg(use_rec)
def _find_citations(bib):
    return get_cited_by(bib[2])


@cached_sym(use_rec)
def _compare_citations(bib1, bib2):
    logger.log("Comparing citations.")

    cites1 = _find_citations(bib1)
    cites2 = _find_citations(bib2)

    cmpv = jaccard(cites1, cites2)
    logger.log(" citations as %s" % cmpv)
    return cmpv


@cached_arg(use_rec)
def _find_citations_by(bib):
    return get_refers_to(bib[2])


@cached_sym(use_rec)
def _compare_citations_by(bib1, bib2):
    logger.log("Comparing citations by.")

    cites1 = _find_citations_by(bib1)
    cites2 = _find_citations_by(bib2)

    cmpv = jaccard(cites1, cites2)

    logger.log(" citations by as %s" % cmpv)

    return cmpv


# compare_bibrefrecs
# Unfortunately doing this assignment at every call of compare_bibrefrec is too expensive.
# Doing it here is much less elegant but much faster. Let's hope for better times to put it back
# where it belongs.

# unfortunately, we have to do all comparisons
if bconfig.CFG_INSPIRE_SITE:
    cbrr_func_weight = (
        (_compare_inspireid, .5, 'inspID'),
        (_compare_affiliations, .3, 'aff'),
        (_compare_names, 1., 'names'),
        #(_compare_citations, .1, 'cit'),
        #(_compare_citations_by, .1, 'citby'),
        #(_compare_key_words, .1, 'kw'),
        (_compare_collaboration, .3, 'collab'),
        #(_compare_coauthors, .1,'coauth')
    )
elif bconfig.CFG_ADS_SITE:
    cbrr_func_weight = (
        (_compare_email, 3., 'email'),
        (_compare_unified_affiliations, 2., 'aff'),
        (_compare_names, 5., 'names'),
        #        register(_compare_citations, .5)
        #        register(_compare_citations_by, .5)
        (_compare_key_words, 2., 'kw')
    )

else:
    cbrr_func_weight = ((_compare_names, 5., 'names'),)
