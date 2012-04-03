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

from invenio.dbquery import run_sql, get_table_update_time, OperationalError, \
        deserialize_via_marshal
from invenio.intbitset import intbitset
from invenio.data_cacher import DataCacher

class CitationDictsDataCacher(DataCacher):
    """
    Cache holding all citation dictionaries (citationdict,
    reversedict, selfcitdict, selfcitedbydict).
    """
    def __init__(self):
        def cache_filler():
            alldicts = {}
            try:
                res = run_sql("SELECT object_name,object_value FROM rnkCITATIONDATA")
            except OperationalError:
                # database problems, return empty cache
                return {}
            for row in res:
                object_name = row[0]
                object_value = row[1]
                try:
                    object_value_dict = deserialize_via_marshal(object_value)
                except:
                    object_value_dict = {}
                alldicts[object_name] = object_value_dict
                if object_name == 'citationdict':
                    # for cited:M->N queries, it is interesting to cache also
                    # some preprocessed citationdict:
                    alldicts['citationdict_keys'] = object_value_dict.keys()
                    alldicts['citationdict_keys_intbitset'] = intbitset(object_value_dict.keys())
            return alldicts
        def timestamp_verifier():
            res = run_sql("""SELECT DATE_FORMAT(last_updated, '%Y-%m-%d %H:%i:%s')
                              FROM rnkMETHOD WHERE name='citation'""")
            if res:
                return res[0][0]
            else:
                return '0000-00-00 00:00:00'

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
    return CACHE_CITATION_DICTS.cache.get(dictname, {})

def get_refers_to(recordid):
    """Return a list of records referenced by this record"""
    ret = []
    cache_cited_by_dictionary = get_citation_dict("reversedict")
    if cache_cited_by_dictionary.has_key(recordid):
        ret = cache_cited_by_dictionary[recordid]
    return ret

def get_cited_by(recordid):
    """Return a list of records that cite recordid"""
    ret = []
    cache_cited_by_dictionary = get_citation_dict("citationdict")
    if cache_cited_by_dictionary.has_key(recordid):
        ret = cache_cited_by_dictionary[recordid]
    return ret

def get_cited_by_count(recordid):
    """Return how many records cite given RECORDID."""
    cache_cited_by_dictionary = get_citation_dict("citationdict")
    return len(cache_cited_by_dictionary.get(recordid, []))

def get_records_with_num_cites(numstr, allrecs = intbitset([])):
    """Return an intbitset of record IDs that are cited X times,
       X defined in numstr.
       Warning: numstr is string and may not be numeric! It can
       be 10,0->100 etc
    """
    cache_cited_by_dictionary = get_citation_dict("citationdict")
    cache_cited_by_dictionary_keys = get_citation_dict("citationdict_keys")
    cache_cited_by_dictionary_keys_intbitset = get_citation_dict("citationdict_keys_intbitset")
    matches = intbitset([])
    #once again, check that the parameter is a string
    if not (type(numstr) == type("thisisastring")):
        return intbitset([])
    numstr = numstr.replace(" ",'')
    numstr = numstr.replace('"','')

    num = 0
    #first, check if numstr is just a number
    singlenum = re.findall("(^\d+$)", numstr)
    if singlenum:
        num = int(singlenum[0])
        if num == 0:
            #we return recids that are not in keys
            return allrecs - cache_cited_by_dictionary_keys_intbitset
        for k in cache_cited_by_dictionary_keys:
            li = cache_cited_by_dictionary[k]
            if len(li) == num:
                matches.add(k)
        return matches

    #try to get 1->10 or such
    firstsec = re.findall("(\d+)->(\d+)", numstr)
    if firstsec:
        first = 0
        sec = -1
        try:
            first = int(firstsec[0][0])
            sec = int(firstsec[0][1])
        except:
            return intbitset([])
        if (first == 0):
            #start with those that have no cites..
            matches = allrecs - cache_cited_by_dictionary_keys_intbitset
        if (first <= sec):
            for k in cache_cited_by_dictionary_keys:
                li = cache_cited_by_dictionary[k]
                if len(li) >= first:
                    if len(li) <= sec:
                        matches.add(k)
            return matches

    firstsec = re.findall("(\d+)\+", numstr)
    if firstsec:
        first = firstsec[0]
        for k in cache_cited_by_dictionary_keys:
            li = cache_cited_by_dictionary[k]
            if len(li) > int(first):
                matches.add(k)
    return matches

def get_cited_by_list(recordlist):
    """Return a tuple of ([recid,list_of_citing_records],...) for all the
       records in recordlist.
    """
    cache_cited_by_dictionary = get_citation_dict("citationdict")
    result = []
    for recid in recordlist:
        result.append([recid, cache_cited_by_dictionary.get(recid, [])])
    return result

