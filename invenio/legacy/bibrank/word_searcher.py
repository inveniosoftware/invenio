# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011, 2012, 2015 CERN.
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


import string
import time
import math
import re

from operator import itemgetter
from six import iteritems

from invenio.legacy.dbquery import run_sql
from invenio.legacy.bibindex.engine_stemmer import stem
from invenio.legacy.bibindex.engine_stopwords import is_stopword
from invenio.utils.serializers import deserialize_via_marshal


def find_similar(rank_method_code, recID, hitset, rank_limit_relevance,verbose, methods):
    """Finding terms to use for calculating similarity. Terms are taken from the recid given, returns a list of recids's and relevance,
    input:
    rank_method_code - the code of the method, from the name field in rnkMETHOD
    recID - records to use for find similar
    hitset - a list of hits for the query found by search_engine
    rank_limit_relevance - show only records with a rank value above this
    verbose - verbose value
    output:
    reclist - a list of sorted records: [[23,34], [344,24], [1,01]]
    prefix - what to show before the rank value
    postfix - what to show after the rank value
    voutput - contains extra information, content dependent on verbose value"""

    startCreate = time.time()
    global voutput
    voutput = ""

    if verbose > 0:
        voutput += "<br />Running rank method: %s, using find_similar/word_frequency in bibrank_record_sorter<br />" % rank_method_code
    rank_limit_relevance = methods[rank_method_code]["default_min_relevance"]

    try:
        recID = int(recID)
    except Exception as e :
        return (None, "Warning: Error in record ID, please check that a number is given.", "", voutput)

    rec_terms = run_sql("""SELECT termlist FROM %sR WHERE id_bibrec=%%s""" % methods[rank_method_code]["rnkWORD_table"][:-1],  (recID,))
    if not rec_terms:
        return (None, "Warning: Requested record does not seem to exist.", "", voutput)
    rec_terms = deserialize_via_marshal(rec_terms[0][0])

    #Get all documents using terms from the selected documents
    if len(rec_terms) == 0:
        return (None, "Warning: Record specified has no content indexed for use with this method.", "", voutput)
    else:
        terms = "%s" % rec_terms.keys()
        terms_recs = dict(run_sql("""SELECT term, hitlist FROM %s WHERE term IN (%s)""" % (methods[rank_method_code]["rnkWORD_table"], terms[1:len(terms) - 1])))

    tf_values = {}
    #Calculate all term frequencies
    for (term, tf) in iteritems(rec_terms):
        if len(term) >= methods[rank_method_code]["min_word_length"] and term in terms_recs and tf[1] != 0:
            tf_values[term] =  int((1 + math.log(tf[0])) * tf[1]) #calculate term weigth
    tf_values = tf_values.items()
    tf_values.sort(lambda x, y: cmp(y[1], x[1])) #sort based on weigth

    lwords = []
    stime = time.time()
    (recdict, rec_termcount) = ({}, {})

    for (t, tf) in tf_values: #t=term, tf=term frequency
        term_recs = deserialize_via_marshal(terms_recs[t])
        if len(tf_values) <= methods[rank_method_code]["max_nr_words_lower"] or (len(term_recs) >= methods[rank_method_code]["min_nr_words_docs"] and (((float(len(term_recs)) / float(methods[rank_method_code]["col_size"])) <=  methods[rank_method_code]["max_word_occurence"]) and ((float(len(term_recs)) / float(methods[rank_method_code]["col_size"])) >= methods[rank_method_code]["min_word_occurence"]))): #too complicated...something must be done
            lwords.append((t, methods[rank_method_code]["rnkWORD_table"])) #list of terms used
            (recdict, rec_termcount) = calculate_record_relevance_findsimilar((t, round(tf, 4)) , term_recs, hitset, recdict, rec_termcount, verbose, "true") #true tells the function to not calculate all unimportant terms
        if len(tf_values) > methods[rank_method_code]["max_nr_words_lower"] and (len(lwords) ==  methods[rank_method_code]["max_nr_words_upper"] or tf < 0):
            break

    if len(recdict) == 0 or len(lwords) == 0:
        return (None, "Could not find similar documents for this query.", "", voutput)
    else: #sort if we got something to sort
        (reclist, hitset) = sort_record_relevance_findsimilar(recdict, rec_termcount, hitset, rank_limit_relevance, verbose)

    if verbose > 0:
        voutput += "<br />Number of terms: %s<br />" % run_sql("SELECT count(id) FROM %s" % methods[rank_method_code]["rnkWORD_table"])[0][0]
        voutput += "Number of terms to use for query: %s<br />" % len(lwords)
        voutput += "Terms: %s<br />" % lwords
        voutput += "Current number of recIDs: %s<br />" % (methods[rank_method_code]["col_size"])
        voutput += "Prepare time: %s<br />" % (str(time.time() - startCreate))
        voutput += "Total time used: %s<br />" % (str(time.time() - startCreate))
        rank_method_stat(rank_method_code, reclist, lwords)

    return (reclist, methods[rank_method_code]["prefix"], methods[rank_method_code]["postfix"], voutput)

