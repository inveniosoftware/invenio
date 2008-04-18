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

def init_db_dictionary(dname):
    """return a dictionary from rnkCITATIONDATA
    """
    query = "select object_value from rnkCITATIONDATA where object_name='"+dname+"'"
    try:
        compressed_sc_dic = run_sql(query)
    except OperationalError:
        compressed_sc_dic = []
    sc_dic = None
    if compressed_sc_dic and compressed_sc_dic[0] and compressed_sc_dic[0][0]:
        try:
            sc_dic = marshal.loads(decompress(compressed_sc_dic[0][0]))
        except error:
            sc_dic = []
    return sc_dic

cache_cited_by_dictionary = init_db_dictionary("citationdict")
cache_reference_list_dictionary = init_db_dictionary("reversedict")

### INTERFACE

def get_cited_by(recordid):
    """Return a list of records that cite recordid"""
    citation_dic = {} #one should always init variables
    query = "select object_value from rnkCITATIONDATA where object_name='citationdict'"
    compressed_citation_dic = run_sql_cached(query, affected_tables=['rnkCITATIONDATA'])
    if compressed_citation_dic and compressed_citation_dic[0]:
        try:
            citation_dic = marshal.loads(decompress(compressed_citation_dic[0][0]))
        except error:
            citation_dic = {}
    ret = [] #empty list
    if citation_dic.has_key(recordid):
        ret = citation_dic[recordid]
    return ret

def get_records_with_num_cites(numstr):
    """returns records are cited X times, X defined in numstr.
      Warning: numstr is string and may not be numeric! It can be 10,0-100,500+ etc"""
    matches = []
    #once again, check that the parameter is a string
    if not (type(numstr) == type("thisisastring")):
        return []
    numstr = numstr.replace(" ",'')
    numstr = numstr.replace('"','')
    #get the cited-by dictionary
    citedbydict = init_db_dictionary("citationdict")

    num = 0
    #first, check if numstr is just a number
    singlenum = re.findall("(^\d+$)", numstr)
    if singlenum:
        num = int(singlenum[0])
        for k in citedbydict.keys():
            li = citedbydict[k]
            if len(li) == num:
                matches.append(k)
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
            return []
        if (first <= sec):
            for k in citedbydict.keys():
                li = citedbydict[k]
                if len(li) >= first:
                    if len(li) <= sec:
                        matches.append(k)
            return matches

    firstsec = re.findall("(\d+)\+", numstr)
    if firstsec:
        first = firstsec[0]
        for k in citedbydict.keys():
            li = citedbydict[k]
            if len(li) > int(first):
                matches.append(k)
    return matches


def get_cited_by_list(recordlist):
    """Return a tuple of ([recid,list_of_citing_records],...) for all the
       records in recordlist.
    """
    result = []
    query = "select object_value from rnkCITATIONDATA where object_name='citationdict'"
    compressed_citation_weight_dic = run_sql(query)
    citation_dic = {} #init variable here in case of compr failure
    if compressed_citation_weight_dic and compressed_citation_weight_dic[0]:
        citation_dic = marshal.loads(decompress(compressed_citation_weight_dic[0][0]))
    rdic = {} #return this, based on values in citation_dic
    for recid in recordlist:
        if citation_dic  and citation_dic.has_key(recid) and citation_dic[recid]:
            tmp = [recid, citation_dic[recid]]
        else:
            tmp = [recid, 0]
        result.append(tmp)
    return result

def get_cited_by_weight(recordlist):
    """Return a tuple of ([recid,number_of_citing_records],...) for all the
       records in recordlist.
    """
    result = []
    tuples = get_cited_by_list(recordlist)
    for recid, rlist in tuples:
        #just return recid - lenght
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
    # get their weights, this is weighted citation_list (x is cited by y)
    query = "select relevance_data from rnkMETHODDATA, rnkMETHOD WHERE rnkMETHOD.id=rnkMETHODDATA.id_rnkMETHOD and rnkMETHOD.name='citation'"
    compressed_citation_weight_dic = run_sql(query)
    if compressed_citation_weight_dic and compressed_citation_weight_dic[0]:
        #has to be prepared for corrupted data!
        try:
            citation_dic = marshal.loads(decompress(compressed_citation_weight_dic[0][0]))
            #citation_dic is {1: 0, .. 81: 4, 82: 0, 83: 0, 84: 3} etc, e.g. recnum-weight
            for id in citation_list:
                if citation_dic.has_key(id):
                    tmp = [id, citation_dic[id]]
                    result.append(tmp)
        except error:
            for id in citation_list:
                tmp = [id, 1]
                result.append(tmp)
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
    #quote authorstring in case there are authors like 't Hoof
    authorstring = authorstring.replace("'","\\'")
    query = """select hitlist from rnkAUTHORDATAR where aterm ='%s'""" % authorstring
    ablob = run_sql(query)
    if ablob and ablob[0] and ablob[0][0]:
        #has to be prepared for corrupted data!
        try:
            citations = marshal.loads(decompress(ablob[0][0]))
        except Error:
            citations = []
    return citations


def get_self_cited_by(record_id):
    """Return a list of doc ids [y1,y2,..] for the
       rec id x given as param, so that x cites y1,y2,.. and x and each y share an author
    """
    result = []
    sc = init_db_dictionary("selfcitdict")
    if sc and sc.has_key(record_id):
        result.extend(sc[record_id])
    if (len(result) == 0):
        return None
    return result

def get_self_cited_in(record_id):
    """Return a list of doc ids [y1,y2,..] for the
       rec id x given as param, so that x is cited in y1,y2,.. and x and each y share an author
    """
    result = []
    sc = init_db_dictionary("selfcitedbydict")
    if sc and sc.has_key(record_id):
        result.extend(sc[record_id])
    if (len(result) == 0):
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