def get_refersto_hitset(ahitset):
    """
    Return a hitset of records that refers to (cite) some records from
    the given ahitset.  Useful for search engine's
    refersto:author:ellis feature.
    """
    cache_cited_by_dictionary = get_citation_dict("citationdict")
    out = intbitset()
    if ahitset:
        try:
            for recid in ahitset:
                out = out | intbitset(cache_cited_by_dictionary.get(recid, []))
        except OverflowError:
            # ignore attempt to iterate over infinite ahitset
            pass
    return out

def get_citedby_hitset(ahitset):
    """
    Return a hitset of records that are cited by records in the given
    ahitset.  Useful for search engine's citedby:author:ellis feature.
    """
    cache_cited_by_dictionary = get_citation_dict("reversedict")
    out = intbitset()
    if ahitset:
        try:
            for recid in ahitset:
                out = out | intbitset(cache_cited_by_dictionary.get(recid, []))
        except OverflowError:
            # ignore attempt to iterate over infinite ahitset
            pass
    return out

def get_cited_by_weight(recordlist):
    """Return a tuple of ([recid,number_of_citing_records],...) for all the
       records in recordlist.
    """
    cache_cited_by_dictionary = get_citation_dict("citationdict")
    result = []
    for recid in recordlist:
        result.append([recid, len(cache_cited_by_dictionary.get(recid, []))])
    return result

def calculate_cited_by_list(record_id, sort_order="d"):
    """Return a tuple of ([recid,citation_weight],...) for all the
       record citing RECORD_ID.  The resulting recids is sorted by
       ascending/descending citation weights depending or SORT_ORDER.
    """
    cache_cited_by_dictionary = get_citation_dict("citationdict")
    citation_list = []
    result = []
    # determine which record cite RECORD_ID:
    if cache_cited_by_dictionary:
        citation_list = cache_cited_by_dictionary.get(record_id, [])
    #add weights i.e. records that cite each of the entries in citation_list
    for c in citation_list:
        ccited = cache_cited_by_dictionary.get(c, [])
        result.append([c, len(ccited)])
    # sort them:
    if result:
        if sort_order == "d":
            result.sort(lambda x, y: cmp(y[1], x[1]))
        else:
            result.sort(lambda x, y: cmp(x[1], y[1]))

    return result

def get_author_cited_by(authorstring):
    """Return a list of doc ids [y1,y2,..] for the
       author given as param, such that y1,y2.. cite that author
    """
    citations = []
    res = run_sql("select hitlist from rnkAUTHORDATA where aterm=%s",
                  (authorstring,))
    if res and res[0] and res[0][0]:
        #has to be prepared for corrupted data!
        try:
            citations = deserialize_via_marshal(res[0][0])
        except:
            citations = []
    return citations

def get_self_cited_by(record_id):
    """Return a list of doc ids [y1,y2,..] for the
       rec id x given as param, so that x cites y1,y2,.. and x and each y share an author
    """
    cache_selfcit_dictionary = get_citation_dict("selfcitdict")
    result = []
    if cache_selfcit_dictionary and cache_selfcit_dictionary.has_key(record_id):
        result.extend(cache_selfcit_dictionary[record_id])
    if not result:
        return None
    return result

def get_self_cited_in(record_id):
    """Return a list of doc ids [y1,y2,..] for the
       rec id x given as param, so that x is cited in y1,y2,.. and x and each y share an author
    """
    cache_selfcitedby_dictionary = get_citation_dict("selfcitedbydict")
    result = []
    if cache_selfcitedby_dictionary and cache_selfcitedby_dictionary.has_key(record_id):
        result.extend(cache_selfcitedby_dictionary[record_id])
    if not result:
        return None
    return result

def calculate_co_cited_with_list(record_id, sort_order="d"):
    """Return a tuple of ([recid,co-cited weight],...) for records
       that are co-cited with RECORD_ID.  The resulting recids is sorted by
       ascending/descending citation weights depending or SORT_ORDER.
    """
    cache_cited_by_dictionary = get_citation_dict("citationdict")
    cache_reference_list_dictionary = get_citation_dict("reversedict")
    result = []
    result_intermediate = {}
    citation_list = []
    if cache_cited_by_dictionary:
        citation_list = cache_cited_by_dictionary.get(record_id, [])
    for cit_id in citation_list:
        reference_list = []
        if cache_reference_list_dictionary:
            reference_list = cache_reference_list_dictionary.get(cit_id, [])
        for ref_id in reference_list:
            if not result_intermediate.has_key(ref_id):
                result_intermediate[ref_id] = 1
            else: result_intermediate[ref_id] += 1
    for key, value in result_intermediate.iteritems():
        if not (key==record_id):
            result.append([key, value])
    if result:
        if sort_order == "d":
            result.sort(lambda x, y: cmp(y[1], x[1]))
        else:
            result.sort(lambda x, y: cmp(x[1], y[1]))
    return result