def calculate_record_relevance_findsimilar(term, invidx, hitset, recdict, rec_termcount, verbose, quick=None):
    """Calculating the relevance of the documents based on the input, calculates only one word
    term - (term, query term factor) the term and its importance in the overall search
    invidx - {recid: tf, Gi: norm value} The Gi value is used as a idf value
    hitset - a hitset with records that are allowed to be ranked
    recdict - contains currently ranked records, is returned with new values
    rec_termcount - {recid: count} the number of terms in this record that matches the query
    verbose - verbose value
    quick - if quick=yes only terms with a positive qtf is used, to limit the number of records to sort"""


    (t, qtf) = term
    if "Gi" in invidx: #Gi = weigth for this term, created by bibrank_word_indexer
        Gi = invidx["Gi"][1]
        del invidx["Gi"]
    else: #if not existing, bibrank should be run with -R
        return (recdict, rec_termcount)

    if not quick or (qtf >= 0 or (qtf < 0 and len(recdict) == 0)):
        #Only accept records existing in the hitset received from the search engine
        for (j, tf) in iteritems(invidx):
            if j in hitset: #only include docs found by search_engine based on query
                #calculate rank value
                recdict[j] = recdict.get(j, 0) + int((1 + math.log(tf[0])) * Gi * tf[1] * qtf)
                rec_termcount[j] = rec_termcount.get(j, 0) + 1 #number of terms from query in document
    elif quick: #much used term, do not include all records, only use already existing ones
        for (j, tf) in iteritems(recdict): #i.e: if doc contains important term, also count unimportant
            if j in invidx:
                tf = invidx[j]
                recdict[j] = recdict[j] + int((1 + math.log(tf[0])) * Gi * tf[1] * qtf)
                rec_termcount[j] = rec_termcount.get(j, 0) + 1 #number of terms from query in document

    return (recdict, rec_termcount)

def sort_record_relevance_findsimilar(recdict, rec_termcount, hitset, rank_limit_relevance, verbose):
    """Sorts the dictionary and returns records with a relevance higher than the given value.
    recdict - {recid: value} unsorted
    rank_limit_relevance - a value > 0 usually
    verbose - verbose value"""

    startCreate = time.time()
    voutput = ""
    reclist = []

    #Multiply with the number of terms of the total number of terms in the query existing in the records
    for recid in recdict.keys():
        if recdict[recid] > 0 and rec_termcount[recid] > 1:
            recdict[recid] = math.log((recdict[recid] * rec_termcount[recid]))
        else:
            recdict[recid] = 0
    hitset -= recdict.keys()
    #gives each record a score between 0-100
    divideby = max(recdict.values())
    for recid, score in iteritems(recdict):
        score = int(score * 100 / divideby)
        if score >= rank_limit_relevance:
            reclist.append((recid, score))

    #sort scores
    reclist.sort(lambda x, y: cmp(x[1], y[1]), reverse=True)

    if verbose > 0:
        voutput += "Number of records sorted: %s<br />" % len(reclist)
        voutput += "Sort time: %s<br />" % (str(time.time() - startCreate))
    return (reclist, hitset)

