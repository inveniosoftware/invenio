# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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

import time
import sys
import os
import marshal
from zlib import decompress, compress, error

from invenio.dbquery import run_sql, serialize_via_marshal, deserialize_via_marshal
from invenio.search_engine import print_record, search_pattern
from invenio.bibrecord import create_records, record_get_field_values, record_get_field_value
from invenio.bibformat_utils import parse_tag
from invenio.bibtask import write_message, task_get_option

class memoise:
    def __init__(self, function):
        self.memo = {}
        self.function = function
    def __call__(self, *args):
        if self.memo.has_key(args):
            return self.memo[args]
        else:
            object = self.memo[args] = self.function(*args)
            return object

def get_recids_matching_query(pvalue, fvalue):
    """Return list of recIDs matching query for PVALUE and FVALUE."""
    rec_id = list(search_pattern(p=pvalue, f=fvalue, m='e'))
    return rec_id
get_recids_matching_query = memoise(get_recids_matching_query)

def get_citation_weight(rank_method_code, config):
    """return a dictionary which is used by bibrank daemon for generating
    the index of sorted research results by citation inforamtion
    """
    begin_time = time.time()
    last_update_time = get_bibrankmethod_lastupdate(rank_method_code)
    #if task_get_option('verbose') >= 3:	
    last_modified_records = get_last_modified_rec(last_update_time)
    write_message("Last update "+str(last_update_time)+" records: "+str(len(last_modified_records)), sys.stderr)	

    if last_modified_records:
        updated_recid_list = create_recordid_list(last_modified_records)
        result_intermediate = last_updated_result(rank_method_code, updated_recid_list)
        #result_intermed should be warranted to exists!
        citation_weight_dic_intermediate = result_intermediate[0]
        citation_list_intermediate = result_intermediate[1]
        reference_list_intermediate = result_intermediate[2]
        citation_informations = get_citation_informations(updated_recid_list, config)
	#write_message("citation_informations: "+str(citation_informations),sys.stderr)
        dic = ref_analyzer(citation_informations, citation_weight_dic_intermediate, citation_list_intermediate, reference_list_intermediate,config) #dic is docid-numberofreferences like {1: 2, 2: 0, 3: 1}
	#write_message("Docid-number of known references "+str(dic),sys.stderr)
        end_time = time.time()
        print "Total time of software: ", (end_time - begin_time)
    else:
        dic = {}
        print "No new records added since last time this rank method was executed"
    return dic

def get_bibrankmethod_lastupdate(rank_method_code):
    """return the last excution date of bibrank method
    """
    query = """select last_updated from rnkMETHOD where name ='%s'""" % rank_method_code
    last_update_time = run_sql(query)
    r = last_update_time[0][0]
    if r is None:
        return "0000-00-00 00:00:00"
    return r

def get_last_modified_rec(bibrank_method_lastupdate):
    """ return the list of recods which have been modified after the last execution
        of bibrank method. The result is expected to have ascending numerical order.
    """
    query = """SELECT id FROM bibrec WHERE modification_date>= '%s' """ % bibrank_method_lastupdate
    query += "order by id ASC"
    list = run_sql(query)
    return list

def create_recordid_list(rec_ids):
    """Create a list of record ids out of RECIDS. The result is expected to have ascending numerical order.
    """
    rec_list = []
    for row in rec_ids:
        rec_list.append(row[0])
    return rec_list

def create_record_tuple(list):
    """Creates a tuple of record id from a list of id.
       The result is expected to have ascending numerical order.
    """
    list_length = len(list)
    if list_length:
        rec_tuple = '('
        for row in list[0:list_length-1]:
            rec_tuple += str(row)
            rec_tuple += ','
        rec_tuple += str(list[list_length-1])
        rec_tuple += ')'
    else: rec_tuple = '()'
    return rec_tuple

