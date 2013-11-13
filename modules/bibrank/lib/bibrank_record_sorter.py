# -*- coding: utf-8 -*-
## Ranking of records using different parameters and methods on the fly.
##
## This file is part of Invenio.
## Copyright (C) 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012 CERN.
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

import string
import time
import math
import re
import ConfigParser
import copy


from invenio.config import \
     CFG_SITE_LANG, \
     CFG_ETCDIR, \
     CFG_WEBSEARCH_DEF_RECORDS_IN_GROUPS
from invenio.dbquery import run_sql, deserialize_via_marshal, wash_table_column_name
from invenio.ext.logging import register_exception
from invenio.webpage import adderrorbox
from invenio.bibindex_engine_stemmer import stem
from invenio.bibindex_engine_stopwords import is_stopword
from invenio.bibrank_citation_searcher import get_cited_by, get_cited_by_weight
from invenio.intbitset import intbitset
from invenio.bibrank_word_searcher import find_similar
# Do not remove these lines, it is necessary for func_object = globals().get(function)
from invenio.bibrank_word_searcher import word_similarity
from invenio.solrutils_bibrank_searcher import word_similarity_solr
from invenio.xapianutils_bibrank_searcher import word_similarity_xapian


def compare_on_val(first, second):
    return cmp(second[1], first[1])

def check_term(term, col_size, term_rec, max_occ, min_occ, termlength):
    """Check if the tem is valid for use
    term - the term to check
    col_size - the number of records in database
    term_rec - the number of records which contains this term
    max_occ - max frequency of the term allowed
    min_occ - min frequence of the term allowed
    termlength - the minimum length of the terms allowed"""

    try:
        if is_stopword(term) or (len(term) <= termlength) or ((float(term_rec) / float(col_size)) >= max_occ) or ((float(term_rec) / float(col_size)) <= min_occ):
            return ""
        if int(term):
            return ""
    except StandardError, e:
        pass
    return "true"


def create_external_ranking_settings(rank_method_code, config):
    methods[rank_method_code]['fields'] = dict()
    sections = config.sections()
    field_pattern = re.compile('field[0-9]+')
    for section in sections:
        if field_pattern.search(section):
            field_name = config.get(section, 'name')
            methods[rank_method_code]['fields'][field_name] = dict()
            for option in config.options(section):
                if option != 'name':
                    create_external_ranking_option(section, option, methods[rank_method_code]['fields'][field_name], config)

        elif section == 'find_similar_to_recid':
            methods[rank_method_code][section] = dict()
            for option in config.options(section):
                create_external_ranking_option(section, option, methods[rank_method_code][section], config)

        elif section == 'field_settings':
            for option in config.options(section):
                create_external_ranking_option(section, option, methods[rank_method_code], config)


def create_external_ranking_option(section, option, dictionary, config):
    value = config.get(section, option)
    if value.isdigit():
        value = int(value)
    dictionary[option] = value


