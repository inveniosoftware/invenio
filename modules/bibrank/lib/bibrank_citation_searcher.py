# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

__revision__ = "$Id$"

import re

from invenio.dbquery import run_sql
from invenio.intbitset import intbitset
from invenio.data_cacher import DataCacher
from invenio.redisutils import get_redis
from invenio.dbquery import deserialize_via_marshal
from operator import itemgetter


class CitationDictsDataCacher(DataCacher):
    """
    Cache holding all citation dictionaries (citationdict,
    reversedict, selfcitdict, selfcitedbydict).
    """
    def __init__(self):

        def fill():
            alldicts = {}
            from invenio.bibrank_tag_based_indexer import fromDB
            redis = get_redis()
            serialized_weights = redis.get('citations_weights')
            if serialized_weights:
                weights = deserialize_via_marshal(serialized_weights)
            else:
                weights = fromDB('citation')

            alldicts['citations_weights'] = weights
            # for cited:M->N queries, it is interesting to cache also
            # some preprocessed citationdict:
            alldicts['citations_keys'] = intbitset(weights.keys())

            # Citation counts
            alldicts['citations_counts'] = [t for t in weights.iteritems()]
            alldicts['citations_counts'].sort(key=itemgetter(1), reverse=True)

            # Self-cites
            serialized_weights = redis.get('selfcites_weights')
            if serialized_weights:
                selfcites = deserialize_via_marshal(serialized_weights)
            else:
                selfcites = fromDB('selfcites')
            selfcites_weights = {}
            for recid, counts in alldicts['citations_counts']:
                selfcites_weights[recid] = counts - selfcites.get(recid, 0)
            alldicts['selfcites_weights'] = selfcites_weights
            alldicts['selfcites_counts'] = [(recid, selfcites_weights.get(recid, cites)) for recid, cites in alldicts['citations_counts']]
            alldicts['selfcites_counts'].sort(key=itemgetter(1), reverse=True)

            return alldicts

        def cache_filler():
            self.cache = None  # misfire from pylint: disable=W0201
                               # this is really defined in DataCacher
            return fill()

        from invenio.bibrank_tag_based_indexer import get_lastupdated

        def timestamp_verifier():
            citation_lastupdate = get_lastupdated('citation')
            if citation_lastupdate:
                return citation_lastupdate.strftime("%Y-%m-%d %H:%M:%S")
            else:
                return "0000-00-00 00:00:00"

        DataCacher.__init__(self, cache_filler, timestamp_verifier)

CACHE_CITATION_DICTS = None


def get_citation_dict(dictname):
    """
    Returns a cached value of a citation dictionary. Performs lazy
    loading, i.e. loads the dictionary the first time it is actually
    used.

    @param dictname: the name of the citation dictionary to return. Can
            be citationdict, reversedict, selfcitdict, selfcitedbydict.
    @type dictname: string
    @return: a citation dictionary. The structure of the dictionary is
            { recid -> [list of recids] }.
    @rtype: dictionary
    """
    global CACHE_CITATION_DICTS
    if CACHE_CITATION_DICTS is None:
        CACHE_CITATION_DICTS = CitationDictsDataCacher()
    else:
        CACHE_CITATION_DICTS.recreate_cache_if_needed()
    return CACHE_CITATION_DICTS.cache[dictname]


def get_refers_to(recordid):
    """Return a list of records referenced by this record"""
    rows = run_sql("SELECT citee FROM rnkCITATIONDICT WHERE citer = %s",
                   [recordid])
    return set(r[0] for r in rows)


def get_cited_by(recordid):
    """Return a list of records that cite recordid"""
    rows = run_sql("SELECT citer FROM rnkCITATIONDICT WHERE citee = %s",
                   [recordid])
    return set(r[0] for r in rows)


def get_cited_by_count(recordid):
    """Return how many records cite given RECORDID."""
    rows = run_sql("SELECT 1 FROM rnkCITATIONDICT WHERE citee = %s",
                   [recordid])
    return len(rows)


def get_records_with_num_cites(numstr, allrecs=intbitset([]),
                               exclude_selfcites=False):
    """Return an intbitset of record IDs that are cited X times,
       X defined in numstr.
       Warning: numstr is string and may not be numeric! It can
       be 10,0->100 etc
    """
    if exclude_selfcites:
        cache_cited_by_dictionary_counts = get_citation_dict("selfcites_counts")
        citations_keys = intbitset(get_citation_dict("selfcites_weights").keys())
    else:
        cache_cited_by_dictionary_counts = get_citation_dict("citations_counts")
        citations_keys = get_citation_dict("citations_keys")

    matches = intbitset()
    #once again, check that the parameter is a string
    if type(numstr) != type("thisisastring"):
        return matches
    numstr = numstr.replace(" ", '')
    numstr = numstr.replace('"', '')

    num = 0
    #first, check if numstr is just a number
    singlenum = re.findall("^\d+$", numstr)
    if singlenum:
        num = int(singlenum[0])
        if num == 0:
            #we return recids that are not in keys
            return allrecs - citations_keys
        else:
            return intbitset([recid for recid, cit_count
                        in cache_cited_by_dictionary_counts
                        if cit_count == num])

    # Try to get 1->10 or such
    firstsec = re.findall("(\d+)->(\d+)", numstr)
    if firstsec:
        first = int(firstsec[0][0])
        sec = int(firstsec[0][1])
        if first == 0:
            # Start with those that have no cites..
    	    matches = allrecs - citations_keys
        if first <= sec:
            matches += intbitset([recid for recid, cit_count
                             in cache_cited_by_dictionary_counts
                             if first <= cit_count <= sec])
        return matches

    # Try to get 10+
    firstsec = re.findall("(\d+)\+", numstr)
    if firstsec:
        first = int(firstsec[0])
        matches = intbitset([recid for recid, cit_count
                         in cache_cited_by_dictionary_counts \
                         if cit_count > first])

    return matches


