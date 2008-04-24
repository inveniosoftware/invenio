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
from invenio.messages import gettext_set_language
from invenio.intbitset import intbitset as HitSet
import re
import string
import zlib
#from invenio.search_engine_utils import get_fieldvalues
#TODO: factoring invenio.search_engine and invenio.search_engine_utils
from invenio.dbquery import run_sql
import invenio.template
websearch_templates = invenio.template.load('websearch')
from invenio.config import CFG_SITE_LANG
try:
    from invenio.config import CFG_CITESUMMARY_COLLECTIONS
except:
    CFG_CITESUMMARY_COLLECTIONS = []


COLLECTION_TAG = "980__b"

def summarize_records(recids, of, ln, defstring=""):
    """Produces a report in the format defined by of in language ln
       defstring is a part of url added to point out how recids were selected
       for instance f=author&p=Smith, Paul"""
    if of == 'hcs':
        #this is a html cite summary
        citedbylist = get_cited_by_list(recids)
        #divide the list into sublists according to the collection (980__b) info of the recs
        collections_citedbys = {}
        #scan the collections in CFG_CITESUMMARY_COLLECTIONS
        for coll in eval(CFG_CITESUMMARY_COLLECTIONS):
            #get the records that have this coll in 980__b
            recsinc = tmp_search_pattern(f=COLLECTION_TAG,p=coll)
            collections_citedbys[coll] = recsinc


        return print_citation_summary_html(citedbylist, ln, defstring, collections_citedbys)
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


def print_citation_summary_html(citedbylist, ln, criteria="", dict_of_lists = {}):
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
                                                     criteria, dict_of_lists)

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



def tmp_get_fieldvalues(recID, tag):
    """Return list of field values for field TAG inside record RECID."""
    out = []
    if tag == "001___":
        # we have asked for recID that is not stored in bibXXx tables
        out.append(str(recID))
    else:
        # we are going to look inside bibXXx tables
        digits = tag[0:2]
        try:
            intdigits = int(digits)
            if intdigits < 0 or intdigits > 99:
                raise ValueError
        except ValueError:
            # invalid tag value asked for
            return []
        bx = "bib%sx" % digits
        bibx = "bibrec_bib%sx" % digits
        query = "SELECT bx.value FROM %s AS bx, %s AS bibx " \
                " WHERE bibx.id_bibrec='%s' AND bx.id=bibx.id_bibxxx AND bx.tag LIKE '%s' " \
                " ORDER BY bibx.field_number, bx.tag ASC" % (bx, bibx, recID, tag)
        res = run_sql(query)
        for row in res:
            out.append(row[0])
    return out

