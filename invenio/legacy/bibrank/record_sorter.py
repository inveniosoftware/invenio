# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2014,
#               2015 CERN.
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

"""Ranking of records using different parameters and methods on the fly."""

import time
import re
import ConfigParser

from operator import itemgetter
from six import iteritems

from invenio.config import \
     CFG_SITE_LANG, \
     CFG_ETCDIR, \
     CFG_WEBSEARCH_DEF_RECORDS_IN_GROUPS, \
     CFG_WEBSEARCH_CITESUMMARY_SCAN_THRESHOLD, \
     CFG_ETCDIR, \
     CFG_WEBSEARCH_CITESUMMARY_SCAN_THRESHOLD
from invenio.legacy.dbquery import run_sql, wash_table_column_name
from invenio.ext.logging import register_exception
from invenio.legacy.bibindex.engine_stopwords import is_stopword
from invenio.legacy.bibrank.citation_searcher import get_cited_by, \
                                                     get_cited_by_weight
from invenio.utils.serializers import deserialize_via_marshal
from intbitset import intbitset
from invenio.legacy.bibrank.word_searcher import find_similar
# Do not remove these lines
# it is necessary for func_object = globals().get(function)
from invenio.legacy.bibrank.word_searcher import word_similarity
from invenio.legacy.miscutil.solrutils_bibrank_searcher import word_similarity_solr
from invenio.legacy.miscutil.xapianutils_bibrank_searcher import word_similarity_xapian
from invenio.modules.ranker.registry import configuration

METHODS = {}


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
    except StandardError:
        pass
    return "true"


def create_external_ranking_settings(rank_method_code, config):
    METHODS[rank_method_code]['fields'] = dict()
    sections = config.sections()
    field_pattern = re.compile('field[0-9]+')
    for section in sections:
        if field_pattern.search(section):
            field_name = config.get(section, 'name')
            METHODS[rank_method_code]['fields'][field_name] = dict()
            for option in config.options(section):
                if option != 'name':
                    create_external_ranking_option(section, option, METHODS[rank_method_code]['fields'][field_name], config)

        elif section == 'find_similar_to_recid':
            METHODS[rank_method_code][section] = dict()
            for option in config.options(section):
                create_external_ranking_option(section, option, METHODS[rank_method_code][section], config)

        elif section == 'field_settings':
            for option in config.options(section):
                create_external_ranking_option(section, option, METHODS[rank_method_code], config)


def create_external_ranking_option(section, option, dictionary, config):
    value = config.get(section, option)
    if value.isdigit():
        value = int(value)
    dictionary[option] = value


def create_rnkmethod_cache():
    """Create cache with vital information for each rank method."""

    bibrank_meths = run_sql("SELECT name from rnkMETHOD")

    for (rank_method_code,) in bibrank_meths:
        filepath = configuration.get(rank_method_code + '.cfg', '')
        config = ConfigParser.ConfigParser()
        try:
            config.readfp(open(filepath))
        except IOError:
            pass

        cfg_function = config.get("rank_method", "function")
        if config.has_section(cfg_function):
            METHODS[rank_method_code] = {}
            METHODS[rank_method_code]["function"] = cfg_function
            METHODS[rank_method_code]["prefix"] = config.get(cfg_function, "relevance_number_output_prologue")
            METHODS[rank_method_code]["postfix"] = config.get(cfg_function, "relevance_number_output_epilogue")
            METHODS[rank_method_code]["chars_alphanumericseparators"] = r"[1234567890\!\"\#\$\%\&\'\(\)\*\+\,\-\.\/\:\;\<\=\>\?\@\[\\\]\^\_\`\{\|\}\~]"
        else:
            raise Exception("Error in configuration config_file: %s" % (config_file + ".cfg", ))

        i8n_names = run_sql("""SELECT ln,value from rnkMETHODNAME,rnkMETHOD where id_rnkMETHOD=rnkMETHOD.id and rnkMETHOD.name=%s""", (rank_method_code,))
        for (ln, value) in i8n_names:
            METHODS[rank_method_code][ln] = value

        if config.has_option(cfg_function, "table"):
            METHODS[rank_method_code]["rnkWORD_table"] = config.get(cfg_function, "table")
            query = "SELECT count(*) FROM %sR" % wash_table_column_name(METHODS[rank_method_code]["rnkWORD_table"][:-1])
            METHODS[rank_method_code]["col_size"] = run_sql(query)[0][0]

        if config.has_option(cfg_function, "stemming") and config.get(cfg_function, "stemming"):
            try:
                METHODS[rank_method_code]["stemmer"] = config.get(cfg_function, "stemming")
            except KeyError:
                pass

        if config.has_option(cfg_function, "stopword"):
            METHODS[rank_method_code]["stopwords"] = config.get(cfg_function, "stopword")

        if config.has_section("find_similar"):
            METHODS[rank_method_code]["max_word_occurence"] = float(config.get("find_similar", "max_word_occurence"))
            METHODS[rank_method_code]["min_word_occurence"] = float(config.get("find_similar", "min_word_occurence"))
            METHODS[rank_method_code]["min_word_length"] = int(config.get("find_similar", "min_word_length"))
            METHODS[rank_method_code]["min_nr_words_docs"] = int(config.get("find_similar", "min_nr_words_docs"))
            METHODS[rank_method_code]["max_nr_words_upper"] = int(config.get("find_similar", "max_nr_words_upper"))
            METHODS[rank_method_code]["max_nr_words_lower"] = int(config.get("find_similar", "max_nr_words_lower"))
            METHODS[rank_method_code]["default_min_relevance"] = int(config.get("find_similar", "default_min_relevance"))

        if cfg_function in ('word_similarity_solr', 'word_similarity_xapian'):
            create_external_ranking_settings(rank_method_code, config)

        if config.has_section("combine_method"):
            i = 1
            METHODS[rank_method_code]["combine_method"] = []
            while config.has_option("combine_method", "method%s" % i):
                METHODS[rank_method_code]["combine_method"].append(config.get("combine_method", "method%s" % i).split(","))
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

    if colID in enabled_colls:
        return 1
    else:
        while colID:
            colID = run_sql("SELECT id_dad FROM collection_collection WHERE id_son=%s", (colID,))
            if colID and colID[0][0] in enabled_colls:
                return 1
            elif colID:
                colID = colID[0][0]
    return 0

