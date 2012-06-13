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

import ConfigParser
import sys

if sys.hexversion < 0x2040000:
    # pylint: disable=W0622
    from sets import Set as set
    # pylint: enable=W0622

from invenio.config import CFG_INSPIRE_SITE, CFG_ETCDIR
from invenio.bibrank_citation_searcher import get_cited_by_list
from invenio.bibrank_citation_indexer import tagify
from invenio.errorlib import register_exception
from invenio.bibformat_utils import parse_tag
from invenio.search_engine_utils import get_fieldvalues
from invenio.bibauthorid_searchinterface import get_personids_from_bibrec
from invenio.bibauthorid_searchinterface import get_person_bibrecs
import search_engine
import invenio.template
websearch_templates = invenio.template.load('websearch')

def load_config_file(key):
    filename = CFG_ETCDIR + "/bibrank/" + key + ".cfg"
    config = ConfigParser.ConfigParser()
    try:
        config.readfp(open(filename))
    except StandardError:
        raise Exception('Unable to load config file %s' % filename)
    return config

CITATION_CONFIG = load_config_file('citation')

## CFG_CITESUMMARY_COLLECTIONS -- how do we break down cite summary
## results according to collections?
if CFG_INSPIRE_SITE:
    CFG_CITESUMMARY_COLLECTIONS = [['All papers', 'collection:citeable'],
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

## CFG_SELFCITATIONS_THRESHOLD -- only calculate self-citations stats if
## we are dealing with less than n records
CFG_CITESUMMARY_SELFCITES_THRESHOLD = 1000


def get_authors_tags(config=CITATION_CONFIG):
    """
    Get the tags for main author, coauthors, alternative authors from config
    """
    function = config.get("rank_method", "function")

    tags_names = [
        'first_author',
        'additional_author',
        'alternative_author_name',
        'collaboration_name',
    ]

    tags = {}
    for t in tags_names:
        r_tag = config.get(function, t)
        tags[t] = tagify(parse_tag(r_tag))

    return tags


def get_authors_from_record(recID, tags):
    """Get all authors for a record

    We need this function because there's 3 different types of authors
    and to fetch each one of them we need look through MARC tags
    """
    authors = get_personids_from_bibrec(recID)

    if not authors:
        mainauth_list = get_fieldvalues(recID, tags['first_author'])
        coauth_list   = get_fieldvalues(recID, tags['additional_author'])
        extauth_list  = get_fieldvalues(recID, tags['alternative_author_name'])

        authors = set(mainauth_list)
        authors.update(coauth_list)
        authors.update(extauth_list)

    return authors


def get_collaborations_from_record(recID, tags):
    """Get all collaborations for a record"""
    return get_fieldvalues(recID, tags['collaboration_name'])


def get_coauthors(author, tags, cache):
    """Get all coauthors for an author

    Given author A, returns all the authors having published
    a record with author A
    """
    if author in cache:
        return cache[author]

    friends = set()

    # sanity check: author may not exist
    if not author:
        return friends

    try:
        authorid = int(author)
        records = get_person_bibrecs(authorid)
    except ValueError:
        records = search_engine.search_pattern(p=author, f='author')
    for recid in records:
        friends.update(get_authors_from_record(recid, tags))

    cache[author] = friends
    return friends


def compute_self_citations(recid, lciters, authors_cache, tags):
    if not lciters:
        return 0

    total_citations = 0

    authors = frozenset(get_authors_from_record(recid, tags))

    collaborations = None
    if len(authors) > 20:
        collaborations = frozenset(
            get_collaborations_from_record(recid, tags))

    if collaborations:
        # Use collaborations names
        for cit in lciters:
            cit_collaborations = frozenset(
                get_collaborations_from_record(cit, tags))
            if not collaborations.intersection(cit_collaborations):
                total_citations += 1
    else:
        # Use authors names
        for cit in lciters:
            cit_authors = get_authors_from_record(cit, tags)
            if len(cit_authors) > 20 and \
                get_collaborations_from_record(cit, tags):
                # Record from a collaboration that cites
                # a record from an author, it's fine
                total_citations += 1
            else:
                cit_authors_set = set(cit_authors)
                # Extend with circle of friends
                for author in list(cit_authors)[:20]:
                    author_friends = get_coauthors(author, tags, authors_cache)
                    cit_authors_set.update(author_friends)

                if not authors.intersection(cit_authors_set):
                    total_citations += 1


    return total_citations


def render_self_citations(d_recids, d_total_recs, ln):
    try:
        tags = get_authors_tags()
    except IndexError, e:
        register_exception(prefix="attribute " + \
            str(e) + " missing in config", alert_admin=True)
        return ""

    d_recid_citers = {}
    d_total_cites = {}
    d_avg_cites = {}
    for coll, dummy_colldef in CFG_CITESUMMARY_COLLECTIONS:
        d_total_cites[coll] = 0
        d_avg_cites[coll] = 0

        d_recid_citers[coll] = get_cited_by_list(d_recids[coll])
        authors_cache = {}
        for recid, lciters in d_recid_citers[coll]:
            d_total_cites[coll] += \
                compute_self_citations(recid, lciters, authors_cache, tags)

        if d_total_recs[coll] != 0:
            d_avg_cites[coll] = d_total_cites[coll] * 1.0 / d_total_recs[coll]

    return websearch_templates.tmpl_citesummary_minus_self_cites(
        d_total_cites, d_avg_cites, CFG_CITESUMMARY_COLLECTIONS, ln)


def summarize_records(recids, of, ln, searchpattern="", searchfield="", req=None):
    """Write summary report for records RECIDS in the format OF in language LN.
       SEARCHPATTERN and SEARCHFIELD are search query that led to RECIDS,
       for instance p='Smith, Paul' and f='author'.  They are used for links.
       REQ is the Apache/mod_python request object.
    """
    if of == 'hcs':
        # this is HTML cite summary
        html = []
        compute_self_citations_p = True

        # 1) hcs prologue:
        d_recids = {}
        d_total_recs = {}
        for coll, colldef in CFG_CITESUMMARY_COLLECTIONS:
            if not colldef:
                d_recids[coll] = recids
            else:
                d_recids[coll] = recids & search_engine.search_pattern(p=colldef)
            d_total_recs[coll] = len(d_recids[coll])
            if d_total_recs[coll] > CFG_CITESUMMARY_SELFCITES_THRESHOLD:
                compute_self_citations_p = False

        prologue = websearch_templates.tmpl_citesummary_prologue(d_total_recs, CFG_CITESUMMARY_COLLECTIONS, searchpattern, searchfield, ln)

        if not req:
            html.append(prologue)
        elif hasattr(req, "write"):
            req.write(prologue)

        # 2) hcs overview:
        d_recid_citers = {}
        d_total_cites = {}
        d_avg_cites = {}
        d_recid_citecount_l = {}
        for coll, dummy_colldef in CFG_CITESUMMARY_COLLECTIONS:
            d_total_cites[coll] = 0
            d_avg_cites[coll] = 0
            d_recid_citecount_l[coll] = []
            d_recid_citers[coll] =  get_cited_by_list(d_recids[coll])
            for recid, lciters in d_recid_citers[coll]:
                if lciters:
                    d_total_cites[coll] += len(lciters)
                    d_recid_citecount_l[coll].append((recid, len(lciters)))
            if d_total_recs[coll] != 0:
                d_avg_cites[coll] = d_total_cites[coll] * 1.0 / d_total_recs[coll]
        overview = websearch_templates.tmpl_citesummary_overview(d_total_cites,
            d_avg_cites, CFG_CITESUMMARY_COLLECTIONS, ln)

        if not req:
            html.append(overview)
        elif hasattr(req, "write"):
            req.write(overview)

        # 3) compute self-citations
        if compute_self_citations_p:
            overview = render_self_citations(d_recids, d_total_recs, ln)

            if not req:
                html.append(overview)
            elif hasattr(req, "write"):
                req.write(overview)

        header = websearch_templates.tmpl_citesummary_breakdown_header(ln)
        if not req:
            html.append(header)
        elif hasattr(req, "write"):
            req.write(header)


        # 4) hcs break down by fame:
        for low, high, fame in CFG_CITESUMMARY_FAME_THRESHOLDS:
            d_cites = {}
            for coll, colldef in CFG_CITESUMMARY_COLLECTIONS:
                d_cites[coll] = 0
                for recid, lciters in d_recid_citers[coll]:
                    numcites = 0
                    if lciters:
                        numcites = len(lciters)
                    if numcites >= low and numcites <= high:
                        d_cites[coll] += 1
            fame_info = websearch_templates.tmpl_citesummary_breakdown_by_fame(d_cites, low, high, fame, CFG_CITESUMMARY_COLLECTIONS, searchpattern, searchfield, ln)

            if not req:
                html.append(fame_info)
            elif hasattr(req, "write"):
                req.write(fame_info)

        # 5) hcs calculate h index
        d_h_factors = {}
        def comparator(x, y):
            if x[1] > y[1]:
                return -1
            elif x[1] == y[1]:
                return 0
            else: return +1
        for coll, colldef in CFG_CITESUMMARY_COLLECTIONS:
            d_h_factors[coll] = 0
            d_recid_citecount_l[coll].sort(cmp=comparator)
            #req.write(repr(d_recid_citecount_l[coll])) # DEBUG
            for citecount in d_recid_citecount_l[coll]:
                d_h_factors[coll] += 1
                if d_h_factors[coll] > citecount[1]:
                    d_h_factors[coll] -= 1
                    break
        h_idx = websearch_templates.tmpl_citesummary_h_index(d_h_factors, CFG_CITESUMMARY_COLLECTIONS, ln)

        if not req:
            html.append(h_idx)
        elif hasattr(req, "write"):
            req.write(h_idx)

        # 6) hcs epilogue:
        eplilogue = websearch_templates.tmpl_citesummary_epilogue(ln)

        if not req:
            html.append(eplilogue)
        elif hasattr(req, "write"):
            req.write(eplilogue)

        if not req:
            return "\n".join(html)
        else:
            return ''

    elif of == 'xcs':
        # this is XML cite summary
        citedbylist = get_cited_by_list(recids)
        return print_citation_summary_xml(citedbylist)

#for citation summary, code xcs/hcs (unless changed)
def print_citation_summary_xml(citedbylist):
    """Prints citation summary in xml."""
    alldict = calculate_citations(citedbylist)
    avgstr = str(alldict['avgcites'])
    totalcites = str(alldict['totalcites'])
    #format avg so that it does not span 10 digits
    avgstr = avgstr[0:4]
    reciddict = alldict['reciddict']
    #output formatting
    outp = "<citationsummary records=\""+str(len(citedbylist))
    outp += "\" citations=\""+str(totalcites)+"\">"
    for low, high, name in CFG_CITESUMMARY_FAME_THRESHOLDS:
        #get the name, print the value
        if reciddict.has_key(name):
            recs = reciddict[name]
            outp += "<citationclass>"+name
            outp += "<records>"+str(recs)+"</records>"
            outp += "</citationclass>\n"
    outp = outp + "</citationsummary>"
    #req.write(outp)
    return outp #just to return something

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
        #take the numbers in CFG_CITESUMMARY_FAME_THRESHOLDS
        for low, high, name in CFG_CITESUMMARY_FAME_THRESHOLDS:
            if (numcites >= low) and (numcites <= high):
                if reciddict.has_key(name):
                    tmp = reciddict[name]
                    tmp.append(recid)
                    reciddict[name] = tmp
                else:
                    reciddict[name] = [recid]
    if (len(citedbylist) == 0):
        avgcites = 0
    else:
        avgcites = totalcites*1.0/len(citedbylist)

    #create a dictionary that contains all the values
    alldict = {}
    alldict['records'] = len(citedbylist)
    alldict['totalcites'] = totalcites
    alldict['avgcites'] = avgcites
    alldict['reciddict'] = reciddict
    return alldict