def last_updated_result(rank_method_code, recid_list):
    """ return the last value of dictionary in rnkMETHODDATA table if it exists and
        initialize the value of last updated records by zero,otherwise an initial dictionary
        with zero as value for all recids
    """
    result = make_initial_result()
    query = """select relevance_data from rnkMETHOD, rnkMETHODDATA where
               rnkMETHOD.id = rnkMETHODDATA.id_rnkMETHOD and rnkMETHOD.Name = '%s'"""% rank_method_code
    dict = run_sql(query)
    if dict and dict[0] and dict[0][0]:
        #has to be prepared for corrupted data!
        try:
            dic = marshal.loads(decompress(dict[0][0]))
        except error:
            return result
        query = "select object_value from rnkCITATIONDATA where object_name='citationdict'"
        cit_compressed = run_sql(query)
        cit = []
        if cit_compressed and cit_compressed[0] and cit_compressed[0][0]:
            cit = marshal.loads(decompress(cit_compressed[0][0]))
            if cit:
                query = "select object_value from rnkCITATIONDATA where object_name='reversedict'"
                ref_compressed = run_sql(query)
                if ref_compressed and ref_compressed[0] and ref_compressed[0][0]:
                    ref = marshal.loads(decompress(ref_compressed[0][0]))
                    result = get_initial_result(dic, cit, ref, recid_list)
    return result

def get_initial_result(dic, cit, ref, recid_list):
    """initialieze the citation weights of the last updated record with zero for
       recalculating it later
    """
    for recid in recid_list:
        dic[recid] = 0
        cit[recid] = []
        if ref.has_key(recid) and ref[recid]:
            for id in ref[recid]:
                if cit.has_key(id) and recid in cit[id]:
                    cit[id].remove(recid)
                    dic[id] -= 1
        if cit.has_key(recid) and cit[recid]:
            for id in cit[recid]:
                if ref.has_key(id) and recid in ref[id]:
                    ref[id].remove(recid)
        ref[recid] = []
    return [dic, cit, ref]

def make_initial_result():
    """return an initial dictinary with recID as key and zero as value
    """
    dic = {}
    cit = {}
    ref = {}
    query = "select id from bibrec"
    res = run_sql(query)
    for key in res:
        dic[key[0]] = 0
        cit[key[0]] = []
        ref[key[0]] = []
    return [dic, cit, ref]

def get_citation_informations(recid_list, config):
    """returns a 3-part dictionary that contains the citation information of cds records
       examples: [ {} {} {} ]
                 [ { 93: ['astro-ph/9812088']},{ 93: ['Phys. Rev. Lett. 96 (2006) 081301'] }, {} ]
	         part 1: parsed from fulltext  part 2: parsed from record
    """
    begin_time = os.times()[4]
    d_reports_numbers = {}
    d_references_report_numbers = {}
    d_references_s = {}
    d_records_s = {}
    citation_informations = []
    record_pri_number_tag = config.get(config.get("rank_method", "function"),"publication_primary_number_tag")
    record_add_number_tag = config.get(config.get("rank_method", "function"),"publication_aditional_number_tag")
    reference_number_tag = config.get(config.get("rank_method", "function"),"publication_reference_number_tag")
    reference_tag = config.get(config.get("rank_method", "function"),"publication_reference_tag")
    record_publication_info_tag = config.get(config.get("rank_method", "function"),"publication_info_tag")

    p_record_pri_number_tag = parse_tag(record_pri_number_tag)
    p_record_add_number_tag = parse_tag(record_add_number_tag)
    p_reference_number_tag = parse_tag(reference_number_tag)
    p_reference_tag = parse_tag(reference_tag)
    p_record_publication_info_tag = parse_tag(record_publication_info_tag)

    for recid in recid_list:
        xml = print_record(int(recid),'xm')
        rs = create_records(xml)
        recs = map((lambda x:x[0]), rs)
        l_report_numbers = []
        for rec in recs:
            pri_report_number = record_get_field_values(rec, p_record_pri_number_tag[0],
                                                        ind1=p_record_pri_number_tag[1],
                                                        ind2=p_record_pri_number_tag[2],
                                                        code=record_pri_number_tag[3])
            add_report_numbers = record_get_field_values(rec, p_record_add_number_tag[0],
                                                         ind1=p_record_add_number_tag[1],
                                                         ind2=p_record_add_number_tag[2],
                                                         code=record_add_number_tag[3])
            if pri_report_number:
                l_report_numbers.extend(pri_report_number)
            if add_report_numbers:
                l_report_numbers.extend(add_report_numbers)
            d_reports_numbers[recid] = l_report_numbers
            reference_report_number = record_get_field_values(rec, p_reference_number_tag[0],
                                                              ind1=p_reference_number_tag[1],
                                                              ind2=p_reference_number_tag[2],
                                                              code=p_reference_number_tag[3])
            if reference_report_number:
                d_references_report_numbers[recid] = reference_report_number
            references_s = record_get_field_values(rec, p_reference_tag[0],
                                                   ind1=p_reference_tag[1],
                                                   ind2=p_reference_tag[2],
                                                   code=p_reference_tag[3])
            if references_s:
                d_references_s[recid] = references_s
            record_s = record_get_field_values(rec,
                                               p_record_publication_info_tag[0],
                                               ind1=p_record_publication_info_tag[1],
                                               ind2=p_record_publication_info_tag[2],
                                               code=p_record_publication_info_tag[3])
            if record_s:
                d_records_s[recid] = record_s[0]
    citation_informations.append(d_reports_numbers)
    citation_informations.append(d_references_report_numbers)
    citation_informations.append(d_references_s)
    citation_informations.append(d_records_s)
    end_time = os.times()[4]
    print "Execution time for generating citation informations by parsing xml contents: ", (end_time - begin_time)
    return citation_informations

