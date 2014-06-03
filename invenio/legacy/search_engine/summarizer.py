# -*- coding: utf-8 -*-

## This file is part of Invenio.
## Copyright (C) 2008, 2010, 2011, 2012 CERN.
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

"""
Search Engine Summarizer, producing summary formats such as citesummary.
The main API is summarize_records().
"""

__lastupdated__ = """$Date$"""

__revision__ = "$Id$"


from invenio.config import CFG_INSPIRE_SITE
from invenio.bibrank_citation_searcher import get_cited_by_list
from invenio.bibrank_selfcites_indexer import get_self_citations_count
from StringIO import StringIO

from invenio.search_engine import search_pattern, perform_request_search
from invenio.intbitset import intbitset

import invenio.template

websearch_templates = invenio.template.load('websearch')


## CFG_CITESUMMARY_COLLECTIONS -- how do we break down cite summary
## results according to collections?
if CFG_INSPIRE_SITE:
    CFG_CITESUMMARY_COLLECTIONS = [['Citeable papers', 'collection:citeable'],
                                   ['Published only', 'collection:published']]
else:
    CFG_CITESUMMARY_COLLECTIONS = [['All papers', ''],
                                   ['Published only', 'collection:article']]

## CFG_CITESUMMARY_FAME_THRESHOLDS -- how do we break down cite
## summary results into famous and less famous paper groups?
CFG_CITESUMMARY_FAME_THRESHOLDS = [
                                   (500, 1000000, 'Renowned papers (500+)'),
                                   (250, 499, 'Famous papers (250-499)'),
                                   (100, 249, 'Very well-known papers (100-249)'),
                                   (50, 99, 'Well-known papers (50-99)'),
                                   (10, 49, 'Known papers (10-49)'),
                                   (1, 9, 'Less known papers (1-9)'),
                                   (0, 0, 'Unknown papers (0)')
                                   ]


def render_self_citations(d_recids, ln):
    """Render the html displayed for self-citations"""
    d_total_cites = {}
    d_avg_cites = {}

    for coll, recids in d_recids.iteritems():
        if recids:
            d_total_cites[coll] = get_self_citations_count(recids)
            d_avg_cites[coll] = d_total_cites[coll] * 1.0 / len(recids)
        else:
            d_total_cites[coll] = 0
            d_avg_cites[coll] = 0

    return websearch_templates.tmpl_citesummary_minus_self_cites(d_total_cites,
                                                                 d_avg_cites,
                                                                 ln)


def render_citations_breakdown(req, ln, collections, d_recid_citers,
                                                search_patterns, searchfield):
    "Render citations break down by fame"
    header = websearch_templates.tmpl_citesummary_breakdown_header(ln)
    req.write(header)

    for low, high, fame in CFG_CITESUMMARY_FAME_THRESHOLDS:
        d_cites = {}
        for coll, citers in d_recid_citers.iteritems():
            d_cites[coll] = 0
            for dummy, lciters in citers:
                numcites = 0
                if lciters:
                    numcites = len(lciters)
                if numcites >= low and numcites <= high:
                    d_cites[coll] += 1
        fame_info = websearch_templates.tmpl_citesummary_breakdown_by_fame(
                                d_cites, low, high, fame, collections,
                                search_patterns, searchfield, ln)
        req.write(fame_info)


def render_citation_summary(req, ln, recids, collections, searchpattern,
                                                                  searchfield):
    title = websearch_templates.tmpl_citesummary_title(ln)
    req.write(title)

    d_recids = get_recids(recids, collections)
    d_recid_citers = get_citers(d_recids)
    search_patterns = dict([(coll, searchpattern) \
                                               for coll, dummy in collections])
    render_citesummary_prologue(req,
                                ln,
                                recids,
                                collections,
                                search_patterns,
                                searchfield,
                                d_recids)
    render_citesummary_overview(req,
                                ln,
                                collections,
                                d_recids,
                                d_recid_citers)
    render_citations_breakdown(req,
                               ln,
                               collections,
                               d_recid_citers,
                               search_patterns,
                               searchfield)

    render_h_index(req, ln, collections, d_recid_citers)

    eplilogue = websearch_templates.tmpl_citesummary_epilogue(ln)
    req.write(eplilogue)

    links = websearch_templates.tmpl_citesummary_more_links(searchpattern, ln)
    req.write(links)


