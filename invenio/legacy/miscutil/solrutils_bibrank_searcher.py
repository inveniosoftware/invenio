# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011 CERN.
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

"""
Solr utilities.
"""


import itertools


from invenio.config import CFG_SOLR_URL
from intbitset import intbitset
from invenio.ext.logging import register_exception


if CFG_SOLR_URL:
    import solr
    conn = solr.Solr(CFG_SOLR_URL)
    SOLR_CONNECTION = solr.SolrConnection(CFG_SOLR_URL) # pylint: disable=E1101
    SOLR_MLT_CONNECTION = solr.SearchHandler(conn, "/mlt")


BOOLEAN_EQUIVALENTS = {"+": "AND",
                       "|": "OR",
                       "-": "NOT"}


def get_collection_filter(hitset, cutoff_amount):
    # The last n hitset records are considered to be newest and therfore most relevant
    start_index = len(hitset) - cutoff_amount
    if start_index < 0:
        start_index = 0
    it = itertools.islice(hitset, start_index, None)
    ids = ' '.join([str(recid) for recid in it])

    if ids:
        return 'id:(%s)' % ids
    else:
        return  ''


def solr_get_ranked(query, hitset, params, ranked_result_amount):
    """
    Queries Solr.
    Returns: a list of ranked record ids [(recid, score), ...) contained in hitset
             and an intbitset of record ids contained in hitset.
    """
    response = SOLR_CONNECTION.query(q=query, fields=['id', 'score'], rows=str(ranked_result_amount), fq=get_collection_filter(hitset, params['cutoff_amount']), timeAllowed=params['cutoff_time_ms'])
    return get_normalized_ranking_scores(response)


def solr_get_similar_ranked(recid, hitset, params, ranked_result_amount):
    """
    Queries Solr for similar records.
    Returns: a list of ranked record ids [(recid, score), ...) contained in hitset
             and an intbitset of record ids contained in hitset.
    """
    # original one first

    query = 'id:%s' % recid
    response = SOLR_MLT_CONNECTION(q=query, fields=['id', 'score'], rows=str(ranked_result_amount * params['find_similar_to_recid']['more_results_factor']),
                                   mlt='true', mlt_fl=params['find_similar_to_recid']['mlt_fl'], timeAllowed=params['cutoff_time_ms'],
                                   mlt_mintf=params['find_similar_to_recid']['mlt_mintf'], mlt_mindf=params['find_similar_to_recid']['mlt_mindf'], mlt_minwl=params['find_similar_to_recid']['mlt_minwl'],
                                   mlt_maxwl=params['find_similar_to_recid']['mlt_maxwl'], mlt_maxqt=params['find_similar_to_recid']['mlt_maxqt'], mlt_maxntp=params['find_similar_to_recid']['mlt_maxntp'],
                                   mlt_boost=params['find_similar_to_recid']['mlt_boost'])

    # Insert original id at the front with guaranteed highest score
    response.results.insert(0, {u'id': u'%s' % recid, u'score': response.maxScore * 1.1})
    return get_normalized_ranking_scores(response, hitset, [recid])


def get_normalized_ranking_scores(response, hitset_filter = None, recids = []):
    """
    Returns the result having normalized ranking scores, interval [0, 100].
    hitset_filter - optional filter for the results
    recids - optional recids that shall remain in the result despite the filter
    """
    if not len(response.results):
        return ([], intbitset())

    # response.maxScore does not work in case of something was added to the response
    max_score = float(response.results[0]['score'])
    ranked_result = []
    matched_recs = intbitset()

    for hit in response.results:
        recid = int(hit['id'])

        if (not hitset_filter and hitset_filter != []) or recid in hitset_filter or recid in recids:
            normalised_score = 0
            if max_score > 0:
                normalised_score = int(100.0 / max_score * float(hit['score']))
            ranked_result.append((recid, normalised_score))
            matched_recs.add(recid)

    ranked_result.reverse()

    return (ranked_result, matched_recs)


def word_similarity_solr(pattern, hitset, params, verbose, explicit_field, ranked_result_amount):
    """
    Ranking a records containing specified words and returns a sorted list.
    input:
    hitset - a list of hits for the query found by search_engine
    verbose - verbose value
    explicit_field - field to search (selected in GUI)
    ranked_result_amount - amount of results to be ranked
    output:
    recset - a list of sorted records: [[23,34], [344,24], [1,01]]
    prefix - what to show before the rank value
    postfix - what to show after the rank value
    voutput - contains extra information, content dependent on verbose value
    """
    voutput = ""
    search_units = []

    if not len(hitset):
        return ([], "", "", voutput)

    if pattern:
        pattern = " ".join(map(str, pattern))
        from invenio.legacy.search_engine import create_basic_search_units
        search_units = create_basic_search_units(None, pattern, explicit_field)
    else:
        return (None, "Records not ranked. The query is not detailed enough, or not enough records found, for ranking to be possible.", "", voutput)

    if verbose > 0:
        voutput += "Hitset: %s<br/>" % hitset
        voutput += "Pattern: %s<br/>" % pattern
        voutput += "Search units: %s<br/>" % search_units

    query = ""

    (ranked_result, matched_recs) = (None, None)

    # Ranks similar records
    if search_units[0][2] == 'recid':
        recid = search_units[0][1]
        if verbose > 0:
            voutput += "Ranked amount: %s<br/>" % ranked_result_amount

        try:
            (ranked_result, matched_recs) = solr_get_similar_ranked(recid, hitset, params, ranked_result_amount)
        except:
            register_exception()
            return (None, "Records not ranked. An error occurred. Please check the query.", "", voutput)

        # Cutoffs potentially large hitset
        it = itertools.islice(hitset, params['find_similar_to_recid']['hitset_cutoff'])
        hitset = intbitset(list(it))

    # Regular word similarity ranking
    else:
        for (operator, pattern, field, unit_type) in search_units:
            # Any field
            if field == '':
                field = 'global'
            # Field might not exist
            elif field not in params["fields"].keys():
                field = params["default_field"]

            if unit_type == "a":
                # Eliminates leading and trailing %
                if pattern[0] == "%":
                    pattern = pattern[1:-1]
                pattern = "\"" + pattern + "\""

            weighting = "^" + str(params["fields"][field]["weight"])

            if ':' in pattern:
                pattern = pattern.rsplit(':', 1)[1]
            query_part = field + ":" + pattern + weighting

            # Considers boolean operator from the second part on, allows negation from the first part on
            if query or operator == "-":
                query += " " + BOOLEAN_EQUIVALENTS[operator] + " "
            query += query_part + " "

        if verbose > 0:
            voutput += "Solr query: %s<br/>" % query

        try:
            (ranked_result, matched_recs) = solr_get_ranked(query, hitset, params, ranked_result_amount)
        except:
            register_exception()
            return (None, "Records not ranked. An error occurred. Please check the query.", "", voutput)

    if verbose > 0:
        voutput += "All matched records: %s<br/>" % matched_recs

    # Considers not ranked records
    not_ranked = hitset.difference(matched_recs)
    if not_ranked:
        lrecIDs = list(not_ranked)
        ranked_result = zip(lrecIDs, [0] * len(lrecIDs)) + ranked_result

    if verbose > 0:
        voutput += "Not ranked: %s<br/>" % not_ranked

    # Similar-to-recid requires reverse order
    if search_units[0][2] == 'recid':
        ranked_result.reverse()

    return (ranked_result, params["prefix"], params["postfix"], voutput)