def word_similarity(rank_method_code, lwords, hitset, rank_limit_relevance, verbose, methods):
    """Ranking a records containing specified words and returns a sorted list.
    input:
    rank_method_code - the code of the method, from the name field in rnkMETHOD
    lwords - a list of words from the query
    hitset - a list of hits for the query found by search_engine
    rank_limit_relevance - show only records with a rank value above this
    verbose - verbose value
    output:
    reclist - a list of sorted records: [[23,34], [344,24], [1,01]]
    prefix - what to show before the rank value
    postfix - what to show after the rank value
    voutput - contains extra information, content dependent on verbose value"""
    voutput = ""
    startCreate = time.time()

    if verbose > 0:
        voutput += "<br />Running rank method: %s, using word_frequency function in bibrank_record_sorter<br />" % rank_method_code

    lwords_old = lwords
    lwords = []
    #Check terms, remove non alphanumeric characters. Use both unstemmed and stemmed version of all terms.
    for i in range(0, len(lwords_old)):
        term = string.lower(lwords_old[i])
        if not methods[rank_method_code]["stopwords"] == "True" or methods[rank_method_code]["stopwords"] and not is_stopword(term):
            lwords.append((term, methods[rank_method_code]["rnkWORD_table"]))
            terms = string.split(string.lower(re.sub(methods[rank_method_code]["chars_alphanumericseparators"], ' ', term)))
            for term in terms:
                if "stemmer" in methods[rank_method_code]: # stem word
                    term = stem(string.replace(term, ' ', ''), methods[rank_method_code]["stemmer"])
                if lwords_old[i] != term: #add if stemmed word is different than original word
                    lwords.append((term, methods[rank_method_code]["rnkWORD_table"]))

    (recdict, rec_termcount, lrecIDs_remove) = ({}, {}, {})
    #For each term, if accepted, get a list of the records using the term
    #calculate then relevance for each term before sorting the list of records
    for (term, table) in lwords:
        term_recs = run_sql("""SELECT term, hitlist FROM %s WHERE term=%%s""" % methods[rank_method_code]["rnkWORD_table"], (term,))
        if term_recs: #if term exists in database, use for ranking
            term_recs = deserialize_via_marshal(term_recs[0][1])
            (recdict, rec_termcount) = calculate_record_relevance((term, int(term_recs["Gi"][1])) , term_recs, hitset, recdict, rec_termcount, verbose, quick=None)
            del term_recs

    if len(recdict) == 0 or (len(lwords) == 1 and lwords[0] == ""):
        return (None, "Records not ranked. The query is not detailed enough, or not enough records found, for ranking to be possible.", "", voutput)
    else: #sort if we got something to sort
        (reclist, hitset) = sort_record_relevance(recdict, rec_termcount, hitset, rank_limit_relevance, verbose)

    #Add any documents not ranked to the end of the list
    if hitset:
        lrecIDs = list(hitset)                       #using 2-3mb
        reclist = zip(lrecIDs, [0] * len(lrecIDs)) + reclist      #using 6mb

    if verbose > 0:
        voutput += "<br />Current number of recIDs: %s<br />" % (methods[rank_method_code]["col_size"])
        voutput += "Number of terms: %s<br />" % run_sql("SELECT count(id) FROM %s" % methods[rank_method_code]["rnkWORD_table"])[0][0]
        voutput += "Terms: %s<br />" % lwords
        voutput += "Prepare and pre calculate time: %s<br />" % (str(time.time() - startCreate))
        voutput += "Total time used: %s<br />" % (str(time.time() - startCreate))
        voutput += str(reclist) + "<br />"
        rank_method_stat(rank_method_code, reclist, lwords)
    return (reclist, methods[rank_method_code]["prefix"], methods[rank_method_code]["postfix"], voutput)

