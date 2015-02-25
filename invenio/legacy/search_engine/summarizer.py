# -*- coding: utf-8 -*-

# This file is part of Invenio.
# Copyright (C) 2008, 2010, 2011, 2012, 2014 CERN.
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
Search Engine Summarizer, producing summary formats such as citesummary.
The main API is summarize_records().
"""

__lastupdated__ = """$Date$"""

__revision__ = "$Id$"

from operator import itemgetter

from invenio.config import CFG_INSPIRE_SITE, \
                           CFG_WEBSEARCH_CITESUMMARY_SCAN_THRESHOLD
from invenio.legacy.bibrank.citation_searcher import get_citation_dict
from six import iteritems, StringIO

from invenio.legacy.search_engine import search_pattern, perform_request_search
from intbitset import intbitset

import invenio.legacy.template

websearch_templates = invenio.legacy.template.load('websearch')


# CFG_CITESUMMARY_COLLECTIONS -- how do we break down cite summary
# results according to collections?
if CFG_INSPIRE_SITE:
    CFG_CITESUMMARY_COLLECTIONS = [['Citeable papers', 'collection:citeable'],
                                   ['Published only', 'collection:published']]
else:
    CFG_CITESUMMARY_COLLECTIONS = [['All papers', ''],
                                   ['Published only', 'collection:article']]

# CFG_CITESUMMARY_FAME_THRESHOLDS -- how do we break down cite
# summary results into famous and less famous paper groups?
CFG_CITESUMMARY_FAME_THRESHOLDS = [
                                   (500, 1000000, 'Renowned papers (500+)'),
                                   (250, 499, 'Famous papers (250-499)'),
                                   (100, 249, 'Very well-known papers (100-249)'),
                                   (50, 99, 'Well-known papers (50-99)'),
                                   (10, 49, 'Known papers (10-49)'),
                                   (1, 9, 'Less known papers (1-9)'),
                                   (0, 0, 'Unknown papers (0)')
                                   ]


def render_citations_breakdown(req, ln, collections, stats,
                               search_patterns, searchfield):
    "Render citations break down by fame"
    header = websearch_templates.tmpl_citesummary_breakdown_header(ln)
    req.write(header)

    for low, high, fame in CFG_CITESUMMARY_FAME_THRESHOLDS:
        counts = {}
        for coll, dummy in collections:
            counts[coll] = stats[coll]['breakdown'][fame]
        fame_info = websearch_templates.tmpl_citesummary_breakdown_by_fame(
                                counts, low, high, fame, collections,
                                search_patterns, searchfield, ln)
        req.write(fame_info)


def compute_citations_counts(recids, dict_name):
    """Compute # cites for each recid

    Input
    - d_recids: list of recids for each collection
           {'HEP': [1,2,3,5,8]}
    Output:
    - citers_counts: list of # cites/recid
           {'HEP': [(1, 10), (2, 5), (3, 23), (5, 0), (8, 0)]}
    """
    cites_count = get_citation_dict(dict_name)
    counts = [(recid, cites_count.get(recid, 0)) for recid in recids]
    counts.sort(key=itemgetter(1), reverse=True)
    return counts


def compute_citation_stats(recids, citers_counts):
    # Total citations
    total_cites = 0
    h_index = 0
    h_index_done = False
    total_recids_without_cites = len(recids)

    # Breakdown
    breakdown = {}
    for low, high, fame in CFG_CITESUMMARY_FAME_THRESHOLDS:
        breakdown[fame] = 0

    for recid, citecount in citers_counts:
        if recid in recids:
            # Total
            total_cites += citecount

            # Recids without cites
            total_recids_without_cites -= 1

            # h-index
            if not h_index_done:
                h_index += 1
                if h_index > citecount:
                    h_index -= 1
                    h_index_done = True

            # Breakdown
            for low, high, fame in CFG_CITESUMMARY_FAME_THRESHOLDS:
                if low <= citecount <= high:
                    breakdown[fame] += 1

    for low, high, fame in CFG_CITESUMMARY_FAME_THRESHOLDS:
        if low == 0:
            breakdown[fame] += total_recids_without_cites

    # Average citations
    try:
        avg_cites = float(total_cites) / len(recids)
    except ZeroDivisionError:
        avg_cites = 0

    return {'total_cites': total_cites,
            'avg_cites': avg_cites,
            'h-index': h_index,
            'breakdown': breakdown}


def get_cites_counts(recids):
    if len(recids) < CFG_WEBSEARCH_CITESUMMARY_SCAN_THRESHOLD:
        cites_counts = compute_citations_counts(recids, 'citations_weights')
    else:
        cites_counts = get_citation_dict('citations_counts')
    return cites_counts


def generate_citation_summary(recids, collections=CFG_CITESUMMARY_COLLECTIONS):

    coll_recids = get_recids(recids, collections)
    cites_counts = get_cites_counts(recids)

    stats = {}
    for coll, dummy in collections:
        stats[coll] = compute_citation_stats(coll_recids[coll], cites_counts)

    return coll_recids, stats

def render_citation_summary(req, ln, recids, searchpattern, searchfield,
                            stats, collections=CFG_CITESUMMARY_COLLECTIONS):
    title = websearch_templates.tmpl_citesummary_title(ln)
    req.write(title)

    search_patterns = dict([(coll, searchpattern) \
                                               for coll, dummy in collections])

    if stats is None:
        status = generate_citation_summary(recids, collections)

    coll_recids, stats = stats

    render_citesummary_prologue(req,
                                ln,
                                recids,
                                collections,
                                search_patterns,
                                searchfield,
                                coll_recids)
    render_citesummary_overview(req,
                                ln,
                                collections,
                                stats)
    render_citations_breakdown(req,
                               ln,
                               collections,
                               stats,
                               search_patterns,
                               searchfield)

    render_h_index(req, ln, collections, stats)

    eplilogue = websearch_templates.tmpl_citesummary_epilogue()
    req.write(eplilogue)

    links = websearch_templates.tmpl_citesummary_more_links(searchpattern, ln)
    req.write(links)


def render_extended_citation_summary(req, ln, recids, collections,
                                                   searchpattern, searchfield):
    title = websearch_templates.tmpl_citesummary2_title(searchpattern, ln)
    req.write(title)

    initial_collections = collections
    collections_recids = get_recids(recids, collections)

    def coll_self_cites(name):
        return name + '<br />excluding self cites'

    def coll_not_rpp(name):
        return name + '<br />excluding RPP'

    # Add self cites sets and "-title:rpp" sets
    if CFG_INSPIRE_SITE:
        notrpp_searchpattern = searchpattern + ' -title:rpp'
        notrpp_recids = intbitset(perform_request_search(p=notrpp_searchpattern))
    for coll, coll_recids in collections_recids.items():
        collections_recids[coll_self_cites(coll)] = coll_recids
        if CFG_INSPIRE_SITE:
            collections_recids[coll_not_rpp(coll)] = notrpp_recids & coll_recids
    # Add self cites collections
    collections = []
    search_patterns = {}
    for coll, query in initial_collections:
        search_patterns[coll] = searchpattern
        search_patterns[coll_self_cites(coll)] = searchpattern
        if CFG_INSPIRE_SITE:
            search_patterns[coll_not_rpp(coll)] = notrpp_searchpattern
            collections += [
                (coll, query),
                (coll_self_cites(coll), query),
                (coll_not_rpp(coll), query),
            ]
        else:
            collections += [
                (coll, query),
                (coll_self_cites(coll), query),
            ]

    cites_counts = get_cites_counts(recids)

    if len(recids) < CFG_WEBSEARCH_CITESUMMARY_SCAN_THRESHOLD:
        selfcites_counts = compute_citations_counts(recids, 'selfcites_weights')
    else:
        selfcites_counts = get_citation_dict('selfcites_counts')

    citers_counts = {}

    for coll, dummy in initial_collections:
        citers_counts[coll] = cites_counts
        citers_counts[coll_self_cites(coll)] = selfcites_counts
        citers_counts[coll_not_rpp(coll)] = cites_counts

    stats = {}
    for coll, dummy in collections:
        stats[coll] = compute_citation_stats(collections_recids[coll], citers_counts[coll])

    render_citesummary_prologue(req,
                                ln,
                                recids,
                                collections,
                                search_patterns,
                                searchfield,
                                collections_recids)
    render_citesummary_overview(req,
                                ln,
                                collections,
                                stats)
    render_citations_breakdown(req,
                               ln,
                               collections,
                               stats,
                               search_patterns,
                               searchfield)
    render_h_index(req, ln, collections, stats)

    # 6) hcs epilogue:
    eplilogue = websearch_templates.tmpl_citesummary_epilogue()
    req.write(eplilogue)

    back_link = websearch_templates.tmpl_citesummary_back_link(searchpattern, ln)
    req.write(back_link)


def render_citesummary_overview(req, ln, collections, stats):
    """Citations overview: total citations"""
    avg_cites = {}
    total_cites = {}
    for coll, dummy in collections:
        avg_cites[coll] = stats[coll]['avg_cites']
        total_cites[coll] = stats[coll]['total_cites']
    overview = websearch_templates.tmpl_citesummary_overview(collections,
                                                             total_cites,
                                                             avg_cites,
                                                             ln)
    req.write(overview)


def get_recids(recids, collections):
    """Compute recids for each column"""
    d_recids = {}
    for coll, colldef in collections:
        if not colldef:
            d_recids[coll] = recids
        else:
            d_recids[coll] = recids & search_pattern(p=colldef)
    return d_recids


def render_citesummary_prologue(req, ln, recids, collections, search_patterns,
                                                     searchfield, coll_recids):
    total_count = len(recids)
    citable_recids = recids & search_pattern(p='collection:citeable')
    prologue = websearch_templates.tmpl_citesummary_prologue(coll_recids,
                                                             collections,
                                                             search_patterns,
                                                             searchfield,
                                                             citable_recids,
                                                             total_count,
                                                             ln)
    req.write(prologue)


def render_h_index(req, ln, collections, stats):
    "Calculate and Render h-hep index"
    h_indexes = {}
    for coll, dummy in collections:
        h_indexes[coll] = stats[coll]['h-index']
    h_idx = websearch_templates.tmpl_citesummary_h_index(collections,
                                                         h_indexes,
                                                         ln)
    req.write(h_idx)


def summarize_records(recids, of, ln, searchpattern="", searchfield="",
                            req=None, collections=CFG_CITESUMMARY_COLLECTIONS):
    """Write summary report for records RECIDS in the format OF in language LN.
       SEARCHPATTERN and SEARCHFIELD are search query that led to RECIDS,
       for instance p='Smith, Paul' and f='author'.  They are used for links.
       REQ is the Apache/mod_python request object.
    """
    # Workaround a intbitset segfault when this is not a intbitset
    if not isinstance(recids, intbitset):
        recids = intbitset(recids)

    if of == 'xcs':
        # This is XML cite summary
        return render_citation_summary_xml(recids)

    has_req = req is not None
    if not has_req:
        req = StringIO()

    if of == 'hcs':
        stats = generate_citation_summary(recids, collections)
        render_citation_summary(req=req,
                                ln=ln,
                                recids=recids,
                                collections=collections,
                                searchpattern=searchpattern,
                                searchfield=searchfield,
                                stats=stats)
    else:
        render_extended_citation_summary(req=req,
                                         ln=ln,
                                         recids=recids,
                                         collections=collections,
                                         searchpattern=searchpattern,
                                         searchfield=searchfield)

    req.write(websearch_templates.tmpl_citesummary_footer())

    if has_req:
        return ''
    else:
        return req.getvalue()


# For citation summary, code xcs/hcs (unless changed)
def render_citation_summary_xml(recids):
    """Prints citation summary in xml."""
    total_cites, recids_breakdown = calculate_citations(recids)

    # output formatting
    out = ["<citationsummary records=\"%s\" citations=\"%s\">" \
                                                  % (len(recids), total_cites)]
    for dummy, dummy, name in CFG_CITESUMMARY_FAME_THRESHOLDS:
        # get the name, print the value
        if name in recids_breakdown:
            out += ["<citationclass>%s<records>%s</records></citationclass>\n"\
                                              % (name, recids_breakdown[name])]
    out += ["</citationsummary>"]
    return '\n'.join(out)


def calculate_citations(recids):
    """calculates records in classes of citations
       defined by thresholds. returns a dictionary that
       contains total, avg, records and a dictionary
       of threshold names and number corresponding to it"""
    total_cites = 0
    recids_breakdown = {}

    if len(recids) < CFG_WEBSEARCH_CITESUMMARY_SCAN_THRESHOLD:
        cites_counts = compute_citations_counts(recids, 'citations_weights')
    else:
        cites_counts = get_citation_dict('citations_counts')

    for recid, numcites in cites_counts:
        if recid in recids:
            total_cites += numcites
            for low, high, name in CFG_CITESUMMARY_FAME_THRESHOLDS:
                if low <= numcites <= high:
                    recids_breakdown.setdefault(name, []).append(recid)
                if low == 0:
                    non_cited = recids - get_citation_dict("citations_keys")
                    recids_breakdown.setdefault(name, []).extend(non_cited)

    return total_cites, recids_breakdown
