## $Id$
## CDSware Search Engine in mod_python.

## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002 CERN.
##
## The CDSware is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## The CDSware is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.  
##
## You should have received a copy of the GNU General Public License
## along with CDSware; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

<protect># -*- coding: utf-8 -*-</protect>

"""CDSware Search Engine in mod_python."""

__lastupdated__ = """<: print `date +"%d %b %Y %H:%M:%S %Z"`; :>"""

<protect> ## okay, rest of the Python code goes below #######

__version__ = "$Id$"

## import general modules:
import cgi
import copy
import Cookie
import cPickle
import marshal
import fileinput
import getopt
import string
from string import split
import os
import sre
import sys
import time
import traceback
import urllib
import zlib
import MySQLdb
import Numeric
import md5
import base64
import unicodedata

## import CDSware stuff:
from config import *
from messages import *
from search_engine_config import *
from dbquery import run_sql
try:
    from webuser import getUid, create_user_infobox
    from webpage import pageheaderonly, pagefooteronly, create_error_box
except ImportError, e:
    pass # ignore user personalisation, needed e.g. for command-line

## global vars:
search_cache = {} # will cache results of previous searches
cfg_nb_browse_seen_records = 100 # limit of the number of records to check when browsing certain collection
cfg_nicely_ordered_collection_list = 0 # do we propose collection list nicely ordered or alphabetical?

## precompile some often-used regexp for speed reasons:
re_word = sre.compile('[\s]')
re_quotes = sre.compile('[\'\"]')
re_doublequote = sre.compile('\"')
re_equal = sre.compile('\=')
re_logical_and = sre.compile('\sand\s', sre.I)
re_logical_or = sre.compile('\sor\s', sre.I)
re_logical_not = sre.compile('\snot\s', sre.I)
re_operands = sre.compile(r'\s([\+\-\|])\s')

def get_alphabetically_ordered_collection_list(collid=1, level=0):
    """Returns nicely ordered (score respected) list of collections, more exactly list of tuples
       (collection name, printable collection name).
       Suitable for create_search_box()."""
    out = []
    query = "SELECT id,name FROM collection ORDER BY name ASC"
    res = run_sql(query)
    for c_id, c_name in res:
        # make a nice printable name (e.g. truncate c_printable for for long collection names):
        if len(c_name)>30:
            c_printable = c_name[:30] + "..."
        else:
            c_printable = c_name
        if level:
            c_printable = " " + level * '-' + " " + c_printable
        out.append([c_name, c_printable])
    return out    
    
def get_nicely_ordered_collection_list(collid=1, level=0):
    """Returns nicely ordered (score respected) list of collections, more exactly list of tuples
       (collection name, printable collection name).
       Suitable for create_search_box()."""
    colls_nicely_ordered = []
    query = "SELECT c.name,cc.id_son FROM collection_collection AS cc, collection AS c "\
            " WHERE c.id=cc.id_son AND cc.id_dad='%s' ORDER BY score DESC" % collid
    res = run_sql(query)
    for c, cid in res:
        # make a nice printable name (e.g. truncate c_printable for for long collection names):
        if len(c)>30:
            c_printable = c[:30] + "..."
        else:
            c_printable = c
        if level:
            c_printable = " " + level * '-' + " " + c_printable
        colls_nicely_ordered.append([c, c_printable])
        colls_nicely_ordered  = colls_nicely_ordered + get_nicely_ordered_collection_list(cid, level+1)
    return colls_nicely_ordered

def get_wordsindex_id(field):
    """Returns first words index id where the field code 'field' is word-indexed.
       Returns zero in case there is no words table for this index.
       Example: field='author', output=4."""
    out = 0
    query = """SELECT w.id FROM wordsindex AS w, wordsindex_field AS wf, field AS f
                WHERE f.code='%s' AND wf.id_field=f.id AND w.id=wf.id_wordsindex
                LIMIT 1""" % MySQLdb.escape_string(field)
    res = run_sql(query, None, 1)
    if res:
        out = res[0][0]
    return out

def get_words_from_pattern(pattern):
    "Returns list of whitespace-separated words from pattern."
    words = {}
    for word in split(pattern):
        if not words.has_key(word):
            words[word] = 1;
    return words.keys()

def create_basic_search_units(req, p, f, m=None):
    """Splits search pattern and search field into a list of independently searchable units.
       - A search unit consists of '(operand, pattern, field, type, hitset)' tuples where
          'operand' is set union (|), set intersection (+) or set exclusion (-);
          'pattern' is either a word (e.g. muon*) or a phrase (e.g. 'nuclear physics');
          'field' is either a code like 'title' or MARC tag like '100__a';
          'type' is the search type ('w' for word file search, 'a' for access file search).
        - Optionally, the function accepts the match type argument 'm'.
          If it is set (e.g. from advanced search interface), then it
          performs this kind of matching.  If it is not set, then a guess is made.
          'm' can have values: 'a'='all of the words', 'o'='any of the words',
                               'p'='phrase/substring', 'r'='regular expression',
                               'e'='exact value'."""

    opfts = [] # will hold (o,p,f,t,h) units

    ## check arguments: if matching type phrase/string/regexp, do we have field defined?
    if (m=='p' or m=='r' or m=='e') and not f:
        m = 'a'        
        print_warning(req, "This matching type cannot be used within <em>any field</em>.  I will perform a word search instead." )
        print_warning(req, "If you want to phrase/substring/regexp search in a specific field, e.g. inside title, then please choose <em>within title</em> search option.")
        
    ## is desired matching type set?
    if m:
        ## A - matching type is known; good!
        if m == 'e':
            # A1 - exact value:
            opfts.append(['|',p,f,'a']) # '|' since we have only one unit
        elif m == 'p':
            # A2 - phrase/substring:
            opfts.append(['|',"%"+p+"%",f,'a']) # '|' since we have only one unit
        elif m == 'r':
            # A3 - regular expression:
            opfts.append(['|',p,f,'r']) # '|' since we have only one unit
        elif m == 'a' or m == 'w':
            # A4 - all of the words:
            for word in get_words_from_pattern(p):
                if len(opfts)==0:
                    opfts.append(['|',word,f,'w']) # '|' in the first unit
                else:
                    opfts.append(['+',word,f,'w']) # '+' in further units
        elif m == 'o':
            # A5 - any of the words:
            for word in get_words_from_pattern(p):
                opfts.append(['|',word,f,'w']) # '|' in all units
        else:
            print_warning(req, "Matching type '%s' is not implemented yet." % m, "Warning")
            opfts.append(['|',"%"+p+"%",f,'a'])            
    else:        
        ## B - matching type is not known: let us try to determine it by some heuristics
        if f and p[0]=='"' and p[-1]=='"':
            ## B0 - does 'p' start and end by double quote, and is 'f' defined? => doing ACC search            
            opfts.append(['|',p[1:-1],f,'a'])
        elif f and p[0]=="'" and p[-1]=="'":
            ## B0bis - does 'p' start and end by single quote, and is 'f' defined? => doing ACC search            
            opfts.append(['|','%'+p[1:-1]+'%',f,'a'])
        elif f and string.find(p, ',') >= 0:
            ## B1 - does 'p' contain comma, and is 'f' defined? => doing ACC search
            opfts.append(['|',p,f,'a'])
        elif f and str(f[0:2]).isdigit():
            ## B2 - does 'f' exist and starts by two digits?  => doing ACC search
            opfts.append(['|',p,f,'a'])            
        else:
            ## B3 - doing WRD search, but maybe ACC too
            # search units are separated by spaces unless the space is within single or double quotes
            # so, let us replace temporarily any space within quotes by '__SPACE__'
            p = sre.sub("'(.*?)'", lambda x: "'"+string.replace(x.group(1), ' ', '__SPACE__')+"'", p) 
            p = sre.sub("\"(.*?)\"", lambda x: "\""+string.replace(x.group(1), ' ', '__SPACEBIS__')+"\"", p) 
            # wash argument:
            p = re_equal.sub(":", p)
            p = re_logical_and.sub(" ", p)
            p = re_logical_or.sub(" |", p)
            p = re_logical_not.sub(" -", p)
            p = re_operands.sub(r' \1', p)
            for pi in split(p): # iterate through separated units (or items, as "pi" stands for "p item")
                pi = sre.sub("__SPACE__", " ", pi) # replace back '__SPACE__' by ' ' 
                pi = sre.sub("__SPACEBIS__", " ", pi) # replace back '__SPACEBIS__' by ' '
                # firstly, determine set operand
                if pi[0] == '+' or pi[0] == '-' or pi[0] == '|':
                    if len(opfts) or pi[0] == '-': # either not first unit, or '-' for the first unit
                        oi = pi[0]
                    else:
                        oi = "|" # we are in the first unit and operand is not '-', so let us do 
                                 # set union (with still null result set) 
                    pi = pi[1:]
                else:
                    # okay, there is no operand, so let us decide what to do by default
                    if len(opfts):
                        oi = '+' # by default we are doing set intersection...
                    else:
                        oi = "|" # ...unless we are in the first unit
                # secondly, determine search pattern and field:
                if string.find(pi, ":") > 0:
                    fi, pi = split(pi, ":", 1)
                else:
                    fi, pi = f, pi
                # look also for old ALEPH field names:
                if fi and cfg_fields_convert.has_key(string.lower(fi)):
                    fi = cfg_fields_convert[string.lower(fi)]
                # wash 'pi' argument:
                if re_quotes.match(pi):
                    # B3a - quotes are found => do ACC search (phrase search)
                    if fi:
                        if re_doublequote.match(pi):
                            pi = string.replace(pi, '"', '') # get rid of quotes
                            opfts.append([oi,pi,fi,'a'])
                        else:
                            pi = string.replace(pi, "'", '') # get rid of quotes
                            opfts.append([oi,"%"+pi+"%",fi,'a'])
                    else:
                        # fi is not defined, look at where we are doing exact or subphrase search (single/double quotes):
                        if pi[0]=='"' and pi[-1]=='"':                        
                            opfts.append([oi,pi[1:-1],"anyfield",'a'])
                            print_warning(req, "Searching for an exact match inside any field may be slow.  You may want to search for words instead, or choose to search within specific field.")
                        else:                        
                            # nope, subphrase in global index is not possible => change back to WRD search
                            for pii in get_words_from_pattern(pi):
                                # since there may be '-' and other chars that we do not index in WRD
                                opfts.append([oi,pii,fi,'w'])
                            print_warning(req, "The partial phrase search does not work in any field.  I'll do a boolean AND searching instead.")
                            print_warning(req, "If you want to do a partial phrase search in a specific field, e.g. inside title, then please choose 'within title' search option.", "Tip")
                            print_warning(req, "If you want to do exact phrase matching, then please use double quotes.", "Tip")
                elif fi and str(fi[0]).isdigit() and str(fi[0]).isdigit():
                    # B3b - fi exists and starts by two digits => do ACC search
                    opfts.append([oi,pi,fi,'a'])            
                elif fi and not get_wordsindex_id(fi):
                    # B3c - fi exists but there is no words table for fi => try ACC search
                    opfts.append([oi,pi,fi,'a'])            
                else:
                    # B3d - general case => do WRD search                    
                    for pii in get_words_from_pattern(pi): 
                        opfts.append([oi,pii,fi,'w'])

    ## sanity check:
    for i in range(0,len(opfts)):
        try:
            pi = opfts[i][1]
            if pi == '*':
                print_warning(req, "Ignoring standalone wildcard word.", "Warning")
                del opfts[i]
            if pi == '' or pi == ' ':
                fi = opfts[i][2]
                if fi:
                    print_warning(req, "Ignoring empty <em>%s</em> search term." % fi, "Warning")
                del opfts[i]
        except:
            pass

    ## return search units:
    return opfts

def page_start(req, of, cc, as, ln, uid):
    "Start page according to given output format."
    if of.startswith('x'):
        # we are doing XML output:
        req.content_type = "text/xml"
        req.send_http_header()
        req.write("""<?xml version="1.0" encoding="UTF-8"?>\n""")
        if of.startswith("xm"):
            req.write("""<collection xmlns="http://www.loc.gov/MARC21/slim">\n""")
        else:
            req.write("""<collection>\n""")
    elif of.startswith('t') or str(of[0:3]).isdigit():
        # we are doing plain text output:
        req.content_type = "text/plain"
        req.send_http_header()
    elif of == "id":
        pass # nothing to do, we shall only return list of recIDs 
    else:
        # we are doing HTML output:
        req.content_type = "text/html"
        req.send_http_header()
        req.write(pageheaderonly(title=msg_search_results[ln],
                                 navtrail=create_navtrail_links(cc, as, ln, 1),
                                 description="%s %s." % (cc, msg_search_results[ln]),
                                 keywords="CDSware, WebSearch, %s" % cc,
                                 uid=uid,
                                 language=ln))
        req.write("""<div class="pagebody">""")
    
def page_end(req, of="hb", ln=cdslang):
    "End page according to given output format: e.g. close XML tags, add HTML footer, etc."
    if of.startswith('h'):
        req.write("""</div>""") # pagebody end
        req.write(pagefooteronly(lastupdated=__lastupdated__, language=ln))
    elif of.startswith('x'):
        req.write("""</collection>\n""")
    if of == "id":
        return []
    else: return "\n"    

def create_inputdate_box(name="d1", selected_year=0, selected_month=0, selected_day=0):
    "Produces 'From Date', 'Until Date' kind of selection box.  Suitable for search options."
    box = ""
    # day
    box += """<select name="%sd">""" % name
    box += """<option value="">any day"""
    for day in range(1,32):
        box += """<option value="%02d"%s>%02d""" % (day, is_selected(day, selected_day), day)
    box += """</select>"""
    # month
    box += """<select name="%sm">""" % name
    box += """<option value="">any month"""
    for mm, month in [(1,'January'), (2,'February'), (3,'March'), (4,'April'), \
                      (5,'May'), (6,'June'), (7,'July'), (8,'August'), \
                      (9,'September'), (10,'October'), (11,'November'), (12,'December')]:
        box += """<option value="%d"%s>%s""" % (mm, is_selected(mm, selected_month), month)
    box += """</select>"""
    # year
    box += """<select name="%sy">""" % name
    box += """<option value="">any year"""
    for year in range(1980,2004):
        box += """<option value="%d"%s>%d""" % (year, is_selected(year, selected_year), year)
    box += """</select>"""        
    return box

def create_google_box(p, f, p1, p2, p3, ln=cdslang,
                      prolog_start="""<table class="googlebox"><tr><th class="googleboxheader">""",
                      prolog_end="""</th></tr><tr><td class="googleboxbody">""",
                      separator= """<br>""",
                      epilog="""</td></tr></table>"""):
    "Creates the box that proposes links to other useful search engines like Google.  'p' is the search pattern."
    out = ""
    if not p and (p1 or p2 or p3):
        p = p1 + " " + p2 + " " + p3 
    if cfg_google_box: # do we want to print it?
        out += prolog_start + msg_try_your_search_on[ln] + prolog_end
        if cfg_cern_site:
            # CERN Intranet:
            out += """<a href="http://search.cern.ch/query.html?qt=%s">CERN&nbsp;Intranet</a>""" % urllib.quote(p)
            # SPIRES
            if f == "author":
                out += separator
                out += """<a href="http://www.slac.stanford.edu/spires/find/hep/www?AUTHOR=%s">SPIRES</a>""" % urllib.quote(p)
            elif f == "title":
                out += separator
                out += """<a href="http://www.slac.stanford.edu/spires/find/hep/www?TITLE=%s">SPIRES</a>""" % urllib.quote(p)
            elif f == "reportnumber":
                out += separator
                out += """<a href="http://www.slac.stanford.edu/spires/find/hep/www?REPORT-NUM=%s">SPIRES</a>""" % urllib.quote(p)
            elif f == "keyword":
                out += separator
                out += """<a href="http://www.slac.stanford.edu/spires/find/hep/www?k=%s">SPIRES</a>""" % urllib.quote(p)
            # KEK
            if f == "author":
                out += separator
                out += """<a href="http://www-lib.kek.jp/cgi-bin/kiss_prepri?AU=%s">KEK</a>""" % urllib.quote(p)        
            elif f == "title":
                out += separator
                out += """<a href="http://www-lib.kek.jp/cgi-bin/kiss_prepri?TI=%s">KEK</a>""" % urllib.quote(p)        
            elif f == "reportnumber":
                out += separator
                out += """<a href="http://www-lib.kek.jp/cgi-bin/kiss_prepri?RP=%s">KEK</a>""" % urllib.quote(p)        
            out += separator
        # Google:
        out += """<a href="http://google.com/search?q=%s">Google</a>""" % urllib.quote(p)
        # AllTheWeb:
        out += separator
        out += """<a href="http://alltheweb.com/search?q=%s">AllTheWeb</a>""" % urllib.quote(p)
        out += epilog
    return out

