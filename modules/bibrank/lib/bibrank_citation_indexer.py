# -*- Coding: utf-8 -*-
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
## along with CDS Invenio; if not, writeto the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

__revision__ = "$Id$"

import re
import time
import sys
import os
import marshal
import traceback
from zlib import decompress, error

from invenio.dbquery import run_sql, serialize_via_marshal, \
                            deserialize_via_marshal
from invenio.search_engine import print_record, search_pattern, get_fieldvalues, \
                           search_unit
from invenio.bibformat_utils import parse_tag
from invenio.bibtask import write_message, task_get_option, task_update_progress, \
                            task_sleep_now_if_required

NO_AUTHOR_CITES = 1
#a config param to turn off self citation searching

try:
    Set = set
except NameError:
    from sets import Set

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
    the index of sorted research results by citation information
    """
    begin_time = time.time()
    last_update_time = get_bibrankmethod_lastupdate(rank_method_code)
    #addition: YOU DO NEED TO RUN WITH OPTION -R SOMETIMES. This is
    #because among the new set (X) there can be records such that the old
    #records Y cite them. But this kind of situation is not detected
    #unless you go though all the records Y+X.
    if task_get_option("quick") == "no":
        last_update_time = "0000-00-00 00:00:00"
    #if task_get_option('verbose') >= 3:
    last_modified_records = get_last_modified_rec(last_update_time)
    #id option forces re-indexing a certain range even if there are no new recs
    if last_modified_records or task_get_option("id"):
        if task_get_option("id"):
            #construct a range of records to index
            id = task_get_option("id")
            first = id[0][0]
            last = id[0][1]
            #make range, last+1 so that e.g. -i 1-2 really means [1,2] not [1]
            updated_recid_list = range(first, last+1)
        else:
            updated_recid_list = create_recordid_list(last_modified_records)

        write_message("Last update "+str(last_update_time)+" records: "+ \
                       str(len(last_modified_records))+" updates: "+ \
                       str(len(updated_recid_list)))

        #write_message("updated_recid_list: "+str(updated_recid_list))
        result_intermediate = last_updated_result(rank_method_code,
                                                  updated_recid_list)
        #result_intermed should be warranted to exists!
        citation_weight_dic_intermediate = result_intermediate[0]
        citation_list_intermediate = result_intermediate[1]
        reference_list_intermediate = result_intermediate[2]
        #call the procedure that does the hard work by reading fields of
        #citations and references in the updated_recid's (but nothing else)!
        citation_informations = get_citation_informations(updated_recid_list, config)
        #write_message("citation_informations: "+str(citation_informations))
        #create_analysis_tables() #temporary.. needed to test how much faster in-mem indexing is
        #call the analyser that uses the citation_informations to really search x-cites-y in the coll..
        dic = ref_analyzer(citation_informations,
                           citation_weight_dic_intermediate,
                           citation_list_intermediate,
                           reference_list_intermediate,
                           config,updated_recid_list)
                    #dic is docid-numberofreferences like {1: 2, 2: 0, 3: 1}
        #write_message("Docid-number of known references "+str(dic))
        end_time = time.time()
        write_message("Total time of get_citation_weight(): %.2f sec" % (end_time - begin_time))
        task_update_progress("citation analysis done")
    else:
        dic = {}
        write_message("No new records added since last time this rank method was executed")
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
    query = """SELECT id FROM bibrec
               WHERE modification_date >= '%s' """ % bibrank_method_lastupdate
    query += "order by id ASC"
    list = run_sql(query)
    return list

def create_recordid_list(rec_ids):
    """Create a list of record ids out of RECIDS.
       The result is expected to have ascending numerical order.
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
               rnkMETHOD.id = rnkMETHODDATA.id_rnkMETHOD
               and rnkMETHOD.Name = '%s'"""% rank_method_code
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
                query = """select object_value from rnkCITATIONDATA
                           where object_name='reversedict'"""
                ref_compressed = run_sql(query)
                if ref_compressed and ref_compressed[0] and ref_compressed[0][0]:
                    ref = marshal.loads(decompress(ref_compressed[0][0]))
                    result = get_initial_result(dic, cit, ref, recid_list)
    return result

def get_initial_result(dic, cit, ref, recid_list):
    """initialize the citation weights of the last updated record with zero for
       recalculating it later
    """
    for recid in recid_list:
        dic[recid] = 0
        cit[recid] = []
        if ref.has_key(recid) and ref[recid]:
            for id in ref[recid]:
                if cit.has_key(id) and recid in cit[id]:
                    cit[id].remove(recid)
                    if dic.has_key(id):
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
    """scans the collections searching references (999C5x -fields) and citations for
       items in the recid_list
       returns a 4 list of dictionaries that contains the citation information of cds records
       examples: [ {} {} {} {} ]
                 [ {5: 'SUT-DP-92-70-5'}, { 93: ['astro-ph/9812088']}, { 93: ['Phys. Rev. Lett. 96 (2006) 081301'] }, {} ]

        NB: stuff here is for analysing new or changed records.
        see "ref_analyzer" for more.
    """
    begin_time = os.times()[4]
    d_reports_numbers = {}
    d_references_report_numbers = {}
    d_references_s = {}
    d_records_s = {}
    citation_informations = []
    record_pri_number_tag = config.get(config.get("rank_method", "function"),
                                       "publication_primary_number_tag")
    record_add_number_tag = config.get(config.get("rank_method", "function"),
                                       "publication_aditional_number_tag")
    reference_number_tag = config.get(config.get("rank_method", "function"),
                                      "publication_reference_number_tag")
    reference_tag = config.get(config.get("rank_method", "function"),
                               "publication_reference_tag")
    record_publication_info_tag = config.get(config.get("rank_method", "function"),
                                             "publication_info_tag")

    p_record_pri_number_tag = tagify(parse_tag(record_pri_number_tag))
    #037a: contains (often) the "hep-ph/0501084" tag of THIS record
    p_record_add_number_tag = tagify(parse_tag(record_add_number_tag))
    #088a: additional short identifier for the record
    p_reference_number_tag = tagify(parse_tag(reference_number_tag))
    #999C5r. this is in the reference list, refers to other records. Looks like: hep-ph/0408002
    p_reference_tag = tagify(parse_tag(reference_tag))
    #999C5s. A standardized way of writing a reference in the reference list. Like: Nucl. Phys. B 710 (2000) 371
    p_record_publication_info_tag = tagify(parse_tag(record_publication_info_tag))
    #909s field in THIS record, should be canonical publication string like Nucl. Phys. B 710 (2000) 371
    #however, this does not exist, do the following tags are needed..
    publication_pages_tag = ""
    publication_year_tag = ""
    publication_journal_tag = ""
    publication_volume_tag = ""
    publication_format_string = "p v (y) c"
    try:
        tag = config.get(config.get("rank_method", "function"), "publication_pages_tag")
        publication_pages_tag = tagify(parse_tag(tag))
        tag = config.get(config.get("rank_method", "function"), "publication_year_tag")
        publication_year_tag = tagify(parse_tag(tag))
        tag = config.get(config.get("rank_method", "function"), "publication_journal_tag")
        publication_journal_tag = tagify(parse_tag(tag))
        tag = config.get(config.get("rank_method", "function"), "publication_volume_tag")
        publication_volume_tag = tagify(parse_tag(tag))
        publication_format_string = config.get(config.get("rank_method", "function"), "publication_format_string")
    except:
        pass

    done = 0 #for status reporting
    numrecs = len(recid_list)
    for recid in recid_list:
        if (done % 10 == 0):
            task_sleep_now_if_required()
            #in fact we can sleep any time here

        if (done % 1000 == 0):
            mesg = "get cit.inf done "+str(done)+" of "+str(numrecs)
            write_message(mesg)
            task_update_progress(mesg)
        done = done+1

        pri_report_numbers = get_fieldvalues(recid, p_record_pri_number_tag)
        add_report_numbers = get_fieldvalues(recid, p_record_add_number_tag)
        reference_report_numbers = get_fieldvalues(recid, p_reference_number_tag)
        references_s = get_fieldvalues(recid, p_reference_tag)

        l_report_numbers = pri_report_numbers
        l_report_numbers.extend(add_report_numbers)
        d_reports_numbers[recid] = l_report_numbers

        if reference_report_numbers:
            d_references_report_numbers[recid] = reference_report_numbers

        references_s = get_fieldvalues(recid, p_reference_tag)
        if references_s:
            d_references_s[recid] = references_s

        #insert "this was published in"
        record_s = get_fieldvalues(recid, p_record_publication_info_tag)
        if record_s:
            d_records_s[recid] = record_s[0]
        else:
            #a "standard" pub field is not always maintained so get a combination of
            #journal vol (year) pages
            if publication_pages_tag and publication_journal_tag and \
               publication_volume_tag and publication_year_tag and publication_format_string:
                tagsvalues = {} #we store the tags and their values here
                                #like c->444 y->1999 p->"journal of foo",v->20
                tagsvalues["p"] = ""
                tagsvalues["y"] = ""
                tagsvalues["c"] = ""
                tagsvalues["v"] = ""

                tmp = get_fieldvalues(recid, publication_journal_tag)
                if tmp:
                    tagsvalues["p"] = tmp[0]
                tmp = get_fieldvalues(recid, publication_volume_tag)
                if tmp:
                    tagsvalues["v"] = tmp[0]
                tmp = get_fieldvalues(recid, publication_year_tag)
                if tmp:
                    tagsvalues["y"] = tmp[0]
                tmp = get_fieldvalues(recid, publication_pages_tag)
                if tmp:
                    #if the page numbers have "x-y" take just x
                    pages = tmp[0]
                    hpos = pages.find("-")
                    if hpos > 0:
                        pages = pages[:hpos]
                    tagsvalues["c"] = pages
                #format the publ infostring according to the format
                publ = ""
                ok = 1
                for i in range (0, len(publication_format_string)):
                    current = publication_format_string[i]
                    #these are supported
                    if current == "p" or current=="c" or current=="v" or current=="y":
                        if tagsvalues[current]:
                            #add the value in the string
                            publ += tagsvalues[current]
                        else:
                            ok = 0
                            break #it was needed and not found
                    else:
                        publ += current #just add the character in the format string
                if ok:
                    d_records_s[recid] = publ
    mesg = "get cit.inf done fully"
    write_message(mesg)
    task_update_progress(mesg)

    citation_informations.append(d_reports_numbers)
    citation_informations.append(d_references_report_numbers)
    citation_informations.append(d_references_s)
    citation_informations.append(d_records_s)
    end_time = os.times()[4]
    write_message("Execution time for generating citation info from record: %.2f sec" % \
                  (end_time - begin_time))
    return citation_informations

def get_self_citations(new_record_list, citationdic, initial_selfcitdict, config):
    """Check which items have been cited by one of the authors of the
       citing item: go through id's in new_record_list, use citationdic to get citations,
       update "selfcites". Selfcites is originally initial_selfcitdict. Return selfcites.
    """
    i = 0 #just for debugging ..
    #get the tags for main author, coauthors, ext authors from config
    r_mainauthortag = config.get(config.get("rank_method", "function"), "main_author_tag")
    r_coauthortag = config.get(config.get("rank_method", "function"), "coauthor_tag")
    r_extauthortag = config.get(config.get("rank_method", "function"), "extauthor_tag")
    #parse the tags
    mainauthortag = tagify(parse_tag(r_mainauthortag))
    coauthortag = tagify(parse_tag(r_coauthortag))
    extauthortag = tagify(parse_tag(r_extauthortag))

    selfcites = initial_selfcitdict
    for k in new_record_list:
        if (i % 1000 == 0):
            mesg = "Selfcites done "+str(i)+" of "+str(len(new_record_list))+" records"
            write_message(mesg)
            task_update_progress(mesg)
        i = i+1
        #get the author of k
        authorlist = get_fieldvalues(k, mainauthortag)
        coauthl = get_fieldvalues(k, coauthortag)
        extauthl = get_fieldvalues(k, extauthortag)
        authorlist.append(coauthl)
        authorlist.append(extauthl)
        #author tag
        #print "record "+str(k)+" by "+str(authorlist)
        #print "is cited by"
        #get the "x-cites-this" list
        if citationdic.has_key(k):
            xct = citationdic[k]
            for c in xct:
                #get authors of c
                cauthorlist = get_fieldvalues(c, mainauthortag)
                coauthl = get_fieldvalues(c, coauthortag)
                extauthl = get_fieldvalues(c, extauthortag)
                cauthorlist.extend(coauthl)
                cauthorlist.extend(extauthl)
                #print str(c)+" by "+str(cauthorlist)
                for ca in cauthorlist:
                    if (ca in authorlist):
                        #found!
                        if selfcites.has_key(k):
                            val = selfcites[k]
                            #add only if not there already
                            if val:
                                if not c in val:
                                    val.append(c)
                            selfcites[k] = val
                        else:
                            #new key for selfcites
                            selfcites[k] = [c]

    mesg = "Selfcites done fully"
    write_message(mesg)
    task_update_progress(mesg)

    return selfcites

def get_author_citations(updated_redic_list, citedbydict, initial_author_dict, config):
    """Traverses citedbydict in order to build "which author is quoted where" dict.
       The keys of this are author names. An entry like "Apollinaire"->[1,2,3] means
       Apollinaire is cited in records 1,2 and 3.
       Input: citedbydict, updated_redic_list = records to be searched, initial_author_dict:
              the dicts from the database.
       Output: authorciteddict. It is initially set to initial_author_dict
    """

    #sorry bout repeated code to get the tags
    r_mainauthortag = config.get(config.get("rank_method", "function"), "main_author_tag")
    r_coauthortag = config.get(config.get("rank_method", "function"), "coauthor_tag")
    r_extauthortag = config.get(config.get("rank_method", "function"), "extauthor_tag")
    #parse the tags
    mainauthortag = tagify(parse_tag(r_mainauthortag))
    coauthortag = tagify(parse_tag(r_coauthortag))
    extauthortag = tagify(parse_tag(r_extauthortag))

    author_cited_in = initial_author_dict
    if citedbydict:
        i = 0 #just a counter for debug
        write_message("Checking records referred to in new records")
        for u in updated_redic_list:
            if (i % 1000 == 0):
                mesg = "Author ref done "+str(i)+" of "+str(len(updated_redic_list))+" records"
                write_message(mesg)
                task_update_progress(mesg)
            i = i + 1

            if citedbydict.has_key(u):
                these_cite_k = citedbydict[u]
                if (these_cite_k is None):
                    these_cite_k = [] #verify it is an empty list, not None
                authors = get_fieldvalues(u, mainauthortag)
                coauthl = get_fieldvalues(u, coauthortag)
                extauthl = get_fieldvalues(u, extauthortag)
                authors.extend(coauthl)
                authors.extend(extauthl)
                for a in authors:
                    if a and author_cited_in.has_key(a):
                        #add all elements in these_cite_k
                        #that are not there already
                        for citer in these_cite_k:
                            tmplist = author_cited_in[a]
                            if (tmplist.count(citer) == 0):
                                tmplist.append(citer)
                                author_cited_in[a] = tmplist
                            else:
                                author_cited_in[a] = these_cite_k

        mesg = "Author ref done fully"
        write_message(mesg)
        task_update_progress(mesg)

        #go through the dictionary again: all keys but search only if new records are cited
        write_message("Checking authors in new records")
        i = 0
        for k in citedbydict.keys():
            if (i % 1000 == 0):
                mesg = "Author cit done "+str(i)+" of "+str(len(citedbydict.keys()))+" records"
                write_message(mesg)
                task_update_progress(mesg)
            i = i + 1

            these_cite_k = citedbydict[k]
            if (these_cite_k is None):
                these_cite_k = [] #verify it is an empty list, not None
            #do things only if these_cite_k contains any new stuff
            intersec_list = list(Set(these_cite_k)&Set(updated_redic_list))
            if intersec_list:
                authors = get_fieldvalues(k, mainauthortag)
                coauthl = get_fieldvalues(k, coauthortag)
                extauthl = get_fieldvalues(k, extauthortag)
                authors.extend(coauthl)
                authors.extend(extauthl)
                for a in authors:
                    if a and author_cited_in.has_key(a):
                        #add all elements in these_cite_k
                        #that are not there already
                        for citer in these_cite_k:
                            tmplist = author_cited_in[a]
                            if (tmplist.count(citer) == 0):
                                tmplist.append(citer)
                                author_cited_in[a] = tmplist
                            else:
                                author_cited_in[a] = these_cite_k

        mesg = "Author cit done fully"
        write_message(mesg)
        task_update_progress(mesg)

    return author_cited_in


def ref_analyzer(citation_informations, initialresult, initial_citationlist,
                 initial_referencelist,config, updated_rec_list ):
    """Analyze the citation informations and calculate the citation weight
       and cited by list dictionary.
    """
    pubrefntag = record_pri_number_tag = config.get(config.get("rank_method", "function"),
                                                    "publication_reference_number_tag")
    pubreftag = record_pri_number_tag = config.get(config.get("rank_method", "function"),
                                                    "publication_reference_tag")
    #pubrefntag is prob 999C5r, pubreftag 999C5s


    citation_list = initial_citationlist
    reference_list = initial_referencelist
    result = initialresult
    d_reports_numbers = citation_informations[0]
    d_references_report_numbers = citation_informations[1]
    d_references_s = citation_informations[2]
       #of type: {77: ['Nucl. Phys. B 72 (1974) 461','blah blah'], 93: ['..'], ..}
    d_records_s = citation_informations[3]
    t1 = os.times()[4]
    if task_get_option('verbose') >= 1:
        write_message("Phase 1: d_references_report_numbers")
    #d_references_report_numbers: e.g 8 -> ([astro-ph/9889],[hep-ph/768])
    #meaning: rec 8 contains these in bibliography

    done = 0
    numrecs = len(d_references_report_numbers)
    for recid, refnumbers in d_references_report_numbers.iteritems():
        if (done % 1000 == 0):
            mesg =  "d_references_report_numbers done "+str(done)+" of "+str(numrecs)
            write_message(mesg)
            task_update_progress(mesg)
            #write to db!
            insert_into_cit_db(reference_list, "reversedict")
            insert_into_cit_db(citation_list, "citationdict")
            #it's ok to sleep too, we got something done
            task_sleep_now_if_required()
        done = done+1

        for refnumber in refnumbers:
            if refnumber:
                p = refnumber
                f = 'reportnumber'
                #sanitise p
                p.replace("\n",'')
                #search for "hep-th/5644654 or such" in existing records
                rec_id = get_recids_matching_query(p, f)
                if rec_id and rec_id[0]:
                    write_citer_cited(recid, rec_id[0])
                    remove_from_missing(p)
                    if result.has_key(rec_id[0]):
                        result[rec_id[0]] += 1
                    # Citation list should have rec_id[0] but check anyway
                    if citation_list.has_key(rec_id[0]):
                        citation_list[rec_id[0]].append(recid)
                    else:
                        citation_list[rec_id[0]] = [recid]
                    if reference_list.has_key(recid):
                        reference_list[recid].append(rec_id[0])
                    else:
                        reference_list[recid] = [rec_id[0]]
                else:
                    #the reference we wanted was not found among our records.
                    #put the reference in the "missing".. however, it will look
                    #bad.. gfhgf/1254312, so  get the corresponding 999C5s (full ref) too
                    #This should really be done in the next loop d_references_s
                    #but the 999C5s fields are not yet normalized

                    #rectext = print_record(recid, format='hm', ot=pubreftag[:-1])
                    rectext = "" # print_record() call disabled to speed things up
                    lines = rectext.split("\n")
                    rpart = p #to be used..
                    for l in lines:
                        if (l.find(p) > 0): #the gfhgf/1254312 was found.. get the s-part of it
                            st = l.find('$s')
                            if (st > 0):
                                end = l.find('$',st)
                                if (end == st):
                                    end = len(l)
                                rpart = l[st+2:end]
                    insert_into_missing(recid, rpart)

    mesg = "d_references_report_numbers done fully"
    write_message(mesg)
    task_update_progress(mesg)

    t2 = os.times()[4]

    #try to find references based on 999C5s, like Phys.Rev.Lett. 53 (1986) 2285
    if task_get_option('verbose') >= 1:
        write_message("Phase 2: d_references_s")
    done = 0
    numrecs = len(d_references_s)
    for recid, refss in d_references_s.iteritems():
        if (done % 1000 == 0):
            mesg = "d_references_s done "+str(done)+" of "+str(numrecs)
            write_message(mesg)
            task_update_progress(mesg)
            #write to db!
            insert_into_cit_db(reference_list, "reversedict")
            insert_into_cit_db(citation_list, "citationdict")
            task_sleep_now_if_required()

        done = done+1

        for refs in refss:
            if refs:
                p = refs
                #remove the latter page number if it is like 67-74
                matches = re.compile("(.*)(-\d+$)").findall(p)
                if matches and matches[0]:
                    p = matches[0][0]
                rec_id = list(search_unit(p, 'journal'))
                #print "These match searching "+p+" in journal: "+str(rec_id)
                if rec_id and rec_id[0]:
                    #the refered publication is in our collection, remove
                    #from missing
                    remove_from_missing(p)
                else:
                    #it was not found so add in missing
                    insert_into_missing(recid, p)
                if rec_id and not recid in citation_list[rec_id[0]]:
                    result[rec_id[0]] += 1
                    citation_list[rec_id[0]].append(recid)
                if rec_id and not rec_id[0] in reference_list[recid]:
                    reference_list[recid].append(rec_id[0])

    mesg = "d_references_s done fully"
    write_message(mesg)
    task_update_progress(mesg)

    t3 = os.times()[4]
    done = 0
    numrecs = len(d_reports_numbers)
    if task_get_option('verbose') >= 1:
        write_message("Phase 3: d_reports_numbers")

    #search for stuff like CERN-TH-4859/87 in list of refs
    for rec_id, recnumbers in d_reports_numbers.iteritems():
        if (done % 1000 == 0):
            mesg = "d_report_numbers done "+str(done)+" of "+str(numrecs)
            write_message(mesg)
            task_update_progress(mesg)
        done = done+1

        for recnumber in recnumbers:
            if recnumber:
                p = recnumber
                recid_list = get_recids_matching_query(p, pubrefntag)
                if recid_list:
                    for recid in recid_list:
                        if not citation_list.has_key(rec_id):
                            citation_list[rec_id] = []
                        if not recid in citation_list[rec_id]:
                            result[rec_id] += 1
                            citation_list[rec_id].append(recid)
                        if not reference_list.has_key(recid):
                            reference_list[recid] = []
                        if not rec_id in reference_list[recid]:
                            reference_list[recid].append(rec_id)

    mesg = "d_report_numbers done fully"
    write_message(mesg)
    task_update_progress(mesg)

    #find this record's pubinfo in other records' references
    if task_get_option('verbose') >= 1:
        write_message("Phase 4: d_records_s")
    done = 0
    numrecs = len(d_records_s)
    t4 = os.times()[4]
    for recid, recs in d_records_s.iteritems():
        if (done % 1000 == 0):
            mesg = "d_records_s done "+str(done)+" of "+str(numrecs)
            write_message(mesg)
            task_update_progress(mesg)
        done = done+1
        p = recs
        #search the publication string like Phys. Lett., B 482 (2000) 417 in 999C5s
        rec_ids = list(search_unit(f=pubreftag, p=p))
        #print "These records match "+p+" in "+pubreftag+" : "+str(rec_ids)
        if rec_ids:
            for rec_id in rec_ids:
                if not rec_id in citation_list[recid]:
                    result[recid] += 1
                    citation_list[recid].append(rec_id)
                if not recid in reference_list[rec_id]:
                    reference_list[rec_id].append(recid)

    mesg = "d_records_s done fully"
    write_message(mesg)
    task_update_progress(mesg)

    if task_get_option('verbose') >= 1:
        write_message("Phase 5: reverse lists")

    #remove empty lists in citation and reference
    keys = citation_list.keys()
    for k in keys:
        if not citation_list[k]:
            del citation_list[k]

    keys = reference_list.keys()
    for k in keys:
        if not reference_list[k]:
            del reference_list[k]

    if task_get_option('verbose') >= 1:
        write_message("Phase 6: self-citations")
    selfdic = {}
    #get the initial self citation dict
    initial_self_dict = get_cit_dict("selfcitdict")
    selfdic = initial_self_dict
    #add new records to selfdic
    if NO_AUTHOR_CITES:
        print "Self cite processing disabled"
    else:
        selfdic = get_self_citations(updated_rec_list, citation_list,
                                 initial_self_dict, config)
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

    if task_get_option('verbose') >= 1:
        write_message("Getting author citations")


    #get author citations for records in updated_rec_list
    initial_author_dict = get_initial_author_dict()
    authorcitdic = initial_author_dict
    if NO_AUTHOR_CITES:
        print "Author cites disabled"
    else:
        authorcitdic = get_author_citations(updated_rec_list, citation_list,
                                        initial_author_dict, config)


    if task_get_option('verbose') >= 3:
        #print only X first to prevent flood
        tmpdict = {}
        tmp = citation_list.keys()[0:10]
        for t in tmp:
            tmpdict[t] = citation_list[t]
        write_message("citation_list (x is cited by y): "+str(tmpdict))
        write_message("size: "+str(len(citation_list.keys())))
        tmp = reference_list.keys()[0:10]
        tmpdict = {}
        for t in tmp:
            tmpdict[t] = reference_list[t]
        write_message("reference_list (x cites y): "+str(tmpdict))
        write_message("size: "+str(len(reference_list.keys())))
        tmp = selfcitedbydic.keys()[0:10]
        tmpdict = {}
        for t in tmp:
            tmpdict[t] = selfcitedbydic[t]
        write_message("selfcitedbydic (x is cited by y and one  \
                       of the authors of x same as y's): "+str(tmpdict))
        write_message("size: "+str(len(selfcitedbydic.keys())))
        tmp = selfdic.keys()[0:100]
        tmpdict = {}
        for t in tmp:
            tmpdict[t] = selfdic[t]
        write_message("selfdic (x cites y and one of the authors \
                       of x same as y's): "+str(tmpdict))
        write_message("size: "+str(len(selfdic.keys())))
        tmp = authorcitdic.keys()[0:10]
        tmpdict = {}
        for t in tmp:
            tmpdict[t] = authorcitdic[t]
        write_message("authorcitdic (author is cited in recs): "+str(tmpdict))
        write_message("size: "+str(len(authorcitdic.keys())))
    insert_cit_ref_list_intodb(citation_list, reference_list,
                               selfcitedbydic, selfdic, authorcitdic)

    t5 = os.times()[4]

    write_message("Execution time for analyzing the citation information generating the dictionary:")
    write_message("... checking ref number: %.2f sec" % (t2-t1))
    write_message("... checking ref ypvt: %.2f sec" % (t3-t2))
    write_message("... checking rec number: %.2f sec" % (t4-t3))
    write_message("... checking rec ypvt: %.2f sec" % (t5-t4))
    write_message("... total time of ref_analyze: %.2f sec" % (t5-t1))

    return result

def get_decompressed_xml(xml):
    """return a decompressed content of xml into a xml content
    """
    decompressed_xml = create_records(decompress(xml))
    return decompressed_xml

def insert_cit_ref_list_intodb(citation_dic, reference_dic, selfcbdic,
                               selfdic, authorcitdic):
    """Insert the reference and citation list into the database"""
    insert_into_cit_db(reference_dic,"reversedict")
    insert_into_cit_db(citation_dic,"citationdict")
    insert_into_cit_db(selfcbdic,"selfcitedbydict")
    insert_into_cit_db(selfdic,"selfcitdict")

    for a in authorcitdic.keys():
        lserarr = (serialize_via_marshal(authorcitdic[a]))
        #author name: replace " with something else
        a.replace('"', '\'')
        a = unicode(a, 'utf-8')
        try:
            ablob = run_sql("select hitlist from rnkAUTHORDATAR where aterm = %s", (a,))
            if not (ablob):
                #print "insert into rnkAUTHORDATAR(aterm,hitlist) values (%s,%s)" , (a,lserarr)
                run_sql("insert into rnkAUTHORDATAR(aterm,hitlist) values (%s,%s)",
                         (a,lserarr))
            else:
                #print "UPDATE rnkAUTHORDATAR SET hitlist  = %s where aterm=%s""" , (lserarr,a)
                run_sql("UPDATE rnkAUTHORDATAR SET hitlist  = %s where aterm=%s",
                        (lserarr,a))
        except:
            print "Critical error: could not read/write rnkAUTHORDATAR "
            print "aterm="+a+" hitlist="+str(lserarr)+"\n"
            traceback.print_tb(sys.exc_info()[2])