#This thing should be imported from search_engine but we cannot since search_engine imports this module
#TODO: refactor
def tmp_search_pattern(req=None, p=None, f=None, m=None, ap=0, of="id", verbose=0, ln=CFG_SITE_LANG):
    """Search for complex pattern 'p' within field 'f' according to
       matching type 'm'.  Return hitset of recIDs.

       The function uses multi-stage searching algorithm in case of no
       exact match found.  See the Search Internals document for
       detailed description.

       The 'ap' argument governs whether an alternative patterns are to
       be used in case there is no direct hit for (p,f,m).  For
       example, whether to replace non-alphanumeric characters by
       spaces if it would give some hits.  See the Search Internals
       document for detailed description.  (ap=0 forbits the
       alternative pattern usage, ap=1 permits it.)

       The 'of' argument governs whether to print or not some
       information to the user in case of no match found.  (Usually it
       prints the information in case of HTML formats, otherwise it's
       silent).

       The 'verbose' argument controls the level of debugging information
       to be printed (0=least, 9=most).

       All the parameters are assumed to have been previously washed.

       This function is suitable as a mid-level API.
    """

    _ = gettext_set_language(ln)

    hitset_empty = HitSet()
    # sanity check:
    if not p:
        hitset_full = HitSet(trailing_bits=1)
        hitset_full.discard(0)
        # no pattern, so return all universe
        return hitset_full
    # search stage 1: break up arguments into basic search units:
    if verbose and of.startswith("h"):
        t1 = os.times()[4]
    basic_search_units = create_basic_search_units(req, p, f, m, of)
    if verbose and of.startswith("h"):
        t2 = os.times()[4]
        print_warning(req, "Search stage 1: basic search units are: %s" % basic_search_units)
        print_warning(req, "Search stage 1: execution took %.2f seconds." % (t2 - t1))
    # search stage 2: do search for each search unit and verify hit presence:
    if verbose and of.startswith("h"):
        t1 = os.times()[4]
    basic_search_units_hitsets = []
    for idx_unit in range(0, len(basic_search_units)):
        bsu_o, bsu_p, bsu_f, bsu_m = basic_search_units[idx_unit]
        basic_search_unit_hitset = search_unit(bsu_p, bsu_f, bsu_m)
        if verbose >= 9 and of.startswith("h"):
            print_warning(req, "Search stage 1: pattern %s gave hitlist %s" % (bsu_p, list(basic_search_unit_hitset)))
        if len(basic_search_unit_hitset) > 0 or \
           ap==0 or \
           bsu_o=="|" or \
           ((idx_unit+1)<len(basic_search_units) and basic_search_units[idx_unit+1][0]=="|"):
            # stage 2-1: this basic search unit is retained, since
            # either the hitset is non-empty, or the approximate
            # pattern treatment is switched off, or the search unit
            # was joined by an OR operator to preceding/following
            # units so we do not require that it exists
            basic_search_units_hitsets.append(basic_search_unit_hitset)
        else:
            # stage 2-2: no hits found for this search unit, try to replace non-alphanumeric chars inside pattern:
            if re.search(r'[^a-zA-Z0-9\s\:]', bsu_p):
                if bsu_p.startswith('"') and bsu_p.endswith('"'): # is it ACC query?
                    bsu_pn = re.sub(r'[^a-zA-Z0-9\s\:]+', "*", bsu_p)
                else: # it is WRD query
                    bsu_pn = re.sub(r'[^a-zA-Z0-9\s\:]+', " ", bsu_p)
                if verbose and of.startswith('h') and req:
                    print_warning(req, "trying (%s,%s,%s)" % (bsu_pn, bsu_f, bsu_m))
                basic_search_unit_hitset = search_pattern(req=None, p=bsu_pn, f=bsu_f, m=bsu_m, of="id", ln=ln)
                if len(basic_search_unit_hitset) > 0:
                    # we retain the new unit instead
                    if of.startswith('h'):
                        print_warning(req, _("No exact match found for %(x_query1)s, using %(x_query2)s instead...") % \
                                      {'x_query1': "<em>" + cgi.escape(bsu_p) + "</em>",
                                       'x_query2': "<em>" + cgi.escape(bsu_pn) + "</em>"})
                    basic_search_units[idx_unit][1] = bsu_pn
                    basic_search_units_hitsets.append(basic_search_unit_hitset)
                else:
                    # stage 2-3: no hits found either, propose nearest indexed terms:
                    if of.startswith('h'):
                        if req:
                            if bsu_f == "recid":
                                print_warning(req, "Requested record does not seem to exist.")
                            else:
                                print_warning(req, create_nearest_terms_box(req.argd, bsu_p, bsu_f, bsu_m, ln=ln))
                    return hitset_empty
            else:
                # stage 2-3: no hits found either, propose nearest indexed terms:
                if of.startswith('h'):
                    if req:
                        if bsu_f == "recid":
                            print_warning(req, "Requested record does not seem to exist.")
                        else:
                            print_warning(req, create_nearest_terms_box(req.argd, bsu_p, bsu_f, bsu_m, ln=ln))
                return hitset_empty
    if verbose and of.startswith("h"):
        t2 = os.times()[4]
        for idx_unit in range(0, len(basic_search_units)):
            print_warning(req, "Search stage 2: basic search unit %s gave %d hits." %
                          (basic_search_units[idx_unit][1:], len(basic_search_units_hitsets[idx_unit])))
        print_warning(req, "Search stage 2: execution took %.2f seconds." % (t2 - t1))
    # search stage 3: apply boolean query for each search unit:
    if verbose and of.startswith("h"):
        t1 = os.times()[4]
    # let the initial set be the complete universe:
    hitset_in_any_collection = HitSet(trailing_bits=1)
    hitset_in_any_collection.discard(0)
    for idx_unit in range(0, len(basic_search_units)):
        this_unit_operation = basic_search_units[idx_unit][0]
        this_unit_hitset = basic_search_units_hitsets[idx_unit]
        if this_unit_operation == '+':
            hitset_in_any_collection.intersection_update(this_unit_hitset)
        elif this_unit_operation == '-':
            hitset_in_any_collection.difference_update(this_unit_hitset)
        elif this_unit_operation == '|':
            hitset_in_any_collection.union_update(this_unit_hitset)
        else:
            if of.startswith("h"):
                print_warning(req, "Invalid set operation %s." % this_unit_operation, "Error")
    if len(hitset_in_any_collection) == 0:
        # no hits found, propose alternative boolean query:
        if of.startswith('h'):
            nearestterms = []
            for idx_unit in range(0, len(basic_search_units)):
                bsu_o, bsu_p, bsu_f, bsu_m = basic_search_units[idx_unit]
                if bsu_p.startswith("%") and bsu_p.endswith("%"):
                    bsu_p = "'" + bsu_p[1:-1] + "'"
                bsu_nbhits = len(basic_search_units_hitsets[idx_unit])

                # create a similar query, but with the basic search unit only
                argd = {}
                argd.update(req.argd)

                argd['p'] = bsu_p
                argd['f'] = bsu_f

                nearestterms.append((bsu_p, bsu_nbhits, argd))

            text = websearch_templates.tmpl_search_no_boolean_hits(
                     ln=ln,  nearestterms=nearestterms)
            print_warning(req, text)
    if verbose and of.startswith("h"):
        t2 = os.times()[4]
        print_warning(req, "Search stage 3: boolean query gave %d hits." % len(hitset_in_any_collection))
        print_warning(req, "Search stage 3: execution took %.2f seconds." % (t2 - t1))
    return hitset_in_any_collection

