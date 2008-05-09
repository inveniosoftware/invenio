# -*- coding: utf-8 -*-
## $Id$

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
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
Search Engine Summarizer, producing summary formats such as citesummary.
The main API is summarize_records().
"""

__lastupdated__ = """$Date$"""

__revision__ = "$Id$"

from invenio.bibrank_citation_searcher import get_cited_by_list
import search_engine
import invenio.template
websearch_templates = invenio.template.load('websearch')

try:
    Set = set
except NameError:
    from sets import Set

try:
    from invenio.config import CFG_CITESUMMARY_COLLECTIONS
except:
    CFG_CITESUMMARY_COLLECTIONS = []


COLLECTION_TAG = "980__a"

def summarize_records(recids, of, ln, defstring="", req=""):
    """Produces a report in the format defined by of in language ln
       defstring is a part of url added to point out how recids were selected
       for instance f=author&p=Smith, Paul
       req is the request. It is passed to print_citation_summary_html where
       it can be used for just-in-time printing
    """

    if of == 'hcs':
        #this is a html cite summary
        citedbylist = get_cited_by_list(recids)
        #divide the list into sublists according to the collection (980__b) info of the recs
        collections_citedbys = {}
        #scan the collections in CFG_CITESUMMARY_COLLECTIONS
        for coll in eval(CFG_CITESUMMARY_COLLECTIONS):
            #get the records that have this coll in 980__b
            recsinc = search_engine.search_pattern(f=COLLECTION_TAG,p=coll)
            #intersect recids and recsinc
            intersec_list = list(Set(recids)&Set(recsinc))
            collections_citedbys[coll] = intersec_list
        return print_citation_summary_html(citedbylist, ln, defstring, collections_citedbys, req)
    if of == 'xcs':
        #this is an xml cite summary
        citedbylist = get_cited_by_list(recids)
        return print_citation_summary_xml(citedbylist)

CFG_CITESUMMARY_THRESHOLD_NAMES = [
                                   (500, 1000000, 'Renowned papers (500+)'),
                                   (250, 499, 'Famous papers (250-499)'),
                                   (100, 249, 'Very well-known papers (100-249)'),
                                   (50, 99, 'Well-known papers (50-99)'),
                                   (10, 49, 'Known papers (10-49)'),
                                   (1, 9, 'Less known papers (1-9)'),
                                   (0, 0, 'Unknown papers (0)')
                                   ]

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
    for low, high, name in CFG_CITESUMMARY_THRESHOLD_NAMES:
        #get the name, print the value
        if reciddict.has_key(name):
            recs = reciddict[name]
            outp += "<citationclass>"+name
            outp += "<records>"+str(recs)+"</records>"
            outp += "</citationclass>\n"
    outp = outp + "</citationsummary>"
    #req.write(outp)
    return outp #just to return something


def print_citation_summary_html(citedbylist, ln, criteria="", dict_of_lists = {}, req=""):
    """Prints citation summary in html.
       The criteria, if any, is added to the link"""
    alldict = calculate_citations(citedbylist)
    avgstr = str(alldict['avgcites'])
    totalrecs = str(alldict['records'])
    totalcites = str(alldict['totalcites'])
    #format avg so that it does not span 10 digits
    avgstr = avgstr[0:4]
    reciddict = alldict['reciddict']
    return websearch_templates.tmpl_citesummary_html(ln, totalrecs,
                                                     totalcites, avgstr,
                                                     reciddict, CFG_CITESUMMARY_THRESHOLD_NAMES,
                                                     criteria, dict_of_lists, req)

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
        #take the numbers in CFG_CITESUMMARY_THRESHOLD_NAMES
        for low, high, name in CFG_CITESUMMARY_THRESHOLD_NAMES:
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