def create_rnkmethod_cache():
    """Create cache with vital information for each rank method."""

    global methods
    bibrank_meths = run_sql("SELECT name from rnkMETHOD")
    methods = {}
    global voutput
    voutput = ""

    for (rank_method_code,) in bibrank_meths:
        try:
            file = CFG_ETCDIR + "/bibrank/" + rank_method_code + ".cfg"
            config = ConfigParser.ConfigParser()
            config.readfp(open(file))
        except StandardError, e:
            pass

        cfg_function = config.get("rank_method", "function")
        if config.has_section(cfg_function):
            methods[rank_method_code] = {}
            methods[rank_method_code]["function"] = cfg_function
            methods[rank_method_code]["prefix"] = config.get(cfg_function, "relevance_number_output_prologue")
            methods[rank_method_code]["postfix"] = config.get(cfg_function, "relevance_number_output_epilogue")
            methods[rank_method_code]["chars_alphanumericseparators"] = r"[1234567890\!\"\#\$\%\&\'\(\)\*\+\,\-\.\/\:\;\<\=\>\?\@\[\\\]\^\_\`\{\|\}\~]"
        else:
            raise Exception("Error in configuration file: %s" % (CFG_ETCDIR + "/bibrank/" + rank_method_code + ".cfg"))

        i8n_names = run_sql("""SELECT ln,value from rnkMETHODNAME,rnkMETHOD where id_rnkMETHOD=rnkMETHOD.id and rnkMETHOD.name=%s""", (rank_method_code,))
        for (ln, value) in i8n_names:
            methods[rank_method_code][ln] = value

        if config.has_option(cfg_function, "table"):
            methods[rank_method_code]["rnkWORD_table"] = config.get(cfg_function, "table")
            query = "SELECT count(*) FROM %sR" % wash_table_column_name(methods[rank_method_code]["rnkWORD_table"][:-1])
            methods[rank_method_code]["col_size"] = run_sql(query)[0][0]

        if config.has_option(cfg_function, "stemming") and config.get(cfg_function, "stemming"):
            try:
                methods[rank_method_code]["stemmer"] = config.get(cfg_function, "stemming")
            except Exception,e:
                pass

        if config.has_option(cfg_function, "stopword"):
            methods[rank_method_code]["stopwords"] = config.get(cfg_function, "stopword")

        if config.has_section("find_similar"):
            methods[rank_method_code]["max_word_occurence"] = float(config.get("find_similar", "max_word_occurence"))
            methods[rank_method_code]["min_word_occurence"] = float(config.get("find_similar", "min_word_occurence"))
            methods[rank_method_code]["min_word_length"] = int(config.get("find_similar", "min_word_length"))
            methods[rank_method_code]["min_nr_words_docs"] = int(config.get("find_similar", "min_nr_words_docs"))
            methods[rank_method_code]["max_nr_words_upper"] = int(config.get("find_similar", "max_nr_words_upper"))
            methods[rank_method_code]["max_nr_words_lower"] = int(config.get("find_similar", "max_nr_words_lower"))
            methods[rank_method_code]["default_min_relevance"] = int(config.get("find_similar", "default_min_relevance"))

        if cfg_function in ('word_similarity_solr', 'word_similarity_xapian'):
            create_external_ranking_settings(rank_method_code, config)

        if config.has_section("combine_method"):
            i = 1
            methods[rank_method_code]["combine_method"] = []
            while config.has_option("combine_method", "method%s" % i):
                methods[rank_method_code]["combine_method"].append(string.split(config.get("combine_method", "method%s" % i), ","))
                i += 1

def is_method_valid(colID, rank_method_code):
    """
    Check if RANK_METHOD_CODE method is valid for the collection given.
    If colID is None, then check for existence regardless of collection.
    """

    if colID is None:
        return run_sql("SELECT COUNT(*) FROM rnkMETHOD WHERE name=%s", (rank_method_code,))[0][0]

    enabled_colls = dict(run_sql("SELECT id_collection, score from collection_rnkMETHOD,rnkMETHOD WHERE id_rnkMETHOD=rnkMETHOD.id AND name=%s", (rank_method_code,)))

    try:
        colID = int(colID)
    except TypeError:
        return 0

    if enabled_colls.has_key(colID):
        return 1
    else:
        while colID:
            colID = run_sql("SELECT id_dad FROM collection_collection WHERE id_son=%s", (colID,))
            if colID and enabled_colls.has_key(colID[0][0]):
                return 1
            elif colID:
                colID = colID[0][0]
    return 0

def get_bibrank_methods(colID, ln=CFG_SITE_LANG):
    """
    Return a list of rank methods enabled for collection colID and the
    name of them in the language defined by the ln parameter.
    """

    if not globals().has_key('methods'):
        create_rnkmethod_cache()

    avail_methods = []
    for (rank_method_code, options) in methods.iteritems():
        if options.has_key("function") and is_method_valid(colID, rank_method_code):
            if options.has_key(ln):
                avail_methods.append((rank_method_code, options[ln]))
            elif options.has_key(CFG_SITE_LANG):
                avail_methods.append((rank_method_code, options[CFG_SITE_LANG]))
            else:
                avail_methods.append((rank_method_code, rank_method_code))
    return avail_methods