def create_search_box(cc, colls, p, f, rg, sf, so, sp, of, ot, as, ln, p1, f1, m1, op1, p2, f2, m2, op2, p3, f3, m3, sc, pl,
                      d1y, d1m, d1d, d2y, d2m, d2d, action=""):
    "Create search box for 'search again in the results page' functionality."
    out = ""    
    # print search box prolog:
    if cc == cdsname:
        cc_intl = cdsnameintl[ln]
    else:
        cc_intl = cc
    out += """
    <h1 class="headline">%s</h1>
    <form action="%s/search.py" method="get">
    <input type="hidden" name="cc" value="%s"> 
    <input type="hidden" name="as" value="%s">
    <input type="hidden" name="ln" value="%s">
    """ % (cc_intl, weburl, cc, as, ln)
    if ot:
        out += """<input type="hidden" name="ot" value="%s">""" % ot
    if sp:
        out += """<input type="hidden" name="sp" value="%s">""" % sp 

    # decide upon leading text:
    leadingtext = msg_search[ln]
    if action == msg_browse[ln]:
        leadingtext = msg_browse[ln]
    ## firstly, print Query box:
    if as==1:
        # print Advanced Search form:
        # define search box elements:
        cell_1_left = create_matchtype_box('m1', m1, ln=ln) + \
                      """<input type="text" name="p1" size="%d" value="%s">""" % (cfg_advancedsearch_pattern_box_width, cgi.escape(p1,1))
        cell_1_right = create_searchwithin_selection_box('f1', f1, ln=ln)
        cell_1_moreright = create_andornot_box('op1', op1, ln=ln)
        cell_2_left = create_matchtype_box('m2', m2, ln=ln) + """<input type="text" name="p2" size="%d" value="%s">""" % (cfg_advancedsearch_pattern_box_width, cgi.escape(p2,1))
        cell_2_right = create_searchwithin_selection_box('f2', f2, ln=ln)
        cell_2_moreright = create_andornot_box('op2', op2, ln=ln)
        cell_3_left = create_matchtype_box('m3', m3, ln=ln) + """<input type="text" name="p3" size="%d" value="%s">""" % (cfg_advancedsearch_pattern_box_width, cgi.escape(p3,1))
        cell_3_right = create_searchwithin_selection_box('f3', f3, ln=ln)
        cell_3_moreright = """<input class="formbutton" type="submit" name="action" value="%s"><input class="formbutton" type="submit" name="action" value="%s">&nbsp;""" % (msg_search[ln], msg_browse[ln])
        cell_4 = """<small><a href="%s/help/search/tips.%s.html">%s</a> ::
                           <a href="%s/search.py?p=%s&amp;f=%s&amp;cc=%s&amp;ln=%s">%s</a></small>""" % \
                    (weburl, ln, msg_search_tips[ln], weburl, urllib.quote(p1), urllib.quote(f1), urllib.quote(cc), ln, msg_simple_search[ln])
        # print them:
        out += """
        <table class="searchbox">
         <thead>
          <tr>
           <th colspan="3" class="searchboxheader">
            %s:
           </th>
          </tr> 
         </thead>
         <tbody>
          <tr valign="bottom">
            <td class="searchboxbody">%s</td>
            <td class="searchboxbody">%s</td>
            <td class="searchboxbody">%s</td>
          </tr>
          <tr valign="bottom">
            <td class="searchboxbody">%s</td>
            <td class="searchboxbody">%s</td>
            <td class="searchboxbody">%s</td>
          </tr>
          <tr valign="bottom">
            <td class="searchboxbody">%s</td>
            <td class="searchboxbody">%s</td>
            <td class="searchboxbody">%s</td>
          </tr>
          <tr valign="bottom">
            <td colspan="3" align="right" class="searchboxbody">%s</td>
          </tr>
         </tbody>
        </table>
        """ % \
         (leadingtext,
          cell_1_left, cell_1_right, cell_1_moreright, \
          cell_2_left, cell_2_right, cell_2_moreright, \
          cell_3_left, cell_3_right, cell_3_moreright,
          cell_4)         
    else:
        # print Simple Search form:
        cell_1_left = """<input type="text" name="p" size="%d" value="%s">""" % \
        (cfg_simplesearch_pattern_box_width, cgi.escape(p, 1))
        cell_1_middle = create_searchwithin_selection_box('f', f, ln=ln)
        cell_1_right = """<input class="formbutton" type="submit" name="action" value="%s"><input class="formbutton" type="submit" name="action" value="%s">&nbsp;""" % (msg_search[ln], msg_browse[ln])
        cell_2 = """<small><a href="%s/help/search/tips.%s.html">%s</a> ::
                           <a href="%s/search.py?p1=%s&amp;f1=%s&amp;as=1&amp;cc=%s&amp;ln=%s">%s</a></small>""" %\
                          (weburl, ln, msg_search_tips[ln], weburl, urllib.quote(p), urllib.quote(f), urllib.quote(cc), ln, msg_advanced_search[ln])
        out += """
        <table class="searchbox">
         <thead>
          <tr>
           <th colspan="3" class="searchboxheader">
            %s:
           </th>
          </tr> 
         </thead>
         <tbody>
          <tr valign="bottom">
            <td class="searchboxbody">%s</td>
            <td class="searchboxbody">%s</td>
            <td class="searchboxbody">%s</td>
          </tr>
          <tr valign="bottom">
            <td colspan="3" align="right" class="searchboxbody">%s</td>
          </tr>
         </tbody>
        </table> 
        """ % (leadingtext,
               cell_1_left, cell_1_middle, cell_1_right,
               cell_2)
    ## secondly, print Collection(s) box:
    out += """
        <table class="searchbox">
         <thead>
          <tr>
           <th colspan="3" class="searchboxheader">
            %s %s:
           </th>
          </tr> 
         </thead>
         <tbody>
          <tr valign="bottom">
           <td valign="top" class="searchboxbody">""" % (leadingtext, msg_collections[ln])
    colls_nicely_ordered = []
    if cfg_nicely_ordered_collection_list:
        colls_nicely_ordered = get_nicely_ordered_collection_list()
    else:
        colls_nicely_ordered = get_alphabetically_ordered_collection_list()    
    if colls and colls[0] != cdsname:
        # some collections are defined, so print these first, and only then print 'add another collection' heading:
        for c in colls:
            if c:
                out += """<select name="c"><option value="">*** %s ***""" % msg_any_collection[ln]
                for (cx, cx_printable) in colls_nicely_ordered:
                    # print collection:
                    if not cx.startswith("Unnamed collection"):                    
                        out+= """<option value="%s"%s>%s""" % (cx, is_selected(c, sre.sub("^[\s\-]*","",cx)), cx_printable)
                out += """</select>"""
        out += """<select name="c"><option value="">*** %s ***""" % msg_add_another_collection[ln]
    else: # we searched in CDSNAME, so print 'any collection' heading
        out += """<select name="c"><option value="">*** %s ***""" % msg_any_collection[ln]
    for (cx, cx_printable) in colls_nicely_ordered:
        if not cx.startswith("Unnamed collection"):
            out += """<option value="%s">%s""" % (cx, cx_printable)
    out += """
    </select>
    </td>
    </tr>
    </tbody>
    </table>"""
    ## thirdly, print search limits, if applicable:
    if action != msg_browse[ln] and pl:
        out += """<table class="searchbox">
                   <thead> 
                    <tr>
                      <th class="searchboxheader">
                        Limit to:
                      </th>
                    </tr>
                   </thead>
                   <tbody>
                    <tr valign="bottom">
                      <td class="searchboxbody">
                       <input type="text" name="pl" value="%s">
                      </td>
                    </tr>
                   </tbody>
                  </table>""" % cgi.escape(pl, 1)
    ## fourthly, print from/until date boxen, if applicable:
    if action==msg_browse[ln] or (d1y==0 and d1m==0 and d1d==0 and d2y==0 and d2m==0 and d2d==0):
        pass # do not need it
    else:
        cell_6_a = create_inputdate_box("d1", d1y, d1m, d1d)
        cell_6_b = create_inputdate_box("d2", d2y, d2m, d2d)
        out += """<table class="searchbox">
                   <thead> 
                    <tr>
                      <th class="searchboxheader">
                        Added since:
                      </th>
                      <th class="searchboxheader">
                        until:
                      </th>                      
                    </tr>
                   </thead>
                   <tbody>
                    <tr valign="bottom">
                      <td class="searchboxbody">%s</td>
                      <td class="searchboxbody">%s</td>
                    </tr>
                   </tbody>
                  </table>""" % \
           (cell_6_a, cell_6_b)        
    ## fifthly, print Display/Sort box:
    if action != msg_browse[ln]:
        cell_1_left = """
        <select name="sf">
        <option value="">- %s -""" % msg_latest_first[ln]
        query = """SELECT DISTINCT(f.code),f.name FROM field AS f, collection_field_fieldvalue AS cff
                    WHERE cff.type='soo' AND cff.id_field=f.id
                    ORDER BY cff.score DESC, f.name ASC""" 
        res = run_sql(query)
        for code, name in res:
            # propose found sort options:
            cell_1_left += """<option value="%s"%s>%s""" % (code, is_selected(sf,code), name)
        cell_1_left += """</select>"""
        cell_1_left += """<select name="so">
                          <option value="a"%s>%s
                          <option value="d"%s>%s
                          </select>""" % (is_selected(so,"a"), msg_ascending[ln], is_selected(so,"d"), msg_descending[ln])
        cell_1_right = """
        <select name="of">"""
        query = """SELECT code,name FROM format ORDER BY name ASC""" 
        res = run_sql(query)
        if res:
            # propose found formats:
            for code, name in res:
                cell_1_right += """<option value="%s"%s>%s""" % (code, is_selected(of,code), name)
        else:
            # no formats are found, so propose the default HTML one:
            cell_1_right += """<option value="hb"%s>HTML %s""" % (is_selected(of,"hb"), msg_brief[ln])
        # is format made of numbers only? if yes, then propose it too:
        if of and str(of[0:3]).isdigit():
            cell_1_right += """<option value="%s" selected>%s MARC tag""" % (of, of)
        cell_1_right += """</select>"""
        ## okay, formats ended
        cell_1_middle = """
        <select name="rg">
        <option value="10"%s>10 %s
        <option value="25"%s>25 %s
        <option value="50"%s>50 %s
        <option value="100"%s>100 %s
        <option value="250"%s>250 %s
        <option value="500"%s>500 %s
        </select>
        <select name="sc">
        <option value="0"%s>%s
        <option value="1"%s>%s
        </select>
        """ % (is_selected(rg,"10"), msg_results[ln], is_selected(rg,"25"), msg_results[ln], is_selected(rg,"50"), msg_results[ln], \
               is_selected(rg,"100"), msg_results[ln], is_selected(rg,"250"), msg_results[ln], is_selected(rg,"500"), msg_results[ln], \
               is_selected(sc,"0"), msg_single_list[ln], is_selected(sc,"1"), msg_split_by_collection[ln])
        out += """
            <table class="searchbox">
             <thead>
              <tr>
               <th class="searchboxheader">
                %s
               </th>
               <th class="searchboxheader">
                %s
               </th>
               <th class="searchboxheader">
                %s
               </th>
              </tr> 
             </thead>
             <tbody>
              <tr valign="bottom">
               <td valign="top" class="searchboxbody">%s</td>
               <td valign="top" class="searchboxbody">%s</td>
               <td valign="top" class="searchboxbody">%s</td>
              </tr>
             </tbody>
            </table>""" % (msg_sort_by[ln], msg_display_results[ln], msg_output_format[ln], cell_1_left, cell_1_middle, cell_1_right)
    ## last but not least, print end of search box:
    out += """</form>"""
    ## now return the search box nicely framed with the google_box:
    return """<table width="100%%" cellspacing="0" cellpadding="0" border="0">
                <tr valign="top">
                 <td>
                   %s
                 </td>
                 <td class="pagestriperight">
                  %s
                 </td>
                </tr>
               </table>""" % (out, create_google_box(p, f, p1, p2, p3, ln))

def create_navtrail_links(cc=cdsname,
                          as=0,
                          ln=cdslang,
                          self_p=1,
                          separator=" &gt; "):
    """Creates navigation trail links, i.e. links to collection ancestors (except Home collection).
    If as==1, then links to Advanced Search interfaces; otherwise Simple Search.        
    """
    out = ""
    for dad in get_coll_ancestors(cc):
        if dad != cdsname: # exclude Home collection
            if out:
                out += separator
            out += """<a class="navtrail" href="%s/?c=%s&amp;as=%d&amp;ln=%s">%s</a>""" % \
                   (weburl, urllib.quote_plus(dad), as, ln, dad)
    if self_p and cc != cdsname:
        if out:
            out += separator
        out += """<a class="navtrail" href="%s/?c=%s&amp;as=%d&amp;ln=%s">%s</a>""" % \
               (weburl, urllib.quote_plus(cc), as, ln, cc)        
    return out

def create_searchwithin_selection_box(fieldname='f', value='', ln='en'):
    "Produces 'search within' selection box for the current collection."
    out = ""
    out += """<select name="%s">""" % fieldname
    out += """<option value="">%s""" % msg_any_field[ln]
    query = "SELECT code,name FROM field ORDER BY name ASC"
    res = run_sql(query)
    for field_code, field_name in res:
        if field_code and field_code != "anyfield":
            out += """<option value="%s"%s>%s""" % (field_code, is_selected(field_code,value), field_name)
    if value and str(value[0]).isdigit():
        out += """<option value="%s" selected>%s MARC tag""" % (value, value)
    out += """</select>""" 
    return out

def create_andornot_box(name='op', value='', ln='en'):
    "Returns HTML code for the AND/OR/NOT selection box."
    out = """
    <select name="%s">
    <option value="a"%s>%s
    <option value="o"%s>%s
    <option value="n"%s>%s
    </select>
    """ % (name,
           is_selected('a', value), msg_and[ln],
           is_selected('o', value), msg_or[ln],
           is_selected('n', value), msg_and_not[ln])
    return out

def create_matchtype_box(name='m', value='', ln='en'):
    "Returns HTML code for the 'match type' selection box."
    out = """
    <select name="%s">
    <option value="a"%s>%s
    <option value="o"%s>%s
    <option value="e"%s>%s
    <option value="p"%s>%s
    <option value="r"%s>%s
    </select>
    """ % (name,
           is_selected('a', value), msg_all_of_the_words[ln],
           is_selected('o', value), msg_any_of_the_words[ln],
           is_selected('e', value), msg_exact_phrase[ln],
           is_selected('p', value), msg_partial_phrase[ln],
           is_selected('r', value), msg_regular_expression[ln])
    return out

def nice_number(num):
    "Returns nice number when using comma as thousands separator."
    chars_in = list(str(num))
    num = len(chars_in)
    chars_out = []
    for i in range(0,num):
        if i % 3 == 0 and i != 0:
            chars_out.append(',')
        chars_out.append(chars_in[num-i-1])
    chars_out.reverse()
    return ''.join(chars_out)

def is_selected(var, fld):
    "Checks if the two are equal, and if yes, returns ' selected'.  Useful for select boxes."
    if type(var) is int and type(fld) is int:
        if var == fld:
            return " selected"
    elif str(var) == str(fld):
        return " selected"
    elif fld and len(fld)==3 and fld[0] == "w" and var == fld[1:]:
        return " selected"
    return ""

def urlargs_replace_text_in_arg(urlargs, regexp_argname, text_old, text_new):
    """Analyze `urlargs' (URL CGI GET query arguments) and for each
       occurrence of argument matching `regexp_argname' replace every
       substring `text_old' by `text_new'.  Return the resulting URL.
       Useful for create_nearest_terms_box."""
    out = ""
    # parse URL arguments into a dictionary:
    urlargsdict = cgi.parse_qs(urlargs)
    ## construct new URL arguments:
    urlargsdictnew = {}
    for key in urlargsdict.keys():
        if sre.match(regexp_argname, key): # replace `arg' by new values
            urlargsdictnew[key] = []
            for parg in urlargsdict[key]:
                urlargsdictnew[key].append(string.replace(parg, text_old, text_new))
        else: # keep old values
            urlargsdictnew[key] = urlargsdict[key]
    # build new URL for this word:
    for key in urlargsdictnew.keys():
        for val in urlargsdictnew[key]:
            out += "&" + key + "=" + urllib.quote_plus(val, '')
    if out.startswith("&"):
        out = out[1:]
    return out