def get_self_citations(citationdic,config):
   """Check which items have been cited by one of the authors of the
      citing item
   """
   selfcites = {}
   keys = citationdic.keys()
   for k in keys:
	#get the author of k
	xml = print_record(int(k),'xm')
        rs = create_records(xml)
        recs = map((lambda x:x[0]), rs)
	for rec in recs:
		#author tag
		author = record_get_field_value(rec,"100","","","a")
		otherauthors = record_get_field_values(rec,"700","","","a")
		moreauthors = record_get_field_values(rec,"720","","","a")
		authorlist = [author]
		authorlist.extend(otherauthors)
		authorlist.extend(moreauthors)
		#print "record "+str(k)+" by "+str(authorlist)
		#print "is cited by"
		#get the "x-cites-this" list
		xct = citationdic[k]
		for c in xct:
			cxml = print_record(int(c),'xm')
			crs = create_records(cxml)
			crecs = map((lambda x:x[0]), crs)
			for crec in crecs:
				cauthor = record_get_field_value(crec,"100","","","a")
				cotherauthors = record_get_field_values(crec,"700","","","a")
				cmoreauthors = record_get_field_values(crec,"720","","","a")
				cauthorlist = [cauthor]
				cauthorlist.extend(cotherauthors)
				cauthorlist.extend(cmoreauthors)
				#print str(c)+" by "+str(cauthorlist)
				for ca in cauthorlist:
					if (ca in authorlist):
						if selfcites.has_key(k):
							val = selfcites[k]
							#add only if not there already
							if val:
								if not c in val:
									val.append(c)
							selfcites[k] = val
						else:
							selfcites[k] = [c]
   return selfcites