def render_extended_citation_summary(req, ln, recids, initial_collections,
                                                   searchpattern, searchfield):
    title = websearch_templates.tmpl_citesummary2_title(searchpattern, ln)
    req.write(title)

    d_recids = get_recids(recids, initial_collections)

    def coll_self_cites(name):
        return name + '<br />excluding self cites'

    def coll_not_rpp(name):
        return name + '<br />excluding RPP'

    # Add self cites sets and "-title:rpp" sets
    if CFG_INSPIRE_SITE:
        notrpp_searchpattern = searchpattern + ' -title:rpp'
        notrpp_recids = intbitset(perform_request_search(p=notrpp_searchpattern))
    for coll, coll_recids in list(d_recids.iteritems()):
        d_recids[coll_self_cites(coll)] = coll_recids
        if CFG_INSPIRE_SITE:
            d_recids[coll_not_rpp(coll)] = notrpp_recids & coll_recids
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
    d_recid_citers = get_citers(d_recids)
    for coll, dummy in initial_collections:
        d_recid_citers[coll_self_cites(coll)] = [
            (recid, range(get_self_citations_count([recid]))) \
                                                for recid in d_recids[coll]
        ]
    render_citesummary_prologue(req,
                                ln,
                                recids,
                                collections,
                                search_patterns,
                                searchfield,
                                d_recids)
    render_citesummary_overview(req,
                                ln,
                                collections,
                                d_recids,
                                d_recid_citers)
    render_citations_breakdown(req,
                               ln,
                               collections,
                               d_recid_citers,
                               search_patterns,
                               searchfield)
    for coll, dummy in initial_collections:
        d_recid_citers[coll_self_cites(coll)] = None
    render_h_index(req, ln, collections, d_recid_citers)

    # 6) hcs epilogue:
    eplilogue = websearch_templates.tmpl_citesummary_epilogue(ln)
    req.write(eplilogue)

    back_link = websearch_templates.tmpl_citesummary_back_link(searchpattern, ln)
    req.write(back_link)


def render_citesummary_overview(req, ln, collections, recids, recid_citers):
    """Citations overview: total citations"""
    total_cites = {}
    avg_cites = {}

    for coll, citers in recid_citers.iteritems():
        total_cites[coll] = sum([len(lciters) for dummy, lciters in citers])
        try:
            avg_cites[coll] = float(total_cites[coll]) / len(recids[coll])
        except ZeroDivisionError:
            avg_cites[coll] = 0

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


def get_citers(d_recids):
    """For each recid fetches the list of citing papers"""
    d_recid_citers = {}
    for coll, recids in d_recids.iteritems():
        d_recid_citers[coll] = get_cited_by_list(recids)
    return d_recid_citers


def render_citesummary_prologue(req, ln, recids, collections, search_patterns,
                                                        searchfield, d_recids):
    total_count = len(recids)
    citable_recids = recids & search_pattern(p='collection:citeable')
    prologue = websearch_templates.tmpl_citesummary_prologue(d_recids,
                                                             collections,
                                                             search_patterns,
                                                             searchfield,
                                                             citable_recids,
                                                             total_count,
                                                             ln)
    req.write(prologue)