class HitSet:
    """Class describing set of records, implemented as bit vectors of recIDs.
    Using Numeric arrays for speed (1 value = 8 bits), can use later "real"
    bit vectors to save space."""

    def __init__(self, init_set=None):
        self._nbhits = -1
        if init_set:
            self._set = init_set
        else:
            self._set = Numeric.zeros(cfg_max_recID+1, Numeric.Int0)

    def __repr__(self, join=string.join):
        return "%s(%s)" % (self.__class__.__name__, join(map(repr, self._set), ', '))

    def add(self, recID):
        "Adds a record to the set."
        self._set[recID] = 1

    def addmany(self, recIDs):
        "Adds several recIDs to the set."
        for recID in recIDs: self._set[recID] = 1

    def addlist(self, arr):
        "Adds an array of recIDs to the set."
        Numeric.put(self._set, arr, 1)

    def remove(self, recID):
        "Removes a record from the set."
        self._set[recID] = 0

    def removemany(self, recIDs):
        "Removes several records from the set."
        for recID in recIDs:
            self.remove(recID)

    def intersect(self, other):
        "Does a set intersection with other.  Keep result in self."
        self._set = Numeric.bitwise_and(self._set, other._set)

    def union(self, other):
        "Does a set union with other. Keep result in self."
        self._set = Numeric.bitwise_or(self._set, other._set)

    def difference(self, other):
        "Does a set difference with other. Keep result in self."
        #self._set = Numeric.bitwise_not(self._set, other._set)
        for recID in Numeric.nonzero(other._set):
            self.remove(recID)

    def contains(self, recID):
        "Checks whether the set contains recID."
        return self._set[recID]

    __contains__ = contains     # Higher performance member-test for python 2.0 and above

    def __getitem__(self, index):
        "Support for the 'for item in set:' protocol."
        return Numeric.nonzero(self._set)[index]
        
    def calculate_nbhits(self):
        "Calculates the number of records set in the hitset."
        self._nbhits = Numeric.sum(self._set.copy().astype(Numeric.Int))

    def items(self):
        "Return an array containing all recID."
        return Numeric.nonzero(self._set)

    def tolist(self):
        "Return an array containing all recID."
        return Numeric.nonzero(self._set).tolist()

# speed up HitSet operations by ~20% if Psyco is installed:
try:
    import psyco
    psyco.bind(HitSet)
except:
    pass

def escape_string(s):
    "Escapes special chars in string.  For MySQL queries."
    s = MySQLdb.escape_string(s)
    return s

def wash_colls(cc, c, split_colls=0):

    """Wash collection list by checking whether user has deselected
    anything under 'Narrow search'.  Checks also if cc is a list or not.
       Return list of cc, colls_to_display, colls_to_search since the list
    of collections to display is different from that to search in.
    This is because users might have chosen 'split by collection'
    functionality.
       The behaviour of "collections to display" depends solely whether

    user has deselected a particular collection: e.g. if it started
    from 'Articles and Preprints' page, and deselected 'Preprints',
    then collection to display is 'Articles'.  If he did not deselect
    anything, then collection to display is 'Articles & Preprints'.
       The behaviour of "collections to search in" depends on the
    'split_colls' parameter:
         * if is equal to 1, then we can wash the colls list down
           and search solely in the collection the user started from;
         * if is equal to 0, then we are splitting to the first level
           of collections, i.e. collections as they appear on the page
           we started to search from;
    """
       
    colls_out = []
    colls_out_for_display = []

    # check what type is 'cc':
    if type(cc) is list:
        for ci in cc:
            if collection_reclist_cache.has_key(ci):
                # yes this collection is real, so use it:
                cc = ci
                break
    else:
        # check once if cc is real:
        if not collection_reclist_cache.has_key(cc):
            cc = cdsname # cc is not real, so replace it with Home collection

    # check type of 'c' argument:
    if type(c) is list:
        colls = c
    else:
        colls = [c]

    # remove all 'unreal' collections:
    colls_real = []
    for coll in colls:
        if collection_reclist_cache.has_key(coll):
            colls_real.append(coll)
    colls = colls_real

    # check if some real collections remain:
    if len(colls)==0:
        colls = [cc]

    # then let us check the list of non-restricted "real" sons of 'cc' and compare it to 'coll':
    query = "SELECT c.name FROM collection AS c, collection_collection AS cc, collection AS ccc WHERE c.id=cc.id_son AND cc.id_dad=ccc.id AND ccc.name='%s' AND cc.type='r' AND c.restricted IS NULL" % MySQLdb.escape_string(cc)
    res = run_sql(query)
    l_cc_nonrestricted_sons = []
    l_c = colls
    for row in res:
        l_cc_nonrestricted_sons.append(row[0]) 
    l_c.sort()
    l_cc_nonrestricted_sons.sort()
    if l_cc_nonrestricted_sons == l_c:
        colls_out_for_display = [cc] # yep, washing permitted, it is sufficient to display 'cc'
    else:
        colls_out_for_display = colls # nope, we need to display all 'colls' successively

    # remove duplicates:
    colls_out_for_display_nondups=filter(lambda x, colls_out_for_display=colls_out_for_display: colls_out_for_display[x-1] not in colls_out_for_display[x:], range(1, len(colls_out_for_display)+1))
    colls_out_for_display = map(lambda x, colls_out_for_display=colls_out_for_display:colls_out_for_display[x-1], colls_out_for_display_nondups)
        
    # second, let us decide on collection splitting:
    if split_colls == 0:
        # type A - no sons are wanted
        colls_out = colls_out_for_display
#    elif split_colls == 1:
    else:
        # type B - sons (first-level descendants) are wanted
        for coll in colls_out_for_display:
            coll_sons = get_coll_sons(coll)
            if coll_sons == []:
                colls_out.append(coll)
            else:
                colls_out = colls_out + coll_sons

    # remove duplicates:
    colls_out_nondups=filter(lambda x, colls_out=colls_out: colls_out[x-1] not in colls_out[x:], range(1, len(colls_out)+1))
    colls_out = map(lambda x, colls_out=colls_out:colls_out[x-1], colls_out_nondups)

    return (cc, colls_out_for_display, colls_out)

def strip_accents(x):
    """Strip accents in the input phrase X (assumed in UTF-8) by replacing
    accented characters with their unaccented cousins (e.g. é by e).
    Return such a stripped X."""
    # convert input into Unicode string:
    try:
        y = unicode(x, "utf-8")
    except:
        return x # something went wrong, probably the input wasn't UTF-8
    # asciify Latin-1 lowercase:
    y = sre.sub(unicode(r"(?u)[áàäâãå]", "utf-8"), "a", y)
    y = sre.sub(unicode(r"(?u)[æ]", "utf-8"), "ae", y)
    y = sre.sub(unicode(r"(?u)[éèëê]", "utf-8"), "e", y)
    y = sre.sub(unicode(r"(?u)[íìïî]", "utf-8"), "i", y)
    y = sre.sub(unicode(r"(?u)[óòöôõø]", "utf-8"), "o", y)
    y = sre.sub(unicode(r"(?u)[úùüû]", "utf-8"), "u", y)
    y = sre.sub(unicode(r"(?u)[ýÿ]", "utf-8"), "y", y)
    y = sre.sub(unicode(r"(?u)[ç]", "utf-8"), "c", y)
    y = sre.sub(unicode(r"(?u)[ñ]", "utf-8"), "n", y)
    # asciify Latin-1 uppercase:
    y = sre.sub(unicode(r"(?u)[ÁÀÄÂÃÅ]", "utf-8"), "A", y)
    y = sre.sub(unicode(r"(?u)[Æ]", "utf-8"), "AE", y)
    y = sre.sub(unicode(r"(?u)[ÉÈËÊ]", "utf-8"), "E", y)
    y = sre.sub(unicode(r"(?u)[ÍÌÏÎ]", "utf-8"), "I", y)
    y = sre.sub(unicode(r"(?u)[ÓÒÖÔÕØ]", "utf-8"), "O", y)
    y = sre.sub(unicode(r"(?u)[ÚÙÜÛ]", "utf-8"), "U", y)
    y = sre.sub(unicode(r"(?u)[Ý]", "utf-8"), "Y", y)
    y = sre.sub(unicode(r"(?u)[Ç]", "utf-8"), "C", y)
    y = sre.sub(unicode(r"(?u)[Ñ]", "utf-8"), "N", y)
    # return UTF-8 representation of the Unicode string:
    return y.encode("utf-8")
 
def wash_pattern(p):
    """Wash pattern passed by URL. Check for sanity of the wildcard by
    removing wildcards if they are appended to extremely short words
    (1-3 letters).  TODO: instead of this approximative treatment, it
    will be much better to introduce a temporal limit, e.g. to kill a
    query if it does not finish in 10 seconds."""
    # strip accents:
    p = strip_accents(p)
    # add leading/trailing whitespace for the two following wildcard-sanity checking regexps:
    p = " " + p + " " 
    # get rid of wildcards at the beginning of words:
    p = sre.sub(r'(\s)[\*\%]+', "\\1", p)
    # replace spaces within quotes by __SPACE__ temporarily:
    p = sre.sub("'(.*?)'", lambda x: "'"+string.replace(x.group(1), ' ', '__SPACE__')+"'", p) 
    p = sre.sub("\"(.*?)\"", lambda x: "\""+string.replace(x.group(1), ' ', '__SPACEBIS__')+"\"", p) 
    # get rid of extremely short words (1-3 letters with wildcards): 
    p = sre.sub(r'([\s\"]\w{1,3})[\*\%]+', "\\1", p)
    # replace back __SPACE__ by spaces:
    p = sre.sub("__SPACE__", " ", p)
    p = sre.sub("__SPACEBIS__", " ", p)
    # remove unnecessary whitespace:
    p = string.strip(p)
    return p
    
def wash_field(f):
    """Wash field passed by URL."""
    # get rid of unnecessary whitespace:
    f = string.strip(f)
    # wash old-style CDSware/ALEPH 'f' field argument, e.g. replaces 'wau' and 'au' by 'author'
    if cfg_fields_convert.has_key(string.lower(f)):
        f = cfg_fields_convert[f]
    return f

def wash_dates(d1y, d1m, d1d, d2y, d2m, d2d):
    """Take user-submitted dates (day, month, year) of the web form and return (day1, day2) in YYYY-MM-DD format
    suitable for time restricted searching.  I.e. pay attention when months are not there to put 01 or 12
    according to if it's the starting or the ending date, etc."""    
    day1, day2 =  "", ""
    # sanity checking:
    if d1y==0 and d1m==0 and d1d==0 and d2y==0 and d2m==0 and d2d==0:
        return ("", "") # nothing selected, so return empty values
    # construct day1 (from):
    if d1y:
        day1 += "%04d" % d1y
    else:
        day1 += "0000"
    if d1m:
        day1 += "-%02d" % d1m
    else:
        day1 += "-01"
    if d1d:
        day1 += "-%02d" % d1d
    else:
        day1 += "-01"
    # construct day2 (until):
    if d2y:
        day2 += "%04d" % d2y
    else:
        day2 += "9999"
    if d2m:
        day2 += "-%02d" % d2m
    else:
        day2 += "-12"
    if d2d:
        day2 += "-%02d" % d2d
    else:
        day2 += "-31" # NOTE: perhaps we should add max(datenumber) in
                      # given month, but for our quering it's not
                      # needed, 31 will always do
    # okay, return constructed YYYY-MM-DD dates
    return (day1, day2)
    
def get_coll_ancestors(coll):
    "Returns a list of ancestors for collection 'coll'."
    coll_ancestors = [] 
    coll_ancestor = coll
    while 1:
        query = "SELECT c.name FROM collection AS c "\
                "LEFT JOIN collection_collection AS cc ON c.id=cc.id_dad "\
                "LEFT JOIN collection AS ccc ON ccc.id=cc.id_son "\
                "WHERE ccc.name='%s' ORDER BY cc.id_dad ASC LIMIT 1" \
                % escape_string(coll_ancestor)
        res = run_sql(query, None, 1)        
        if res:
            coll_name = res[0][0]
            coll_ancestors.append(coll_name)
            coll_ancestor = coll_name
        else:
            break
    # ancestors found, return reversed list:
    coll_ancestors.reverse()
    return coll_ancestors

def get_coll_sons(coll, type='r', public_only=1):
    """Return a list of sons (first-level descendants) of type 'type' for collection 'coll'.
       If public_only, then return only non-restricted son collections.
    """
    coll_sons = [] 
    query = "SELECT c.name FROM collection AS c "\
            "LEFT JOIN collection_collection AS cc ON c.id=cc.id_son "\
            "LEFT JOIN collection AS ccc ON ccc.id=cc.id_dad "\
            "WHERE cc.type='%s' AND ccc.name='%s'" \
            % (escape_string(type), escape_string(coll))
    if public_only:
        query += " AND c.restricted IS NULL "
    query += " ORDER BY cc.score DESC" 
    res = run_sql(query)
    for name in res:
        coll_sons.append(name[0])
    return coll_sons

def get_coll_real_descendants(coll):
    """Return a list of all descendants of collection 'coll' that are defined by a 'dbquery'.
       IOW, we need to decompose compound collections like "A & B" into "A" and "B" provided
       that "A & B" has no associated database query defined.
    """
    coll_sons = [] 
    query = "SELECT c.name,c.dbquery FROM collection AS c "\
            "LEFT JOIN collection_collection AS cc ON c.id=cc.id_son "\
            "LEFT JOIN collection AS ccc ON ccc.id=cc.id_dad "\
            "WHERE ccc.name='%s' ORDER BY cc.score DESC" \
            % escape_string(coll)
    res = run_sql(query)
    for name, dbquery in res:
        if dbquery: # this is 'real' collection, so return it:
            coll_sons.append(name)
        else: # this is 'composed' collection, so recurse:
            coll_sons.extend(get_coll_real_descendants(name))
    return coll_sons

def get_collection_reclist(coll):
    """Return hitset of recIDs that belong to the collection 'coll'."""
    global collection_reclist_cache
    if not collection_reclist_cache[coll]:
        set = HitSet()
        query = "SELECT nbrecs,reclist FROM collection WHERE name='%s'" % coll
        # launch the query:
        res = run_sql(query, None, 1)
        # fill the result set:
        if res:
            try:
                set._nbhits, set._set = res[0][0], Numeric.loads(zlib.decompress(res[0][1]))
            except:
                set._nbhits = 0
        collection_reclist_cache[coll] = set
    return collection_reclist_cache[coll]

def coll_restricted_p(coll):
    "Predicate to test if the collection coll is restricted or not."
    if not coll:
        return 0
    query = "SELECT restricted FROM collection WHERE name='%s'" % MySQLdb.escape_string(coll)
    res = run_sql(query, None, 1)
    if res and res[0][0] != None:       
        return 1
    else:
        return 0

def coll_restricted_group(coll):
    "Return Apache group to which the collection is restricted.  Return None if it's public."
    if not coll:
        return None
    query = "SELECT restricted FROM collection WHERE name='%s'" % MySQLdb.escape_string(coll)
    res = run_sql(query, None, 1)
    if res:
        return res[0][0]
    else:
        return None
    
def create_collection_reclist_cache():
    """Creates list of records belonging to collections.  Called on startup
    and used later for intersecting search results with collection universe."""
    collrecs = {}
    res = run_sql("SELECT name,reclist FROM collection")
    for name,reclist in res:
        collrecs[name] = None # this will be filled later during runtime by calling get_collection_reclist(coll)
    return collrecs

try:
    collection_reclist_cache.has_key(cdsname)
except:
    try:
        collection_reclist_cache = create_collection_reclist_cache()
    except:
        collection_reclist_cache = {}

def browse_pattern(req, colls, p, f, rg, ln=cdslang):
    """Browse either biliographic phrases or words indexes, and display it."""
    ## do we search in words indexes?
    if not f:
        return browse_in_bibwords(req, p, f)
    ## prepare collection urlargument for later printing:
    p_orig = p
    urlarg_colls = ""
    for coll in colls:
        urlarg_colls += "&c=%s" % urllib.quote(coll)
    ## okay, "real browse" follows:
    browsed_phrases = get_nearest_terms_in_bibxxx(p, f, rg, 1)
    while not browsed_phrases:
        # try again and again with shorter and shorter pattern:
        try:
            p = p[:-1]
            browsed_phrases = get_nearest_terms_in_bibxxx(p, f, rg, 1)
        except:
            # probably there are no hits at all:
            req.write("<p>No values found.")
            return

    ## try to check hits in these particular collection selection:
    browsed_phrases_in_colls = []
    if 0:
        for phrase in browsed_phrases:
            phrase_hitset = HitSet()
            phrase_hitsets = search_pattern("", phrase, f, 'e')
            for coll in colls:
                phrase_hitset.union(phrase_hitsets[coll])
            phrase_hitset.calculate_nbhits()
            if phrase_hitset._nbhits > 0:
                # okay, this phrase has some hits in colls, so add it:
                browsed_phrases_in_colls.append([phrase, phrase_hitset._nbhits])

    ## were there hits in collections?
    if browsed_phrases_in_colls == []:
        if browsed_phrases != []:
            #print_warning(req, """<p>No match close to <em>%s</em> found in given collections.
            #Please try different term.<p>Displaying matches in any collection...""" % p_orig)
            ## try to get nbhits for these phrases in any collection:
            for phrase in browsed_phrases:
                browsed_phrases_in_colls.append([phrase, get_nbhits_in_bibxxx(phrase, f)])

    ## display results now:
    out = """<table class="searchresultsbox">
              <thead>
               <tr>
                <th class="searchresultsboxheader" align="left">
                  hits
                </th>
                <th class="searchresultsboxheader" width="15">
                  &nbsp;
                </th>
                <th class="searchresultsboxheader" align="left">
                  %s
                </th>
               </tr>
              </thead>
              <tbody>""" % f
    if len(browsed_phrases_in_colls) == 1:
        # one hit only found:
        phrase, nbhits = browsed_phrases_in_colls[0][0], browsed_phrases_in_colls[0][1]
        out += """<tr>
                   <td class="searchresultsboxbody" align="right">
                    %s
                   </td>
                   <td class="searchresultsboxbody" width="15">
                    &nbsp;
                   </td>
                   <td class="searchresultsboxbody" align="left">
                    <a href="%s/search.py?p=%%22%s%%22&f=%s%s">%s</a>
                   </td>
                  </tr>""" % (nbhits, weburl, urllib.quote(phrase), urllib.quote(f), urlarg_colls, phrase)        
    elif len(browsed_phrases_in_colls) > 1:
        # first display what was found but the last one:
        for phrase, nbhits in browsed_phrases_in_colls[:-1]:
            out += """<tr>
                       <td class="searchresultsboxbody" align="right">
                        %s
                       </td>
                       <td class="searchresultsboxbody" width="15">
                        &nbsp;
                       </td>
                       <td class="searchresultsboxbody" align="left">
                        <a href="%s/search.py?p=%%22%s%%22&f=%s%s">%s</a>
                       </td>
                      </tr>""" % (nbhits, weburl, urllib.quote(phrase), urllib.quote(f), urlarg_colls, phrase)
        # now display last hit as "next term":
        phrase, nbhits = browsed_phrases_in_colls[-1]        
        out += """<tr><td colspan="2" class="normal">
                                   &nbsp;
                                 </td>
                                 <td class="normal">
                                   <img src="%s/img/sn.gif" alt="" border="0">
                                   <a href="%s/search.py?action=%s&p=%s&f=%s%s">next</a>
                                 </td>
                             </tr>""" % (weburl, weburl, msg_browse[ln], urllib.quote(phrase), urllib.quote(f), urlarg_colls)        
    out += """</tbody>
        </table>"""        
    req.write(out)
    return 