#This thing should be imported from search_engine but we cannot since search_engine imports this module
#TODO: refactor
def create_basic_search_units(req, p, f, m=None, of='hb'):
    """Splits search pattern and search field into a list of independently searchable units.
       - A search unit consists of '(operator, pattern, field, type, hitset)' tuples where
          'operator' is set union (|), set intersection (+) or set exclusion (-);
          'pattern' is either a word (e.g. muon*) or a phrase (e.g. 'nuclear physics');
          'field' is either a code like 'title' or MARC tag like '100__a';
          'type' is the search type ('w' for word file search, 'a' for access file search).
        - Optionally, the function accepts the match type argument 'm'.
          If it is set (e.g. from advanced search interface), then it
          performs this kind of matching.  If it is not set, then a guess is made.
          'm' can have values: 'a'='all of the words', 'o'='any of the words',
                               'p'='phrase/substring', 'r'='regular expression',
                               'e'='exact value'.
        - Warnings are printed on req (when not None) in case of HTML output formats."""

    opfts = [] # will hold (o,p,f,t,h) units

    ## check arguments: if matching type phrase/string/regexp, do we have field defined?
    if (m=='p' or m=='r' or m=='e') and not f:
        m = 'a'
        if of.startswith("h"):
            print_warning(req, "This matching type cannot be used within <em>any field</em>.  I will perform a word search instead." )
            print_warning(req, "If you want to phrase/substring/regexp search in a specific field, e.g. inside title, then please choose <em>within title</em> search option.")

    ## is desired matching type set?
    if m:
        ## A - matching type is known; good!
        if m == 'e':
            # A1 - exact value:
            opfts.append(['+', p, f, 'a']) # '+' since we have only one unit
        elif m == 'p':
            # A2 - phrase/substring:
            opfts.append(['+', "%" + p + "%", f, 'a']) # '+' since we have only one unit
        elif m == 'r':
            # A3 - regular expression:
            opfts.append(['+', p, f, 'r']) # '+' since we have only one unit
        elif m == 'a' or m == 'w':
            # A4 - all of the words:
            p = strip_accents(p) # strip accents for 'w' mode, FIXME: delete when not needed
            for word in get_words_from_pattern(p):
                opfts.append(['+', word, f, 'w']) # '+' in all units
        elif m == 'o':
            # A5 - any of the words:
            p = strip_accents(p) # strip accents for 'w' mode, FIXME: delete when not needed
            for word in get_words_from_pattern(p):
                if len(opfts)==0:
                    opfts.append(['+', word, f, 'w']) # '+' in the first unit
                else:
                    opfts.append(['|', word, f, 'w']) # '|' in further units
        else:
            if of.startswith("h"):
                print_warning(req, "Matching type '%s' is not implemented yet." % m, "Warning")
            opfts.append(['+', "%" + p + "%", f, 'a'])
    else:
        ## B - matching type is not known: let us try to determine it by some heuristics
        if f and p[0] == '"' and p[-1] == '"':
            ## B0 - does 'p' start and end by double quote, and is 'f' defined? => doing ACC search
            opfts.append(['+', p[1:-1], f, 'a'])
        elif f and p[0] == "'" and p[-1] == "'":
            ## B0bis - does 'p' start and end by single quote, and is 'f' defined? => doing ACC search
            opfts.append(['+', '%' + p[1:-1] + '%', f, 'a'])
        elif f and p[0] == "/" and p[-1] == "/":
            ## B0ter - does 'p' start and end by a slash, and is 'f' defined? => doing regexp search
            opfts.append(['+', p[1:-1], f, 'r'])
        elif f and string.find(p, ',') >= 0:
            ## B1 - does 'p' contain comma, and is 'f' defined? => doing ACC search
            opfts.append(['+', p, f, 'a'])
        elif f and str(f[0:2]).isdigit():
            ## B2 - does 'f' exist and starts by two digits?  => doing ACC search
            opfts.append(['+', p, f, 'a'])
        else:
            ## B3 - doing WRD search, but maybe ACC too
            # search units are separated by spaces unless the space is within single or double quotes
            # so, let us replace temporarily any space within quotes by '__SPACE__'
            p = re_pattern_single_quotes.sub(lambda x: "'"+string.replace(x.group(1), ' ', '__SPACE__')+"'", p)
            p = re_pattern_double_quotes.sub(lambda x: "\""+string.replace(x.group(1), ' ', '__SPACE__')+"\"", p)
            p = re_pattern_regexp_quotes.sub(lambda x: "/"+string.replace(x.group(1), ' ', '__SPACE__')+"/", p)
            # wash argument:
            p = re_equal.sub(":", p)
            p = re_logical_and.sub(" ", p)
            p = re_logical_or.sub(" |", p)
            p = re_logical_not.sub(" -", p)
            p = re_operators.sub(r' \1', p)
            for pi in string.split(p): # iterate through separated units (or items, as "pi" stands for "p item")
                pi = re_pattern_space.sub(" ", pi) # replace back '__SPACE__' by ' '
                # firstly, determine set operator
                if pi[0] == '+' or pi[0] == '-' or pi[0] == '|':
                    oi = pi[0]
                    pi = pi[1:]
                else:
                    # okay, there is no operator, so let us decide what to do by default
                    oi = '+' # by default we are doing set intersection...
                # secondly, determine search pattern and field:
                if string.find(pi, ":") > 0:
                    fi, pi = string.split(pi, ":", 1)
                else:
                    fi, pi = f, pi
                # look also for old ALEPH field names:
                if fi and CFG_WEBSEARCH_FIELDS_CONVERT.has_key(string.lower(fi)):
                    fi = CFG_WEBSEARCH_FIELDS_CONVERT[string.lower(fi)]
                # wash 'pi' argument:
                if re_quotes.match(pi):
                    # B3a - quotes are found => do ACC search (phrase search)
                    if fi:
                        if pi[0] == '"' and pi[-1] == '"':
                            pi = string.replace(pi, '"', '') # remove quote signs
                            opfts.append([oi, pi, fi, 'a'])
                        elif pi[0] == "'" and pi[-1] == "'":
                            pi = string.replace(pi, "'", "") # remove quote signs
                            opfts.append([oi, "%" + pi + "%", fi, 'a'])
                        else: # unbalanced quotes, so do WRD query:
                            opfts.append([oi, pi, fi, 'w'])
                    else:
                        # fi is not defined, look at where we are doing exact or subphrase search (single/double quotes):
                        if pi[0] == '"' and pi[-1] == '"':
                            opfts.append([oi, pi[1:-1], "anyfield", 'a'])
                            if of.startswith("h"):
                                print_warning(req, "Searching for an exact match inside any field may be slow.  You may want to search for words instead, or choose to search within specific field.")
                        else:
                            # nope, subphrase in global index is not possible => change back to WRD search
                            pi = strip_accents(pi) # strip accents for 'w' mode, FIXME: delete when not needed
                            for pii in get_words_from_pattern(pi):
                                # since there may be '-' and other chars that we do not index in WRD
                                opfts.append([oi, pii, fi, 'w'])
                            if of.startswith("h"):
                                print_warning(req, "The partial phrase search does not work in any field.  I'll do a boolean AND searching instead.")
                                print_warning(req, "If you want to do a partial phrase search in a specific field, e.g. inside title, then please choose 'within title' search option.", "Tip")
                                print_warning(req, "If you want to do exact phrase matching, then please use double quotes.", "Tip")
                elif fi and str(fi[0]).isdigit() and str(fi[0]).isdigit():
                    # B3b - fi exists and starts by two digits => do ACC search
                    opfts.append([oi, pi, fi, 'a'])
                elif fi and not get_index_id_from_field(fi):
                    # B3c - fi exists but there is no words table for fi => try ACC search
                    opfts.append([oi, pi, fi, 'a'])
                elif fi and pi.startswith('/') and pi.endswith('/'):
                    # B3d - fi exists and slashes found => try regexp search
                    opfts.append([oi, pi[1:-1], fi, 'r'])
                else:
                    # B3e - general case => do WRD search
                    pi = strip_accents(pi) # strip accents for 'w' mode, FIXME: delete when not needed
                    for pii in get_words_from_pattern(pi):
                        opfts.append([oi, pii, fi, 'w'])

    ## sanity check:
    for i in range(0, len(opfts)):
        try:
            pi = opfts[i][1]
            if pi == '*':
                if of.startswith("h"):
                    print_warning(req, "Ignoring standalone wildcard word.", "Warning")
                del opfts[i]
            if pi == '' or pi == ' ':
                fi = opfts[i][2]
                if fi:
                    if of.startswith("h"):
                        print_warning(req, "Ignoring empty <em>%s</em> search term." % fi, "Warning")
                del opfts[i]
        except:
            pass

    ## return search units:
    return opfts