def get_bibrank_methods(colID, ln=CFG_SITE_LANG):
    """
    Return a list of rank methods enabled for collection colID and the
    name of them in the language defined by the ln parameter.
    """

    if 'methods' not in globals():
        create_rnkmethod_cache()

    avail_methods = []
    for rank_method_code, options in iteritems(METHODS):
        if "function" in options and is_method_valid(colID, rank_method_code):
            if ln in options:
                avail_methods.append((rank_method_code, options[ln]))
            elif CFG_SITE_LANG in options:
                avail_methods.append((rank_method_code, options[CFG_SITE_LANG]))
            else:
                avail_methods.append((rank_method_code, rank_method_code))
    return avail_methods


def citation(rank_method_code, related_to, hitset, rank_limit_relevance, verbose):
    """Sort records by number of citations"""
    if related_to:
        from invenio.legacy.search_engine import search_pattern
        hits = intbitset()
        for pattern in related_to:
            hits |= hitset & intbitset(search_pattern(p='refersto:%s' % pattern))
    else:
        hits = hitset
    return rank_by_citations(hits, verbose)


def rank_records(rank_method_code, rank_limit_relevance, hitset, related_to=[], verbose=0, field='', rg=None, jrec=None):
    """Sorts given records or related records according to given method

       Parameters:
        - rank_method_code: Sort records using this method
                            e.g. `jif' or `sbr' (word frequency vector model)
        - rank_limit_relevance: A parameter given to the sorting method
                                e.g. `23' for `nbc' (number of citations)
                                     or `0.10' for `vec'
                                     This is ignored when sorting by
                                     citations. But I don't know what it means.
        - hitset: records to sort
        - related_to: if specified, instead of sorting given records,
                      we first fetch the related records ("related" being
                      defined by the method), then we sort these related
                      records
        - verbose, verbose level
        - field: stuff
        - rg: more stuff
        - jrec: even more stuff

       Output:
       - list of records
       - list of rank values
       - prefix, useless it is always '('
       - postfix, useless it is always ')'
       - verbose_output
    """
    voutput = ""
    configcreated = ""

    starttime = time.time()
    afterfind = starttime - time.time()
    aftermap = starttime - time.time()

    try:
        # We are receiving a global hitset
        hitset_global = hitset
        hitset = intbitset(hitset_global)

        if 'methods' not in globals():
            create_rnkmethod_cache()

        function = METHODS[rank_method_code]["function"]
        # Check if we have specific function for sorting by this method
        func_object = globals().get(function)

        if verbose > 0:
            voutput += "function: %s <br/> " % function
            voutput += "related_to:  %s <br/>" % str(related_to)

        if func_object and related_to and related_to[0][0:6] == "recid:" and function == "word_similarity":
            result = find_similar(rank_method_code, related_to[0][6:], hitset, rank_limit_relevance, verbose, METHODS)
        elif func_object:
            if function == "word_similarity":
                result = func_object(rank_method_code, related_to, hitset, rank_limit_relevance, verbose, METHODS)
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
                    result = word_similarity_solr(related_to, hitset, METHODS[rank_method_code], verbose, field, ranked_result_amount)
                if function == "word_similarity_xapian":
                    if verbose > 0:
                        voutput += "In Xapian part:<br/>"
                    result = word_similarity_xapian(related_to, hitset, METHODS[rank_method_code], verbose, field, ranked_result_amount)
            else:
                result = func_object(rank_method_code, related_to, hitset, rank_limit_relevance, verbose)
        else:
            result = rank_by_method(rank_method_code, related_to, hitset, rank_limit_relevance, verbose)
    except Exception as e:
        register_exception()
        from invenio.legacy.webpage import adderrorbox
        result = (None, "", adderrorbox("An error occured when trying to rank the search result "+rank_method_code, ["Unexpected error: %s<br />" % (e,)]), voutput)

    afterfind = time.time() - starttime

    if result[0] and result[1]: #split into two lists for search_engine
        results_similar_recIDs = [x[0] for x in result[0]]
        results_similar_relevances = [x[1] for x in result[0]]
        result = (results_similar_recIDs, results_similar_relevances, result[1], result[2], "%s%s" % (configcreated, result[3]))
        aftermap = time.time() - starttime
    else:
        result = (None, None, result[1], result[2], result[3])

    #add stuff from here into voutput from result
    tmp = voutput+result[4]
    if verbose > 0:
        tmp += "<br/>Elapsed time after finding: %s\nElapsed after mapping: %s" % (afterfind, aftermap)
    result = (result[0], result[1], result[2], result[3], tmp)

    #dbg = string.join(map(str,methods[rank_method_code].items()))
    #result = (None, "", adderrorbox("Debug ",rank_method_code+" "+dbg),"",voutput)
    return result


