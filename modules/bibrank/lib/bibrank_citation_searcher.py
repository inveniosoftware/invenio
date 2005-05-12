# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002 CERN.
##
## The CDSware is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## The CDSware is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDSware; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from marshal import loads
from zlib import decompress
from dbquery import run_sql

def init_cited_by_dictionary():
    """return citation list dictionary from rnkCITATIONDATA
    """
    query = "select citation_data from rnkCITATIONDATA"
    compressed_citation_dic = run_sql(query)
    citation_dic = None
    if compressed_citation_dic and compressed_citation_dic[0]:
        citation_dic = loads(decompress(compressed_citation_dic[0][0]))
    return citation_dic

def init_reference_list_dictionary():
    """return reference list dictionary from rnkCITATIONDATA
    """
    query = "select citation_data_reversed from rnkCITATIONDATA"
    compressed_ref_dic = run_sql(query)
    ref_dic = None
    if compressed_ref_dic and compressed_ref_dic[0]:
        ref_dic = loads(decompress(compressed_ref_dic[0][0]))
    return ref_dic

cache_cited_by_dictionary = init_cited_by_dictionary()
cache_reference_list_dictionary = init_reference_list_dictionary()

### INTERFACE

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
    # get their weights:
    query = "select relevance_data from rnkMETHODDATA, rnkMETHOD WHERE rnkMETHOD.id=rnkMETHODDATA.id_rnkMETHOD and rnkMETHOD.name='cit'"
    compressed_citation_weight_dic = run_sql(query)
    if compressed_citation_weight_dic and compressed_citation_weight_dic[0]:
        citation_dic = loads(decompress(compressed_citation_weight_dic[0][0]))
        for id in citation_list:
            tmp = [id, citation_dic[id]]
            result.append(tmp)
    # sort them:
    if result:
        if sort_order == "d":
            result.sort(lambda x, y: cmp(y[1], x[1]))
        else:
            result.sort(lambda x, y: cmp(x[1], y[1]))
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