#This thing should be imported from search_engine but we cannot since search_engine imports this module
#TODO: refactor
def search_unit(p, f=None, m=None):
    """Search for basic search unit defined by pattern 'p' and field
       'f' and matching type 'm'.  Return hitset of recIDs.

       All the parameters are assumed to have been previously washed.
       'p' is assumed to be already a ``basic search unit'' so that it
       is searched as such and is not broken up in any way.  Only
       wildcard and span queries are being detected inside 'p'.

       This function is suitable as a low-level API.
    """

    ## create empty output results set:
    set = HitSet()
    if not p: # sanity checking
        return set
    if m == 'a' or m == 'r':
        # we are doing either direct bibxxx search or phrase search or regexp search
        set = search_unit_in_bibxxx(p, f, m)
    else:
        # we are doing bibwords search by default
        set = search_unit_in_bibwords(p, f)
    return set

#This thing should be imported from search_engine but we cannot since search_engine imports this module
#TODO: refactor
def search_unit_in_bibwords(word, f, decompress=zlib.decompress):
    """Searches for 'word' inside bibwordsX table for field 'f' and returns hitset of recIDs."""
    set = HitSet() # will hold output result set
    set_used = 0 # not-yet-used flag, to be able to circumvent set operations
    # deduce into which bibwordsX table we will search:
    stemming_language = get_index_stemming_language(get_index_id_from_field("anyfield"))
    bibwordsX = "idxWORD%02dF" % get_index_id_from_field("anyfield")
    if f:
        index_id = get_index_id_from_field(f)
        if index_id:
            bibwordsX = "idxWORD%02dF" % index_id
            stemming_language = get_index_stemming_language(index_id)
        else:
            return HitSet() # word index f does not exist

    # wash 'word' argument and run query:
    word = string.replace(word, '*', '%') # we now use '*' as the truncation character
    words = string.split(word, "->", 1) # check for span query
    if len(words) == 2:
        word0 = re_word.sub('', words[0])
        word1 = re_word.sub('', words[1])
        if stemming_language:
            word0 = stem(word0, stemming_language)
            word1 = stem(word1, stemming_language)
        res = run_sql("SELECT term,hitlist FROM %s WHERE term BETWEEN %%s AND %%s" % bibwordsX,
                      (wash_index_term(word0), wash_index_term(word1)))
    else:
        word = re_word.sub('', word)
        if stemming_language:
            word = stem(word, stemming_language)
        if string.find(word, '%') >= 0: # do we have wildcard in the word?
            res = run_sql("SELECT term,hitlist FROM %s WHERE term LIKE %%s" % bibwordsX,
                          (wash_index_term(word),))
        else:
            res = run_sql("SELECT term,hitlist FROM %s WHERE term=%%s" % bibwordsX,
                          (wash_index_term(word),))
    # fill the result set:
    for word, hitlist in res:
        hitset_bibwrd = HitSet(hitlist)
        # add the results:
        if set_used:
            set.union_update(hitset_bibwrd)
        else:
            set = hitset_bibwrd
            set_used = 1
    # okay, return result set:
    return set