def rank_records(rank_method_code, rank_limit_relevance, hitset_global, pattern=[], verbose=0, field='', rg=None, jrec=None):
    """rank_method_code, e.g. `jif' or `sbr' (word frequency vector model)
       rank_limit_relevance, e.g. `23' for `nbc' (number of citations) or `0.10' for `vec'
       hitset, search engine hits;
       pattern, search engine query or record ID (you check the type)
       verbose, verbose level
       output:
       list of records
       list of rank values
       prefix
       postfix
       verbose_output"""

    voutput = ""
    configcreated = ""

    starttime = time.time()
    afterfind = starttime - time.time()
    aftermap = starttime - time.time()

    try:
        hitset = copy.deepcopy(hitset_global) #we are receiving a global hitset
        if not globals().has_key('methods'):
            create_rnkmethod_cache()

        function = methods[rank_method_code]["function"]
        #we get 'citation' method correctly here
        func_object = globals().get(function)

        if verbose > 0:
            voutput += "function: %s <br/> " % function
            voutput += "pattern:  %s <br/>" % str(pattern)

        if func_object and pattern and pattern[0][0:6] == "recid:" and function == "word_similarity":
            result = find_similar(rank_method_code, pattern[0][6:], hitset, rank_limit_relevance, verbose, methods)
        elif rank_method_code == "citation":
            #we get rank_method_code correctly here. pattern[0] is the search word - not used by find_cit
            p = ""
            if pattern and pattern[0]:
                p = pattern[0][6:]
            result = find_citations(rank_method_code, p, hitset, verbose)

        elif func_object:
            if function == "word_similarity":
                result = func_object(rank_method_code, pattern, hitset, rank_limit_relevance, verbose, methods)
            elif function in ("word_similarity_solr", "word_similarity_xapian"):
                if not rg:
                    rg = CFG_WEBSEARCH_DEF_RECORDS_IN_GROUPS
                if not jrec:
                    jrec = 0
                ranked_result_amount = rg + jrec
                if verbose > 0:
                    voutput += "Ranked result amount: %s<br/><br/>" % ranked_result_amount

                if verbose > 0:
                    voutput += "field: %s<br/>" % field

                if function == "word_similarity_solr":
                    if verbose > 0:
                        voutput += "In Solr part:<br/>"
                    result = word_similarity_solr(pattern, hitset, methods[rank_method_code], verbose, field, ranked_result_amount)
                if function == "word_similarity_xapian":
                    if verbose > 0:
                        voutput += "In Xapian part:<br/>"
                    result = word_similarity_xapian(pattern, hitset, methods[rank_method_code], verbose, field, ranked_result_amount)
            else:
                result = func_object(rank_method_code, pattern, hitset, rank_limit_relevance, verbose)
        else:
            result = rank_by_method(rank_method_code, pattern, hitset, rank_limit_relevance, verbose)
    except Exception, e:
        register_exception()
        result = (None, "", adderrorbox("An error occured when trying to rank the search result "+rank_method_code, ["Unexpected error: %s<br />" % (e,)]), voutput)

    afterfind = time.time() - starttime

    if result[0] and result[1]: #split into two lists for search_engine
        results_similar_recIDs = map(lambda x: x[0], result[0])
        results_similar_relevances = map(lambda x: x[1], result[0])
        result = (results_similar_recIDs, results_similar_relevances, result[1], result[2], "%s" % configcreated + result[3])
        aftermap = time.time() - starttime;
    else:
        result = (None, None, result[1], result[2], result[3])

    #add stuff from here into voutput from result
    tmp = voutput+result[4]
    if verbose > 0:
        tmp += "<br/>Elapsed time after finding: "+str(afterfind)+"\nElapsed after mapping: "+str(aftermap)
    result = (result[0],result[1],result[2],result[3],tmp)

    #dbg = string.join(map(str,methods[rank_method_code].items()))
    #result = (None, "", adderrorbox("Debug ",rank_method_code+" "+dbg),"",voutput);
    return result

def combine_method(rank_method_code, pattern, hitset, rank_limit_relevance,verbose):
    """combining several methods into one based on methods/percentage in config file"""

    global voutput
    result = {}
    try:
        for (method, percent) in methods[rank_method_code]["combine_method"]:
            function = methods[method]["function"]
            func_object = globals().get(function)
            percent = int(percent)

            if func_object:
                this_result = func_object(method, pattern, hitset, rank_limit_relevance, verbose)[0]
            else:
                this_result = rank_by_method(method, pattern, hitset, rank_limit_relevance, verbose)[0]

            for i in range(0, len(this_result)):
                (recID, value) = this_result[i]
                if value > 0:
                    result[recID] = result.get(recID, 0) + int((float(i) / len(this_result)) * float(percent))

        result = result.items()
        result.sort(lambda x, y: cmp(x[1], y[1]))
        return (result, "(", ")", voutput)
    except Exception, e:
        return (None, "Warning: %s method cannot be used for ranking your query." % rank_method_code, "", voutput)

