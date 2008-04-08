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
import invenio.template
websearch_templates = invenio.template.load('websearch')

def summarize_records(recids, of, ln):
    """Produces a report in the format defined by of in language ln"""
    if of == 'hcs':
        #this is a html cite summary
        citedbylist = get_cited_by_list(recids)
        return print_citation_summary_html(citedbylist, ln)
    if of == 'xcs':
        #this is an xml cite summary
        citedbylist = get_cited_by_list(recids)
        return print_citation_summary_xml(citedbylist)

CFG_CITESUMMARY_THRESHOLD_NAMES = [(0, 0, 'Unknown papers (0)'),
                                   (1, 9, 'Less known papers (1-9)'),
                                   (10, 49, 'Known papers (10-49)'),
                                   (50, 99, 'Well-known papers (50-99)'),
                                   (100, 249, 'Very well-known papers (100-249)'),
                                   (250, 499, 'Famous papers (250-499)'),
                                   (500, 1000000, 'Renowned papers (500+)'),]

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


def print_citation_summary_html(citedbylist, ln, criteria=""):
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
                                                     reciddict)

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