def browse_in_bibwords(req, p, f, ln=cdslang):
    """Browse inside words indexes."""
    if not p:
        return
    req.write("<p>Words nearest to <em>%s</em> " % p)
    if f:
        req.write(" inside <em>%s</em> " % f)
    req.write(" in any collection are:<br>")
    urlargs = string.replace(req.args, "action=%s","action=%s" % (msg_search[ln], msg_browse[ln]))
    req.write(create_nearest_terms_box(urlargs, p, f, 'w')) 
    return

def search_pattern(req=None, p=None, f=None, m=None, ap=0, of="id", verbose=0):
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
    
    hitset_empty = HitSet()
    hitset_empty._nbhits = 0
    # sanity check:
    if not p:
        hitset_full = HitSet(Numeric.ones(cfg_max_recID+1, Numeric.Int0))
        hitset_full._nbhits = cfg_max_recID
        # no pattern, so return all universe
        return hitset_full
    # search stage 1: break up arguments into basic search units:
    if verbose:
        t1 = os.times()[4]
    basic_search_units = create_basic_search_units(req, p, f, m)
    if verbose:
        t2 = os.times()[4]
        print_warning(req, "Search stage 1: basic search units are: %s" % basic_search_units)
        print_warning(req, "Search stage 1: execution took %.2f seconds." % (t2 - t1))
    # search stage 2: do search for each search unit and verify hit presence:
    if verbose:
        t1 = os.times()[4]
    basic_search_units_hitsets = []
    for idx_unit in range(0,len(basic_search_units)):
        bsu_o, bsu_p, bsu_f, bsu_m = basic_search_units[idx_unit]
        basic_search_unit_hitset = search_unit(bsu_p, bsu_f, bsu_m)
        if verbose >= 9:
            print_warning(req, "Search stage 1: pattern %s gave hitlist %s" % (bsu_p, Numeric.nonzero(basic_search_unit_hitset._set)))
        if ap==0 or basic_search_unit_hitset._nbhits > 0:
            # stage 2-1: this basic search unit is retained
            basic_search_units_hitsets.append(basic_search_unit_hitset)                    
        else:
            # stage 2-2: no hits found for this search unit, try to replace non-alphanumeric chars inside pattern:
            if sre.search(r'\w[^a-zA-Z0-9\s\:]+(\w|$)', bsu_p):
                if bsu_p.startswith('"') and bsu_p.endswith('"'): # is it ACC query?
                    bsu_pn = sre.sub(r'(\w)[^a-zA-Z0-9\s\:]+(\w|$)', "\\1*\\2", bsu_p)
                else: # it is WRD query
                    bsu_pn = sre.sub(r'(\w)[^a-zA-Z0-9\s\:]+(\w|$)', "\\1 \\2", bsu_p)
                if verbose and of.startswith('h') and req:
                    print_warning(req, "trying %s/%s/%s" % (bsu_pn,bsu_f,bsu_m))
                basic_search_unit_hitset = search_pattern(req=None, p=bsu_pn, f=bsu_f, m=bsu_m, of="id")
                if basic_search_unit_hitset._nbhits > 0:
                    # we retain the new unit instead
                    if of.startswith('h'):
                        print_warning(req, "No exact match found for <em>%s</em>, using <em>%s</em> instead..." % (bsu_p,bsu_pn))
                    basic_search_units[idx_unit][1] = bsu_pn
                    basic_search_units_hitsets.append(basic_search_unit_hitset)
                else:
                    # stage 2-3: no hits found either, propose nearest indexed terms:
                    if of.startswith('h'):
                        if req:
                            print_warning(req, create_nearest_terms_box(req.args, bsu_p, bsu_f, bsu_m))
                    return hitset_empty
            else:        
                # stage 2-3: no hits found either, propose nearest indexed terms:
                if of.startswith('h'):
                    if req:
                        print_warning(req, create_nearest_terms_box(req.args, bsu_p, bsu_f, bsu_m))
                return hitset_empty
    if verbose:
        t2 = os.times()[4]
        for idx_unit in range(0,len(basic_search_units)):
            print_warning(req, "Search stage 2: basic search unit %s gave %d hits." %
                          (basic_search_units[idx_unit][1:], basic_search_units_hitsets[idx_unit]._nbhits))
        print_warning(req, "Search stage 2: execution took %.2f seconds." % (t2 - t1))
    # search stage 3: apply boolean query for each search unit:
    if verbose:
        t1 = os.times()[4]
    hitset_in_any_collection = HitSet()
    for idx_unit in range(0,len(basic_search_units)):
        this_unit_operation = basic_search_units[idx_unit][0]
        this_unit_hitset = basic_search_units_hitsets[idx_unit]
        if this_unit_operation == '+':
            hitset_in_any_collection.intersect(this_unit_hitset)
        elif this_unit_operation == '-':
            hitset_in_any_collection.difference(this_unit_hitset)
        elif this_unit_operation == '|':
            hitset_in_any_collection.union(this_unit_hitset)
        else:
            print_warning(req, "Invalid set operation %s." % this_unit_operation, "Error")
    hitset_in_any_collection.calculate_nbhits()
    if hitset_in_any_collection._nbhits == 0:
        # no hits found, propose alternative boolean query:
        if of.startswith('h'):
            text = """All search terms matched but boolean query returned no hits.  Please combine your search terms differently."""
            text += """<blockquote><table class="nearesttermsbox" cellpadding="0" cellspacing="0" border="0">"""
            for idx_unit in range(0,len(basic_search_units)):
                bsu_o, bsu_p, bsu_f, bsu_m = basic_search_units[idx_unit]
                bsu_nbhits = basic_search_units_hitsets[idx_unit]._nbhits
                url_args_new = sre.sub(r'(^|\&)p=.*?(\&|$)', r'\1p='+urllib.quote(bsu_p)+r'\2', req.args)
                url_args_new = sre.sub(r'(^|\&)f=.*?(\&|$)', r'\1f='+urllib.quote(bsu_f)+r'\2', url_args_new)
                text += """<tr><td class="nearesttermsboxbody" align="right">%s</td>
                               <td class="nearesttermsboxbody" width="15">&nbsp;</td>
                               <td class="nearesttermsboxbody" align="left">
                                <a class="nearestterms" href="%s/search.py?%s">%s</a>
                               </td>
                           </tr>""" % \
                        (bsu_nbhits, weburl, url_args_new, bsu_p)
            text += """</table></blockquote>"""
            print_warning(req, text)                
    if verbose:
        t2 = os.times()[4]
        print_warning(req, "Search stage 3: boolean query gave %d hits." % hitset_in_any_collection._nbhits)
        print_warning(req, "Search stage 3: execution took %.2f seconds." % (t2 - t1))
    return hitset_in_any_collection

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
    set.calculate_nbhits()
    return set

def search_unit_in_bibwords(word, f, decompress=zlib.decompress):
    """Searches for 'word' inside bibwordsX table for field 'f' and returns hitset of recIDs."""
    set = HitSet() # will hold output result set
    set_used = 0 # not-yet-used flag, to be able to circumvent set operations
    # deduce into which bibwordsX table we will search:
    bibwordsX = "bibwords%d" % get_wordsindex_id("anyfield")
    if f:
        wordsindex_id = get_wordsindex_id(f)
        if wordsindex_id:
            bibwordsX = "bibwords%d" % wordsindex_id

    # wash 'word' argument and construct query:
    word = string.replace(word, '*', '%') # we now use '*' as the truncation character
    words = string.split(word, "->", 1) # check for span query
    if len(words) == 2:
        word0 = re_word.sub('', words[0])
        word1 = re_word.sub('', words[1])
        query = "SELECT word,hitlist FROM %s WHERE word BETWEEN '%s' AND '%s'" % (bibwordsX, escape_string(word0[:50]), escape_string(word1[:50]))
    else:
        word = re_word.sub('', word)
        if string.find(word, '%') >= 0: # do we have wildcard in the word?
            query = "SELECT word,hitlist FROM %s WHERE word LIKE '%s'" % (bibwordsX, escape_string(word[:50]))
        else:
            query = "SELECT word,hitlist FROM %s WHERE word='%s'" % (bibwordsX, escape_string(word[:50]))
    # launch the query:
    res = run_sql(query)
    # fill the result set:
    for word,hitlist in res:
        hitset_bibwrd = HitSet(Numeric.loads(decompress(hitlist)))
        # add the results:
        if set_used:
            set.union(hitset_bibwrd)
        else:            
            set = hitset_bibwrd
            set_used = 1
    # okay, return result set:
    return set

def search_unit_in_bibxxx(p, f, type):
    """Searches for pattern 'p' inside bibxxx tables for field 'f' and returns hitset of recIDs found.
    The search type is defined by 'type' (e.g. equals to 'r' for a regexp search)."""
    p_orig = p # saving for eventual future 'no match' reporting
    # wash arguments:
    f = string.replace(f, '*', '%') # replace truncation char '*' in field definition
    if type == 'r':
        pattern = "REGEXP '%s'" % MySQLdb.escape_string(p)
    else:
        p = string.replace(p, '*', '%') # we now use '*' as the truncation character
        ps = string.split(p, "->", 1) # check for span query:
        if len(ps) == 2:
            pattern = "BETWEEN '%s' AND '%s'" % (MySQLdb.escape_string(ps[0]), MySQLdb.escape_string(ps[1]))
        else:
            if string.find(p, '%') > -1:
                pattern = "LIKE '%s'" % MySQLdb.escape_string(ps[0])
            else:
                pattern = "='%s'" % MySQLdb.escape_string(ps[0])
    # construct 'tl' which defines the tag list (MARC tags) to search in:
    tl = []
    if str(f[0]).isdigit() and str(f[1]).isdigit():
        tl.append(f) # 'f' seems to be okay as it starts by two digits
    else:
        # convert old ALEPH tag names, if appropriate: (TODO: get rid of this before entering this function)
        if cfg_fields_convert.has_key(string.lower(f)): 
            f = cfg_fields_convert[string.lower(f)]
        # deduce desired MARC tags on the basis of chosen 'f'
        tl = get_field_tags(f)
        if not tl:
            # by default we are searching in author index:
            tl = get_field_tags("author")
    # okay, start search:
    l = [] # will hold list of recID that matched
    for t in tl:
        # deduce into which bibxxx table we will search:
        digit1, digit2 = int(t[0]), int(t[1])
        bx = "bib%d%dx" % (digit1, digit2)
        bibx = "bibrec_bib%d%dx" % (digit1, digit2)
        # construct query:
        if t == "001":
            query = "SELECT id FROM bibrec WHERE id %s" % pattern
        else:
            if len(t) != 6 or t[-1:]=='%': # only the beginning of field 't' is defined, so add wildcard character:
                query = "SELECT bibx.id_bibrec FROM %s AS bx LEFT JOIN %s AS bibx ON bx.id=bibx.id_bibxxx WHERE bx.value %s AND bx.tag LIKE '%s%%'" %\
                        (bx, bibx, pattern, t)
            else:
                query = "SELECT bibx.id_bibrec FROM %s AS bx LEFT JOIN %s AS bibx ON bx.id=bibx.id_bibxxx WHERE bx.value %s AND bx.tag='%s'" %\
                        (bx, bibx, pattern, t)        
        # launch the query:
        res = run_sql(query)
        # fill the result set:
        for id_bibrec in res:
            if id_bibrec[0]:
                l.append(id_bibrec[0])
    # check no of hits found:
    nb_hits = len(l)
    # okay, return result set:
    set = HitSet()
    set.addlist(Numeric.array(l))
    return set

def search_unit_in_bibrec(day1, day2, type='creation_date'):
    """Return hitset of recIDs found that were either created or modified (see 'type' arg)
       from day1 until day2, inclusive.  Does not pay attention to pattern, collection, anything.
       Useful to intersect later on with the 'real' query."""
    set = HitSet()
    if type != "creation_date" and type != "modification_date":
        # type argument is invalid, so search for creation dates by default
        type = "creation_date"
    res = run_sql("SELECT id FROM bibrec WHERE %s>=%s AND %s<=%s" % (type, "%s", type, "%s"),
                  (day1, day2))
    l = []
    for row in res:
        l.append(row[0])        
    set.addlist(Numeric.array(l))
    return set

def intersect_results_with_collrecs(req, hitset_in_any_collection, colls, ap=0, of="hb", verbose=0):
    """Return dict of hitsets given by intersection of hitset with the collection universes."""
    # search stage 4: intersect with the collection universe:
    if verbose:
        t1 = os.times()[4]
    results = {}
    results_nbhits = 0
    for coll in colls:
        results[coll] = HitSet()
        results[coll]._set = Numeric.bitwise_and(hitset_in_any_collection._set, get_collection_reclist(coll)._set)
        results[coll].calculate_nbhits()
        results_nbhits += results[coll]._nbhits    
    if results_nbhits == 0:
        # no hits found, try to search in Home:
        results_in_Home = HitSet()
        results_in_Home._set = Numeric.bitwise_and(hitset_in_any_collection._set, get_collection_reclist(cdsname)._set)
        results_in_Home.calculate_nbhits()
        if results_in_Home._nbhits > 0:
            # some hits found in Home, so propose this search:
            if ap:
                if of.startswith("h"):
                    print_warning(req, """No exact match found in selected collection(s).  Results from the whole public database follow.""")
                results = {}
                results[cdsname] = results_in_Home
            else:
                results = {}
        else:
            # no hits found in Home, recommend different search terms:
            if of.startswith("h"):            
                print_warning(req, """No public collection matched your query.  If you were looking for a non-public document,
                                      please choose the desired restricted collection first.""")
            results = {}
    if verbose:
        t2 = os.times()[4]
        print_warning(req, "Search stage 4: intersecting with collection universe gave %d hits." % results_nbhits)
        print_warning(req, "Search stage 4: execution took %.2f seconds." % (t2 - t1))                                        
    return results

def intersect_results_with_hitset(req, results, hitset, ap=0, aptext="", of="hb"):
    """Return intersection of search 'results' (a dict of hitsets
       with collection as key) with the 'hitset', i.e. apply
       'hitset' intersection to each collection within search
       'results'.

       If the final 'results' set is to be empty, and 'ap'
       (approximate pattern) is true, and then print the `warningtext'
       and return the original 'results' set unchanged.  If 'ap' is
       false, then return empty results set.
    """
    
    if ap:
        results_ap = copy.deepcopy(results)
    else:
        results_ap = {} # will return empty dict in case of no hits found
    nb_total = 0
    for coll in results.keys():
        results[coll].intersect(hitset)
        results[coll].calculate_nbhits()
        nb_total += results[coll]._nbhits
    if nb_total == 0:
        if of.startswith("h"):
            print_warning(req, aptext)
        results = results_ap
    return results        