def insert_into_cit_db(dic, name):
    """an aux thing to avoid repeating code"""
    ndate = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    try:
        s = serialize_via_marshal(dic)
        write_message("size of "+name+" "+str(len(s)))
        #check that this column really exists
        testres = run_sql("select object_name from rnkCITATIONDATA where object_name = %s",
                       (name,))
        if testres:
            run_sql("UPDATE rnkCITATIONDATA SET object_value = %s where object_name = %s",
                    (s, name))
        else:
            #there was no entry for name, let's force..
            run_sql("INSERT INTO rnkCITATIONDATA(object_name,object_value) values (%s,%s)",
                     (name,s))
        run_sql("UPDATE rnkCITATIONDATA SET last_updated = %s where object_name = %s",
               (ndate,name))
    except:
        print "Critical error: could not write "+name+" into db"
        traceback.print_tb(sys.exc_info()[2])


def get_cit_dict(name):
    """get a named citation dict from the db"""
    cdict = {}
    try:
        cdict = run_sql("select object_value from rnkCITATIONDATA where object_name = %s",
                       (name,))
        if cdict and cdict[0] and cdict[0][0]:
            dict_from_db = marshal.loads(decompress(cdict[0][0]))
            return dict_from_db
        else:
            return {}
    except:
        print "Critical error: could not read "+name+" from db"
        traceback.print_tb(sys.exc_info()[2])
    return dict