def get_cited_by_list(recids):
    """Return a tuple of ([recid,list_of_citing_records],...) for all the
       records in recordlist.
    """
    if not recids:
        return []

    in_sql = ','.join('%s' for dummy in recids)
    rows = run_sql("""SELECT citer, citee FROM rnkCITATIONDICT
                       WHERE citee IN (%s)""" % in_sql, recids)

    cites = {}
    for citer, citee in rows:
        cites.setdefault(citee, set()).add(citer)

    return [(recid, cites.get(recid, set())) for recid in recids]


def get_refers_to_list(recids):
    """Return a tuple of ([recid,list_of_citing_records],...) for all the
       records in recordlist.
    """
    if not recids:
        return []

    in_sql = ','.join('%s' for dummy in recids)
    rows = run_sql("""SELECT citee, citer FROM rnkCITATIONDICT
                       WHERE citer IN (%s)""" % in_sql, recids)

    refs = {}
    for citee, citer in rows:
        refs.setdefault(citer, set()).add(citee)

    return [(recid, refs.get(recid, set())) for recid in recids]


def get_refersto_hitset(ahitset):
    """
    Return a hitset of records that refers to (cite) some records from
    the given ahitset.  Useful for search engine's
    refersto:author:ellis feature.
    """
    out = intbitset()
    if ahitset:
        try:
            iter(ahitset)
        except OverflowError:
            # ignore attempt to iterate over infinite ahitset
            pass
        else:
            in_sql = ','.join('%s' for dummy in ahitset)
            rows = run_sql("""SELECT citer FROM rnkCITATIONDICT
                              WHERE citee IN (%s)""" % in_sql, ahitset)
            out = intbitset(rows)
    return out

def get_one_cited_by_weight(recID):
    """Returns a number_of_citing_records for one record
    """
    weight = get_citation_dict("citations_weights")

    return weight.get(recID, 0)

def get_cited_by_weight(recordlist):
    """Return a tuple of ([recid,number_of_citing_records],...) for all the
       records in recordlist.
    """
    weights = get_citation_dict("citations_weights")

    result = []
    for recid in recordlist:
        result.append([recid, weights.get(recid, 0)])

    return result


def get_citedby_hitset(ahitset):
    """
    Return a hitset of records that are cited by records in the given
    ahitset.  Useful for search engine's citedby:author:ellis feature.
    """
    out = intbitset()
    if ahitset:
        try:
            iter(ahitset)
        except OverflowError:
            # ignore attempt to iterate over infinite ahitset
            pass
        else:
            in_sql = ','.join('%s' for dummy in ahitset)
            rows = run_sql("""SELECT citee FROM rnkCITATIONDICT
                              WHERE citer IN (%s)""" % in_sql, ahitset)
            out = intbitset(rows)
    return out


def calculate_cited_by_list(record_id, sort_order="d"):
    """Return a tuple of ([recid,citation_weight],...) for all the
       record citing RECORD_ID.  The resulting recids is sorted by
       ascending/descending citation weights depending or SORT_ORDER.
    """
    result = []

    citation_list = get_cited_by(record_id)

    # Add weights i.e. records that cite each of the entries in citation_list
    weights = get_citation_dict("citations_weights")
    for c in citation_list:
        result.append([c, weights.get(c, 0)])

    # sort them
    reverse = sort_order == "d"
    result.sort(key=itemgetter(1), reverse=reverse)
    return result


def calculate_co_cited_with_list(record_id, sort_order="d"):
    """Return a tuple of ([recid,co-cited weight],...) for records
       that are co-cited with RECORD_ID.  The resulting recids is sorted by
       ascending/descending citation weights depending or SORT_ORDER.
    """
    result = []
    result_intermediate = {}

    for cit_id in get_cited_by(record_id):
        for ref_id in get_refers_to(cit_id):
            if ref_id not in result_intermediate:
                result_intermediate[ref_id] = 1
            else:
                result_intermediate[ref_id] += 1
    for key, value in result_intermediate.iteritems():
        if key != record_id:
            result.append([key, value])
    reverse = sort_order == "d"
    result.sort(key=itemgetter(1), reverse=reverse)
    return result


def get_citers_log(recid):
    return run_sql("""SELECT citer, type, action_date
                      FROM rnkCITATIONLOG
                      WHERE citee = %s
                      ORDER BY action_date DESC""", [recid])