def create_nearest_terms_box(urlargs, p, f, t='w', n=5):
    """Return text box containing list of 'n' nearest terms above/below 'p'
       for the field 'f' for matching type 't' (words/phrases).
       Propose new searches according to `urlargs' with the new words.
    """    
    out = ""
    nearest_terms = []
    if not p: # sanity check
        p = "."
    # look for nearest terms:
    if t == 'w':
        nearest_terms = get_nearest_terms_in_bibwords(p, f, n, n)
        if not nearest_terms:
            return "%sNo words index available for %s.%s" % (prologue, f, epilogue)            
    else:
        nearest_terms = get_nearest_terms_in_bibxxx(p, f, n, n)
        if not nearest_terms:
            return "%sNo phrases available for %s.%s" % (prologue, f, epilogue)                        
    # display them:
    out += """<table class="nearesttermsbox" cellpadding="0" cellspacing="0" border="0">"""
    for term in nearest_terms:
        if t == 'w':
            term_nbhits = get_nbhits_in_bibwords(term, f)
        else:
            term_nbhits = get_nbhits_in_bibxxx(term, f)
        if term == p: # print search word for orientation:
            if term_nbhits > 0:
                out += """<tr>
                           <td class="nearesttermsboxbodyselected" align="right">%d</td>
                           <td class="nearesttermsboxbodyselected" width="15">&nbsp;</td>
                           <td class="nearesttermsboxbodyselected" align="left">
                             <a class="nearesttermsselected" href="%s/search.py?%s">%s</a>
                           </td>
                          </tr>""" % \
                           (term_nbhits, weburl, urlargs_replace_text_in_arg(urlargs, r'^p\d?$', p, term), term)
            else:
                out += """<tr>
                           <td class="nearesttermsboxbodyselected" align="right">-</td>
                           <td class="nearesttermsboxbodyselected" width="15">&nbsp;</td>
                           <td class="nearesttermsboxbodyselected" align="left">%s</td>
                          </tr>""" % term
        else:
            out += """<tr>
                       <td class="nearesttermsboxbody" align="right">%s</td>
                       <td class="nearesttermsboxbody" width="15">&nbsp;</td>
                       <td class="nearesttermsboxbody" align="left">
                         <a class="nearestterms" href="%s/search.py?%s">%s</a>
                       </td>
                      </tr>""" % \
                       (term_nbhits, weburl, urlargs_replace_text_in_arg(urlargs, r'^p\d?$', p, term), term)
    out += "</table>"
    # add leading introductory text and return:
    intro = "Search term <em>%s</em>" % p
    if f:
        intro += " inside <em>%s</em>" % f
    intro += " did not match any record.  Nearest terms in any collection are:"
    return intro + "<blockquote>" + out + "</blockquote>"

def get_nearest_terms_in_bibwords(p, f, n_below, n_above):
    """Return list of +n -n nearest terms to word `p' in wordsindex for field `f'."""
    nearest_words = [] # will hold the (sorted) list of nearest words to return
    # deduce into which bibwordsX table we will search:
    bibwordsX = "bibwords%d" % get_wordsindex_id("anyfield")
    if f:
        wordsindex_id = get_wordsindex_id(f)
        if wordsindex_id:
            bibwordsX = "bibwords%d" % wordsindex_id
        else:
            return nearest_words
    # firstly try to get `n' closest words above `p':
    query = "SELECT word FROM %s WHERE word<'%s' ORDER BY word DESC LIMIT %d" % (bibwordsX, escape_string(p), n_above)
    res = run_sql(query)
    for row in res:
        nearest_words.append(row[0])
    nearest_words.reverse()
    # secondly insert given word `p':
    nearest_words.append(p)
    # finally try to get `n' closest words below `p':
    query = "SELECT word FROM %s WHERE word>'%s' ORDER BY word ASC LIMIT %d" % (bibwordsX, escape_string(p), n_below)
    res = run_sql(query)
    for row in res:
        nearest_words.append(row[0])        
    return nearest_words

def get_nearest_terms_in_bibxxx(p, f, n_below, n_above):
    """Browse (-n_above, +n_below) closest bibliographic phrases
       for the given pattern p in the given field f, regardless
       of collection.
       Return list of [phrase1, phrase2, ... , phrase_n]."""
    ## determine browse field:
    if string.find(p, ":") > 0: # does 'p' contain ':'?
        f, p = split(p, ":", 1)
    ## wash 'p' argument:
    p = re_quotes.sub("", p)
    ## construct 'tl' which defines the tag list (MARC tags) to search in:
    tl = []
    if str(f[0]).isdigit() and str(f[1]).isdigit():
        tl.append(f) # 'f' seems to be okay as it starts by two digits
    else:
        # deduce desired MARC tags on the basis of chosen 'f'
        tl = get_field_tags(f)
    ## start browsing to fetch list of hits:
    browsed_phrases_above = {} # will hold {phrase1: 1, phrase2: 1, ..., phraseN: 1} dict of browsed phrases above p (to make them unique)
    browsed_phrases_exact = {} # will hold {phrase1: 1, phrase2: 1, ..., phraseN: 1} dict of browsed phrases exactly equal to p 
    browsed_phrases_below = {} # will hold {phrase1: 1, phrase2: 1, ..., phraseN: 1} dict of browsed phrases below p (to make them unique)
    for t in tl:
        # deduce into which bibxxx table we will search:
        digit1, digit2 = int(t[0]), int(t[1])
        bx = "bib%d%dx" % (digit1, digit2)
        bibx = "bibrec_bib%d%dx" % (digit1, digit2)
        # firstly try to get `n' closest phrases above `p':
        if len(t) != 6 or t[-1:]=='%': # only the beginning of field 't' is defined, so add wildcard character:
            query = "SELECT bx.value FROM %s AS bx WHERE bx.value<'%s' AND bx.tag LIKE '%s%%' ORDER BY bx.value DESC LIMIT %d" \
                    % (bx, escape_string(p), t, n_above)
        else:
            query = "SELECT bx.value FROM %s AS bx WHERE bx.value<'%s' AND bx.tag='%s' ORDER BY bx.value DESC LIMIT %d" \
                    % (bx, escape_string(p), t, n_above)
        res = run_sql(query)
        for row in res:
            browsed_phrases_above[row[0]] = 1
        # secondly try to get phrases equal to `p':
        if len(t) != 6 or t[-1:]=='%': # only the beginning of field 't' is defined, so add wildcard character:
            query = "SELECT bx.value FROM %s AS bx WHERE bx.value='%s' AND bx.tag LIKE '%s%%' ORDER BY bx.value ASC" \
                    % (bx, escape_string(p), t)
        else:
            query = "SELECT bx.value FROM %s AS bx WHERE bx.value='%s' AND bx.tag='%s' ORDER BY bx.value ASC" \
                    % (bx, escape_string(p), t)
        res = run_sql(query)
        for row in res:
            browsed_phrases_exact[row[0]] = 1            
        # thirdly try to get `n' closest phrases below `p':
        if len(t) != 6 or t[-1:]=='%': # only the beginning of field 't' is defined, so add wildcard character:
            query = "SELECT bx.value FROM %s AS bx WHERE bx.value>'%s' AND bx.tag LIKE '%s%%' ORDER BY bx.value ASC LIMIT %d" \
                    % (bx, escape_string(p), t, n_below)
        else:
            query = "SELECT bx.value FROM %s AS bx WHERE bx.value>'%s' AND bx.tag='%s' ORDER BY bx.value ASC LIMIT %d" \
                    % (bx, escape_string(p), t, n_below)
        res = run_sql(query)
        for row in res:
            browsed_phrases_below[row[0]] = 1
    # select first n words only: (this is needed as we were searching
    # in many different tables and so aren't sure we have more than n
    # words right; this of course won't be needed when we shall have
    # one ACC table only for given field):
    l1 = browsed_phrases_above.keys()
    l1.sort()
    l1.reverse()
    l1 = l1[:n_above]
    l1.reverse()
    l2 = browsed_phrases_below.keys()
    l2.sort()
    out = []
    for phrase in l1[:n_above]:
        out.append(phrase)
    if len(browsed_phrases_exact)>0:
        for phrase in browsed_phrases_exact.keys():
            out.append(phrase)
    else:
        out.append(p) # always append self, even if no hits, to indicate our position
    for phrase in l2[:n_below]:
        out.append(phrase)
    return out

def get_nbhits_in_bibwords(word, f):
    """Return number of hits for word 'word' inside words index for field 'f'."""
    out = 0
    # deduce into which bibwordsX table we will search:
    bibwordsX = "bibwords%d" % get_wordsindex_id("anyfield")
    if f:
        wordsindex_id = get_wordsindex_id(f)
        if wordsindex_id:
            bibwordsX = "bibwords%d" % wordsindex_id
        else:
            return 0
    if word:
        query = "SELECT hitlist FROM %s WHERE word='%s'" % (bibwordsX, escape_string(word))
        res = run_sql(query)
        for hitlist in res:
            out += Numeric.sum(Numeric.loads(zlib.decompress(hitlist[0])).copy().astype(Numeric.Int))
    return out

def get_nbhits_in_bibxxx(p, f):
    """Return number of hits for word 'word' inside words index for field 'f'."""
    ## determine browse field:
    if string.find(p, ":") > 0: # does 'p' contain ':'?
        f, p = split(p, ":", 1)
    ## wash 'p' argument:
    p = re_quotes.sub("", p)
    ## construct 'tl' which defines the tag list (MARC tags) to search in:
    tl = []
    if str(f[0]).isdigit() and str(f[1]).isdigit():
        tl.append(f) # 'f' seems to be okay as it starts by two digits
    else:
        # deduce desired MARC tags on the basis of chosen 'f'
        tl = get_field_tags(f)
    # start searching:
    recIDs = {} # will hold dict of {recID1: 1, recID2: 1, ..., }  (unique recIDs, therefore)
    for t in tl:
        # deduce into which bibxxx table we will search:
        digit1, digit2 = int(t[0]), int(t[1])
        bx = "bib%d%dx" % (digit1, digit2)
        bibx = "bibrec_bib%d%dx" % (digit1, digit2)
        if len(t) != 6 or t[-1:]=='%': # only the beginning of field 't' is defined, so add wildcard character:
            query = """SELECT bibx.id_bibrec FROM %s AS bibx, %s AS bx
                        WHERE bx.value='%s' AND bx.tag LIKE '%s%%' AND bibx.id_bibxxx=bx.id""" \
                     % (bibx, bx, escape_string(p), t)
        else:
            query = """SELECT bibx.id_bibrec FROM %s AS bibx, %s AS bx
                        WHERE bx.value='%s' AND bx.tag='%s' AND bibx.id_bibxxx=bx.id""" \
                     % (bibx, bx, escape_string(p), t)
        res = run_sql(query)
        for row in res:
            recIDs[row[0]] = 1
    return len(recIDs)         

def get_mysql_recid_from_aleph_sysno(sysno):
    """Returns MySQL's recID for ALEPH sysno passed in the argument (e.g. "002379334CER").
       Returns None in case of failure."""
    out = None
    query = "SELECT bb.id_bibrec FROM bibrec_bib97x AS bb, bib97x AS b WHERE b.value='%s' AND b.tag='970__a' AND bb.id_bibxxx=b.id" %\
            (escape_string(sysno))
    res = run_sql(query, None, 1)
    if res:        
        out = res[0][0]
    return out

def guess_primary_collection_of_a_record(recID):
    """Return primary collection name a record recid belongs to, by testing 980 identifier.
       May lead to bad guesses when a collection is defined dynamically bia dbquery.
       In that case, return 'cdsname'."""
    out = cdsname
    dbcollids = get_fieldvalues(recID, "980__a")
    if dbcollids:
        dbquery = "collection:" + dbcollids[0]
        res = run_sql("SELECT name FROM collection WHERE dbquery=%s", (dbquery,))
        if res:
            out = res[0][0]
    return out
    
def get_tag_name(tag_value, prolog="", epilog=""):
    """Return tag name from the known tag value, by looking up the 'tag' table.
       Return empty string in case of failure.
       Example: input='100__%', output=first author'."""    
    out = ""
    res = run_sql("SELECT name FROM tag WHERE value=%s", (tag_value,))
    if res:
        out = prolog + res[0][0] + epilog
    return out

def get_fieldcodes():
    """Returns a list of field codes that may have been passed as 'search options' in URL.
       Example: output=['subject','division']."""
    out = []
    res = run_sql("SELECT DISTINCT(code) FROM field")
    for row in res:
        out.append(row[0])
    return out

def get_field_tags(field):
    """Returns a list of MARC tags for the field code 'field'.
       Returns empty list in case of error.
       Example: field='author', output=['100__%','700__%']."""
    out = []
    query = """SELECT t.value FROM tag AS t, field_tag AS ft, field AS f
                WHERE f.code='%s' AND ft.id_field=f.id AND t.id=ft.id_tag
                ORDER BY ft.score DESC""" % field
    res = run_sql(query)
    for val in res:
        out.append(val[0])
    return out

def get_fieldvalues(recID, tag):
    """Return list of field values for field 'tag' inside record 'recID'."""
    out = []
    if tag == "001___":
        # we have asked for recID that is not stored in bibXXx tables
        out.append(str(recID))
    else:
        # we are going to look inside bibXXx tables
        digit = tag[0:2]
        bx = "bib%sx" % digit
        bibx = "bibrec_bib%sx" % digit
        query = "SELECT bx.value FROM %s AS bx, %s AS bibx WHERE bibx.id_bibrec='%s' AND bx.id=bibx.id_bibxxx AND bx.tag LIKE '%s'" \
                "ORDER BY bibx.field_number, bx.tag ASC" % (bx, bibx, recID, tag)
        res = run_sql(query)
        for row in res:
            out.append(row[0])
    return out

def get_fieldvalues_alephseq_like(recID, tags):
    """Return textual lines in ALEPH sequential like format for field 'tag' inside record 'recID'."""
    out = ""    
    # clean passed 'tag':
    tags_in = string.split(tags, ",")
    if len(tags_in) == 1 and len(tags_in[0]) == 6:
        ## case A: one concrete subfield asked, so print its value if found
        ##         (use with care: can false you if field has multiple occurrences)
        out += string.join(get_fieldvalues(recID, tags_in[0]),"\n")
    else:
        ## case B: print our "text MARC" format; works safely all the time        
        tags_out = []
        for tag in tags_in:
            if len(tag) == 0:
                for i in range(0,10):
                    for j in range(0,10):
                        tags_out.append("%d%d%%" % (i, j))
            elif len(tag) == 1:
                for j in range(0,10):
                    tags_out.append("%s%d%%" % (tag, j))        
            elif len(tag) < 5:
                tags_out.append("%s%%" % tag)
            elif tag >= 6:
                tags_out.append(tag[0:5])
        # search all bibXXx tables as needed:
        for tag in tags_out:
            digits = tag[0:2]
            if tag.startswith("001") or tag.startswith("00%"):
                if out:
                    out += "\n"
                out += "%09d %s %d" % (recID, "001__", recID)
            bx = "bib%sx" % digits
            bibx = "bibrec_bib%sx" % digits
            query = "SELECT b.tag,b.value,bb.field_number FROM %s AS b, %s AS bb "\
                    "WHERE bb.id_bibrec='%s' AND b.id=bb.id_bibxxx AND b.tag LIKE '%s%%' "\
                    "ORDER BY bb.field_number, b.tag ASC" % (bx, bibx, recID, tag)
            res = run_sql(query)
            # go through fields:
            field_number_old = -999
            field_old = ""
            for row in res:
                field, value, field_number = row[0], row[1], row[2]
                ind1, ind2 = field[3], field[4]
                if ind1 == "_":
                    ind1 = ""
                if ind2 == "_":
                    ind2 = ""                        
                # print field tag
                if field_number != field_number_old or field[:-1] != field_old[:-1]:
                    if out:
                        out += "\n"
                    out += "%09d %s " % (recID, field[:5])
                    field_number_old = field_number
                    field_old = field
                # print subfield value
                out += "$$%s%s" % (field[-1:], value)
    return out

def record_exists(recID):
    "Returns 1 if record 'recID' exists.  Returns 0 otherwise."
    out = 0
    query = "SELECT id FROM bibrec WHERE id='%s'" % recID
    res = run_sql(query, None, 1)
    if res:        
        out = 1
    return out    

def get_creation_date(recID):
    "Returns the creation date of the record 'recID'."
    out = ""
    query = "SELECT DATE_FORMAT(creation_date,'%%Y-%%m-%%d') FROM bibrec WHERE id='%s'" % (recID)
    res = run_sql(query, None, 1)
    if res:        
        out = res[0][0]
    return out

def get_modification_date(recID):
    "Returns the date of last modification for the record 'recID'."
    out = ""
    query = "SELECT DATE_FORMAT(modification_date,'%%Y-%%m-%%d') FROM bibrec WHERE id='%s'" % (recID)
    res = run_sql(query, None, 1)
    if res:        
        out = res[0][0]
    return out

def print_warning(req, msg, type='', prologue='<br>', epilogue='<br>'):
    "Prints warning message and flushes output."
    if req:
        req.write('\n%s<span class="quicknote">' % (prologue))
        if type:
            req.write('%s: ' % type)
        req.write('%s</span>%s' % (msg, epilogue))

