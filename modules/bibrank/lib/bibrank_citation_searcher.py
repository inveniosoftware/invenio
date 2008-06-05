# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

__revision__ = "$Id$"

import re
import marshal
from zlib import decompress, error

from invenio.dbquery import run_sql, run_sql_cached, OperationalError
from invenio.intbitset import intbitset

def init_db_dictionary(dname):
    """return a dictionary from rnkCITATIONDATA
    """
    query = "select object_value from rnkCITATIONDATA where object_name='"+dname+"'"
    try:
        compressed_sc_dic = run_sql(query)
    except OperationalError:
        compressed_sc_dic = []
    sc_dic = {}
    if compressed_sc_dic and compressed_sc_dic[0] and compressed_sc_dic[0][0]:
        try:
            sc_dic = marshal.loads(decompress(compressed_sc_dic[0][0]))
        except error:
            sc_dic = {}
    return sc_dic

cache_cited_by_dictionary = init_db_dictionary("citationdict")
cache_cited_by_dictionary_keys = cache_cited_by_dictionary.keys()
cache_cited_by_dictionary_keys_intbitset = intbitset(cache_cited_by_dictionary.keys())
cache_reference_list_dictionary = init_db_dictionary("reversedict")
cache_selfcit_dictionary = init_db_dictionary("selfcitdict")
cache_selfcitedby_dictionary = init_db_dictionary("selfcitdict")

### INTERFACE

def get_cited_by(recordid):
    """Return a list of records that cite recordid"""
    ret = []
    if cache_cited_by_dictionary.has_key(recordid):
        ret = cache_cited_by_dictionary[recordid]
    return ret

def get_cited_by_count(recordid):
    """Return how many records cite given RECORDID."""
    return len(cache_cited_by_dictionary.get(recordid, []))

def get_records_with_num_cites(numstr, allrecs = intbitset([])):
    """Return an intbitset of record IDs that are cited X times,
       X defined in numstr.
       Warning: numstr is string and may not be numeric! It can
       be 10,0->100 etc
    """
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
    result = []
    for recid in recordlist:
        if cache_cited_by_dictionary.has_key(recid):
            tmp = [recid, cache_cited_by_dictionary[recid]]
        else:
            tmp = [recid, []]
        result.append(tmp)
    return result

def get_cited_by_weight(recordlist):
    """Return a tuple of ([recid,number_of_citing_records],...) for all the
       records in recordlist.
    """
    result = []
    tuples = get_cited_by_list(recordlist)
    for recid, rlist in tuples:
        #just return recid - length
        if rlist:
            tmp = [recid, len(rlist)]
        else:
            tmp = [recid, 0]
        result.append(tmp)
    return result

def calculate_cited_by_list(record_id, sort_order="d"):
    """Return a tuple of ([recid,citation_weight],...) for all the
       record in citing RECORD_ID.  The resulting recids is sorted by
       ascending/descending citation weights depending or SORT_ORDER.
    """
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
    res = run_sql("select hitlist from rnkAUTHORDATAR where aterm=%s",
                  (authorstring,))
    if res and res[0] and res[0][0]:
        #has to be prepared for corrupted data!
        try:
            citations = marshal.loads(decompress(res[0][0]))
        except Error:
            citations = []
    return citations

def get_self_cited_by(record_id):
    """Return a list of doc ids [y1,y2,..] for the
       rec id x given as param, so that x cites y1,y2,.. and x and each y share an author
    """
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