def get_initial_author_dict():
    """read author->citedinlist dict from the db"""
    dict = {}
    try:
        ah = run_sql("select aterm,hitlist from rnkAUTHORDATAR")
        for (a, h) in ah:
            dict[a] = deserialize_via_marshal(h)
        return dict
    except:
        print "Critical error: could not read rnkAUTHORDATAR"
        traceback.print_tb(sys.exc_info()[2])
        dict = {}
        return dict


def insert_into_missing(recid, report):
    """put the referingrecordnum-publicationstring into
       the "we are missing these" table"""
    report.replace('"','\'')
    try:
        srecid = str(recid)
        wasalready = run_sql("select id_bibrec from rnkCITATIONDATAEXT where id_bibrec = %s and extcitepubinfo = %s",
                              (srecid,report))
        if not wasalready:
            run_sql("insert into rnkCITATIONDATAEXT(id_bibrec, extcitepubinfo) values (%s,%s)",
                   (srecid, report))
    except:
        #we should complain but it can result to million lines of warnings so just pass..
        pass

def remove_from_missing(report):
    """remove the recid-ref -pairs from the "missing" table for report x: prob
       in the case ref got in our library collection"""
    report.replace('"','\'')
    try:
        run_sql("delete from rnkCITATIONDATAEXT where extcitepubinfo= %s", (report,))
    except:
        #we should complain but it can result to million lines of warnings so just pass..
        pass