def print_search_info(p, f, sf, so, sp, of, ot, collection=cdsname, nb_found=-1, jrec=1, rg=10,
                      as=0, ln=cdslang, p1="", p2="", p3="", f1="", f2="", f3="", m1="", m2="", m3="", op1="", op2="",
                      d1y=0, d1m=0, d1d=0, d2y=0, d2m=0, d2d=0,
                      cpu_time=-1, middle_only=0):
    """Prints stripe with the information on 'collection' and 'nb_found' results oand CPU time.
       Also, prints navigation links (beg/next/prev/end) inside the results set.
       If middle_only is set to 1, it will only print the middle box information (beg/netx/prev/end/etc) links.
       This is suitable for displaying navigation links at the bottom of the search results page."""

    out = ""
    # left table cells: print collection name
    if not middle_only:
        out += "\n<a name=\"%s\"></a>" \
              "\n<form action=\"%s/search.py\" method=\"get\">"\
              "\n<table width=\"100%%\" class=\"searchresultsbox\"><tr><td class=\"searchresultsboxheader\" align=\"left\">" \
              "<strong><big>" \
              "<a href=\"%s/?c=%s&as=%d\">%s</a></big></strong></td>\n" % \
              (urllib.quote(collection), weburl, weburl, urllib.quote_plus(collection), as, collection)
    else:
        out += """\n<form action="%s/search.py" method="get"><div align="center">\n""" % weburl

    # sanity check:
    if jrec < 1:
        jrec = 1
    if jrec > nb_found:
        jrec = max(nb_found-rg+1, 1)        

    # middle table cell: print beg/next/prev/end arrows:
    if not middle_only:
        out += "<td class=\"searchresultsboxheader\" align=\"center\">\n"
        out += msg_x_records_found[ln] % nice_number(nb_found) + " &nbsp; "
    else:
        out += "<small>"
        if nb_found > rg:
            out += collection + " : " + msg_x_records_found[ln] % nice_number(nb_found) + " &nbsp; "

    if nb_found > rg: # navig.arrows are needed, since we have many hits
        url = '%s/search.py?p=%s&amp;c=%s&amp;f=%s&amp;sf=%s&amp;so=%s&amp;sp=%s&amp;of=%s&amp;ot=%s' % (weburl, urllib.quote(p), urllib.quote(collection), f, sf, so, sp, of, ot)
        url += '&amp;as=%s&amp;ln=%s&amp;p1=%s&amp;p2=%s&amp;p3=%s&amp;f1=%s&amp;f2=%s&amp;f3=%s&amp;m1=%s&amp;m2=%s&amp;m3=%s&amp;op1=%s&amp;op2=%s' \
               % (as, ln, urllib.quote(p1), urllib.quote(p2), urllib.quote(p3), f1, f2, f3, m1, m2, m3, op1, op2)
        url += '&amp;d1y=%d&amp;d1m=%d&amp;d1d=%d&amp;d2y=%d&amp;d2m=%d&amp;d2d=%d' \
               % (d1y, d1m, d1d, d2y, d2m, d2d)
        if jrec-rg > 1:
            out += "<a class=\"img\" href=\"%s&amp;jrec=1&amp;rg=%d\"><img src=\"%s/img/sb.gif\" alt=\"begin\" border=0></a>" % (url, rg, weburl)
        if jrec > 1:
            out += "<a class=\"img\" href=\"%s&amp;jrec=%d&amp;rg=%d\"><img src=\"%s/img/sp.gif\" alt=\"previous\" border=0></a>" % (url, max(jrec-rg,1), rg, weburl)
        if jrec+rg-1 < nb_found:
            out += "%d - %d" % (jrec, jrec+rg-1)
        else:
            out += "%d - %d" % (jrec, nb_found)
        if nb_found >= jrec+rg:
            out += "<a class=\"img\" href=\"%s&amp;jrec=%d&amp;rg=%d\"><img src=\"%s/img/sn.gif\" alt=\"next\" border=0></a>" % \
                  (url, jrec+rg, rg, weburl)
        if nb_found >= jrec+rg+rg:
            out += "<a class=\"img\" href=\"%s&amp;jrec=%d&amp;rg=%d\"><img src=\"%s/img/se.gif\" alt=\"end\" border=0></a>" % \
                  (url, nb_found-rg+1, rg, weburl)
        out += "<input type=\"hidden\" name=\"p\" value=\"%s\">" % p
        out += "<input type=\"hidden\" name=\"c\" value=\"%s\">" % collection
        out += "<input type=\"hidden\" name=\"f\" value=\"%s\">" % f 
        out += "<input type=\"hidden\" name=\"sf\" value=\"%s\">" % sf
        out += "<input type=\"hidden\" name=\"so\" value=\"%s\">" % so
        out += "<input type=\"hidden\" name=\"of\" value=\"%s\">" % of
        if ot:
            out += """<input type="hidden" name="ot" value="%s">""" % ot
        if sp:
            out += """<input type="hidden" name="sp" value="%s">""" % sp 
        out += "<input type=\"hidden\" name=\"rg\" value=\"%d\">" % rg
        out += "<input type=\"hidden\" name=\"as\" value=\"%d\">" % as
        out += "<input type=\"hidden\" name=\"ln\" value=\"%s\">" % ln
        out += "<input type=\"hidden\" name=\"p1\" value=\"%s\">" % p1
        out += "<input type=\"hidden\" name=\"p2\" value=\"%s\">" % p2
        out += "<input type=\"hidden\" name=\"p3\" value=\"%s\">" % p3
        out += "<input type=\"hidden\" name=\"f1\" value=\"%s\">" % f1
        out += "<input type=\"hidden\" name=\"f2\" value=\"%s\">" % f2
        out += "<input type=\"hidden\" name=\"f3\" value=\"%s\">" % f3
        out += "<input type=\"hidden\" name=\"m1\" value=\"%s\">" % m1
        out += "<input type=\"hidden\" name=\"m2\" value=\"%s\">" % m2
        out += "<input type=\"hidden\" name=\"m3\" value=\"%s\">" % m3
        out += "<input type=\"hidden\" name=\"op1\" value=\"%s\">" % op1
        out += "<input type=\"hidden\" name=\"op2\" value=\"%s\">" % op2
        out += "<input type=\"hidden\" name=\"d1y\" value=\"%d\">" % d1y
        out += "<input type=\"hidden\" name=\"d1m\" value=\"%d\">" % d1m
        out += "<input type=\"hidden\" name=\"d1d\" value=\"%d\">" % d1d
        out += "<input type=\"hidden\" name=\"d2y\" value=\"%d\">" % d2y
        out += "<input type=\"hidden\" name=\"d2m\" value=\"%d\">" % d2m
        out += "<input type=\"hidden\" name=\"d2d\" value=\"%d\">" % d2d
        out += "&nbsp; %s <input type=\"text\" name=\"jrec\" size=\"4\" value=\"%d\">" % (msg_jump_to_record[ln], jrec)
    if not middle_only:
        out += "</td>"
    else:
        out += "</small>"
        
    # right table cell: cpu time info
    if not middle_only:
        if cpu_time > -1:            
            out +="<td class=\"searchresultsboxheader\" align=\"right\"><small>%s</small>&nbsp;</td>" % (msg_search_took_x_seconds[ln] % cpu_time)
        out += "</tr></table>"
    else:
        out += "</div>"
    out += "</form>"
    return out

def print_results_overview(colls, results_final_nb_total, results_final_nb, cpu_time, ln=cdslang):
    "Prints results overview box with links to particular collections below."
    out = ""
    if len(colls) == 1:
        # if one collection only, print nothing:
        return out
    # first find total number of hits:
    out += "<p><table class=\"searchresultsbox\" width=\"100%%\">" \
           "<thead><tr><th class=\"searchresultsboxheader\">%s</th></tr></thead>" % \
             (msg_results_overview_found_x_records_in_y_seconds[ln] % (nice_number(results_final_nb_total), cpu_time))
    # then print hits per collection:
    out += "<tbody><tr><td class=\"searchresultsboxbody\">"
    for coll in colls:
        if results_final_nb.has_key(coll) and results_final_nb[coll] > 0:
            out += "<strong><a href=\"#%s\">%s</a></strong>, " \
                  "<a href=\"#%s\">%s</a><br>" \
                  % (urllib.quote(coll), coll, urllib.quote(coll), msg_x_records_found[ln] % nice_number(results_final_nb[coll]))
    out += "</td></tr></tbody></table>\n"
    return out

def sort_records(req, recIDs, sort_field='', sort_order='d', sort_pattern=''):
    """Sort records in 'recIDs' list according sort field 'sort_field' in order 'sort_order'.
       If more than one instance of 'sort_field' is found for a given record, try to choose that that is given by
       'sort pattern', for example "sort by report number that starts by CERN-PS".
       Note that 'sort_field' can be field code like 'author' or MARC tag like '100__a' directly."""

    ## check arguments:
    if not sort_field:
        return recIDs
    if len(recIDs) > cfg_nb_records_to_sort:
        print_warning(req, "Sorry, sorting is allowed on sets of up to %d records only.  Using default sort order (\"latest first\")." % cfg_nb_records_to_sort,"Warning")
        return recIDs

    recIDs_dict = {}
    recIDs_out = []

    ## first deduce sorting MARC tag out of the 'sort_field' argument:
    tags = []
    if sort_field and str(sort_field[0:2]).isdigit():
        # sort_field starts by two digits, so this is probably a MARC tag already
        tags.append(sort_field)
    else:
        # let us check the 'field' table
        query = """SELECT DISTINCT(t.value) FROM tag AS t, field_tag AS ft, field AS f
                    WHERE f.code='%s' AND ft.id_field=f.id AND t.id=ft.id_tag
                    ORDER BY ft.score DESC""" % sort_field
        res = run_sql(query)
        if res:
            for row in res:
                tags.append(row[0])
        else:
            print_warning(req, "Sorry, '%s' does not seem to be a valid sort option.  Choosing title sort instead." % sort_field, "Error")
            tags.append("245__a")
        
    ## check if we have sorting tag defined:
    if tags:
        # fetch the necessary field values:
        for recID in recIDs:
            val = "" # will hold value for recID according to which sort
            vals = [] # will hold all values found in sorting tag for recID
            for tag in tags:
                vals.extend(get_fieldvalues(recID, tag))
            if sort_pattern: 
                # try to pick that tag value that corresponds to sort pattern
                bingo = 0
                for v in vals: 
                    if v.startswith(sort_pattern): # bingo!
                        bingo = 1
                        val = v
                        break
                if not bingo: # not found, so joint them all together
                    val = string.join(vals)                    
            else:
                # no sort pattern defined, so join them all together
                val = string.join(vals)
            val = val.lower()
            if recIDs_dict.has_key(val):
                recIDs_dict[val].append(recID)
            else:
                recIDs_dict[val] = [recID]
        # sort them:
        recIDs_dict_keys = recIDs_dict.keys()
        recIDs_dict_keys.sort()
        # now that keys are sorted, create output array:
        for k in recIDs_dict_keys:
            for s in recIDs_dict[k]:
                recIDs_out.append(s)        
        # ascending or descending?
        if sort_order == 'a':
            recIDs_out.reverse()
        # okay, we are done
        return recIDs_out
    else:
        # good, no sort needed
        return recIDs
        
def print_records(req, recIDs, jrec=1, rg=10, format='hb', ot='', ln=cdslang, decompress=zlib.decompress):
    """Prints list of records 'recIDs' formatted accoding to 'format' in groups of 'rg' starting from 'jrec'.
    Assumes that the input list 'recIDs' is sorted in reverse order, so it counts records from tail to head.
    A value of 'rg=-9999' means to print all records: to be used with care.
    """

    # sanity checking:
    if req == None:
        return

    if len(recIDs):
        nb_found = len(recIDs)

        if rg == -9999: # print all records
            rg = nb_found
        else:
            rg = abs(rg)
        if jrec < 1: # sanity checks
            jrec = 1
        if jrec > nb_found:
            jrec = max(nb_found-rg+1, 1)

        # will print records from irec_max to irec_min excluded:
        irec_max = nb_found - jrec
        irec_min = nb_found - jrec - rg
        if irec_min < 0:
            irec_min = -1
        if irec_max >= nb_found:
            irec_max = nb_found - 1
        
        #req.write("%s:%d-%d" % (recIDs, irec_min, irec_max))

        if format.startswith('x'):
            # we are doing XML output:
            for irec in range(irec_max,irec_min,-1):
                req.write(print_record(recIDs[irec], format, ot, ln))

        elif format.startswith('t') or str(format[0:3]).isdigit():
            # we are doing plain text output:
            for irec in range(irec_max,irec_min,-1):
                x = print_record(recIDs[irec], format, ot, ln)
                req.write(x)
                if x:
                    req.write('\n')
        else:
            # we are doing HTML output:
            if format.startswith("hp"):
                # portfolio format:
                for irec in range(irec_max,irec_min,-1):
                    req.write(print_record(recIDs[irec], format, ot, ln))                
            elif format.startswith("hb"):
                # HTML brief format:
                req.write("""\n<form action="%s/yourbaskets.py/add" method="post">""" % weburl)
                req.write("""\n<table>""")            
                for irec in range(irec_max,irec_min,-1):
                    req.write("""\n<tr><td valign="top"><input name="recid" type="checkbox" value="%s"></td>""" % recIDs[irec])
                    req.write("""<td valign="top" align="right">%d.</td><td valign="top">""" % (jrec+irec_max-irec))
                    req.write(print_record(recIDs[irec], format, ot, ln))
                    req.write("</td></tr>")
                req.write("\n</table>")
                req.write("""<br><input class="formbutton" type="submit" name="action" value="%s">""" % msg_add_to_basket[ln])
                req.write("""\n</form>""")
            else:
                # deduce url without 'of' argument:
                url_args = sre.sub(r'(^|\&)of=.*?(\&|$)',r'\1',req.args)
                url_args = sre.sub(r'^\&+', '', url_args)
                url_args = sre.sub(r'\&+$', '', url_args)
                # print other formatting choices:
                req.write("""<p><div align="right"><small>Format: \n""")
                if format != "hm":
                    req.write('HTML | <a href="%s/search.py?%s&of=hm">HTML MARC</a> | <a href="%s/search.py?%s&of=xd">XML DC</a> | <a href="%s/search.py?%s&of=xm">XML MARC</a>' % (weburl, url_args, weburl, url_args, weburl, url_args))
                else:
                    req.write('<a href="%s/search.py?%s">HTML</a> | HTML MARC | <a href="%s/search.py?%s&of=xd">XML DC</a> | <a href="%s/search.py?%s&of=xm">XML MARC</a>' % (weburl, url_args, weburl, url_args, weburl, url_args))
                req.write("</small></div>\n")
                for irec in range(irec_max,irec_min,-1):
                    req.write(print_record(recIDs[irec], format, ot, ln))
                    req.write("""\n<form action="%s/yourbaskets.py/add" method="post">""" % weburl)
                    req.write("""<input name="recid" type="hidden" value="%s"></td>""" % recIDs[irec])
                    req.write("""<br><input class="formbutton" type="submit" name="action" value="%s">"""  % msg_add_to_basket[ln])
                    req.write("""\n</form>""")
                    req.write("<p>&nbsp;")
    else:        
        print_warning(req, 'Use different search terms.')        