def render_h_index(req, ln, collections, d_recid_citers):
    "Calculate and Render h-hep index"
    d_recid_citecount_l = {}
    for coll, citers in d_recid_citers.iteritems():
        if citers is None:
            d_recid_citecount_l[coll] = None
        else:
            d_recid_citecount_l[coll] = []
            for recid, lciters in citers:
                d_recid_citecount_l[coll].append((recid, len(lciters)))

    d_h_factors = {}

    def comparator(x, y):
        if x[1] > y[1]:
            return -1
        elif x[1] == y[1]:
            return 0
        else:
            return 1
    for coll, citecount in d_recid_citecount_l.iteritems():
        if citecount is None:
            d_h_factors[coll] = 'n/a'
        else:
            d_h_factors[coll] = 0
            d_recid_citecount_l[coll].sort(cmp=comparator)
            for citecount in citecount:
                d_h_factors[coll] += 1
                if d_h_factors[coll] > citecount[1]:
                    d_h_factors[coll] -= 1
                    break
    h_idx = websearch_templates.tmpl_citesummary_h_index(collections,
                                                         d_h_factors,
                                                         ln)

    req.write(h_idx)


def summarize_records(recids, of, ln, searchpattern="", searchfield="",
                            req=None, collections=CFG_CITESUMMARY_COLLECTIONS):
    """Write summary report for records RECIDS in the format OF in language LN.
       SEARCHPATTERN and SEARCHFIELD are search query that led to RECIDS,
       for instance p='Smith, Paul' and f='author'.  They are used for links.
       REQ is the Apache/mod_python request object.
    """
    if of == 'xcs':
        # this is XML cite summary
        citedbylist = get_cited_by_list(recids)
        return render_citation_summary_xml(citedbylist)

    has_req = req is not None
    if not has_req:
        req = StringIO()

    if of == 'hcs':
        renderer = render_citation_summary
    else:
        renderer = render_extended_citation_summary

    renderer(req,
             ln,
             recids,
             collections,
             searchpattern,
             searchfield)

    req.write(websearch_templates.tmpl_citesummary_footer())

    if has_req:
        return ''
    else:
        return req.getvalue()


# For citation summary, code xcs/hcs (unless changed)
def render_citation_summary_xml(citedbylist):
    """Prints citation summary in xml."""
    alldict = calculate_citations(citedbylist)
    avgstr = str(alldict['avgcites'])
    totalcites = str(alldict['totalcites'])
    # format avg so that it does not span 10 digits
    avgstr = avgstr[0:4]
    reciddict = alldict['reciddict']
    # output formatting
    outp = "<citationsummary records=\"" + str(len(citedbylist))
    outp += "\" citations=\"" + str(totalcites) + "\">"
    for dummy, dummy, name in CFG_CITESUMMARY_FAME_THRESHOLDS:
        # get the name, print the value
        if name in reciddict:
            recs = reciddict[name]
            outp += "<citationclass>" + name
            outp += "<records>%s</records>" % recs
            outp += "</citationclass>\n"
    outp = outp + "</citationsummary>"
    return outp  # just to return something


def calculate_citations(citedbylist):
    """calculates records in classes of citations
       defined by thresholds. returns a dictionary that
       contains total, avg, records and a dictionary
       of threshold names and number corresponding to it"""
    totalcites = 0
    avgcites = 0
    reciddict = {}
    for recid, cites in citedbylist:
        numcites = 0
        if cites:
            numcites = len(cites)
        totalcites = totalcites + numcites
        # take the numbers in CFG_CITESUMMARY_FAME_THRESHOLDS
        for low, high, name in CFG_CITESUMMARY_FAME_THRESHOLDS:
            if (numcites >= low) and (numcites <= high):
                if name in reciddict:
                    tmp = reciddict[name]
                    tmp.append(recid)
                    reciddict[name] = tmp
                else:
                    reciddict[name] = [recid]
    if (len(citedbylist) == 0):
        avgcites = 0
    else:
        avgcites = totalcites * 1.0 / len(citedbylist)

    # create a dictionary that contains all the values
    alldict = {}
    alldict['records'] = len(citedbylist)
    alldict['totalcites'] = totalcites
    alldict['avgcites'] = avgcites
    alldict['reciddict'] = reciddict
    return alldict