def create_analysis_tables():
    """temporary simple table + index"""
    sql1 = "CREATE TABLE IF NOT EXISTS tmpcit (citer mediumint(10), cited mediumint(10)) TYPE=MyISAM"
    sql2 = "CREATE UNIQUE INDEX citercited on tmpcit(citer, cited)"
    sql3 = "CREATE INDEX citer on tmpcit(citer)"
    sql4 = "CREATE INDEX cited on tmpcit(cited)"
    try:
        run_sql(sql1)
        run_sql(sql2)
        run_sql(sql3)
        run_sql(sql4)
    except:
        pass

def write_citer_cited(citer, cited):
    """write an entry to tmp table"""
    sciter = str(citer)
    scited = str(cited)
    try:
        run_sql("insert into tmpcit(citer, cited) values (%s,%s)", (sciter,scited))
    except:
        pass

def print_missing(num):
    """
    Print the contents of rnkCITATIONDATAEXT table containing external
    records that were cited by NUM or more internal records.

    NUM is by default taken from the -E command line option.
    """
    if not num:
        num = task_get_option("print-extcites")

    write_message("Listing external papers cited by %i or more internal records:" % num)

    res = run_sql("SELECT COUNT(id_bibrec), extcitepubinfo FROM rnkCITATIONDATAEXT \
                   GROUP BY extcitepubinfo HAVING COUNT(id_bibrec) >= %s \
                   ORDER BY COUNT(id_bibrec) DESC", (num,))
    for (cnt, brec) in res:
        print str(cnt)+"\t"+brec

    write_message("Listing done.")

def tagify(parsedtag):
    """aux auf to make '100__a' out of ['100','','','a']"""
    tag = ""
    for t in parsedtag:
        if t == '':
            t = '_'
        tag = tag+t
    return tag