def print_record(recID, format='hb', ot='', ln=cdslang, decompress=zlib.decompress):
    "Prints record 'recID' formatted accoding to 'format'."
    out = ""

    # sanity check:
    if not record_exists(recID):
        return out

    # print record opening tags, if needed:
    if format == "marcxml" or format == "oai_dc":
        out += "  <record>\n"
        out += "   <header>\n"
        for id in get_fieldvalues(recID,oaiidfield):
            out += "    <identifier>%s</identifier>\n" % id
        out += "    <datestamp>%s</datestamp>\n" % get_modification_date(recID)
        out += "   </header>\n"
        out += "   <metadata>\n"

    if format.startswith("xm") or format == "marcxml":
        # look for detailed format existence:
        query = "SELECT value FROM bibfmt WHERE id_bibrec='%s' AND format='%s'" % (recID, format)
        res = run_sql(query, None, 1)
        if res:
            # record 'recID' is formatted in 'format', so print it
            out += "%s" % decompress(res[0][0])
        else:
            # record 'recID' is not formatted in 'format' -- they are not in "bibfmt" table; so fetch all the data from "bibXXx" tables:
            if format == "marcxml":
                out += """    <record xmlns="http://www.loc.gov/MARC21/slim">\n"""
                out += "        <controlfield tag=\"001\">%d</controlfield>\n" % int(recID)
            elif format.startswith("xm"):
                out += """    <record>\n"""
                out += "        <controlfield tag=\"001\">%d</controlfield>\n" % int(recID)
            for digit1 in range(0,10):
                for digit2 in range(0,10):
                    bx = "bib%d%dx" % (digit1, digit2)
                    bibx = "bibrec_bib%d%dx" % (digit1, digit2)
                    query = "SELECT b.tag,b.value,bb.field_number FROM %s AS b, %s AS bb "\
                            "WHERE bb.id_bibrec='%s' AND b.id=bb.id_bibxxx AND b.tag LIKE '%s%%' "\
                            "ORDER BY bb.field_number, b.tag ASC" % (bx, bibx, recID, str(digit1)+str(digit2))
                    res = run_sql(query)
                    field_number_old = -999
                    field_old = ""
                    for row in res:
                        field, value, field_number = row[0], row[1], row[2]
                        ind1, ind2 = field[3], field[4]
                        if ind1 == "_":
                            ind1 = ""
                        if ind2 == "_":
                            ind2 = ""                        
                        # print field tag
                        if field_number != field_number_old or field[:-1] != field_old[:-1]:
                            if format.startswith("xm") or format == "marcxml":

                                fieldid = encode_for_xml(field[0:3])

                                if field_number_old != -999:
                                    out += """        </datafield>\n"""

                                out += """        <datafield tag="%s" ind1="%s" ind2="%s">\n""" % (encode_for_xml(field[0:3]), encode_for_xml(ind1), encode_for_xml(ind2))

                            field_number_old = field_number
                            field_old = field
                        # print subfield value
                        if format.startswith("xm") or format == "marcxml":
                            value = encode_for_xml(value)
                            out += """            <subfield code="%s">%s</subfield>\n""" % (encode_for_xml(field[-1:]), value)

                    # all fields/subfields printed in this run, so close the tag:
                    if (format.startswith("xm") or format == "marcxml") and field_number_old != -999:
                        out += """        </datafield>\n"""
            # we are at the end of printing the record:
            if format.startswith("xm") or format == "marcxml":
                out += "    </record>\n"

    elif format == "xd" or format == "oai_dc":
        # XML Dublin Core format, possibly OAI -- select only some bibXXx fields:
        out += """    <dc xmlns="http://purl.org/dc/elements/1.1/"
                         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                         xsi:schemaLocation="http://purl.org/dc/elements/1.1/
                                             http://www.openarchives.org/OAI/1.1/dc.xsd">\n"""
        for f in get_fieldvalues(recID, "041__a"):
            out += "        <language>%s</language>\n" % f

        for f in get_fieldvalues(recID, "100__a"):
            out += "        <creator>%s</creator>\n" % encode_for_xml(f)

        for f in get_fieldvalues(recID, "700__a"):
            out += "        <creator>%s</creator>\n" % encode_for_xml(f)

        for f in get_fieldvalues(recID, "245__a"):
            out += "        <title>%s</title>\n" % encode_for_xml(f)

        for f in get_fieldvalues(recID, "65017a"):
            out += "        <subject>%s</subject>\n" % encode_for_xml(f)

        for f in get_fieldvalues(recID, "8564_u"):
            out += "        <identifier>%s</identifier>\n" % encode_for_xml(f)
        
        for f in get_fieldvalues(recID, "520__a"):
            out += "        <description>%s</description>\n" % encode_for_xml(f)            

        out += "        <date>%s</date>\n" % get_creation_date(recID)
        out += "    </dc>\n"                    

    elif str(format[0:3]).isdigit():
        # user has asked to print some fields only
        if format == "001":
            out += "<!--%s-begin-->%s<!--%s-end-->\n" % (format, recID, format)
        else:
            vals = get_fieldvalues(recID, format)
            for val in vals:
                out += "<!--%s-begin-->%s<!--%s-end-->\n" % (format, val, format)

    elif format.startswith('t'):
        ## user directly asked for some tags to be displayed only
        out += get_fieldvalues_alephseq_like(recID, ot)

    elif format == "hm":
        out += "<pre>" + cgi.escape(get_fieldvalues_alephseq_like(recID, ot)) + "</pre>"

    elif format.startswith("h") and ot:
        ## user directly asked for some tags to be displayed only
        out += "<pre>" + get_fieldvalues_alephseq_like(recID, ot) + "</pre>"

    elif format == "hd":
        # HTML detailed format
        # look for detailed format existence:
        query = "SELECT value FROM bibfmt WHERE id_bibrec='%s' AND format='%s'" % (recID, format)
        res = run_sql(query, None, 1)
        if res:
            # record 'recID' is formatted in 'format', so print it
            out += "%s" % decompress(res[0][0])
        else:
            # record 'recID' is not formatted in 'format', so either call BibFormat on the fly or use default format
            # second, see if we are calling BibFormat on the fly:
            if cfg_call_bibformat:
                out += call_bibformat(recID)
            else:
                # okay, need to construct a simple "Detailed record" format of our own:
                out += "<p>&nbsp;"
                # secondly, title:
                titles = get_fieldvalues(recID, "245__a")
                for title in titles:
                    out += "<p><p><center><big><strong>%s</strong></big></center>" % title
                # thirdly, authors:
                authors = get_fieldvalues(recID, "100__a") + get_fieldvalues(recID, "700__a")
                if authors:
                    out += "<p><p><center>"
                    for author in authors:
                        out += """<a href="%s/search.py?p=%s&f=author">%s</a> ;""" % (weburl, urllib.quote(author), author)
                    out += "</center>"
                # fourthly, date of creation:
                dates = get_fieldvalues(recID, "260__c")
                for date in dates:
                    out += "<p><center><small>%s</small></center>" % date
                # fifthly, abstract:
                abstracts = get_fieldvalues(recID, "520__a")
                for abstract in abstracts:
                    out += """<p style="margin-left: 15%%; width: 70%%">
                             <small><strong>Abstract:</strong> %s</small></p>""" % abstract
                # fifthly bis, keywords:
                keywords = get_fieldvalues(recID, "6531_a")
                if len(keywords):
                    out += """<p style="margin-left: 15%; width: 70%">
                             <small><strong>Keyword(s):</strong></small>"""
                    for keyword in keywords:
                        out += """<small><a href="%s/search.py?p=%s&f=keyword">%s</a> ;</small> """ % (weburl, urllib.quote(keyword), keyword)
                # fifthly bis bis, published in:
                prs_p = get_fieldvalues(recID, "909C4p")
                prs_v = get_fieldvalues(recID, "909C4v")
                prs_y = get_fieldvalues(recID, "909C4y")
                prs_n = get_fieldvalues(recID, "909C4n")
                prs_c = get_fieldvalues(recID, "909C4c")
                for idx in range(0,len(prs_p)):
                    out += """<p style="margin-left: 15%%; width: 70%%">
                             <small><strong>Publ. in:</strong> %s"""  % prs_p[idx]
                    if prs_v and prs_v[idx]:
                        out += """<strong>%s</strong>""" % prs_v[idx]
                    if prs_y and prs_y[idx]:
                        out += """(%s)""" % prs_y[idx]
                    if prs_n and prs_n[idx]:
                        out += """, no.%s""" % prs_n[idx]
                    if prs_c and prs_c[idx]:
                        out += """, p.%s""" % prs_c[idx]
                    out += """.</small>"""
                # sixthly, fulltext link:
                urls_z = get_fieldvalues(recID, "8564_z")
                urls_u = get_fieldvalues(recID, "8564_u")
                for idx in range(0,len(urls_u)):
                    link_text = "URL"
                    if urls_z[idx]:
                        link_text = urls_z[idx]
                    out += """<p style="margin-left: 15%%; width: 70%%">
                    <small><strong>%s:</strong> <a href="%s">%s</a></small>""" % (link_text, urls_u[idx], urls_u[idx])
                # print some white space at the end:
                out += "<p><p>"

    elif format == "hb-fly":
        # HTML brief called on the fly; suitable for testing brief formats
        out += call_bibformat(recID, "BRIEF_HTML")
        out += """<br><span class="moreinfo"><a class="moreinfo" href="%s/search.py?recid=%s">%s</a></span>""" \
               % (weburl, recID, msg_detailed_record[ln])

    elif cfg_cern_site and format == "hp":
        # HTML portfolio format called on the fly
        out += call_bibformat(recID, "HB_P")

    elif cfg_cern_site and format == "hd-ejournalsite":
        # HTML brief called on the fly; suitable for testing brief formats
        out += call_bibformat(recID, "EJOURNALSITE")
        out += """<br><span class="moreinfo"><a class="moreinfo" href="%s/search.py?recid=%s">%s</a></span>""" \
               % (weburl, recID, msg_detailed_record[ln])

    else:
        # HTML brief format by default
        query = "SELECT value FROM bibfmt WHERE id_bibrec='%s' AND format='%s'" % (recID, format)
        res = run_sql(query)
        if res:
            # record 'recID' is formatted in 'format', so print it
            out += "%s" % decompress(res[0][0])
        else:
            # record 'recID' does not exist in format 'format', so print some default format:
            # firstly, title:
            titles = get_fieldvalues(recID, "245__a")
            for title in titles:
                out += "<strong>%s</strong> " % title
            # secondly, authors:
            authors = get_fieldvalues(recID, "100__a") + get_fieldvalues(recID, "700__a")
            if authors:
                out += " / "
                for i in range (0,cfg_author_et_al_threshold):
                    if i < len(authors):
                        out += """<a href="%s/search.py?p=%s&f=author">%s</a> ;""" % (weburl, urllib.quote(authors[i]), authors[i])
                if len(authors) > cfg_author_et_al_threshold:
                    out += " <em>et al.</em>"
            # thirdly, date of creation:
            dates = get_fieldvalues(recID, "260__c")
            for date in dates:
                out += " %s." % date
            # thirdly bis, report numbers:
            rns = get_fieldvalues(recID, "037__a")
            for rn in rns:
                out += """ <small class="quicknote">[%s]</small>""" % rn
            rns = get_fieldvalues(recID, "088__a")
            for rn in rns:
                out += """ <small class="quicknote">[%s]</small>""" % rn
            # fourthly, beginning of abstract:
            abstracts = get_fieldvalues(recID, "520__a")
            for abstract in abstracts:
                out += "<br><small>%s [...]</small>" % abstract[:1+string.find(abstract, '.')]
            # fifthly, fulltext link:
            urls_z = get_fieldvalues(recID, "8564_z")
            urls_u = get_fieldvalues(recID, "8564_u")
            for idx in range(0,len(urls_u)):
                out += """<br><small class="note"><a class="note" href="%s">%s</a></small>""" % (urls_u[idx], urls_u[idx])

        # at the end of HTML mode, print the "Detailed record" functionality:
        if format != "hp":
            if cfg_use_aleph_sysnos:
                alephsysnos = get_fieldvalues(recID, "970__a")
                if len(alephsysnos)>0:
                    alephsysno = alephsysnos[0]
                    out += """<br><span class="moreinfo"><a class="moreinfo" href="%s/search.py?sysno=%s">%s</a></span>""" \
                           % (weburl, alephsysno, msg_detailed_record[ln])
                else:
                    out += """<br><span class="moreinfo"><a class="moreinfo" href="%s/search.py?recid=%s">%s</a></span>""" \
                           % (weburl, recID, msg_detailed_record[ln])
            else:
                out += """<br><span class="moreinfo"><a class="moreinfo" href="%s/search.py?recid=%s">%s</a></span>""" \
                       % (weburl, recID, msg_detailed_record[ln])

    # print record closing tags, if needed:
    if format == "marcxml" or format == "oai_dc":
        out += "   </metadata>\n"
        out += "  </record>\n"

    return out

def encode_for_xml(s):
    "Encode special chars in string so that it would be XML-compliant."
    s = string.replace(s, '&', '&amp;')
    s = string.replace(s, '<', '&lt;')
    return s

def call_bibformat(id, otype="HD"):
    """Calls BibFormat for the record 'id'.  Desired BibFormat output type is passed in 'otype' argument.
       This function is mainly used to display full format, if they are not stored in the 'bibfmt' table."""
    f = urllib.urlopen("%s/bibformat/bibformat.php?id=%s&otype=%s" % (weburl, id, otype))
    out = f.read()
    f.close()
    return out

def log_query(hostname, query_args, uid=-1):
    """Log query into the query and user_query tables."""
    if uid > 0:
        # log the query only if uid is reasonable
        res = run_sql("SELECT id FROM query WHERE urlargs=%s", (query_args,), 1)
        try:
            id_query = res[0][0]
        except:
            id_query = run_sql("INSERT INTO query (type, urlargs) VALUES ('r', %s)", (query_args,))        
        if id_query:
            run_sql("INSERT INTO user_query (id_user, id_query, hostname, date) VALUES (%s, %s, %s, %s)",
                    (uid, id_query, hostname,
                     time.strftime("%04Y-%02m-%02d %02H:%02M:%02S", time.localtime())))
    return

def log_query_info(action, p, f, colls, nb_records_found_total=-1):
    """Write some info to the log file for later analysis."""
    try:
        log = open(logdir + "/search.log", "a")
        log.write(time.strftime("%04Y%02m%02d%02H%02M%02S#", time.localtime()))
        log.write(action+"#")
        log.write(p+"#")
        log.write(f+"#")
        for coll in colls[:-1]:
            log.write("%s," % coll)
        log.write("%s#" % colls[-1])
        log.write("%d" % nb_records_found_total)
        log.write("\n")
        log.close()
    except:
        pass
    return

def wash_url_argument(var, new_type):
    """Wash list argument into 'new_type', that can be 'list',
       'str', or 'int'.  Useful for washing mod_python passed
       arguments, that are all lists of strings (URL args may be
       multiple), but we sometimes want only to take the first value,
       and sometimes to represent it as string or numerical value."""
    out = []
    if new_type == 'list':  # return lst
        if type(var) is list:
            out = var
        else:
            out = [var]
    elif new_type == 'str':  # return str
        if type(var) is list:
            try:
                out = "%s" % var[0]
            except:
                out = ""
        elif type(var) is str:
            out = var
        else:
            out = "%s" % var
    elif new_type == 'int': # return int
        if type(var) is list:
            try:
                out = string.atoi(var[0])
            except:
                out = 0
        elif type(var) is int:
            out = var
        elif type(var) is str:
            try:
                out = string.atoi(var)
            except:
                out = 0
        else:
            out = 0
    return out       

### CALLABLES