def calculate_record_relevance(term, invidx, hitset, recdict, rec_termcount, verbose, quick=None):
    """Calculating the relevance of the documents based on the input, calculates only one word
    term - (term, query term factor) the term and its importance in the overall search
    invidx - {recid: tf, Gi: norm value} The Gi value is used as a idf value
    hitset - a hitset with records that are allowed to be ranked
    recdict - contains currently ranked records, is returned with new values
    rec_termcount - {recid: count} the number of terms in this record that matches the query
    verbose - verbose value
    quick - if quick=yes only terms with a positive qtf is used, to limit the number of records to sort"""


    (t, qtf) = term
    if "Gi" in invidx:#Gi = weigth for this term, created by bibrank_word_indexer
        Gi = invidx["Gi"][1]
        del invidx["Gi"]
    else: #if not existing, bibrank should be run with -R
        return (recdict, rec_termcount)

    if not quick or (qtf >= 0 or (qtf < 0 and len(recdict) == 0)):
        #Only accept records existing in the hitset received from the search engine
        for (j, tf) in iteritems(invidx):
            if j in hitset:#only include docs found by search_engine based on query
                try: #calculates rank value
                    recdict[j] = recdict.get(j, 0) + int(math.log(tf[0] * Gi * tf[1] * qtf))
                except:
                    return (recdict, rec_termcount)
                rec_termcount[j] = rec_termcount.get(j, 0) + 1 #number of terms from query in document
    elif quick: #much used term, do not include all records, only use already existing ones
        for (j, tf) in iteritems(recdict): #i.e: if doc contains important term, also count unimportant
            if j in invidx:
                tf = invidx[j]
                recdict[j] = recdict.get(j, 0) + int(math.log(tf[0] * Gi * tf[1] * qtf))
                rec_termcount[j] = rec_termcount.get(j, 0) + 1 #number of terms from query in document

    return (recdict, rec_termcount)

def sort_record_relevance(recdict, rec_termcount, hitset, rank_limit_relevance, verbose):
    """Sorts the dictionary and returns records with a relevance higher than the given value.
    recdict - {recid: value} unsorted
    rank_limit_relevance - a value > 0 usually
    verbose - verbose value"""

    startCreate = time.time()
    voutput = ""
    reclist = []

    #remove all ranked documents so that unranked can be added to the end
    hitset -= recdict.keys()

    #gives each record a score between 0-100
    divideby = max(recdict.values())
    for (j, w) in iteritems(recdict):
        w = int(w * 100 / divideby)
        if w >= rank_limit_relevance:
            reclist.append((j, w))

    #sort scores
    reclist.sort(key=itemgetter(1, 0))
    # reclist.sort(lambda x, y: cmp(x[1], y[1]))

    if verbose > 0:
        voutput += "Number of records sorted: %s<br />" % len(reclist)
        voutput += "Sort time: %s<br />" % (str(time.time() - startCreate))
    return (reclist, hitset)

def rank_method_stat(rank_method_code, reclist, lwords):
    """Shows some statistics about the searchresult.
    rank_method_code - name field from rnkMETHOD
    reclist - a list of sorted and ranked records
    lwords - the words in the query"""

    voutput = ""
    if len(reclist) > 20:
        j = 20
    else:
        j = len(reclist)

    voutput += "<br />Rank statistics:<br />"
    for i in range(1, j + 1):
        voutput += "%s,Recid:%s,Score:%s<br />" % (i,reclist[len(reclist) - i][0],reclist[len(reclist) - i][1])
        for (term, table) in lwords:
            term_recs = run_sql("""SELECT hitlist FROM %s WHERE term=%%s""" % table, (term,))
            if term_recs:
                term_recs = deserialize_via_marshal(term_recs[0][0])
                if reclist[len(reclist) - i][0] in term_recs:
                    voutput += "%s-%s / " % (term, term_recs[reclist[len(reclist) - i][0]])
        voutput += "<br />"

    voutput += "<br />Score variation:<br />"
    count = {}
    for i in range(0, len(reclist)):
        count[reclist[i][1]] = count.get(reclist[i][1], 0) + 1
    i = 100
    while i >= 0:
        if i in count:
            voutput += "%s-%s<br />" % (i, count[i])
        i -= 1

#TODO: use Cython instead of psycho