def rank_by_method(rank_method_code, lwords, hitset, rank_limit_relevance,verbose):
    """Ranking of records based on predetermined values.
    input:
    rank_method_code - the code of the method, from the name field in rnkMETHOD, used to get predetermined values from
    rnkMETHODDATA
    lwords - a list of words from the query
    hitset - a list of hits for the query found by search_engine
    rank_limit_relevance - show only records with a rank value above this
    verbose - verbose value
    output:
    reclist - a list of sorted records, with unsorted added to the end: [[23,34], [344,24], [1,01]]
    prefix - what to show before the rank value
    postfix - what to show after the rank value
    voutput - contains extra information, content dependent on verbose value"""

    global voutput
    voutput = ""
    rnkdict = run_sql("SELECT relevance_data FROM rnkMETHODDATA,rnkMETHOD where rnkMETHOD.id=id_rnkMETHOD and rnkMETHOD.name=%s", (rank_method_code,))

    if not rnkdict:
        return (None, "Warning: Could not load ranking data for method %s." % rank_method_code, "", voutput)

    max_recid = 0
    res = run_sql("SELECT max(id) FROM bibrec")
    if res and res[0][0]:
        max_recid = int(res[0][0])

    lwords_hitset = None
    for j in range(0, len(lwords)): #find which docs to search based on ranges..should be done in search_engine...
        if lwords[j] and lwords[j][:6] == "recid:":
            if not lwords_hitset:
                lwords_hitset = intbitset()
            lword = lwords[j][6:]
            if string.find(lword, "->") > -1:
                lword = string.split(lword, "->")
                if int(lword[0]) >= max_recid or int(lword[1]) >= max_recid + 1:
                    return (None, "Warning: Given record IDs are out of range.", "", voutput)
                for i in range(int(lword[0]), int(lword[1])):
                    lwords_hitset.add(int(i))
            elif lword < max_recid + 1:
                lwords_hitset.add(int(lword))
            else:
                return (None, "Warning: Given record IDs are out of range.", "", voutput)

    rnkdict = deserialize_via_marshal(rnkdict[0][0])
    if verbose > 0:
        voutput += "<br />Running rank method: %s, using rank_by_method function in bibrank_record_sorter<br />" % rank_method_code
        voutput += "Ranking data loaded, size of structure: %s<br />" % len(rnkdict)
    lrecIDs = list(hitset)

    if verbose > 0:
        voutput += "Number of records to rank: %s<br />" % len(lrecIDs)
    reclist = []
    reclist_addend = []

    if not lwords_hitset: #rank all docs, can this be speed up using something else than for loop?
        for recID in lrecIDs:
            if rnkdict.has_key(recID):
                reclist.append((recID, rnkdict[recID]))
                del rnkdict[recID]
            else:
                reclist_addend.append((recID, 0))
    else: #rank docs in hitset, can this be speed up using something else than for loop?
        for recID in lwords_hitset:
            if rnkdict.has_key(recID) and recID in hitset:
                reclist.append((recID, rnkdict[recID]))
                del rnkdict[recID]
            elif recID in hitset:
                reclist_addend.append((recID, 0))

    if verbose > 0:
        voutput += "Number of records ranked: %s<br />" % len(reclist)
        voutput += "Number of records not ranked: %s<br />" % len(reclist_addend)

    reclist.sort(lambda x, y: cmp(x[1], y[1]))
    return (reclist_addend + reclist, methods[rank_method_code]["prefix"], methods[rank_method_code]["postfix"], voutput)

def find_citations(rank_method_code, recID, hitset, verbose):
    """Rank by the amount of citations."""
    #calculate the cited-by values for all the members of the hitset
    #returns: ((recordid,weight),prefix,postfix,message)

    global voutput
    voutput = ""

    #If the recID is numeric, return only stuff that cites it. Otherwise return
    #stuff that cites hitset

    #try to convert to int
    recisint = True
    recidint = 0
    try:
        recidint = int(recID)
    except:
        recisint = False
    ret = []
    if recisint:
        myrecords = get_cited_by(recidint) #this is a simple list
        ret = get_cited_by_weight(myrecords)
    else:
        ret = get_cited_by_weight(hitset)
    ret.sort(lambda x,y:cmp(x[1],y[1]))      #ascending by the second member of the tuples

    if verbose > 0:
        voutput = voutput+"\nrecID "+str(recID)+" is int: "+str(recisint)+" hitset "+str(hitset)+"\n"+"find_citations retlist "+str(ret)

    #voutput = voutput + str(ret)

    if ret:
        return (ret,"(", ")", "")
    else:
        return ((),"", "", "")