def combine_method(rank_method_code, pattern, hitset, rank_limit_relevance, verbose):
    """combining several methods into one based on methods/percentage in config file"""

    voutput = ""
    result = {}
    try:
        for (method, percent) in METHODS[rank_method_code]["combine_method"]:
            function = METHODS[method]["function"]
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
    except Exception:
        return (None, "Warning: %s method cannot be used for ranking your query." % rank_method_code, "", voutput)


def rank_by_method(rank_method_code, lwords, hitset, rank_limit_relevance, verbose):
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
            if lword.find("->") > -1:
                lword = lword.split("->")
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
            if recID in rnkdict:
                reclist.append((recID, rnkdict[recID]))
                del rnkdict[recID]
            else:
                reclist_addend.append((recID, 0))
    else: #rank docs in hitset, can this be speed up using something else than for loop?
        for recID in lwords_hitset:
            if recID in rnkdict and recID in hitset:
                reclist.append((recID, rnkdict[recID]))
                del rnkdict[recID]
            elif recID in hitset:
                reclist_addend.append((recID, 0))

    if verbose > 0:
        voutput += "Number of records ranked: %s<br />" % len(reclist)
        voutput += "Number of records not ranked: %s<br />" % len(reclist_addend)

    reclist.sort(lambda x, y: cmp(x[1], y[1]))
    return (reclist_addend + reclist, METHODS[rank_method_code]["prefix"], METHODS[rank_method_code]["postfix"], voutput)


def rank_by_citations(hitset, verbose):
    """Rank by the amount of citations.

    Calculate the cited-by values for all the members of the hitset
    Rreturns: ((recordid,weight),prefix,postfix,message)
    """
    voutput = ""

    if len(hitset) > CFG_WEBSEARCH_CITESUMMARY_SCAN_THRESHOLD:
        cites_counts = get_citation_dict('citations_counts')
        ret = [(recid, weight) for recid, weight in cites_counts
                                                        if recid in hitset]
        recids_without_cites = hitset - get_citation_dict('citations_keys')
        ret.extend([(recid, 0) for recid in recids_without_cites])
        ret = list(reversed(ret))
    else:
        ret = get_cited_by_weight(hitset)
        ret.sort(key=itemgetter(1))

    if verbose > 0:
        voutput += "\nhitset %s\nrank_by_citations ret %s" % (hitset, ret)

    if ret:
        return ret, "(", ")", voutput
    else:
        return [], "", "", voutput