#This thing should be imported from search_engine but we cannot since search_engine imports this module
#TODO: refactor
def search_unit_in_bibxxx(p, f, type):
    """Searches for pattern 'p' inside bibxxx tables for field 'f' and returns hitset of recIDs found.
    The search type is defined by 'type' (e.g. equals to 'r' for a regexp search)."""
    p_orig = p # saving for eventual future 'no match' reporting
    query_addons = "" # will hold additional SQL code for the query
    query_params = () # will hold parameters for the query (their number may vary depending on TYPE argument)
    # wash arguments:
    f = string.replace(f, '*', '%') # replace truncation char '*' in field definition
    if type == 'r':
        query_addons = "REGEXP %s"
        query_params = (p,)
    else:
        p = string.replace(p, '*', '%') # we now use '*' as the truncation character
        ps = string.split(p, "->", 1) # check for span query:
        if len(ps) == 2:
            query_addons = "BETWEEN %s AND %s"
            query_params = (ps[0], ps[1])
        else:
            if string.find(p, '%') > -1:
                query_addons = "LIKE %s"
                query_params = (ps[0],)
            else:
                query_addons = "= %s"
                query_params = (ps[0],)
    # construct 'tl' which defines the tag list (MARC tags) to search in:
    tl = []
    if str(f[0]).isdigit() and str(f[1]).isdigit():
        tl.append(f) # 'f' seems to be okay as it starts by two digits
    else:
        # convert old ALEPH tag names, if appropriate: (TODO: get rid of this before entering this function)
        if CFG_WEBSEARCH_FIELDS_CONVERT.has_key(string.lower(f)):
            f = CFG_WEBSEARCH_FIELDS_CONVERT[string.lower(f)]
        # deduce desired MARC tags on the basis of chosen 'f'
        tl = get_field_tags(f)
        if not tl:
            # f index does not exist, nevermind
            pass
    # okay, start search:
    l = [] # will hold list of recID that matched
    for t in tl:
        # deduce into which bibxxx table we will search:
        digit1, digit2 = int(t[0]), int(t[1])
        bx = "bib%d%dx" % (digit1, digit2)
        bibx = "bibrec_bib%d%dx" % (digit1, digit2)
        # construct and run query:
        if t == "001":
            res = run_sql("SELECT id FROM bibrec WHERE id %s" % query_addons,
                          query_params)
        else:
            query = "SELECT bibx.id_bibrec FROM %s AS bx LEFT JOIN %s AS bibx ON bx.id=bibx.id_bibxxx WHERE bx.value %s" % \
                    (bx, bibx, query_addons)
            if len(t) != 6 or t[-1:]=='%':
                # wildcard query, or only the beginning of field 't'
                # is defined, so add wildcard character:
                query += " AND bx.tag LIKE %s"
                res = run_sql(query, query_params + (t + '%',))
            else:
                # exact query for 't':
                query += " AND bx.tag=%s"
                res = run_sql(query, query_params + (t,))
        # fill the result set:
        for id_bibrec in res:
            if id_bibrec[0]:
                l.append(id_bibrec[0])
    # check no of hits found:
    nb_hits = len(l)
    # okay, return result set:
    set = HitSet(l)
    return set

#This thing should be imported from search_engine but we cannot since search_engine imports this module
#TODO: refactor
def search_unit_in_bibrec(datetext1, datetext2, type='c'):
    """
    Return hitset of recIDs found that were either created or modified
    (according to 'type' arg being 'c' or 'm') from datetext1 until datetext2, inclusive.
    Does not pay attention to pattern, collection, anything.  Useful
    to intersect later on with the 'real' query.
    """
    set = HitSet()
    if type.startswith("m"):
        type = "modification_date"
    else:
        type = "creation_date" # by default we are searching for creation dates
    res = run_sql("SELECT id FROM bibrec WHERE %s>=%%s AND %s<=%%s" % (type, type),
                  (datetext1, datetext2))
    for row in res:
        set += row[0]
    return set