def ref_analyzer(citation_informations, initialresult, initial_citationlist, initial_referencelist,config):
    """Analyze the citation informations and calculate the citation weight
       and cited by list dictionary
    """
    pubrefntag = record_pri_number_tag = config.get(config.get("rank_method", "function"),"publication_reference_number_tag")
    pubreftag = record_pri_number_tag = config.get(config.get("rank_method", "function"),"publication_reference_tag")
    #pubrefntab is prob 999C5r, pubreftab 999c5s
    citation_list = initial_citationlist
    reference_list = initial_referencelist
    result = initialresult
    d_reports_numbers = citation_informations[0]
    d_references_report_numbers = citation_informations[1]
    d_references_s = citation_informations[2] #of type: {77: ['Nucl. Phys. B 72 (1974) 461','blah blah'], 93: ['..'], ..}
    d_records_s = citation_informations[3]
    t1 = os.times()[4]
    for recid, refnumbers in d_references_report_numbers.iteritems():
        for refnumber in refnumbers:
            p = refnumber
            f = 'reportnumber'
            rec_id = get_recids_matching_query(p, f)
            if rec_id:
                if result.has_key(rec_id[0]):
                    result[rec_id[0]] += 1
                citation_list[rec_id[0]].append(recid)
                reference_list[recid].append(rec_id[0])
    t2 = os.times()[4]
    for recid, refss in d_references_s.iteritems():
        for refs in refss:
            p = refs
            f = 'publref'
            rec_id = get_recids_matching_query(p, f)
            if rec_id and not recid in citation_list[rec_id[0]]:
                result[rec_id[0]] += 1
                citation_list[rec_id[0]].append(recid)
            if rec_id and not rec_id[0] in reference_list[recid]:
                reference_list[recid].append(rec_id[0])
    t3 = os.times()[4]
    for rec_id, recnumbers in d_reports_numbers.iteritems():
        for recnumber in recnumbers:
            p = recnumber
            recid_list = get_recids_matching_query(p, pubrefntag)
            if recid_list:
                for recid in recid_list:
                    if not recid in citation_list[rec_id]:
                        result[rec_id] += 1
                        citation_list[rec_id].append(recid)
                    if not rec_id in reference_list[recid]:
                        reference_list[recid].append(rec_id)
    t4 = os.times()[4]
    for recid, recs in d_records_s.iteritems():
        tmp = recs.find("-")
        if tmp < 0:
            recs_modified = recs
        else:
            recs_modified = recs[:tmp]
        p = recs_modified
        rec_ids = get_recids_matching_query(p, pubreftab)
        if rec_ids:
            for rec_id in rec_ids:
                if not rec_id in citation_list[recid]:
                    result[recid] += 1
                    citation_list[recid].append(rec_id)
                if not recid in reference_list[rec_id]:
                    reference_list[rec_id].append(recid)

    #remove empty lists in citation and reference
    keys = citation_list.keys()
    for k in keys:
	if not citation_list[k]:
		del citation_list[k]

    keys = reference_list.keys()
    for k in keys:
	if not reference_list[k]:
		del reference_list[k]

    selfdic = get_self_citations(citation_list,config)
    #selfdic consists of
    #key k -> list of values [v1,v2,..]
    #where k is a record with author A and k cites v1,v2.. and A appears in v1,v2..

    #create a reverse "x cited by y" self cit dict
    selfcitedbydic = {}
    for k in selfdic.keys():
	vlist = selfdic[k]
	for v in vlist:
		if selfcitedbydic.has_key(v):
			tmplist = selfcitedbydic[v]
			tmplist.append(k)
		else:
			tmplist = [k]
		selfcitedbydic[v] = tmplist

    if task_get_option('verbose') >= 9:		
    	write_message("citation_list (x is cited by y): "+str(citation_list),sys.stderr)	
	write_message("reference_list (x cites y): "+str(reference_list),sys.stderr)	
	write_message("selfcitedbydic (x is cited by y and one of the authors of x same as y's): "+str(selfcitedbydic),sys.stderr)	
	write_message("selfdic (x cites y and one of the authors of x same as y's): "+str(selfdic),sys.stderr)	
    insert_cit_ref_list_intodb(citation_list, reference_list, selfcitedbydic, selfdic)

    t5 = os.times()[4]
    print "\nExecution time for analyzing the citation information generating the dictionary: "
    print "checking ref number: ", (t2-t1)
    print "checking ref ypvt: ", (t3-t2)
    print "checking rec number: ", (t4-t3)
    print "checking rec ypvt: ", (t5-t4)
    print "total time of ref_analyze: ", (t5-t1)
    return result

def get_decompressed_xml(xml):
    """return a decompressed content of xml into a xml content
    """
    decompressed_xml = create_records(decompress(xml))
    return decompressed_xml

def insert_cit_ref_list_intodb(citation_dic, reference_dic, selfcbdic,selfdic):
    """Insert the reference and citation list into the database"""
    date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    run_sql("UPDATE rnkCITATIONDATA SET object_value = %s where object_name='reversedict'",
                (serialize_via_marshal(reference_dic), ))
    run_sql("UPDATE rnkCITATIONDATA SET object_value = %s where object_name='citationdict'",
                (serialize_via_marshal(citation_dic), ))
    run_sql("UPDATE rnkCITATIONDATA SET object_value = %s where object_name='selfcitedbydict'",
                (serialize_via_marshal(selfcbdic), ))
    run_sql("UPDATE rnkCITATIONDATA SET object_value = %s where object_name='selfcitdict'",
                (serialize_via_marshal(selfdic), ))
    run_sql("UPDATE rnkCITATIONDATA SET last_updated = '"+date+"' where object_name='reversedict'")
    run_sql("UPDATE rnkCITATIONDATA SET last_updated = '"+date+"' where object_name='citationdict'")
    run_sql("UPDATE rnkCITATIONDATA SET last_updated = '"+date+"' where object_name='selfcitdict'")
    run_sql("UPDATE rnkCITATIONDATA SET last_updated = '"+date+"' where object_name='selfcitedbydict'")

