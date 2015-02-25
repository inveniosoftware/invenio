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
Xapian utilities.
"""


from invenio.config import CFG_XAPIAN_ENABLED
from intbitset import intbitset
from invenio.legacy.miscutil.xapianutils_config import INDEXES, XAPIAN_DIR


if CFG_XAPIAN_ENABLED:
    import xapian

    class MatchDecider(xapian.MatchDecider):
        def __init__(self, ids):
            xapian.MatchDecider.__init__(self)
            self.ids = ids
        def __call__(self, document):
            return document.get_docid() in self.ids


DATABASES = dict()


def xapian_get_ranked_index(index, pattern, params, hitset, ranked_result_amount):
    """
    Queries a Xapian index.
    Returns: a list of ranked record ids [(recid, score), ...) contained in hitset
             and an intbitset of record ids contained in hitset.
    """
    result = []
    matched_recs = intbitset()

    database = DATABASES[index]
    enquire = xapian.Enquire(database)
    qp = xapian.QueryParser()
    stemmer = xapian.Stem("english")
    qp.set_stemmer(stemmer)
    qp.set_database(database)
    qp.set_stemming_strategy(xapian.QueryParser.STEM_SOME)

    # Avoids phrase search to increase performance
    if "avoid_phrase_search_threshold" in params and len(hitset) >= params["avoid_phrase_search_threshold"] and pattern.startswith('"'):
        pattern = pattern[1:-1]
        query_string = ' AND '.join(pattern.split(' '))
        pattern = qp.parse_query(query_string)
    else:
        query_string = pattern
        pattern = qp.parse_query(query_string, xapian.QueryParser.FLAG_PHRASE)

    enquire.set_query(pattern)
    matches = enquire.get_mset(0, ranked_result_amount, None, MatchDecider(hitset))

    weight = params["weight"]
    for match in matches:
        recid = match.docid
        if recid in hitset:
            score = int(match.percent) * weight
            result.append((recid, score))
            matched_recs.add(recid)
    return (result, matched_recs)


def xapian_init_databases():
    """
    Initializes all database objects.
    """
    for field in INDEXES:
        database = xapian.Database(XAPIAN_DIR + "/" + field)
        DATABASES[field] = database


def get_greatest_ranked_records(raw_reclist):
    """
    Returns unique records having selecting the ones with the greatest records
    in case of duplicates.
    """
    unique_records = dict()
    for (recid, score) in raw_reclist:
        if not recid in unique_records:
            unique_records[recid] = score
        else:
            current_score = unique_records[recid]
            if score > current_score:
                unique_records[recid] = score

    result = []
    for recid in unique_records.keys():
        result.append((recid, unique_records[recid]))

    return result


def word_similarity_xapian(pattern, hitset, params, verbose, field, ranked_result_amount):
    """
    Ranking a records containing specified words and returns a sorted list.
    input:
    hitset - a list of hits for the query found by search_engine
    verbose - verbose value
    field - field to search (selected in GUI)
    ranked_result_amount - amount of results to be ranked
    output:
    recset - a list of sorted records: [[23,34], [344,24], [1,01]]
    prefix - what to show before the rank value
    postfix - what to show after the rank value
    voutput - contains extra information, content dependent on verbose value
    """
    voutput = ""
    search_units = []

    if pattern:
        xapian_init_databases()
        pattern = " ".join(map(str, pattern))
        from invenio.legacy.search_engine import create_basic_search_units
        search_units = create_basic_search_units(None, pattern, field)

    if verbose > 0:
        voutput += "Hitset: %s<br/>" % hitset
        voutput += "Pattern: %s<br/>" % pattern
        voutput += "Search units: %s<br/>" % search_units

    all_ranked_results = []
    included_hits = intbitset()
    excluded_hits = intbitset()
    for (operator, pattern, field, unit_type) in search_units: #@UnusedVariable
        # Field might not exist
        if field not in params["fields"].keys():
            field = params["default_field"]

        if unit_type == "a":
            # Eliminates leading and trailing %
            if pattern[0] == "%":
                pattern = pattern[1:-1]
            pattern = "\"" + pattern + "\""

        (ranked_result_part, matched_recs) = xapian_get_ranked_index(field, pattern, params["fields"][field], hitset, ranked_result_amount)

        if verbose > 0:
            voutput += "Index %s: %s<br/>" % (field, ranked_result_part)
            voutput += "Index records %s: %s<br/>" % (field, matched_recs)

        # Excludes - results
        if operator == "-":
            excluded_hits = excluded_hits.union(matched_recs)
        # + and | are interpreted as OR
        else:
            included_hits = included_hits.union(matched_recs)
            all_ranked_results.extend(ranked_result_part)

    ranked_result = []
    if hitset:
        # Removes the excluded records
        result_hits = included_hits.difference(excluded_hits)

        # Avoids duplicate results and normalises scores
        ranked_result = get_greatest_ranked_records(all_ranked_results)
        ranked_result = get_normalized_ranking_scores(ranked_result)

        # Considers not ranked records
        not_ranked = hitset.difference(result_hits)
        if not_ranked:
            lrecIDs = list(not_ranked)
            ranked_result = zip(lrecIDs, [0] * len(lrecIDs)) + ranked_result

        if verbose > 0:
            voutput += "All matched records: %s<br/>" % result_hits
            voutput += "All ranked records: %s<br/>" % ranked_result
            voutput += "All not ranked records: %s<br/>" % not_ranked

        ranked_result.sort(lambda x, y: cmp(x[1], y[1]))
        return (ranked_result, params["prefix"], params["postfix"], voutput)

    return (ranked_result, "", "", voutput)


def get_normalized_ranking_scores(ranked_result):
    max_score = 0
    for res in ranked_result:
        if res[1] > max_score:
            max_score = res[1]

    normalized_ranked_result = []

    for res in ranked_result:
        normalized_score = int(100.0 / max_score * res[1])
        normalized_ranked_result.append((res[0], normalized_score))

    return normalized_ranked_result