def perform_request_search(req=None, cc=cdsname, c=None, p="", f="", rg="10", sf="", so="d", sp="", of="id", ot="", as="0",
                           p1="", f1="", m1="", op1="", p2="", f2="", m2="", op2="", p3="", f3="", m3="", sc="0", jrec="0",
                           recid="-1", recidb="-1", sysno="", id="-1", idb="-1", sysnb="", action="",
                           d1y="0", d1m="0", d1d="0", d2y="0", d2m="0", d2d="0", verbose="0", ap="0", ln=cdslang):
    """Perform search or browse request, without checking for
       authentication.  Return list of recIDs found, if of=id.
       Otherwise create web page.

       The arguments are as follows:

         req - mod_python Request class instance.

          cc - current collection (e.g. "ATLAS").  The collection the
               user started to search/browse from.

           c - collectin list (e.g. ["Theses", "Books"]).  The
               collections user may have selected/deselected when
               starting to search from 'cc'.

           p - pattern to search for (e.g. "ellis and muon or kaon").

           f - field to search within (e.g. "author").

          rg - records in groups of (e.g. "10").  Defines how many hits
               per collection in the search results page are
               displayed.

          sf - sort field (e.g. "title").  

          so - sort order ("a"=ascending, "d"=descending).

          sp - sort pattern (e.g. "CERN-") -- in case there are more
               values in a sort field, this argument tells which one
               to prefer
          
          of - output format (e.g. "hb").  Usually starting "h" means
               HTML output (and "hb" for HTML brief, "hd" for HTML
               detailed), "x" means XML output, "t" means plain text
               output, "id" means no output at all but to return list
               of recIDs found.  (Suitable for high-level API.)
          
          ot - output only these MARC tags (e.g. "100,700,909C0b").
               Useful if only some fields are to be shown in the
               output, e.g. for library to control some fields.
          
          as - advanced search ("0" means no, "1" means yes).  Whether
               search was called from within the advanced search
               interface.
          
          p1 - first pattern to search for in the advanced search
               interface.  Much like 'p'.
          
          f1 - first field to search within in the advanced search
               interface.  Much like 'f'.
          
          m1 - first matching type in the advanced search interface.
               ("a" all of the words, "o" any of the words, "e" exact
               phrase, "p" partial phrase, "r" regular expression).
          
         op1 - first operator, to join the first and the second unit
               in the advanced search interface.  ("a" add, "o" or,
               "n" not).

          p2 - second pattern to search for in the advanced search
               interface.  Much like 'p'.
          
          f2 - second field to search within in the advanced search
               interface.  Much like 'f'.
          
          m2 - second matching type in the advanced search interface.
               ("a" all of the words, "o" any of the words, "e" exact
               phrase, "p" partial phrase, "r" regular expression).
          
         op2 - second operator, to join the second and the third unit
               in the advanced search interface.  ("a" add, "o" or,
               "n" not).

          p3 - third pattern to search for in the advanced search
               interface.  Much like 'p'.
          
          f3 - third field to search within in the advanced search
               interface.  Much like 'f'.
          
          m3 - third matching type in the advanced search interface.
               ("a" all of the words, "o" any of the words, "e" exact
               phrase, "p" partial phrase, "r" regular expression).
          
          sc - split by collection ("0" no, "1" yes).  Governs whether
               we want to present the results in a single huge list,
               or splitted by collection.
          
        jrec - jump to record (e.g. "234").  Used for navigation
               inside the search results.
          
       recid - display record ID (e.g. "20000").  Do not
               search/browse but go straight away to the Detailed
               record page for the given recID.
       
      recidb - display record ID bis (e.g. "20010").  If greater than
               'recid', then display records from recid to recidb.
               Useful for example for dumping records from the
               database for reformatting.
      
       sysno - display old system SYS number (e.g. "").  If you
               migrate to CDSware from another system, and store your
               old SYS call numbers, you can use them instead of recid
               if you wish so.
       
          id - the same as recid, in case recid is not set.  For
               backwards compatibility.
          
         idb - the same as recid, in case recidb is not set.  For
               backwards compatibility.

       sysnb - the same as sysno, in case sysno is not set.  For
               backwards compatibility.
               
      action - action to do.  "SEARCH" for searching, "Browse" for
               browsing.  Default is to search.
      
         d1y - first date year (e.g. "1998").  Useful for search
               limits on creation date.
                    
         d1m - first date month (e.g. "08").  Useful for search
               limits on creation date.
               
         d1d - first date day (e.g. "23").  Useful for search
               limits on creation date.
               
         d2y - second date year (e.g. "1998").  Useful for search
               limits on creation date.
                    
         d2m - second date month (e.g. "08").  Useful for search
               limits on creation date.
               
         d2d - second date day (e.g. "23").  Useful for search limits
               on creation date.
               
     verbose - verbose level (0=min, 9=max).  Useful to print some
               internal information on the searching process in case
               something goes wrong.

          ap - alternative patterns (0=no, 1=yes).  In case no exact
               match is found, the search engine can try alternative
               patterns e.g. to replace non-alphanumeric characters by
               a boolean query.  ap defines if this is wanted.

          ln - language of the search interface (e.g. "en").  Useful
               for internationalization.
          
    """
    
    # wash all passed arguments:
    cc = wash_url_argument(cc, 'str')
    sc = wash_url_argument(sc, 'int')
    (cc, colls_to_display, colls_to_search) = wash_colls(cc, c, sc) # which colls to search and to display?
    p = wash_pattern(wash_url_argument(p, 'str'))
    f = wash_field(wash_url_argument(f, 'str'))
    rg = wash_url_argument(rg, 'int')
    sf = wash_url_argument(sf, 'str')
    so = wash_url_argument(so, 'str')
    sp = wash_url_argument(sp, 'string')
    of = wash_url_argument(of, 'str')
    if type(ot) is list:
        ot = string.join(ot,",")
    ot = wash_url_argument(ot, 'str')
    as = wash_url_argument(as, 'int')
    p1 = wash_pattern(wash_url_argument(p1, 'str'))
    f1 = wash_field(wash_url_argument(f1, 'str'))
    m1 = wash_url_argument(m1, 'str')
    op1 = wash_url_argument(op1, 'str')
    p2 = wash_pattern(wash_url_argument(p2, 'str'))
    f2 = wash_field(wash_url_argument(f2, 'str'))
    m2 = wash_url_argument(m2, 'str')
    op2 = wash_url_argument(op2, 'str')
    p3 = wash_pattern(wash_url_argument(p3, 'str'))
    f3 = wash_field(wash_url_argument(f3, 'str'))
    m3 = wash_url_argument(m3, 'str')
    jrec = wash_url_argument(jrec, 'int')
    recid = wash_url_argument(recid, 'int')
    recidb = wash_url_argument(recidb, 'int')
    sysno = wash_url_argument(sysno, 'str')
    id = wash_url_argument(id, 'int')
    idb = wash_url_argument(idb, 'int')
    sysnb = wash_url_argument(sysnb, 'str')
    action = wash_url_argument(action, 'str')
    d1y = wash_url_argument(d1y, 'int')
    d1m = wash_url_argument(d1m, 'int')
    d1d = wash_url_argument(d1d, 'int')
    d2y = wash_url_argument(d2y, 'int')
    d2m = wash_url_argument(d2m, 'int')
    d2d = wash_url_argument(d2d, 'int')
    day1, day2 = wash_dates(d1y, d1m, d1d, d2y, d2m, d2d)
    verbose = wash_url_argument(verbose, 'int')
    ap = wash_url_argument(ap, 'int')
    ln = wash_language(ln)
    # backwards compatibility: id, idb, sysnb -> recid, recidb, sysno (if applicable)
    if sysnb != "" and sysno == "":
        sysno = sysnb
    if id > 0 and recid == -1:
        recid = id
    if idb > 0 and recidb == -1:
        recidb = idb
    # TODO deduce passed search limiting criterias (if applicable)
    pl = "" # no limits by default
    if action != msg_browse[ln] and req and req.args: # we do not want to add options while browsing or while calling via command-line
        fieldargs = cgi.parse_qs(req.args)
        for fieldcode in get_fieldcodes():
            if fieldargs.has_key(fieldcode):
                for val in fieldargs[fieldcode]:
                    pl += "+%s:\"%s\" " % (fieldcode, val)
    # deduce recid from sysno argument (if applicable):
    if sysno: # ALEPH SYS number was passed, so deduce MySQL recID for the record:            
        recid = get_mysql_recid_from_aleph_sysno(sysno)
    # deduce collection we are in (if applicable):
    if recid>0:
        cc = guess_primary_collection_of_a_record(recid)
    # deduce user id (if applicable):
    try:
        uid = getUid(req)
    except:
        uid = 0
    ## 0 - start output
    page_start(req, of, cc, as, ln, uid)
    if recid>0:
        ## 1 - detailed record display
        if of == "hb":
            of = "hd"
        if record_exists(recid):
            if recidb<=recid: # sanity check
                recidb=recid+1
            print_records(req, range(recid,recidb), -1, -9999, of, ot, ln)
        else: # record does not exist
            if of.startswith("h"):
                print_warning(req, "Requested record does not seem to exist.")
    elif action == msg_browse[ln]:
        ## 2 - browse needed
        if of.startswith("h"):
            req.write(create_search_box(cc, colls_to_display, p, f, rg, sf, so, sp, of, ot, as, ln, p1, f1, m1, op1,
                                        p2, f2, m2, op2, p3, f3, m3, sc, pl, d1y, d1m, d1d, d2y, d2m, d2d, action))
        try:
            if as==1 or (p1 or p2 or p3):
                browse_pattern(req, colls_to_search, p1, f1, rg)
                browse_pattern(req, colls_to_search, p2, f2, rg)
                browse_pattern(req, colls_to_search, p3, f3, rg)
            else:
                browse_pattern(req, colls_to_search, p, f, rg)
        except:
            if of.startswith("h"):
                req.write(create_error_box(req))
            return page_end(req, of, ln)            

    else:
        ## 3 - search needed
        if of.startswith("h"):
            req.write(create_search_box(cc, colls_to_display, p, f, rg, sf, so, sp, of, ot, as, ln, p1, f1, m1, op1,
                                        p2, f2, m2, op2, p3, f3, m3, sc, pl, d1y, d1m, d1d, d2y, d2m, d2d, action))
        t1 = os.times()[4]
        results_in_any_collection = HitSet()
        if as == 1 or (p1 or p2 or p3):
            ## 3A - advanced search
            try:
                results_in_any_collection = search_pattern(req, p1, f1, m1, ap=ap, of=of, verbose=verbose)
                if results_in_any_collection._nbhits == 0:                
                    return page_end(req, of)                
                if p2:
                    results_tmp = search_pattern(req, p2, f2, m2, ap=ap, of=of, verbose=verbose)
                    if op1 == "a": # add
                        results_in_any_collection.intersect(results_tmp)
                    elif op1 == "o": # or
                        results_in_any_collection.union(results_tmp)
                    elif op1 == "n": # not
                        results_in_any_collection.difference(results_tmp)
                    else:
                        if of.startswith("h"):
                            print_warning(req, "Invalid set operation %s." % op1, "Error")
                    results_in_any_collection.calculate_nbhits()
                    if results_in_any_collection._nbhits == 0:                
                        return page_end(req, of)                
                if p3:
                    results_tmp = search_pattern(req, p3, f3, m3, ap=ap, of=of, verbose=verbose)
                    if op2 == "a": # add
                        results_in_any_collection.intersect(results_tmp)
                    elif op2 == "o": # or
                        results_in_any_collection.union(results_tmp)
                    elif op2 == "n": # not
                        results_in_any_collection.difference(results_tmp)
                    else:
                        if of.startswith("h"):
                            print_warning(req, "Invalid set operation %s." % op2, "Error")            
                    results_in_any_collection.calculate_nbhits()
            except:
                if of.startswith("h"):
                    req.write(create_error_box(req))
                return page_end(req, of)                            
        else:
            ## 3B - simple search
            try:
                results_in_any_collection = search_pattern(req, p, f, ap=ap, of=of, verbose=verbose)
            except:
                if of.startswith("h"):
                    req.write(create_error_box(req))
                return page_end(req, of)

        if results_in_any_collection._nbhits == 0:                
            return page_end(req, of)
                
#             search_cache_key = p+"@"+f+"@"+string.join(colls_to_search,",")
#             if search_cache.has_key(search_cache_key): # is the result in search cache?
#                 results_final = search_cache[search_cache_key]        
#             else:       
#                 results_final = search_pattern(req, p, f, colls_to_search)
#                 search_cache[search_cache_key] = results_final
#             if len(search_cache) > cfg_search_cache_size: # is the cache full? (sanity cleaning)
#                 search_cache.clear()

        # search stage 4: intersection with collection universe:
        try:
            results_final = intersect_results_with_collrecs(req, results_in_any_collection, colls_to_search, ap, of, verbose)
        except:
            if of.startswith("h"):
                req.write(create_error_box(req))
            return page_end(req, of)
        
        if results_final == {}:
            return page_end(req, of)
        
        # search stage 5: apply search option limits and restrictions:
        if day1 != "":
            try:
                results_final = intersect_results_with_hitset(req,
                                                              results_final,
                                                              search_unit_in_bibrec(day1, day2),
                                                              ap,
                                                              aptext="No match within your time limits, "\
                                                                     "discarding this condition...")
            except:
                if of.startswith("h"):
                    req.write(create_error_box(req))
                return page_end(req, of)                            
            if results_final == {}:
                return page_end(req, of)

        if pl:
            try:
                results_final = intersect_results_with_hitset(req,
                                                              results_final,
                                                              search_pattern(req, pl, ap=0),
                                                              ap,
                                                              aptext="No match within your search limits, "\
                                                                     "discarding this condition...")
            except:
                if of.startswith("h"):
                    req.write(create_error_box(req))
                return page_end(req, of)                            
            if results_final == {}:
                return page_end(req, of)

        t2 = os.times()[4]
        cpu_time = t2 - t1
        ## search stage 6: display results:            
        results_final_nb_total = 0
        results_final_nb = {} # will hold number of records found in each collection
                              # (in simple dict to display overview more easily; may refactor later)
        for coll in results_final.keys():
            results_final_nb[coll] = results_final[coll]._nbhits
            results_final_nb_total += results_final_nb[coll]
        if results_final_nb_total == 0:
            if of.startswith('h'):
                print_warning(req, "No match found, please enter different search terms.")
        else:
            # yes, some hits found: good!
            # collection list may have changed due to not-exact-match-found policy so check it out:
            for coll in results_final.keys(): 
                if coll not in colls_to_search:
                    colls_to_search.append(coll)
            # print results overview:
            if of == "id":
                # we have been asked to return list of recIDs
                results_final_for_all_colls = HitSet()
                for coll in results_final.keys():
                    results_final_for_all_colls.union(results_final[coll])
                recIDs = results_final_for_all_colls.items().tolist()
                if sf: # do we have to sort first?
                    recIDs = sort_records(req, recIDs, sf, so, sp)
                return recIDs
            elif of.startswith("h"):
                req.write(print_results_overview(colls_to_search, results_final_nb_total, results_final_nb, cpu_time, ln))
            # print records:
            if len(colls_to_search)>1:
                cpu_time = -1 # we do not want to have search time printed on each collection
            for coll in colls_to_search:                
                if results_final.has_key(coll) and results_final[coll]._nbhits:
                    if of.startswith("h"):
                        req.write(print_search_info(p, f, sf, so, sp, of, ot, coll, results_final_nb[coll],
                                                    jrec, rg, as, ln, p1, p2, p3, f1, f2, f3, m1, m2, m3, op1, op2,
                                                    d1y, d1m, d1d, d2y, d2m, d2d, cpu_time))
                    results_final_sorted = results_final[coll].items()
                    if sf:
                        results_final_sorted = sort_records(req, results_final_sorted, sf, so, sp)
                    print_records(req, results_final_sorted, jrec, rg, of, ot, ln)
                    if of.startswith("h"):
                        req.write(print_search_info(p, f, sf, so, sp, of, ot, coll, results_final_nb[coll],
                                                    jrec, rg, as, ln, p1, p2, p3, f1, f2, f3, m1, m2, m3, op1, op2,
                                                    d1y, d1m, d1d, d2y, d2m, d2d, cpu_time, 1))
            # log query:
            try:
                log_query(req.get_remote_host(), req.args, uid)
            except:
                # do not log query if req is None (used by CLI interface)
                pass
            log_query_info("ss", p, f, colls_to_search, results_final_nb_total)
    ## 4 - write footer:
    return page_end(req, of, ln)

def perform_request_cache(req, action="show"):
    """Manipulates the search engine cache."""
    global search_cache
    global collection_reclist_cache
    req.content_type = "text/html"
    req.send_http_header() 
    out = ""
    out += "<h1>Search Cache</h1>"
    # clear cache if requested:
    if action == "clear":
        search_cache = {}
        collection_reclist_cache = create_collection_reclist_cache()
    # show collection cache:
    out += "<h3>Collection Cache</h3>"
    out += "<blockquote>"
    for coll in collection_reclist_cache.keys():
        if collection_reclist_cache[coll]:
            out += "%s (%d)<br>" % (coll, get_collection_reclist(coll)._nbhits)
    out += "</blockquote>"
    # show search cache:
    out += "<h3>Search Cache</h3>"
    out += "<blockquote>"
    if len(search_cache):
        out += """<table border="=">"""
        out += "<tr><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td></tr>" % ("Pattern","Field","Collection","Number of Hits")
        for search_cache_key in search_cache.keys():
            p, f, c = string.split(search_cache_key, "@", 2)
            # find out about length of cached data:
            l = 0
            for coll in search_cache[search_cache_key]:
                l += search_cache[search_cache_key][coll]._nbhits
            out += "<tr><td>%s</td><td>%s</td><td>%s</td><td>%d</td></tr>" % (p, f, c, l)
        out += "</table>"
    else:
        out += "<p>Search cache is empty."
    out += "</blockquote>"
    out += """<p><a href="%s/search.py/cache?action=clear">clear cache</a>""" % weburl
    req.write(out)
    return "\n"

def perform_request_log(req, date=""):
    """Display search log information for given date."""
    req.content_type = "text/html"
    req.send_http_header() 
    req.write("<h1>Search Log</h1>")
    if date: # case A: display stats for a day
        yyyymmdd = string.atoi(date)
        req.write("<p><big><strong>Date: %d</strong></big><p>" % yyyymmdd)
        req.write("""<table border="1">""")
        req.write("<tr><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td></tr>" % ("No.","Time", "Pattern","Field","Collection","Number of Hits"))
        # read file:
        p = os.popen("grep ^%d %s/search.log" % (yyyymmdd,logdir), 'r')
        lines = p.readlines()
        p.close()
        # process lines:
        i = 0
        for line in lines:
            try:
                datetime, as, p, f, c, nbhits = string.split(line,"#")
                i += 1
                req.write("<tr><td align=\"right\">#%d</td><td>%s:%s:%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" \
                          % (i, datetime[8:10], datetime[10:12], datetime[12:], p, f, c, nbhits))
            except:
                pass # ignore eventual wrong log lines
        req.write("</table>")
    else: # case B: display summary stats per day
        yyyymm01 = int(time.strftime("%04Y%02m01", time.localtime()))
        yyyymmdd = int(time.strftime("%04Y%02m%02d", time.localtime()))
        req.write("""<table border="1">""")
        req.write("<tr><td><strong>%s</strong></td><td><strong>%s</strong></tr>" % ("Day", "Number of Queries"))
        for day in range(yyyymm01,yyyymmdd+1):
            p = os.popen("grep -c ^%d %s/search.log" % (day,logdir), 'r')
            for line in p.readlines():
                req.write("""<tr><td>%s</td><td align="right"><a href="%s/search.py/log?date=%d">%s</a></td></tr>""" % (day, weburl,day,line))
            p.close()
        req.write("</table>")
    return "\n"    

def profile(p="", f="", c=cdsname):
    """Profile search time."""
    import profile
    import pstats
    profile.run("perform_request_search(p='%s',f='%s', c='%s')" % (p, f, c), "perform_request_search_profile")
    p = pstats.Stats("perform_request_search_profile")
    p.strip_dirs().sort_stats("cumulative").print_stats()        
    return 0

## test cases:
#print wash_colls(cdsname,"Library Catalogue", 0)
#print wash_colls("Periodicals & Progress Reports",["Periodicals","Progress Reports"], 0)
#print wash_field("wau")
#print print_record(20,"tm","001,245")
#print create_opft_search_units(None, "PHE-87-13","reportnumber")
#print ":"+wash_pattern("* and % doo * %")+":\n"
#print ":"+wash_pattern("*")+":\n"
#print ":"+wash_pattern("ellis* ell* e*%")+":\n"
#print run_sql("SELECT name,dbquery from collection")
#print get_wordsindex_id("author")
#print get_coll_ancestors("Theses")
#print get_coll_sons("Articles & Preprints")
#print get_coll_real_descendants("Articles & Preprints")
#print get_collection_reclist("Theses")
#print log(sys.stdin)
#print search_unit_in_bibrec('2002-12-01','2002-12-12')
#print wash_dates('1980', '', '28', '2003','02','')
#print type(wash_url_argument("-1",'int'))

## profiling:
#profile("of the this")
</protect>

