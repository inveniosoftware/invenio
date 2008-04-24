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

# pylint: disable-msg=C0301

"""CDS Invenio Search Engine in mod_python."""

__lastupdated__ = """$Date$"""

__revision__ = "$Id$"

## import general modules:
import cgi
import copy
import string
import os
import re
import time
import urllib
import zlib

## import CDS Invenio stuff:
from invenio.config import \
     CFG_CERN_SITE, \
     CFG_OAI_ID_FIELD, \
     CFG_WEBCOMMENT_ALLOW_REVIEWS, \
     CFG_WEBSEARCH_CALL_BIBFORMAT, \
     CFG_WEBSEARCH_CREATE_SIMILARLY_NAMED_AUTHORS_LINK_BOX, \
     CFG_WEBSEARCH_FIELDS_CONVERT, \
     CFG_WEBSEARCH_NB_RECORDS_TO_SORT, \
     CFG_WEBSEARCH_SEARCH_CACHE_SIZE, \
     CFG_WEBSEARCH_USE_JSMATH_FOR_FORMATS, \
     CFG_BIBRANK_SHOW_DOWNLOAD_GRAPHS, \
     CFG_SITE_LANG, \
     CFG_SITE_NAME, \
     CFG_LOGDIR, \
     CFG_SITE_URL
from invenio.search_engine_config import CFG_EXPERIMENTAL_FEATURES, InvenioWebSearchUnknownCollectionError
from invenio.search_engine_summarizer import summarize_records
from invenio.bibrecord import create_records, record_get_field_value, record_get_field_values
from invenio.bibrank_record_sorter import get_bibrank_methods, rank_records
from invenio.bibrank_downloads_similarity import register_page_view_event, calculate_reading_similarity_list
from invenio.bibindex_engine_stemmer import stem
from invenio.bibformat import format_record, format_records, get_output_format_content_type, create_excel
from invenio.bibformat_config import CFG_BIBFORMAT_USE_OLD_BIBFORMAT
from invenio.bibrank_downloads_grapher import create_download_history_graph_and_box
from invenio.data_cacher import DataCacher
from invenio.websearch_external_collections import print_external_results_overview, perform_external_collection_search
from invenio.access_control_admin import acc_get_action_id
from invenio.access_control_config import VIEWRESTRCOLL, \
    CFG_ACC_GRANT_AUTHOR_RIGHTS_TO_EMAILS_IN_TAGS
from invenio.websearchadminlib import get_detailed_page_tabs
from invenio.intbitset import intbitset as HitSet
from invenio.webinterface_handler import wash_urlargd
from invenio.urlutils import make_canonical_urlargd
from invenio.dbquery import DatabaseError
from invenio.access_control_engine import acc_authorize_action

import invenio.template
webstyle_templates = invenio.template.load('webstyle')
webcomment_templates = invenio.template.load('webcomment')

from invenio.bibrank_citation_searcher import calculate_cited_by_list, \
calculate_co_cited_with_list, get_self_cited_in, get_self_cited_by, get_records_with_num_cites
from invenio.bibrank_citation_grapher import create_citation_history_graph_and_box

from invenio.dbquery import run_sql, run_sql_cached, get_table_update_time, Error
from invenio.webuser import getUid, collect_user_info
from invenio.webpage import page, pageheaderonly, pagefooteronly, create_error_box
from invenio.messages import gettext_set_language
from invenio.search_engine_query_parser import SearchQueryParenthesisedParser, InvenioWebSearchQueryParserException

try:
    from mod_python import apache
except ImportError, e:
    pass # ignore user personalisation, needed e.g. for command-line

try:
    import invenio.template
    websearch_templates = invenio.template.load('websearch')
except:
    pass

## global vars:
search_cache = {} # will cache results of previous searches
cfg_nb_browse_seen_records = 100 # limit of the number of records to check when browsing certain collection
cfg_nicely_ordered_collection_list = 0 # do we propose collection list nicely ordered or alphabetical?
collection_reclist_cache_timestamp = 0
field_i18nname_cache_timestamp = 0
collection_i18nname_cache_timestamp = 0

## precompile some often-used regexp for speed reasons:
re_word = re.compile('[\s]')
re_quotes = re.compile('[\'\"]')
re_doublequote = re.compile('\"')
re_equal = re.compile('\=')
re_logical_and = re.compile('\sand\s', re.I)
re_logical_or = re.compile('\sor\s', re.I)
re_logical_not = re.compile('\snot\s', re.I)
re_operators = re.compile(r'\s([\+\-\|])\s')
re_pattern_wildcards_at_beginning = re.compile(r'(\s)[\*\%]+')
re_pattern_single_quotes = re.compile("'(.*?)'")
re_pattern_double_quotes = re.compile("\"(.*?)\"")
re_pattern_regexp_quotes = re.compile("\/(.*?)\/")
re_pattern_short_words = re.compile(r'([\s\"]\w{1,3})[\*\%]+')
re_pattern_space = re.compile("__SPACE__")
re_pattern_today = re.compile("\$TODAY\$")
re_unicode_lowercase_a = re.compile(unicode(r"(?u)[áàäâãå]", "utf-8"))
re_unicode_lowercase_ae = re.compile(unicode(r"(?u)[æ]", "utf-8"))
re_unicode_lowercase_e = re.compile(unicode(r"(?u)[éèëê]", "utf-8"))
re_unicode_lowercase_i = re.compile(unicode(r"(?u)[íìïî]", "utf-8"))
re_unicode_lowercase_o = re.compile(unicode(r"(?u)[óòöôõø]", "utf-8"))
re_unicode_lowercase_u = re.compile(unicode(r"(?u)[úùüû]", "utf-8"))
re_unicode_lowercase_y = re.compile(unicode(r"(?u)[ýÿ]", "utf-8"))
re_unicode_lowercase_c = re.compile(unicode(r"(?u)[çć]", "utf-8"))
re_unicode_lowercase_n = re.compile(unicode(r"(?u)[ñ]", "utf-8"))
re_unicode_uppercase_a = re.compile(unicode(r"(?u)[ÁÀÄÂÃÅ]", "utf-8"))
re_unicode_uppercase_ae = re.compile(unicode(r"(?u)[Æ]", "utf-8"))
re_unicode_uppercase_e = re.compile(unicode(r"(?u)[ÉÈËÊ]", "utf-8"))
re_unicode_uppercase_i = re.compile(unicode(r"(?u)[ÍÌÏÎ]", "utf-8"))
re_unicode_uppercase_o = re.compile(unicode(r"(?u)[ÓÒÖÔÕØ]", "utf-8"))
re_unicode_uppercase_u = re.compile(unicode(r"(?u)[ÚÙÜÛ]", "utf-8"))
re_unicode_uppercase_y = re.compile(unicode(r"(?u)[Ý]", "utf-8"))
re_unicode_uppercase_c = re.compile(unicode(r"(?u)[ÇĆ]", "utf-8"))
re_unicode_uppercase_n = re.compile(unicode(r"(?u)[Ñ]", "utf-8"))
re_latex_lowercase_a = re.compile("\\\\[\"H'`~^vu=k]\{?a\}?")
re_latex_lowercase_ae = re.compile("\\\\ae\\{\\}?")
re_latex_lowercase_e = re.compile("\\\\[\"H'`~^vu=k]\\{?e\\}?")
re_latex_lowercase_i = re.compile("\\\\[\"H'`~^vu=k]\\{?i\\}?")
re_latex_lowercase_o = re.compile("\\\\[\"H'`~^vu=k]\\{?o\\}?")
re_latex_lowercase_u = re.compile("\\\\[\"H'`~^vu=k]\\{?u\\}?")
re_latex_lowercase_y = re.compile("\\\\[\"']\\{?y\\}?")
re_latex_lowercase_c = re.compile("\\\\['uc]\\{?c\\}?")
re_latex_lowercase_n = re.compile("\\\\[c'~^vu]\\{?n\\}?")
re_latex_uppercase_a = re.compile("\\\\[\"H'`~^vu=k]\\{?A\\}?")
re_latex_uppercase_ae = re.compile("\\\\AE\\{?\\}?")
re_latex_uppercase_e = re.compile("\\\\[\"H'`~^vu=k]\\{?E\\}?")
re_latex_uppercase_i = re.compile("\\\\[\"H'`~^vu=k]\\{?I\\}?")
re_latex_uppercase_o = re.compile("\\\\[\"H'`~^vu=k]\\{?O\\}?")
re_latex_uppercase_u = re.compile("\\\\[\"H'`~^vu=k]\\{?U\\}?")
re_latex_uppercase_y = re.compile("\\\\[\"']\\{?Y\\}?")
re_latex_uppercase_c = re.compile("\\\\['uc]\\{?C\\}?")
re_latex_uppercase_n = re.compile("\\\\[c'~^vu]\\{?N\\}?")



class RestrictedCollectionDataCacher(DataCacher):
    def __init__(self):
        def cache_filler():
            ret = []
            try:
                viewcollid = acc_get_action_id(VIEWRESTRCOLL)
                res = run_sql("""SELECT DISTINCT ar.value
                    FROM accROLE_accACTION_accARGUMENT raa JOIN accARGUMENT ar ON raa.id_accARGUMENT = ar.id
                    WHERE ar.keyword = 'collection' AND raa.id_accACTION = %s""", (viewcollid,))
            except Exception:
                # database problems, return empty cache
                return []
            for coll in res:
                ret.append(coll[0])
            return ret

        def timestamp_getter():
            return max(get_table_update_time('accROLE_accACTION_accARGUMENT'), get_table_update_time('accARGUMENT'))

        DataCacher.__init__(self, cache_filler, timestamp_getter)

def collection_restricted_p(collection):
    cache = restricted_collection_cache.get_cache()
    return collection in cache

try:
    restricted_collection_cache.is_ok_p
except Exception:
    restricted_collection_cache = RestrictedCollectionDataCacher()


def check_user_can_view_record(user_info, recid):
    """Check if the user is authorized to view the given recid. The function
    grants access in two cases: either user has author rights on ths record,
    or he has view rights to the primary collection this record belongs to.
    Returns the same type as acc_authorize_action
    """

    def _is_user_in_authorized_author_list_for_recid(user_info, recid):
        """Return True if the user have submitted the given record."""
        authorized_emails = []
        for tag in CFG_ACC_GRANT_AUTHOR_RIGHTS_TO_EMAILS_IN_TAGS:
            authorized_emails.extend(get_fieldvalues(recid, tag))
        for email in authorized_emails:
            email = email.strip().lower()
            if user_info['email'].strip().lower() == email:
                return True
        return False

    record_primary_collection = guess_primary_collection_of_a_record(recid)
    if collection_restricted_p(record_primary_collection):
        (auth_code, auth_msg) = acc_authorize_action(user_info, VIEWRESTRCOLL, collection=record_primary_collection)
        if auth_code == 0 or _is_user_in_authorized_author_list_for_recid(user_info, recid):
            return (0, '')
        else:
            return (auth_code, auth_msg)
    else:
        return (0, '')

class IndexStemmingDataCacher(DataCacher):
    def __init__(self):
        def cache_filler():
            try:
                res = run_sql("""SELECT id, stemming_language FROM idxINDEX""")
            except DatabaseError:
                # database problems, return empty cache
                return {}
            return dict(res)

        def timestamp_getter():
            return get_table_update_time('idxINDEX')

        DataCacher.__init__(self, cache_filler, timestamp_getter)

def get_index_stemming_language(index_id):
    cache = index_stemming_cache.get_cache()
    return cache[index_id]

try:
    index_stemming_cache.is_ok_p
except Exception:
    index_stemming_cache = IndexStemmingDataCacher()

class FieldI18nNameDataCacher(DataCacher):
    def __init__(self):
        def cache_filler():
            ret = {}
            try:
                res = run_sql("SELECT f.name,fn.ln,fn.value FROM fieldname AS fn, field AS f WHERE fn.id_field=f.id AND fn.type='ln'") # ln=long name
            except Exception:
                # database problems, return empty cache
                return {}
            for f, ln, i18nname in res:
                if i18nname:
                    if not ret.has_key(f):
                        ret[f] = {}
                    ret[f][ln] = i18nname
            return ret

        def timestamp_getter():
            return get_table_update_time('fieldname')

        DataCacher.__init__(self, cache_filler, timestamp_getter)

    def get_field_i18nname(self, f, ln=CFG_SITE_LANG):
        out = f
        try:
            out = self.get_cache()[f][ln]
        except KeyError:
            pass # translation in LN does not exist
        return out

try:
    if not field_i18n_name_cache.is_ok_p:
        raise Exception
except Exception:
    field_i18n_name_cache = FieldI18nNameDataCacher()


class CollectionRecListDataCacher(DataCacher):
    def __init__(self):
        def cache_filler():
            ret = {}
            try:
                res = run_sql("SELECT name,reclist FROM collection")
            except Exception:
                # database problems, return empty cache
                return {}
            for name, reclist in res:
                ret[name] = None # this will be filled later during runtime by calling get_collection_reclist(coll)
            return ret

        def timestamp_getter():
            return get_table_update_time('collection')

        DataCacher.__init__(self, cache_filler, timestamp_getter)

    def get_collection_reclist(self, coll):
        cache = self.get_cache()
        if not cache[coll]:
            # not yet it the cache, so calculate it and fill the cache:
            set = HitSet()
            query = "SELECT nbrecs,reclist FROM collection WHERE name='%s'" % coll
            res = run_sql(query, None, 1)
            if res:
                try:
                    set = HitSet(res[0][1])
                except:
                    pass
            self.cache[coll] = set
            cache[coll] = set
        # finally, return reclist:
        return cache[coll]

try:
    if not collection_reclist_cache.is_ok_p:
        raise Exception
except Exception:
    collection_reclist_cache = CollectionRecListDataCacher()


class CollectionI18nDataCacher(DataCacher):
    def __init__(self):
        def cache_filler():
            ret = {}
            try:
                res = run_sql("SELECT c.name,cn.ln,cn.value FROM collectionname AS cn, collection AS c WHERE cn.id_collection=c.id AND cn.type='ln'") # ln=long name
            except Exception:
                # database problems,
                return {}
            for c, ln, i18nname in res:
                if i18nname:
                    if not ret.has_key(c):
                        ret[c] = {}
                    ret[c][ln] = i18nname
            return ret

        def timestamp_getter():
            return get_table_update_time('collectionname')

        DataCacher.__init__(self, cache_filler, timestamp_getter)

    def get_coll_i18nname(self, c, ln=CFG_SITE_LANG):
        """Return nicely formatted collection name (of name type 'ln',
        'long name') for collection C in language LN."""
        cache = self.get_cache()
        out = c
        try:
            out = cache[c][ln]
        except KeyError:
            pass # translation in LN does not exist
        return out

try:
    if not collection_i18n_name_cache.is_ok_p:
        raise Exception
except Exception:
    collection_i18n_name_cache = CollectionI18nDataCacher()


def get_alphabetically_ordered_collection_list(level=0, ln=CFG_SITE_LANG):
    """Returns nicely ordered (score respected) list of collections, more exactly list of tuples
       (collection name, printable collection name).
       Suitable for create_search_box()."""
    out = []
    query = "SELECT id,name FROM collection ORDER BY name ASC"
    res = run_sql(query)
    for c_id, c_name in res:
        # make a nice printable name (e.g. truncate c_printable for
        # long collection names in given language):
        c_printable = get_coll_i18nname(c_name, ln)
        if len(c_printable)>30:
            c_printable = c_printable[:30] + "..."
        if level:
            c_printable = " " + level * '-' + " " + c_printable
        out.append([c_name, c_printable])
    return out

def get_nicely_ordered_collection_list(collid=1, level=0, ln=CFG_SITE_LANG):
    """Returns nicely ordered (score respected) list of collections, more exactly list of tuples
       (collection name, printable collection name).
       Suitable for create_search_box()."""
    colls_nicely_ordered = []
    query = "SELECT c.name,cc.id_son FROM collection_collection AS cc, collection AS c "\
            " WHERE c.id=cc.id_son AND cc.id_dad='%s' ORDER BY score DESC" % collid
    res = run_sql(query)
    for c, cid in res:
        # make a nice printable name (e.g. truncate c_printable for
        # long collection names in given language):
        c_printable = get_coll_i18nname(c, ln)
        if len(c_printable)>30:
            c_printable = c_printable[:30] + "..."
        if level:
            c_printable = " " + level * '-' + " " + c_printable
        colls_nicely_ordered.append([c, c_printable])
        colls_nicely_ordered  = colls_nicely_ordered + get_nicely_ordered_collection_list(cid, level+1, ln=ln)
    return colls_nicely_ordered

def get_index_id_from_field(field):
    """Returns first index id where the field code FIELD is indexed.
       Returns zero in case there is no table for this index.
       Example: field='author', output=4."""
    out = 0
    res = run_sql("""SELECT w.id FROM idxINDEX AS w, idxINDEX_field AS wf, field AS f
                      WHERE f.code=%s AND wf.id_field=f.id AND w.id=wf.id_idxINDEX
                      LIMIT 1""", (field,))
    if res:
        out = res[0][0]
    return out

def get_words_from_pattern(pattern):
    "Returns list of whitespace-separated words from pattern."
    words = {}
    for word in string.split(pattern):
        if not words.has_key(word):
            words[word] = 1;
    return words.keys()

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

def page_start(req, of, cc, as, ln, uid, title_message=None,
               description='', keywords='', recID=-1, tab=''):
    "Start page according to given output format."
    _ = gettext_set_language(ln)

    if not title_message: title_message = _("Search Results")

    if not req:
        return # we were called from CLI

    content_type = get_output_format_content_type(of)

    if of.startswith('x'):
        if of == 'xr':
            # we are doing RSS output
            req.content_type = "application/rss+xml"
            req.send_http_header()
            req.write("""<?xml version="1.0" encoding="UTF-8"?>\n""")
        else:
            # we are doing XML output:
            req.content_type = "text/xml"
            req.send_http_header()
            req.write("""<?xml version="1.0" encoding="UTF-8"?>\n""")
    elif of.startswith('t') or str(of[0:3]).isdigit():
        # we are doing plain text output:
        req.content_type = "text/plain"
        req.send_http_header()
    elif of == "id":
        pass # nothing to do, we shall only return list of recIDs
    elif content_type == 'text/html':
        # we are doing HTML output:
        req.content_type = "text/html"
        req.send_http_header()

        if not description:
            description = "%s %s." % (cc, _("Search Results"))

        if not keywords:
            keywords = "%s, WebSearch, %s" % (get_coll_i18nname(CFG_SITE_NAME, ln), get_coll_i18nname(cc, ln))

        argd = {}
        if req.args:
            argd = cgi.parse_qs(req.args)
        rssurl = websearch_templates.build_rss_url(argd)

        navtrail = create_navtrail_links(cc, as, ln)
        navtrail_append_title_p = 1

        # FIXME: Find a good point to put this code.
        # This is a nice hack to trigger jsMath only when displaying single
        # records.
        if of.lower() in CFG_WEBSEARCH_USE_JSMATH_FOR_FORMATS:
            metaheaderadd = """
  <script type='text/javascript'>
    jsMath = {
        styles: {'#jsMath_button': 'display: none'},
        Controls: {cookie: {printwarn: 0}}
    };
  </script>
  <script src='/jsMath/easy/invenio-jsmath.js' type='text/javascript'></script>
"""
        else:
            metaheaderadd = ''
        if tab != '' or ((of != '' or of.lower() != 'hd') and of != 'hb'):
            # If we are not in information tab in HD format, customize
            # the nav. trail to have a link back to main record. (Due
            # to the way perform_request_search() works, hb
            # (lowercase) is equal to hd)
            if (of != '' or of.lower() != 'hd') and of != 'hb':
                # Export
                format_name = of
                query = "SELECT name FROM format WHERE code=%s"
                res = run_sql(query, (of,))
                if res:
                    format_name = res[0][0]
                navtrail += ' &gt; <a class="navtrail" href="%s/record/%s">%s</a> &gt; %s' % \
                            (CFG_SITE_URL, recID, title_message, format_name)
            else:
                # Discussion, citations, etc. tabs
                tab_label = get_detailed_page_tabs(cc, ln=ln)[tab]['label']
                navtrail += ' &gt; <a class="navtrail" href="%s/record/%s">%s</a> &gt; %s' % \
                            (CFG_SITE_URL, recID, title_message, _(tab_label))
            navtrail_append_title_p = 0

        req.write(pageheaderonly(req=req, title=title_message,
                                 navtrail=navtrail,
                                 description=description,
                                 keywords=keywords,
                                 metaheaderadd=metaheaderadd,
                                 uid=uid,
                                 language=ln,
                                 navmenuid='search',
                                 navtrail_append_title_p=\
                                 navtrail_append_title_p,
                                 rssurl=rssurl))
        req.write(websearch_templates.tmpl_search_pagestart(ln=ln))
    #else:
    #    req.send_http_header()

def page_end(req, of="hb", ln=CFG_SITE_LANG):
    "End page according to given output format: e.g. close XML tags, add HTML footer, etc."
    if of == "id":
        return [] # empty recID list
    if not req:
        return # we were called from CLI
    if of.startswith('h'):
        req.write(websearch_templates.tmpl_search_pageend(ln = ln)) # pagebody end
        req.write(pagefooteronly(lastupdated=__lastupdated__, language=ln, req=req))
    return "\n"

def create_inputdate_box(name="d1", selected_year=0, selected_month=0, selected_day=0, ln=CFG_SITE_LANG):
    "Produces 'From Date', 'Until Date' kind of selection box.  Suitable for search options."

    _ = gettext_set_language(ln)

    box = ""
    # day
    box += """<select name="%sd">""" % name
    box += """<option value="">%s""" % _("any day")
    for day in range(1, 32):
        box += """<option value="%02d"%s>%02d""" % (day, is_selected(day, selected_day), day)
    box += """</select>"""
    # month
    box += """<select name="%sm">""" % name
    box += """<option value="">%s""" % _("any month")
    for mm, month in [(1, _("January")), (2, _("February")), (3, _("March")), (4, _("April")), \
                      (5, _("May")), (6, _("June")), (7, _("July")), (8, _("August")), \
                      (9, _("September")), (10, _("October")), (11, _("November")), (12, _("December"))]:
        box += """<option value="%02d"%s>%s""" % (mm, is_selected(mm, selected_month), month)
    box += """</select>"""
    # year
    box += """<select name="%sy">""" % name
    box += """<option value="">%s""" % _("any year")
    this_year = int(time.strftime("%Y", time.localtime()))
    for year in range(this_year-20, this_year+1):
        box += """<option value="%d"%s>%d""" % (year, is_selected(year, selected_year), year)
    box += """</select>"""
    return box

def create_search_box(cc, colls, p, f, rg, sf, so, sp, rm, of, ot, as,
                      ln, p1, f1, m1, op1, p2, f2, m2, op2, p3, f3,
                      m3, sc, pl, d1y, d1m, d1d, d2y, d2m, d2d, dt, jrec, ec,
                      action=""):

    """Create search box for 'search again in the results page' functionality."""

    # load the right message language
    _ = gettext_set_language(ln)

    # some computations
    cc_intl = get_coll_i18nname(cc, ln)
    cc_colID = get_colID(cc)

    colls_nicely_ordered = []
    if cfg_nicely_ordered_collection_list:
        colls_nicely_ordered = get_nicely_ordered_collection_list(ln=ln)
    else:
        colls_nicely_ordered = get_alphabetically_ordered_collection_list(ln=ln)

    colls_nice = []
    for (cx, cx_printable) in colls_nicely_ordered:
        if not cx.startswith("Unnamed collection"):
            colls_nice.append({ 'value' : cx,
                                'text' : cx_printable
                              })

    coll_selects = []
    if colls and colls[0] != CFG_SITE_NAME:
        # some collections are defined, so print these first, and only then print 'add another collection' heading:
        for c in colls:
            if c:
                temp = []
                temp.append({ 'value' : CFG_SITE_NAME,
                              'text' : '*** %s ***' % _("any collection")
                            })
                for val in colls_nice:
                    # print collection:
                    if not cx.startswith("Unnamed collection"):
                        temp.append({ 'value' : val['value'],
                                      'text' : val['text'],
                                      'selected' : (c == re.sub("^[\s\-]*","", val['value']))
                                    })
                coll_selects.append(temp)
        coll_selects.append([{ 'value' : '',
                               'text' : '*** %s ***' % _("add another collection")
                             }] + colls_nice)
    else: # we searched in CFG_SITE_NAME, so print 'any collection' heading
        coll_selects.append([{ 'value' : CFG_SITE_NAME,
                               'text' : '*** %s ***' % _("any collection")
                             }] + colls_nice)

    ## ranking methods
    ranks = [{
               'value' : '',
               'text' : "- %s %s -" % (_("OR").lower (), _("rank by")),
             }]
    for (code, name) in get_bibrank_methods(cc_colID, ln):
        # propose found rank methods:
        ranks.append({
                       'value' : code,
                       'text' : name,
                     })

    formats = []
    query = """SELECT code,name FROM format WHERE visibility='1' ORDER BY name ASC"""
    res = run_sql(query)
    if res:
        # propose found formats:
        for code, name in res:
            formats.append({ 'value' : code,
                             'text' : name
                           })
    else:
        formats.append({'value' : 'hb',
                        'text' : _("HTML brief")
                       })

    return websearch_templates.tmpl_search_box(
             ln = ln,
             as = as,
             cc_intl = cc_intl,
             cc = cc,
             ot = ot,
             sp = sp,
             action = action,
             fieldslist = get_searchwithin_fields(ln=ln, colID=cc_colID),
             f1 = f1,
             f2 = f2,
             f3 = f3,
             m1 = m1,
             m2 = m2,
             m3 = m3,
             p1 = p1,
             p2 = p2,
             p3 = p3,
             op1 = op1,
             op2 = op2,
             rm = rm,
             p = p,
             f = f,
             coll_selects = coll_selects,
             d1y = d1y, d2y = d2y, d1m = d1m, d2m = d2m, d1d = d1d, d2d = d2d,
             dt = dt,
             sort_fields = get_sortby_fields(ln=ln, colID=cc_colID),
             sf = sf,
             so = so,
             ranks = ranks,
             sc = sc,
             rg = rg,
             formats = formats,
             of = of,
             pl = pl,
             jrec = jrec,
             ec = ec,
           )

def create_navtrail_links(cc=CFG_SITE_NAME, as=0, ln=CFG_SITE_LANG, self_p=1, tab=''):
    """Creates navigation trail links, i.e. links to collection
    ancestors (except Home collection).  If as==1, then links to
    Advanced Search interfaces; otherwise Simple Search.
    """

    dads = []
    for dad in get_coll_ancestors(cc):
        if dad != CFG_SITE_NAME: # exclude Home collection
            dads.append ((dad, get_coll_i18nname (dad, ln)))

    if self_p and cc != CFG_SITE_NAME:
        dads.append((cc, get_coll_i18nname(cc, ln)))

    return websearch_templates.tmpl_navtrail_links(
        as=as, ln=ln, dads=dads)

def get_searchwithin_fields(ln='en', colID=None):
    """Retrieves the fields name used in the 'search within' selection box for the collection ID colID."""
    res = None
    if colID:
        res = run_sql_cached("""SELECT f.code,f.name FROM field AS f, collection_field_fieldvalue AS cff
                                 WHERE cff.type='sew' AND cff.id_collection=%s AND cff.id_field=f.id
                              ORDER BY cff.score DESC, f.name ASC""", (colID,))
    if not res:
        res = run_sql_cached("SELECT code,name FROM field ORDER BY name ASC")
    fields = [{
                'value' : '',
                'text' : get_field_i18nname("any field", ln)
              }]
    for field_code, field_name in res:
        if field_code and field_code != "anyfield":
            fields.append({ 'value' : field_code,
                            'text' : get_field_i18nname(field_name, ln)
                          })
    return fields

def get_sortby_fields(ln='en', colID=None):
    """Retrieves the fields name used in the 'sort by' selection box for the collection ID colID."""
    _ = gettext_set_language(ln)
    res = None
    if colID:
        res = run_sql_cached("""SELECT DISTINCT(f.code),f.name FROM field AS f, collection_field_fieldvalue AS cff
                                 WHERE cff.type='soo' AND cff.id_collection=%s AND cff.id_field=f.id
                              ORDER BY cff.score DESC, f.name ASC""", (colID,))
    if not res:
        # no sort fields defined for this colID, try to take Home collection:
        res = run_sql_cached("""SELECT DISTINCT(f.code),f.name FROM field AS f, collection_field_fieldvalue AS cff
                                 WHERE cff.type='soo' AND cff.id_collection=%s AND cff.id_field=f.id
                                 ORDER BY cff.score DESC, f.name ASC""", (1,))
    if not res:
        # no sort fields defined for the Home collection, take all sort fields defined wherever they are:
        res = run_sql_cached("""SELECT DISTINCT(f.code),f.name FROM field AS f, collection_field_fieldvalue AS cff
                                 WHERE cff.type='soo' AND cff.id_field=f.id
                                 ORDER BY cff.score DESC, f.name ASC""")
    fields = [{
                'value' : '',
                'text' : _("latest first")
              }]
    for field_code, field_name in res:
        if field_code and field_code != "anyfield":
            fields.append({ 'value' : field_code,
                            'text' : get_field_i18nname(field_name, ln)
                          })
    return fields

def create_andornot_box(name='op', value='', ln='en'):
    "Returns HTML code for the AND/OR/NOT selection box."

    _ = gettext_set_language(ln)

    out = """
    <select name="%s">
    <option value="a"%s>%s
    <option value="o"%s>%s
    <option value="n"%s>%s
    </select>
    """ % (name,
           is_selected('a', value), _("AND"),
           is_selected('o', value), _("OR"),
           is_selected('n', value), _("AND NOT"))

    return out

def create_matchtype_box(name='m', value='', ln='en'):
    "Returns HTML code for the 'match type' selection box."

    _ = gettext_set_language(ln)

    out = """
    <select name="%s">
    <option value="a"%s>%s
    <option value="o"%s>%s
    <option value="e"%s>%s
    <option value="p"%s>%s
    <option value="r"%s>%s
    </select>
    """ % (name,
           is_selected('a', value), _("All of the words:"),
           is_selected('o', value), _("Any of the words:"),
           is_selected('e', value), _("Exact phrase:"),
           is_selected('p', value), _("Partial phrase:"),
           is_selected('r', value), _("Regular expression:"))
    return out

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

    The function raises exception
    InvenioWebSearchUnknownCollectionError
    if cc or one of c collections is not known.
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
            if cc:
                raise InvenioWebSearchUnknownCollectionError(cc)
            else:
                cc = CFG_SITE_NAME # cc is not set, so replace it with Home collection

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
        else:
            if coll:
                raise InvenioWebSearchUnknownCollectionError(coll)
    colls = colls_real

    # check if some real collections remain:
    if len(colls)==0:
        colls = [cc]

    # then let us check the list of non-restricted "real" sons of 'cc' and compare it to 'coll':
    res = run_sql("""SELECT c.name FROM collection AS c,
                                        collection_collection AS cc,
                                        collection AS ccc
                     WHERE c.id=cc.id_son AND cc.id_dad=ccc.id
                       AND ccc.name=%s AND cc.type='r'
                       AND c.restricted IS NULL""", (cc,))
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
    x = re_latex_lowercase_a.sub("a", x)
    x = re_latex_lowercase_ae.sub("ae", x)
    x = re_latex_lowercase_e.sub("e", x)
    x = re_latex_lowercase_i.sub("i", x)
    x = re_latex_lowercase_o.sub("o", x)
    x = re_latex_lowercase_u.sub("u", x)
    x = re_latex_lowercase_y.sub("x", x)
    x = re_latex_lowercase_c.sub("c", x)
    x = re_latex_lowercase_n.sub("n", x)
    x = re_latex_uppercase_a.sub("A", x)
    x = re_latex_uppercase_ae.sub("AE", x)
    x = re_latex_uppercase_e.sub("E", x)
    x = re_latex_uppercase_i.sub("I", x)
    x = re_latex_uppercase_o.sub("O", x)
    x = re_latex_uppercase_u.sub("U", x)
    x = re_latex_uppercase_y.sub("Y", x)
    x = re_latex_uppercase_c.sub("C", x)
    x = re_latex_uppercase_n.sub("N", x)

    # convert input into Unicode string:
    try:
        y = unicode(x, "utf-8")
    except:
        return x # something went wrong, probably the input wasn't UTF-8
    # asciify Latin-1 lowercase characters:
    y = re_unicode_lowercase_a.sub("a", y)
    y = re_unicode_lowercase_ae.sub("ae", y)
    y = re_unicode_lowercase_e.sub("e", y)
    y = re_unicode_lowercase_i.sub("i", y)
    y = re_unicode_lowercase_o.sub("o", y)
    y = re_unicode_lowercase_u.sub("u", y)
    y = re_unicode_lowercase_y.sub("y", y)
    y = re_unicode_lowercase_c.sub("c", y)
    y = re_unicode_lowercase_n.sub("n", y)
    # asciify Latin-1 uppercase characters:
    y = re_unicode_uppercase_a.sub("A", y)
    y = re_unicode_uppercase_ae.sub("AE", y)
    y = re_unicode_uppercase_e.sub("E", y)
    y = re_unicode_uppercase_i.sub("I", y)
    y = re_unicode_uppercase_o.sub("O", y)
    y = re_unicode_uppercase_u.sub("U", y)
    y = re_unicode_uppercase_y.sub("Y", y)
    y = re_unicode_uppercase_c.sub("C", y)
    y = re_unicode_uppercase_n.sub("N", y)
    # return UTF-8 representation of the Unicode string:
    return y.encode("utf-8")

def wash_index_term(term, max_char_length=50):
    """
    Return washed form of the index term TERM that would be suitable
    for storing into idxWORD* tables.  I.e., lower the TERM, and
    truncate it safely to MAX_CHAR_LENGTH UTF-8 characters (meaning,
    in principle, 4*MAX_CHAR_LENGTH bytes).

    The function works by an internal conversion of TERM, when needed,
    from its input Python UTF-8 binary string format into Python
    Unicode format, and then truncating it safely to the given number
    of TF-8 characters, without possible mis-truncation in the middle
    of a multi-byte UTF-8 character that could otherwise happen if we
    would have been working with UTF-8 binary representation directly.

    Note that MAX_CHAR_LENGTH corresponds to the length of the term
    column in idxINDEX* tables.
    """
    washed_term = unicode(term, 'utf-8').lower()
    if len(washed_term) <= max_char_length:
        # no need to truncate the term, because it will fit
        # nicely even if it uses four-byte UTF-8 characters
        return washed_term.encode('utf-8')
    else:
        # truncate the term in a safe position:
        return washed_term[:max_char_length].encode('utf-8')

def wash_pattern(p):
    """Wash pattern passed by URL. Check for sanity of the wildcard by
    removing wildcards if they are appended to extremely short words
    (1-3 letters).  TODO: instead of this approximative treatment, it
    will be much better to introduce a temporal limit, e.g. to kill a
    query if it does not finish in 10 seconds."""
    # strip accents:
    # p = strip_accents(p) # FIXME: when available, strip accents all the time
    # add leading/trailing whitespace for the two following wildcard-sanity checking regexps:
    p = " " + p + " "
    # get rid of wildcards at the beginning of words:
    p = re_pattern_wildcards_at_beginning.sub("\\1", p)
    # replace spaces within quotes by __SPACE__ temporarily:
    p = re_pattern_single_quotes.sub(lambda x: "'"+string.replace(x.group(1), ' ', '__SPACE__')+"'", p)
    p = re_pattern_double_quotes.sub(lambda x: "\""+string.replace(x.group(1), ' ', '__SPACE__')+"\"", p)
    p = re_pattern_regexp_quotes.sub(lambda x: "/"+string.replace(x.group(1), ' ', '__SPACE__')+"/", p)
    # get rid of extremely short words (1-3 letters with wildcards):
    p = re_pattern_short_words.sub("\\1", p)
    # replace back __SPACE__ by spaces:
    p = re_pattern_space.sub(" ", p)
    # replace special terms:
    p = re_pattern_today.sub(time.strftime("%Y-%m-%d", time.localtime()), p)
    # remove unnecessary whitespace:
    p = string.strip(p)
    return p

def wash_field(f):
    """Wash field passed by URL."""
    # get rid of unnecessary whitespace:
    f = string.strip(f)
    # wash old-style CDS Invenio/ALEPH 'f' field argument, e.g. replaces 'wau' and 'au' by 'author'
    if CFG_WEBSEARCH_FIELDS_CONVERT.has_key(string.lower(f)):
        f = CFG_WEBSEARCH_FIELDS_CONVERT[f]
    return f

def wash_dates(d1="", d1y=0, d1m=0, d1d=0, d2="", d2y=0, d2m=0, d2d=0):
    """
    Take user-submitted date arguments D1 (full datetime string) or
    (D1Y, D1M, D1Y) year, month, day tuple and D2 or (D2Y, D2M, D2Y)
    and return (YYY1-M1-D2 H1:M1:S2, YYY2-M2-D2 H2:M2:S2) datetime
    strings in the YYYY-MM-DD HH:MM:SS format suitable for time
    restricted searching.

    Note that when both D1 and (D1Y, D1M, D1D) parameters are present,
    the precedence goes to D1.  Ditto for D2*.

    Note that when (D1Y, D1M, D1D) are taken into account, some values
    may be missing and are completed e.g. to 01 or 12 according to
    whether it is the starting or the ending date.
    """
    datetext1, datetext2 =  "", ""
    # sanity checking:
    if d1 == "" and d1y == 0 and d1m == 0 and d1d == 0 and d2 == "" and d2y == 0 and d2m == 0 and d2d == 0:
        return ("", "") # nothing selected, so return empty values
    # wash first (starting) date:
    if d1:
        # full datetime string takes precedence:
        datetext1 = d1
    else:
        # okay, first date passed as (year,month,day):
        if d1y:
            datetext1 += "%04d" % d1y
        else:
            datetext1 += "0000"
        if d1m:
            datetext1 += "-%02d" % d1m
        else:
            datetext1 += "-01"
        if d1d:
            datetext1 += "-%02d" % d1d
        else:
            datetext1 += "-01"
        datetext1 += " 00:00:00"
    # wash second (ending) date:
    if d2:
        # full datetime string takes precedence:
        datetext2 = d2
    else:
        # okay, second date passed as (year,month,day):
        if d2y:
            datetext2 += "%04d" % d2y
        else:
            datetext2 += "9999"
        if d2m:
            datetext2 += "-%02d" % d2m
        else:
            datetext2 += "-12"
        if d2d:
            datetext2 += "-%02d" % d2d
        else:
            datetext2 += "-31" # NOTE: perhaps we should add max(datenumber) in
                               # given month, but for our quering it's not
                               # needed, 31 will always do
        datetext2 += " 00:00:00"
    # okay, return constructed YYYY-MM-DD HH:MM:SS datetexts:
    return (datetext1, datetext2)

def get_colID(c):
    "Return collection ID for collection name C.  Return None if no match found."
    colID = None
    res = run_sql("SELECT id FROM collection WHERE name=%s", (c,), 1)
    if res:
        colID = res[0][0]
    return colID

def get_coll_i18nname(c, ln=CFG_SITE_LANG):
    """Return nicely formatted collection name (of name type 'ln',
    'long name') for collection C in language LN."""
    global collection_i18nname_cache
    global collection_i18nname_cache_timestamp
    # firstly, check whether the collectionname table was modified:
    if get_table_update_time('collectionname') > collection_i18nname_cache_timestamp:
        # yes it was, cache clear-up needed:
        collection_i18nname_cache = create_collection_i18nname_cache()
    # secondly, read i18n name from either the cache or return common name:
    out = c
    try:
        out = collection_i18nname_cache[c][ln]
    except KeyError:
        pass # translation in LN does not exist
    return out

def get_field_i18nname(f, ln=CFG_SITE_LANG):
    """Return nicely formatted field name (of type 'ln', 'long name')
       for field F in language LN."""
    global field_i18nname_cache
    global field_i18nname_cache_timestamp
    # firstly, check whether the fieldname table was modified:
    if get_table_update_time('fieldname') > field_i18nname_cache_timestamp:
        # yes it was, cache clear-up needed:
        field_i18nname_cache = create_field_i18nname_cache()
    # secondly, read i18n name from either the cache or return common name:
    out = f
    try:
        out = field_i18nname_cache[f][ln]
    except KeyError:
        pass # translation in LN does not exist
    return out

def get_coll_ancestors(coll):
    "Returns a list of ancestors for collection 'coll'."
    coll_ancestors = []
    coll_ancestor = coll
    while 1:
        res = run_sql("""SELECT c.name FROM collection AS c
                          LEFT JOIN collection_collection AS cc ON c.id=cc.id_dad
                          LEFT JOIN collection AS ccc ON ccc.id=cc.id_son
                          WHERE ccc.name=%s ORDER BY cc.id_dad ASC LIMIT 1""",
                      (coll_ancestor,))
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
            "WHERE cc.type=%s AND ccc.name=%s"
    if public_only:
        query += " AND c.restricted IS NULL "
    query += " ORDER BY cc.score DESC"
    res = run_sql(query, (type, coll))
    for name in res:
        coll_sons.append(name[0])
    return coll_sons

def get_coll_real_descendants(coll):
    """Return a list of all descendants of collection 'coll' that are defined by a 'dbquery'.
       IOW, we need to decompose compound collections like "A & B" into "A" and "B" provided
       that "A & B" has no associated database query defined.
    """
    coll_sons = []
    res = run_sql("""SELECT c.name,c.dbquery FROM collection AS c
                     LEFT JOIN collection_collection AS cc ON c.id=cc.id_son
                     LEFT JOIN collection AS ccc ON ccc.id=cc.id_dad
                     WHERE ccc.name=%s ORDER BY cc.score DESC""",
                  (coll,))
    for name, dbquery in res:
        if dbquery: # this is 'real' collection, so return it:
            coll_sons.append(name)
        else: # this is 'composed' collection, so recurse:
            coll_sons.extend(get_coll_real_descendants(name))
    return coll_sons

def get_collection_reclist(coll):
    """Return hitset of recIDs that belong to the collection 'coll'.
       But firstly check the last updated date of the collection table.
       If it's newer than the cache timestamp, then empty the cache,
       since new records could have been added."""
    global collection_reclist_cache
    global collection_reclist_cache_timestamp
    # firstly, check whether the collection table was modified:
    if get_table_update_time('collection') > collection_reclist_cache_timestamp:
        # yes it was, cache clear-up needed:
        collection_reclist_cache = create_collection_reclist_cache()
    # secondly, read reclist from either the cache or the database:
    if not collection_reclist_cache[coll]:
        # not yet it the cache, so calculate it and fill the cache:
        query = "SELECT nbrecs,reclist FROM collection WHERE name='%s'" % coll
        res = run_sql(query, None, 1)
        if res:
            try:
                set = HitSet(res[0][1])
            except:
                set = HitSet()
        collection_reclist_cache[coll] = set
    # finally, return reclist:
    return collection_reclist_cache[coll]

def coll_restricted_p(coll):
    "Predicate to test if the collection coll is restricted or not."
    if not coll:
        return 0
    res = run_sql("SELECT restricted FROM collection WHERE name=%s", (coll,))
    if res and res[0][0] is not None:
        return 1
    else:
        return 0

def coll_restricted_group(coll):
    "Return Apache group to which the collection is restricted.  Return None if it's public."
    if not coll:
        return None
    res = run_sql("SELECT restricted FROM collection WHERE name=%s", (coll,))
    if res:
        return res[0][0]
    else:
        return None

def create_collection_reclist_cache():
    """Creates list of records belonging to collections.  Called on startup
    and used later for intersecting search results with collection universe."""
    global collection_reclist_cache_timestamp
    # populate collection reclist cache:
    collrecs = {}
    try:
        res = run_sql("SELECT name,reclist FROM collection")
    except Error:
        # database problems, set timestamp to zero and return empty cache
        collection_reclist_cache_timestamp = 0
        return collrecs
    for name, reclist in res:
        collrecs[name] = None # this will be filled later during runtime by calling get_collection_reclist(coll)
    # update timestamp:
    try:
        collection_reclist_cache_timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    except NameError:
        collection_reclist_cache_timestamp = 0
    return collrecs

try:
    collection_reclist_cache.has_key(CFG_SITE_NAME)
except:
    try:
        collection_reclist_cache = create_collection_reclist_cache()
    except:
        collection_reclist_cache = {}

def create_collection_i18nname_cache():
    """Create cache of I18N collection names of type 'ln' (=long name).
    Called on startup and used later during the search time."""
    global collection_i18nname_cache_timestamp
    # populate collection I18N name cache:
    names = {}
    try:
        res = run_sql("SELECT c.name,cn.ln,cn.value FROM collectionname AS cn, collection AS c WHERE cn.id_collection=c.id AND cn.type='ln'") # ln=long name
    except Error:
        # database problems, set timestamp to zero and return empty cache
        collection_i18nname_cache_timestamp = 0
        return names
    for c, ln, i18nname in res:
        if i18nname:
            if not names.has_key(c):
                names[c] = {}
            names[c][ln] = i18nname
    # update timestamp:
    try:
        collection_i18nname_cache_timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    except NameError:
        collection_i18nname_cache_timestamp = 0
    return names

try:
    collection_i18nname_cache.has_key(CFG_SITE_NAME)
except:
    try:
        collection_i18nname_cache = create_collection_i18nname_cache()
    except:
        collection_i18nname_cache = {}

def create_field_i18nname_cache():
    """Create cache of I18N field names of type 'ln' (=long name).
    Called on startup and used later during the search time."""
    global field_i18nname_cache_timestamp
    # populate field I18 name cache:
    names = {}
    try:
        res = run_sql("SELECT f.name,fn.ln,fn.value FROM fieldname AS fn, field AS f WHERE fn.id_field=f.id AND fn.type='ln'") # ln=long name
    except Error:
        # database problems, set timestamp to zero and return empty cache
        field_i18nname_cache_timestamp = 0
        return names
    for f, ln, i18nname in res:
        if i18nname:
            if not names.has_key(f):
                names[f] = {}
            names[f][ln] = i18nname
    # update timestamp:
    try:
        field_i18nname_cache_timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    except NameError:
        field_i18nname_cache_timestamp = 0
    return names

try:
    field_i18nname_cache.has_key(CFG_SITE_NAME)
except:
    try:
        field_i18nname_cache = create_field_i18nname_cache()
    except:
        field_i18nname_cache = {}

def browse_pattern(req, colls, p, f, rg, ln=CFG_SITE_LANG):
    """Browse either biliographic phrases or words indexes, and display it."""

    # load the right message language
    _ = gettext_set_language(ln)

    ## do we search in words indexes?
    if not f:
        return browse_in_bibwords(req, p, f)

    ## is p enclosed in quotes? (coming from exact search)
    if p.startswith('"') and p.endswith('"'):
        p = p[1:-1]

    p_orig = p
    ## okay, "real browse" follows:
    browsed_phrases = get_nearest_terms_in_bibxxx(p, f, rg, 1)
    while not browsed_phrases:
        # try again and again with shorter and shorter pattern:
        try:
            p = p[:-1]
            browsed_phrases = get_nearest_terms_in_bibxxx(p, f, rg, 1)
        except:
            # probably there are no hits at all:
            req.write(_("No values found."))
            return

    ## try to check hits in these particular collection selection:
    browsed_phrases_in_colls = []
    if 0:
        for phrase in browsed_phrases:
            phrase_hitset = HitSet()
            phrase_hitsets = search_pattern("", phrase, f, 'e')
            for coll in colls:
                phrase_hitset.union_update(phrase_hitsets[coll])
            if len(phrase_hitset) > 0:
                # okay, this phrase has some hits in colls, so add it:
                browsed_phrases_in_colls.append([phrase, len(phrase_hitset)])

    ## were there hits in collections?
    if browsed_phrases_in_colls == []:
        if browsed_phrases != []:
            #print_warning(req, """<p>No match close to <em>%s</em> found in given collections.
            #Please try different term.<p>Displaying matches in any collection...""" % p_orig)
            ## try to get nbhits for these phrases in any collection:
            for phrase in browsed_phrases:
                browsed_phrases_in_colls.append([phrase, get_nbhits_in_bibxxx(phrase, f)])

    ## display results now:
    out = websearch_templates.tmpl_browse_pattern(
            f=f,
            fn=get_field_i18nname(f, ln),
            ln=ln,
            browsed_phrases_in_colls=browsed_phrases_in_colls,
            colls=colls,
          )
    req.write(out)
    return

def browse_in_bibwords(req, p, f, ln=CFG_SITE_LANG):
    """Browse inside words indexes."""
    if not p:
        return
    _ = gettext_set_language(ln)

    urlargd = {}
    urlargd.update(req.argd)
    urlargd['action'] = 'search'

    nearest_box = create_nearest_terms_box(urlargd, p, f, 'w', ln=ln, intro_text_p=0)

    req.write(websearch_templates.tmpl_search_in_bibwords(
        p = p,
        f = f,
        ln = ln,
        nearest_box = nearest_box
    ))
    return


def search_special_fields(bsu_p, bsu_f, bsu_m):
    """Stuff that actually cannot be found from just one record goes here.
       Example: give records that have been cited 200 times: cites=200"""
    if bsu_f == "cited":
        #search.. bsu_p will look like "200" or "0->9"
        numstr = "\""+bsu_p+"\""
        #this is sort of stupid but since we may need to
        #get the records that do _not_ have cites, we have to
        #know the ids of all records, too
        #but this is needed only if bsu_p is 0 or 0 or 0->0
        allrecs = []
        if bsu_p == 0 or bsu_p == "0" or \
                bsu_p.startswith("0->") or bsu_p.endswith("->0"):
            allrecs = perform_request_search(of="id")
        x = get_records_with_num_cites(numstr, allrecs)
        return HitSet(x)
    return HitSet([])

def search_pattern(req=None, p=None, f=None, m=None, ap=0, of="id", verbose=0, ln=CFG_SITE_LANG):
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
        if not basic_search_unit_hitset:
            #stuff like "search by number of citations" i.e. cites>500 or such goes here
            basic_search_unit_hitset = search_special_fields(bsu_p, bsu_f, bsu_m)
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

def search_pattern_parenthesised(req=None, p=None, f=None, m=None, ap=0, of="id", verbose=0, ln=CFG_SITE_LANG):
    """Search for complex pattern 'p' containing parenthesis within field 'f' according to
       matching type 'm'.  Return hitset of recIDs.

       For more details on the parameters see 'search_pattern'
    """
    # Try searching with parentheses
    try:
        parser = SearchQueryParenthesisedParser()

        # get a hitset with all recids
        result_hitset = get_collection_reclist(CFG_SITE_NAME)

        # parse the query. The result is list of [op1, expr1, op2, expr2, ..., opN, exprN]
        parsing_result = parser.parse_query(p)

        # go through every pattern
        # calculate hitset for it
        # combine pattern's hitset with the result using the corresponding operator
        for index in xrange(0, len(parsing_result)-1, 2 ):
            current_operator = parsing_result[index]
            current_pattern = parsing_result[index+1]

            # obtain a hitset for the current patter
            current_hitset = search_pattern(req, current_pattern, f, m, ap, of, verbose, ln)

            # combine the current hitset with resulting hitset using the current operator
            if current_operator == '+':
                result_hitset = result_hitset & current_hitset
            elif current_operator == '-':
                result_hitset = result_hitset - current_hitset
            elif current_operator == '|':
                result_hitset = result_hitset | current_hitset
            else:
                assert False, "Unknown operator in search_pattern_parenthesised()"

        return result_hitset

    # If searching with parenteses fails, perform search ignoring parentheses
    except InvenioWebSearchQueryParserException:

        print_warning(req, "Nested or mismatched parethneses. Continue search ignoring paretheses.")

        # remove the parentheses in the query. Current implementation removes all the parentheses,
        # but it could be improved to romove only these that are not insede quotes
        p = p.replace('(', ' ')
        p = p.replace(')', ' ')

        return search_pattern(req, p, f, m, ap, of, verbose, ln)

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

def intersect_results_with_collrecs(req, hitset_in_any_collection, colls, ap=0, of="hb", verbose=0, ln=CFG_SITE_LANG):
    """Return dict of hitsets given by intersection of hitset with the collection universes."""
    _ = gettext_set_language(ln)

    # search stage 4: intersect with the collection universe:
    if verbose and of.startswith("h"):
        t1 = os.times()[4]
    results = {}
    results_nbhits = 0
    for coll in colls:
        results[coll] = hitset_in_any_collection & get_collection_reclist(coll)
        results_nbhits += len(results[coll])
    if results_nbhits == 0:
        # no hits found, try to search in Home:
        results_in_Home = hitset_in_any_collection & get_collection_reclist(CFG_SITE_NAME)
        if len(results_in_Home) > 0:
            # some hits found in Home, so propose this search:
            if of.startswith("h"):
                url = websearch_templates.build_search_url(req.argd, cc=CFG_SITE_NAME, c=[])
                print_warning(req, _("No match found in collection %(x_collection)s. Other public collections gave %(x_url_open)s%(x_nb_hits)d hits%(x_url_close)s.") %\
                              {'x_collection': '<em>' + string.join([get_coll_i18nname(coll, ln) for coll in colls], ', ') + '</em>',
                               'x_url_open': '<a class="nearestterms" href="%s">' % (url),
                               'x_nb_hits': len(results_in_Home),
                               'x_url_close': '</a>'})
            results = {}
        else:
            # no hits found in Home, recommend different search terms:
            if of.startswith("h"):
                print_warning(req, _("No public collection matched your query. "
                                     "If you were looking for a non-public document, please choose "
                                     "the desired restricted collection first."))
            results = {}
    if verbose and of.startswith("h"):
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
        results[coll].intersection_update(hitset)
        nb_total += len(results[coll])
    if nb_total == 0:
        if of.startswith("h"):
            print_warning(req, aptext)
        results = results_ap
    return results

def create_similarly_named_authors_link_box(author_name, ln=CFG_SITE_LANG):
    """Return a box similar to ``Not satisfied...'' one by proposing
       author searches for similar names.  Namely, take AUTHOR_NAME
       and the first initial of the firstame (after comma) and look
       into author index whether authors with e.g. middle names exist.
       Useful mainly for CERN Library that sometimes contains name
       forms like Ellis-N, Ellis-Nick, Ellis-Nicolas all denoting the
       same person.  The box isn't proposed if no similarly named
       authors are found to exist.
    """
    # return nothing if not configured:
    if CFG_WEBSEARCH_CREATE_SIMILARLY_NAMED_AUTHORS_LINK_BOX == 0:
        return ""
    # return empty box if there is no initial:
    if re.match(r'[^ ,]+, [^ ]', author_name) is None:
        return ""
    # firstly find name comma initial:
    author_name_to_search = re.sub(r'^([^ ,]+, +[^ ,]).*$', '\\1', author_name)

    # secondly search for similar name forms:
    similar_author_names = {}
    for name in author_name_to_search, strip_accents(author_name_to_search):
        for tag in get_field_tags("author"):
            # deduce into which bibxxx table we will search:
            digit1, digit2 = int(tag[0]), int(tag[1])
            bx = "bib%d%dx" % (digit1, digit2)
            bibx = "bibrec_bib%d%dx" % (digit1, digit2)
            if len(tag) != 6 or tag[-1:]=='%':
                # only the beginning of field 't' is defined, so add wildcard character:
                res = run_sql("""SELECT bx.value FROM %s AS bx
                                  WHERE bx.value LIKE %%s AND bx.tag LIKE %%s""" % bx,
                              (name + "%", tag + "%"))
            else:
                res = run_sql("""SELECT bx.value FROM %s AS bx
                                  WHERE bx.value LIKE %%s AND bx.tag=%%s""" % bx,
                              (name + "%", tag))
            for row in res:
                similar_author_names[row[0]] = 1
    # remove the original name and sort the list:
    try:
        del similar_author_names[author_name]
    except KeyError:
        pass
    # thirdly print the box:
    out = ""
    if similar_author_names:
        out_authors = similar_author_names.keys()
        out_authors.sort()

        tmp_authors = []
        for out_author in out_authors:
            nbhits = get_nbhits_in_bibxxx(out_author, "author")
            if nbhits:
                tmp_authors.append((out_author, nbhits))
        out += websearch_templates.tmpl_similar_author_names(
                 authors=tmp_authors, ln=ln)

    return out

def create_nearest_terms_box(urlargd, p, f, t='w', n=5, ln=CFG_SITE_LANG, intro_text_p=True):
    """Return text box containing list of 'n' nearest terms above/below 'p'
       for the field 'f' for matching type 't' (words/phrases) in
       language 'ln'.
       Propose new searches according to `urlargs' with the new words.
       If `intro_text_p' is true, then display the introductory message,
       otherwise print only the nearest terms in the box content.
    """
    # load the right message language
    _ = gettext_set_language(ln)

    out = ""
    nearest_terms = []
    if not p: # sanity check
        p = "."
    # look for nearest terms:
    if t == 'w':
        nearest_terms = get_nearest_terms_in_bibwords(p, f, n, n)
        if not nearest_terms:
            return "%s %s." % (_("No words index available for"), get_field_i18nname(f, ln))
    else:
        nearest_terms = get_nearest_terms_in_bibxxx(p, f, n, n)
        if not nearest_terms:
            return "%s %s." % (_("No phrase index available for"), get_field_i18nname(f, ln))

    terminfo = []
    for term in nearest_terms:
        if t == 'w':
            hits = get_nbhits_in_bibwords(term, f)
        else:
            hits = get_nbhits_in_bibxxx(term, f)

        argd = {}
        argd.update(urlargd)

        # check which fields contained the requested parameter, and replace it.
        for (px, fx) in ('p', 'f'), ('p1', 'f1'), ('p2', 'f2'), ('p3', 'f3'):
            if px in argd:
                if f == argd[fx] or f == "anyfield" or f == "":
                    if string.find(argd[px], p) > -1:
                        argd[px] = string.replace(argd[px], p, term)
                        break
                else:
                    if string.find(argd[px], f+':'+p) > -1:
                        argd[px] = string.replace(argd[px], f+':'+p, f+':'+term)
                        break
                    elif string.find(argd[px], f+':"'+p+'"') > -1:
                        argd[px] = string.replace(argd[px], f+':"'+p+'"', f+':"'+term+'"')
                        break

        terminfo.append((term, hits, argd))

    intro = ""
    if intro_text_p: # add full leading introductory text
        if f:
            intro = _("Search term %(x_term)s inside index %(x_index)s did not match any record. Nearest terms in any collection are:") % \
                     {'x_term': "<em>" + cgi.escape(p.startswith("%") and p.endswith("%") and p[1:-1] or p) + "</em>",
                      'x_index': "<em>" + cgi.escape(get_field_i18nname(f, ln)) + "</em>"}
        else:
            intro = _("Search term %s did not match any record. Nearest terms in any collection are:") % \
                     ("<em>" + cgi.escape(p.startswith("%") and p.endswith("%") and p[1:-1] or p) + "</em>")

    return websearch_templates.tmpl_nearest_term_box(p=p, ln=ln, f=f, terminfo=terminfo,
                                                     intro=intro)

def get_nearest_terms_in_bibwords(p, f, n_below, n_above):
    """Return list of +n -n nearest terms to word `p' in index for field `f'."""
    nearest_words = [] # will hold the (sorted) list of nearest words to return
    # deduce into which bibwordsX table we will search:
    bibwordsX = "idxWORD%02dF" % get_index_id_from_field("anyfield")
    if f:
        index_id = get_index_id_from_field(f)
        if index_id:
            bibwordsX = "idxWORD%02dF" % index_id
        else:
            return nearest_words
    # firstly try to get `n' closest words above `p':
    res = run_sql("SELECT term FROM %s WHERE term<%%s ORDER BY term DESC LIMIT %%s" % bibwordsX,
                  (p, n_above))
    for row in res:
        nearest_words.append(row[0])
    nearest_words.reverse()
    # secondly insert given word `p':
    nearest_words.append(p)
    # finally try to get `n' closest words below `p':
    res = run_sql("SELECT term FROM %s WHERE term>%%s ORDER BY term ASC LIMIT %%s" % bibwordsX,
                  (p, n_below))
    for row in res:
        nearest_words.append(row[0])
    return nearest_words

def get_nearest_terms_in_bibxxx(p, f, n_below, n_above):
    """Browse (-n_above, +n_below) closest bibliographic phrases
       for the given pattern p in the given field f, regardless
       of collection.
       Return list of [phrase1, phrase2, ... , phrase_n]."""
    ## determine browse field:
    if not f and string.find(p, ":") > 0: # does 'p' contain ':'?
        f, p = string.split(p, ":", 1)
    ## We are going to take max(n_below, n_above) as the number of
    ## values to ferch from bibXXx.  This is needed to work around
    ## MySQL UTF-8 sorting troubles in 4.0.x.  Proper solution is to
    ## use MySQL 4.1.x or our own idxPHRASE in the future.
    n_fetch = 2*max(n_below, n_above)
    ## construct 'tl' which defines the tag list (MARC tags) to search in:
    tl = []
    if str(f[0]).isdigit() and str(f[1]).isdigit():
        tl.append(f) # 'f' seems to be okay as it starts by two digits
    else:
        # deduce desired MARC tags on the basis of chosen 'f'
        tl = get_field_tags(f)
    ## start browsing to fetch list of hits:
    browsed_phrases = {} # will hold {phrase1: 1, phrase2: 1, ..., phraseN: 1} dict of browsed phrases (to make them unique)
    # always add self to the results set:
    browsed_phrases[p.startswith("%") and p.endswith("%") and p[1:-1] or p] = 1
    for t in tl:
        # deduce into which bibxxx table we will search:
        digit1, digit2 = int(t[0]), int(t[1])
        bx = "bib%d%dx" % (digit1, digit2)
        bibx = "bibrec_bib%d%dx" % (digit1, digit2)
        # firstly try to get `n' closest phrases above `p':
        if len(t) != 6 or t[-1:]=='%': # only the beginning of field 't' is defined, so add wildcard character:
            res = run_sql("""SELECT bx.value FROM %s AS bx
                              WHERE bx.value<%%s AND bx.tag LIKE %%s
                              ORDER BY bx.value DESC LIMIT %%s""" % bx,
                          (p, t + "%", n_fetch))
        else:
            res = run_sql("""SELECT bx.value FROM %s AS bx
                              WHERE bx.value<%%s AND bx.tag=%%s
                              ORDER BY bx.value DESC LIMIT %%s""" % bx,
                          (p, t, n_fetch))
        for row in res:
            browsed_phrases[row[0]] = 1
        # secondly try to get `n' closest phrases equal to or below `p':
        if len(t) != 6 or t[-1:]=='%': # only the beginning of field 't' is defined, so add wildcard character:
            res = run_sql("""SELECT bx.value FROM %s AS bx
                              WHERE bx.value>=%%s AND bx.tag LIKE %%s
                              ORDER BY bx.value ASC LIMIT %%s""" % bx,
                          (p, t + "%", n_fetch))
        else:
            res = run_sql("""SELECT bx.value FROM %s AS bx
                              WHERE bx.value>=%%s AND bx.tag=%%s
                              ORDER BY bx.value ASC LIMIT %%s""" % bx,
                          (p, t, n_fetch))
        for row in res:
            browsed_phrases[row[0]] = 1
    # select first n words only: (this is needed as we were searching
    # in many different tables and so aren't sure we have more than n
    # words right; this of course won't be needed when we shall have
    # one ACC table only for given field):
    phrases_out = browsed_phrases.keys()
    phrases_out.sort(lambda x, y: cmp(string.lower(strip_accents(x)),
                                      string.lower(strip_accents(y))))
    # find position of self:
    try:
        idx_p = phrases_out.index(p)
    except:
        idx_p = len(phrases_out)/2
    # return n_above and n_below:
    return phrases_out[max(0, idx_p-n_above):idx_p+n_below]

def get_nbhits_in_bibwords(word, f):
    """Return number of hits for word 'word' inside words index for field 'f'."""
    out = 0
    # deduce into which bibwordsX table we will search:
    bibwordsX = "idxWORD%02dF" % get_index_id_from_field("anyfield")
    if f:
        index_id = get_index_id_from_field(f)
        if index_id:
            bibwordsX = "idxWORD%02dF" % index_id
        else:
            return 0
    if word:
        res = run_sql("SELECT hitlist FROM %s WHERE term=%%s" % bibwordsX,
                      (word,))
        for hitlist in res:
            out += len(HitSet(hitlist[0]))
    return out

def get_nbhits_in_bibxxx(p, f):
    """Return number of hits for word 'word' inside words index for field 'f'."""
    ## determine browse field:
    if not f and string.find(p, ":") > 0: # does 'p' contain ':'?
        f, p = string.split(p, ":", 1)
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
            res = run_sql("""SELECT bibx.id_bibrec FROM %s AS bibx, %s AS bx
                              WHERE bx.value=%%s AND bx.tag LIKE %%s
                                AND bibx.id_bibxxx=bx.id""" % (bibx, bx),
                          (p, t + "%"))
        else:
            res = run_sql("""SELECT bibx.id_bibrec FROM %s AS bibx, %s AS bx
                              WHERE bx.value=%%s AND bx.tag=%%s
                                AND bibx.id_bibxxx=bx.id""" % (bibx, bx),
                          (p, t))
        for row in res:
            recIDs[row[0]] = 1
    return len(recIDs)

def get_mysql_recid_from_aleph_sysno(sysno):
    """Returns DB's recID for ALEPH sysno passed in the argument (e.g. "002379334CER").
       Returns None in case of failure."""
    out = None
    res = run_sql("""SELECT bb.id_bibrec FROM bibrec_bib97x AS bb, bib97x AS b
                      WHERE b.value=%s AND b.tag='970__a' AND bb.id_bibxxx=b.id""",
                  (sysno,))
    if res:
        out = res[0][0]
    return out

def guess_primary_collection_of_a_record(recID):
    """Return primary collection name a record recid belongs to, by testing 980 identifier.
       May lead to bad guesses when a collection is defined dynamically bia dbquery.
       In that case, return 'CFG_SITE_NAME'."""
    out = CFG_SITE_NAME
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
                WHERE f.code=%s AND ft.id_field=f.id AND t.id=ft.id_tag
                ORDER BY ft.score DESC"""
    res = run_sql(query, (field, ))
    for val in res:
        out.append(val[0])
    return out

def get_fieldvalues(recID, tag):
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

def get_fieldvalues_alephseq_like(recID, tags_in):
    """Return buffer of ALEPH sequential-like textual format with fields found in the list TAGS_IN for record RECID."""
    out = ""
    if type(tags_in) is not list:
        tags_in = [tags_in,]
    if len(tags_in) == 1 and len(tags_in[0]) == 6:
        ## case A: one concrete subfield asked, so print its value if found
        ##         (use with care: can false you if field has multiple occurrences)
        out += string.join(get_fieldvalues(recID, tags_in[0]),"\n")
    else:
        ## case B: print our "text MARC" format; works safely all the time
        # find out which tags to output:
        dict_of_tags_out = {}
        if not tags_in:
            for i in range(0, 10):
                for j in range(0, 10):
                    dict_of_tags_out["%d%d%%" % (i, j)] = 1
        else:
            for tag in tags_in:
                if len(tag) == 0:
                    for i in range(0, 10):
                        for j in range(0, 10):
                            dict_of_tags_out["%d%d%%" % (i, j)] = 1
                elif len(tag) == 1:
                    for j in range(0, 10):
                        dict_of_tags_out["%s%d%%" % (tag, j)] = 1
                elif len(tag) < 5:
                    dict_of_tags_out["%s%%" % tag] = 1
                elif tag >= 6:
                    dict_of_tags_out[tag[0:5]] = 1
        tags_out = dict_of_tags_out.keys()
        tags_out.sort()
        # search all bibXXx tables as needed:
        for tag in tags_out:
            digits = tag[0:2]
            try:
                intdigits = int(digits)
                if intdigits < 0 or intdigits > 99:
                    raise ValueError
            except ValueError:
                # invalid tag value asked for
                continue
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
                if field[0:2] == "00" and field[-1:] == "_":
                    out += value
                else:
                    out += "$$%s%s" % (field[-1:], value)
    return out

def record_exists(recID):
    """Return 1 if record RECID exists.
       Return 0 if it doesn't exist.
       Return -1 if it exists but is marked as deleted."""
    out = 0
    query = "SELECT id FROM bibrec WHERE id='%s'" % recID
    res = run_sql(query, None, 1)
    if res:
        # record exists; now check whether it isn't marked as deleted:
        dbcollids = get_fieldvalues(recID, "980__%")
        if ("DELETED" in dbcollids) or (CFG_CERN_SITE and "DUMMY" in dbcollids):
            out = -1 # exists, but marked as deleted
        else:
            out = 1 # exists fine
    return out

def record_public_p(recID):
    """Return 1 if the record is public, i.e. if it can be found in the Home collection.
       Return 0 otherwise.
    """
    return recID in get_collection_reclist(CFG_SITE_NAME)

def get_creation_date(recID, fmt="%Y-%m-%d"):
    "Returns the creation date of the record 'recID'."
    out = ""
    res = run_sql("SELECT DATE_FORMAT(creation_date,%s) FROM bibrec WHERE id=%s", (fmt, recID), 1)
    if res:
        out = res[0][0]
    return out

def get_modification_date(recID, fmt="%Y-%m-%d"):
    "Returns the date of last modification for the record 'recID'."
    out = ""
    res = run_sql("SELECT DATE_FORMAT(modification_date,%s) FROM bibrec WHERE id=%s", (fmt, recID), 1)
    if res:
        out = res[0][0]
    return out

def print_warning(req, msg, type='', prologue='<br />', epilogue='<br />'):
    "Prints warning message and flushes output."
    if req and msg:
        req.write(websearch_templates.tmpl_print_warning(
                   msg = msg,
                   type = type,
                   prologue = prologue,
                   epilogue = epilogue,
                 ))
        return

def print_search_info(p, f, sf, so, sp, rm, of, ot, collection=CFG_SITE_NAME, nb_found=-1, jrec=1, rg=10,
                      as=0, ln=CFG_SITE_LANG, p1="", p2="", p3="", f1="", f2="", f3="", m1="", m2="", m3="", op1="", op2="",
                      sc=1, pl_in_url="",
                      d1y=0, d1m=0, d1d=0, d2y=0, d2m=0, d2d=0, dt="",
                      cpu_time=-1, middle_only=0):
    """Prints stripe with the information on 'collection' and 'nb_found' results and CPU time.
       Also, prints navigation links (beg/next/prev/end) inside the results set.
       If middle_only is set to 1, it will only print the middle box information (beg/netx/prev/end/etc) links.
       This is suitable for displaying navigation links at the bottom of the search results page."""

    out = ""

    # sanity check:
    if jrec < 1:
        jrec = 1
    if jrec > nb_found:
        jrec = max(nb_found-rg+1, 1)

    return websearch_templates.tmpl_print_search_info(
             ln = ln,
             collection = collection,
             as = as,
             collection_name = get_coll_i18nname(collection, ln),
             collection_id = get_colID(collection),
             middle_only = middle_only,
             rg = rg,
             nb_found = nb_found,
             sf = sf,
             so = so,
             rm = rm,
             of = of,
             ot = ot,
             p = p,
             f = f,
             p1 = p1,
             p2 = p2,
             p3 = p3,
             f1 = f1,
             f2 = f2,
             f3 = f3,
             m1 = m1,
             m2 = m2,
             m3 = m3,
             op1 = op1,
             op2 = op2,
             pl_in_url = pl_in_url,
             d1y = d1y,
             d1m = d1m,
             d1d = d1d,
             d2y = d2y,
             d2m = d2m,
             d2d = d2d,
             dt = dt,
             jrec = jrec,
             sc = sc,
             sp = sp,
             all_fieldcodes = get_fieldcodes(),
             cpu_time = cpu_time,
           )

def print_results_overview(req, colls, results_final_nb_total, results_final_nb, cpu_time, ln=CFG_SITE_LANG, ec=[]):
    """Prints results overview box with links to particular collections below."""

    out = ""
    new_colls = []
    for coll in colls:
        new_colls.append({
                          'id': get_colID(coll),
                          'code': coll,
                          'name': get_coll_i18nname(coll, ln),
                         })

    return websearch_templates.tmpl_print_results_overview(
             ln = ln,
             results_final_nb_total = results_final_nb_total,
             results_final_nb = results_final_nb,
             cpu_time = cpu_time,
             colls = new_colls,
             ec = ec,
           )

def sort_records(req, recIDs, sort_field='', sort_order='d', sort_pattern='', verbose=0, of='hb', ln=CFG_SITE_LANG):
    """Sort records in 'recIDs' list according sort field 'sort_field' in order 'sort_order'.
       If more than one instance of 'sort_field' is found for a given record, try to choose that that is given by
       'sort pattern', for example "sort by report number that starts by CERN-PS".
       Note that 'sort_field' can be field code like 'author' or MARC tag like '100__a' directly."""

    _ = gettext_set_language(ln)

    ## check arguments:
    if not sort_field:
        return recIDs
    if len(recIDs) > CFG_WEBSEARCH_NB_RECORDS_TO_SORT:
        if of.startswith('h'):
            print_warning(req, _("Sorry, sorting is allowed on sets of up to %d records only. Using default sort order.") % CFG_WEBSEARCH_NB_RECORDS_TO_SORT, "Warning")
        return recIDs

    sort_fields = string.split(sort_field, ",")
    recIDs_dict = {}
    recIDs_out = []

    ## first deduce sorting MARC tag out of the 'sort_field' argument:
    tags = []
    for sort_field in sort_fields:
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
                if of.startswith('h'):
                    print_warning(req, _("Sorry, %s does not seem to be a valid sort option. Choosing title sort instead.") % sort_field, "Error")
                tags.append("245__a")
    if verbose >= 3:
        print_warning(req, "Sorting by tags %s." % tags)
        if sort_pattern:
            print_warning(req, "Sorting preferentially by %s." % sort_pattern)

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
                    if v.lower().startswith(sort_pattern.lower()): # bingo!
                        bingo = 1
                        val = v
                        break
                if not bingo: # sort_pattern not present, so add other vals after spaces
                    val = sort_pattern + "          " + string.join(vals)
            else:
                # no sort pattern defined, so join them all together
                val = string.join(vals)
            val = strip_accents(val.lower()) # sort values regardless of accents and case
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

def print_records(req, recIDs, jrec=1, rg=10, format='hb', ot='', ln=CFG_SITE_LANG, relevances=[], relevances_prologue="(", relevances_epilogue="%%)", decompress=zlib.decompress, search_pattern='', print_records_prologue_p=True, print_records_epilogue_p=True, verbose=0, tab=''):

    """
    Prints list of records 'recIDs' formatted according to 'format' in
    groups of 'rg' starting from 'jrec'.

    Assumes that the input list 'recIDs' is sorted in reverse order,
    so it counts records from tail to head.

    A value of 'rg=-9999' means to print all records: to be used with care.

    Print also list of RELEVANCES for each record (if defined), in
    between RELEVANCE_PROLOGUE and RELEVANCE_EPILOGUE.

    Print prologue and/or epilogue specific to 'format' if
    'print_records_prologue_p' and/or print_records_epilogue_p' are
    True.
    """

    # load the right message language
    _ = gettext_set_language(ln)

    # sanity checking:
    if req is None:
        return

    # get user_info (for formatting based on user)
    user_info = collect_user_info(req)

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

            # print header if needed
            if print_records_prologue_p:
                print_records_prologue(req, format)

            # print records
            recIDs_to_print = [recIDs[x] for x in range(irec_max, irec_min, -1)]
            format_records(recIDs_to_print,
                           format,
                           ln=ln,
                           search_pattern=search_pattern,
                           record_separator="\n",
                           user_info=user_info,
                           req=req)
            # print footer if needed
            if print_records_epilogue_p:
                print_records_epilogue(req, format)

        elif format.startswith('t') or str(format[0:3]).isdigit():
            # we are doing plain text output:
            for irec in range(irec_max, irec_min, -1):
                x = print_record(recIDs[irec], format, ot, ln, search_pattern=search_pattern,
                                 user_info=user_info, verbose=verbose)
                req.write(x)
                if x:
                    req.write('\n')
        elif format == 'excel':
            recIDs_to_print = [recIDs[x] for x in range(irec_max, irec_min, -1)]
            create_excel(recIDs=recIDs_to_print, req=req, ln=ln)
        else:
            # we are doing HTML output:
            if format == 'hp' or format.startswith("hb_") or format.startswith("hd_"):
                # portfolio and on-the-fly formats:
                for irec in range(irec_max, irec_min, -1):
                    req.write(print_record(recIDs[irec], format, ot, ln, search_pattern=search_pattern,
                                           user_info=user_info, verbose=verbose))
            elif format.startswith("hb"):
                # HTML brief format:
                req.write(websearch_templates.tmpl_record_format_htmlbrief_header(
                    ln = ln))
                for irec in range(irec_max, irec_min, -1):
                    row_number = jrec+irec_max-irec
                    recid = recIDs[irec]
                    if relevances and relevances[irec]:
                        relevance = relevances[irec]
                    else:
                        relevance = ''
                    record = print_record(recIDs[irec], format, ot, ln, search_pattern=search_pattern,
                                                  user_info=user_info, verbose=verbose)

                    req.write(websearch_templates.tmpl_record_format_htmlbrief_body(
                        ln = ln,
                        recid = recid,
                        row_number = row_number,
                        relevance = relevance,
                        record = record,
                        relevances_prologue = relevances_prologue,
                        relevances_epilogue = relevances_epilogue,
                        ))
                req.write(websearch_templates.tmpl_record_format_htmlbrief_footer(
                    ln = ln))

            elif format.startswith("hd"):
                # HTML detailed format:
                for irec in range(irec_max, irec_min, -1):
                    unordered_tabs = get_detailed_page_tabs(get_colID(guess_primary_collection_of_a_record(recIDs[irec])),
                                                            recIDs[irec], ln=ln)
                    ordered_tabs_id = [(tab_id, values['order']) for (tab_id, values) in unordered_tabs.iteritems()]
                    ordered_tabs_id.sort(lambda x,y: cmp(x[1],y[1]))
                    link_ln = ''
                    if ln != CFG_SITE_LANG:
                        link_ln = '?ln=%s' % ln
                    tabs = [(unordered_tabs[tab_id]['label'], \
                             '%s/record/%s/%s%s' % (CFG_SITE_URL, recIDs[irec], tab_id, link_ln), \
                             tab_id == tab,
                             unordered_tabs[tab_id]['enabled']) \
                            for (tab_id, order) in ordered_tabs_id
                            if unordered_tabs[tab_id]['visible'] == True]

                    content = ''
                    # load content
                    if tab == 'usage':
                        r = calculate_reading_similarity_list(recIDs[irec], "downloads")
                        downloadsimilarity = None
                        downloadhistory = None
                        #if r:
                        #    downloadsimilarity = r
                        if CFG_BIBRANK_SHOW_DOWNLOAD_GRAPHS:
                            downloadhistory = create_download_history_graph_and_box(recIDs[irec], ln)

                        r = calculate_reading_similarity_list(recIDs[irec], "pageviews")
                        viewsimilarity = None
                        if r: viewsimilarity = r
                        content = websearch_templates.tmpl_detailed_record_statistics(recIDs[irec],
                                                                                      ln,
                                                                                      downloadsimilarity=downloadsimilarity,
                                                                                      downloadhistory=downloadhistory,
                                                                                      viewsimilarity=viewsimilarity)
                        req.write(webstyle_templates.detailed_record_container(content,
                                                                               recIDs[irec],
                                                                               tabs,
                                                                               ln))
                    elif tab == 'citations':
                        citinglist = []
                        citationhistory = None
                        recid = recIDs[irec]
                        selfcited = get_self_cited_by(recid)
                        r = calculate_cited_by_list(recid)
                        if r:
                            citinglist = r
                            citationhistory = create_citation_history_graph_and_box(recid, ln)

                        r = calculate_co_cited_with_list(recid)
                        cociting = None
                        if r:
                            cociting = r

                        content = websearch_templates.tmpl_detailed_record_citations(recid,
                                                                                     ln,
                                                                                     citinglist=citinglist,
                                                                                     citationhistory=citationhistory,
                                                                                     cociting=cociting,
                                             selfcited=selfcited)
                        req.write(webstyle_templates.detailed_record_container(content,
                                                                               recid,
                                                                               tabs,
                                                                               ln))
                    elif tab == 'references':
                        content = format_record(recIDs[irec], 'HDREF', ln=ln, user_info=user_info, verbose=verbose)
                        req.write(webstyle_templates.detailed_record_container(content,
                                                                               recIDs[irec],
                                                                               tabs,
                                                                               ln))
                    else:
                        # Metadata tab
                        content = print_record(recIDs[irec], format, ot, ln,
                                               search_pattern=search_pattern,
                                               user_info=user_info, verbose=verbose)

                        creationdate = None
                        modificationdate = None
                        if record_exists(recIDs[irec]) == 1:
                            creationdate = get_creation_date(recIDs[irec])
                            modificationdate = get_modification_date(recIDs[irec])

                        content = websearch_templates.tmpl_detailed_record_metadata(
                            recID = recIDs[irec],
                            ln = ln,
                            format = format,
                            creationdate = creationdate,
                            modificationdate = modificationdate,
                            content = content)

                        req.write(webstyle_templates.detailed_record_container(content,
                                                                               recIDs[irec],
                                                                               tabs,
                                                                               ln=ln,
                                                                               creationdate=creationdate,
                                                                               modificationdate=modificationdate,
                                                                               show_short_rec_p=False))

                        if len(tabs) > 0:
                            # Add the mini box at bottom of the page
                            if CFG_WEBCOMMENT_ALLOW_REVIEWS:
                                from invenio.webcomment import get_mini_reviews
                                reviews = get_mini_reviews(recid = recIDs[irec], ln=ln)
                            else:
                                reviews = ''
                            actions = format_record(recIDs[irec], 'HDACT', ln=ln, user_info=user_info, verbose=verbose)
                            files = format_record(recIDs[irec], 'HDFILE', ln=ln, user_info=user_info, verbose=verbose)
                            req.write(webstyle_templates.detailed_record_mini_panel(recIDs[irec],
                                                                                    ln,
                                                                                    format,
                                                                                    files=files,
                                                                                    reviews=reviews,
                                                                                    actions=actions))
            else:
                # Other formats
                for irec in range(irec_max, irec_min, -1):
                    req.write(print_record(recIDs[irec], format, ot, ln,
                                           search_pattern=search_pattern,
                                           user_info=user_info, verbose=verbose))

    else:
        print_warning(req, _("Use different search terms."))

def print_records_prologue(req, format):
    """
    Print the appropriate prologue for list of records in the given
    format.
    """
    prologue = "" # no prologue needed for HTML or Text formats
    if format.startswith('xm'):
        prologue = websearch_templates.tmpl_xml_marc_prologue()
    elif format.startswith('xn'):
        prologue = websearch_templates.tmpl_xml_nlm_prologue()
    elif format.startswith('xr'):
        prologue = websearch_templates.tmpl_xml_rss_prologue()
    elif format.startswith('x'):
        prologue = websearch_templates.tmpl_xml_default_prologue()
    req.write(prologue)

def print_records_epilogue(req, format):
    """
    Print the appropriate epilogue for list of records in the given
    format.
    """
    epilogue = "" # no epilogue needed for HTML or Text formats
    if format.startswith('xm'):
        epilogue = websearch_templates.tmpl_xml_marc_epilogue()
    elif format.startswith('xn'):
        epilogue = websearch_templates.tmpl_xml_nlm_epilogue()
    elif format.startswith('xr'):
        epilogue = websearch_templates.tmpl_xml_rss_epilogue()
    elif format.startswith('x'):
        epilogue = websearch_templates.tmpl_xml_default_epilogue()
    req.write(epilogue)

def print_record(recID, format='hb', ot='', ln=CFG_SITE_LANG, decompress=zlib.decompress,
                 search_pattern=None, user_info=None, verbose=0):
    """Prints record 'recID' formatted accoding to 'format'."""

    _ = gettext_set_language(ln)

    out = ""

    # sanity check:
    record_exist_p = record_exists(recID)
    if record_exist_p == 0: # doesn't exist
        return out

    # New Python BibFormat procedure for formatting
    # Old procedure follows further below
    # We must still check some special formats, but these
    # should disappear when BibFormat improves.
    if not (CFG_BIBFORMAT_USE_OLD_BIBFORMAT \
            or format.lower().startswith('t') \
            or format.lower().startswith('hm') \
            or str(format[0:3]).isdigit() \
            or ot):

        # Unspecified format is hd
        if format == '':
            format = 'hd'

        if record_exist_p == -1 and get_output_format_content_type(format) == 'text/html':
            # HTML output displays a default value for deleted records.
            # Other format have to deal with it.
            out += _("The record has been deleted.")
        else:
            out += call_bibformat(recID, format, ln, search_pattern=search_pattern,
                                  user_info=user_info, verbose=verbose)

            # at the end of HTML brief mode, print the "Detailed record" functionality:
            if format.lower().startswith('hb') and \
                   format.lower() != 'hb_p':
                out += websearch_templates.tmpl_print_record_brief_links(
                    ln = ln,
                    recID = recID,
                    )
        return out

    # Old PHP BibFormat procedure for formatting
    # print record opening tags, if needed:
    if format == "marcxml" or format == "oai_dc":
        out += "  <record>\n"
        out += "   <header>\n"
        for oai_id in get_fieldvalues(recID, CFG_OAI_ID_FIELD):
            out += "    <identifier>%s</identifier>\n" % oai_id
        out += "    <datestamp>%s</datestamp>\n" % get_modification_date(recID)
        out += "   </header>\n"
        out += "   <metadata>\n"

    if format.startswith("xm") or format == "marcxml":
        # look for detailed format existence:
        query = "SELECT value FROM bibfmt WHERE id_bibrec='%s' AND format='%s'" % (recID, format)
        res = run_sql(query, None, 1)
        if res and record_exist_p == 1:
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
            if record_exist_p == -1:
                # deleted record, so display only OAI ID and 980:
                oai_ids = get_fieldvalues(recID, CFG_OAI_ID_FIELD)
                if oai_ids:
                    out += "<datafield tag=\"%s\" ind1=\"%s\" ind2=\"%s\"><subfield code=\"%s\">%s</subfield></datafield>\n" % \
                           (CFG_OAI_ID_FIELD[0:3], CFG_OAI_ID_FIELD[3:4], CFG_OAI_ID_FIELD[4:5], CFG_OAI_ID_FIELD[5:6], oai_ids[0])
                out += "<datafield tag=\"980\" ind1=\"\" ind2=\"\"><subfield code=\"c\">DELETED</subfield></datafield>\n"
            else:
                # controlfields
                query = "SELECT b.tag,b.value,bb.field_number FROM bib00x AS b, bibrec_bib00x AS bb "\
                        "WHERE bb.id_bibrec='%s' AND b.id=bb.id_bibxxx AND b.tag LIKE '00%%' "\
                        "ORDER BY bb.field_number, b.tag ASC" % recID
                res = run_sql(query)
                for row in res:
                    field, value = row[0], row[1]
                    value = encode_for_xml(value)
                    out += """        <controlfield tag="%s" >%s</controlfield>\n""" % \
                           (encode_for_xml(field[0:3]), value)
                # datafields
                i = 1 # Do not process bib00x and bibrec_bib00x, as
                      # they are controlfields. So start at bib01x and
                      # bibrec_bib00x (and set i = 0 at the end of
                      # first loop)
                for digit1 in range(0, 10):
                    for digit2 in range(i, 10):
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
                            if ind1 == "_" or ind1 == "":
                                ind1 = " "
                            if ind2 == "_" or ind2 == "":
                                ind2 = " "
                            # print field tag
                            if field_number != field_number_old or field[:-1] != field_old[:-1]:
                                if field_number_old != -999:
                                    out += """        </datafield>\n"""
                                out += """        <datafield tag="%s" ind1="%s" ind2="%s">\n""" % \
                                           (encode_for_xml(field[0:3]), encode_for_xml(ind1), encode_for_xml(ind2))
                                field_number_old = field_number
                                field_old = field
                            # print subfield value
                            value = encode_for_xml(value)
                            out += """            <subfield code="%s">%s</subfield>\n""" % \
                                   (encode_for_xml(field[-1:]), value)

                        # all fields/subfields printed in this run, so close the tag:
                        if field_number_old != -999:
                            out += """        </datafield>\n"""
                    i = 0 # Next loop should start looking at bib%0 and bibrec_bib00x
            # we are at the end of printing the record:
            out += "    </record>\n"

    elif format == "xd" or format == "oai_dc":
        # XML Dublin Core format, possibly OAI -- select only some bibXXx fields:
        out += """    <dc xmlns="http://purl.org/dc/elements/1.1/"
                         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                         xsi:schemaLocation="http://purl.org/dc/elements/1.1/
                                             http://www.openarchives.org/OAI/1.1/dc.xsd">\n"""
        if record_exist_p == -1:
            out += ""
        else:
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
        if record_exist_p == -1:
            out += get_fieldvalues_alephseq_like(recID, ["001", CFG_OAI_ID_FIELD, "980"])
        else:
            out += get_fieldvalues_alephseq_like(recID, ot)

    elif format == "hm":
        if record_exist_p == -1:
            out += "<pre>" + cgi.escape(get_fieldvalues_alephseq_like(recID, ["001", CFG_OAI_ID_FIELD, "980"])) + "</pre>"
        else:
            out += "<pre>" + cgi.escape(get_fieldvalues_alephseq_like(recID, ot)) + "</pre>"

    elif format.startswith("h") and ot:
        ## user directly asked for some tags to be displayed only
        if record_exist_p == -1:
            out += "<pre>" + get_fieldvalues_alephseq_like(recID, ["001", CFG_OAI_ID_FIELD, "980"]) + "</pre>"
        else:
            out += "<pre>" + get_fieldvalues_alephseq_like(recID, ot) + "</pre>"

    elif format == "hd":
        # HTML detailed format
        if record_exist_p == -1:
            out += _("The record has been deleted.")
        else:
            # look for detailed format existence:
            query = "SELECT value FROM bibfmt WHERE id_bibrec='%s' AND format='%s'" % (recID, format)
            res = run_sql(query, None, 1)
            if res:
                # record 'recID' is formatted in 'format', so print it
                out += "%s" % decompress(res[0][0])
            else:
                # record 'recID' is not formatted in 'format', so try to call BibFormat on the fly or use default format:
                out_record_in_format = call_bibformat(recID, format, ln, search_pattern=search_pattern,
                                                      user_info=user_info, verbose=verbose)
                if out_record_in_format:
                    out += out_record_in_format
                else:
                    out += websearch_templates.tmpl_print_record_detailed(
                             ln = ln,
                             recID = recID,
                           )

    elif format.startswith("hb_") or format.startswith("hd_"):
        # underscore means that HTML brief/detailed formats should be called on-the-fly; suitable for testing formats
        if record_exist_p == -1:
            out += _("The record has been deleted.")
        else:
            out += call_bibformat(recID, format, ln, search_pattern=search_pattern,
                                  user_info=user_info, verbose=verbose)

    elif format.startswith("hx"):
        # BibTeX format, called on the fly:
        if record_exist_p == -1:
            out += _("The record has been deleted.")
        else:
            out += call_bibformat(recID, format, ln, search_pattern=search_pattern,
                                  user_info=user_info, verbose=verbose)

    elif format.startswith("hs"):
        # for citation/download similarity navigation links:
        if record_exist_p == -1:
            out += _("The record has been deleted.")
        else:
            out += '<a href="%s">' % websearch_templates.build_search_url(recid=recID, ln=ln)
            # firstly, title:
            titles = get_fieldvalues(recID, "245__a")
            if titles:
                for title in titles:
                    out += "<strong>%s</strong>" % title
            else:
                # usual title not found, try conference title:
                titles = get_fieldvalues(recID, "111__a")
                if titles:
                    for title in titles:
                        out += "<strong>%s</strong>" % title
                else:
                    # just print record ID:
                    out += "<strong>%s %d</strong>" % (get_field_i18nname("record ID", ln), recID)
            out += "</a>"
            # secondly, authors:
            authors = get_fieldvalues(recID, "100__a") + get_fieldvalues(recID, "700__a")
            if authors:
                out += " - %s" % authors[0]
                if len(authors) > 1:
                    out += " <em>et al</em>"
            # thirdly publication info:
            publinfos = get_fieldvalues(recID, "773__s")
            if not publinfos:
                publinfos = get_fieldvalues(recID, "909C4s")
                if not publinfos:
                    publinfos = get_fieldvalues(recID, "037__a")
                    if not publinfos:
                        publinfos = get_fieldvalues(recID, "088__a")
            if publinfos:
                out += " - %s" % publinfos[0]
            else:
                # fourthly publication year (if not publication info):
                years = get_fieldvalues(recID, "773__y")
                if not years:
                    years = get_fieldvalues(recID, "909C4y")
                    if not years:
                        years = get_fieldvalues(recID, "260__c")
                if years:
                    out += " (%s)" % years[0]
    else:
        # HTML brief format by default
        if record_exist_p == -1:
            out += _("The record has been deleted.")
        else:
            query = "SELECT value FROM bibfmt WHERE id_bibrec='%s' AND format='%s'" % (recID, format)
            res = run_sql(query)
            if res:
                # record 'recID' is formatted in 'format', so print it
                out += "%s" % decompress(res[0][0])
            else:
                # record 'recID' is not formatted in 'format', so try to call BibFormat on the fly: or use default format:
                if CFG_WEBSEARCH_CALL_BIBFORMAT:
                    out_record_in_format = call_bibformat(recID, format, ln, search_pattern=search_pattern,
                                                          user_info=user_info, verbose=verbose)
                    if out_record_in_format:
                        out += out_record_in_format
                    else:
                        out += websearch_templates.tmpl_print_record_brief(
                                 ln = ln,
                                 recID = recID,
                               )
                else:
                    out += websearch_templates.tmpl_print_record_brief(
                             ln = ln,
                             recID = recID,
                           )

            # at the end of HTML brief mode, print the "Detailed record" functionality:
            if format == 'hp' or format.startswith("hb_") or format.startswith("hd_"):
                pass # do nothing for portfolio and on-the-fly formats
            else:
                out += websearch_templates.tmpl_print_record_brief_links(
                         ln = ln,
                         recID = recID,
                       )

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

def call_bibformat(recID, format="HD", ln=CFG_SITE_LANG, search_pattern=None, user_info=None, verbose=0):
    """
    Calls BibFormat and returns formatted record.

    BibFormat will decide by itself if old or new BibFormat must be used.
    """

    keywords = []
    if search_pattern is not None:
        units = create_basic_search_units(None, str(search_pattern), None)
        keywords = [unit[1] for unit in units if unit[0] != '-']

    return format_record(recID,
                         of=format,
                         ln=ln,
                         search_pattern=keywords,
                         user_info=user_info,
                         verbose=verbose)

def log_query(hostname, query_args, uid=-1):
    """
    Log query into the query and user_query tables.
    Return id_query or None in case of problems.
    """
    id_query = None
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
                     time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
    return id_query

def log_query_info(action, p, f, colls, nb_records_found_total=-1):
    """Write some info to the log file for later analysis."""
    try:
        log = open(CFG_LOGDIR + "/search.log", "a")
        log.write(time.strftime("%Y%m%d%H%M%S#", time.localtime()))
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

def perform_request_search(req=None, cc=CFG_SITE_NAME, c=None, p="", f="", rg=10, sf="", so="d", sp="", rm="", of="id", ot="", as=0,
                           p1="", f1="", m1="", op1="", p2="", f2="", m2="", op2="", p3="", f3="", m3="", sc=0, jrec=0,
                           recid=-1, recidb=-1, sysno="", id=-1, idb=-1, sysnb="", action="", d1="",
                           d1y=0, d1m=0, d1d=0, d2="", d2y=0, d2m=0, d2d=0, dt="", verbose=0, ap=0, ln=CFG_SITE_LANG, ec=None, tab=""):
    """Perform search or browse request, without checking for
       authentication.  Return list of recIDs found, if of=id.
       Otherwise create web page.

       The arguments are as follows:

         req - mod_python Request class instance.

          cc - current collection (e.g. "ATLAS").  The collection the
               user started to search/browse from.

           c - collection list (e.g. ["Theses", "Books"]).  The
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

          rm - ranking method (e.g. "jif").  Defines whether results
               should be ranked by some known ranking method.

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
               migrate to CDS Invenio from another system, and store your
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

          d1 - first datetime in full YYYY-mm-dd HH:MM:DD format
               (e.g. "1998-08-23 12:34:56"). Useful for search limits
               on creation/modification date (see 'dt' argument
               below).  Note that 'd1' takes precedence over d1y, d1m,
               d1d if these are defined.

         d1y - first date's year (e.g. "1998").  Useful for search
               limits on creation/modification date.

         d1m - first date's month (e.g. "08").  Useful for search
               limits on creation/modification date.

         d1d - first date's day (e.g. "23").  Useful for search
               limits on creation/modification date.

          d2 - second datetime in full YYYY-mm-dd HH:MM:DD format
               (e.g. "1998-09-02 12:34:56"). Useful for search limits
               on creation/modification date (see 'dt' argument
               below).  Note that 'd2' takes precedence over d2y, d2m,
               d2d if these are defined.

         d2y - second date's year (e.g. "1998").  Useful for search
               limits on creation/modification date.

         d2m - second date's month (e.g. "09").  Useful for search
               limits on creation/modification date.

         d2d - second date's day (e.g. "02").  Useful for search
               limits on creation/modification date.

          dt - first and second date's type (e.g. "c").  Specifies
               whether to search in creation dates ("c") or in
               modification dates ("m").  When dt is not set and d1*
               and d2* are set, the default is "c".

     verbose - verbose level (0=min, 9=max).  Useful to print some
               internal information on the searching process in case
               something goes wrong.

          ap - alternative patterns (0=no, 1=yes).  In case no exact
               match is found, the search engine can try alternative
               patterns e.g. to replace non-alphanumeric characters by
               a boolean query.  ap defines if this is wanted.

          ln - language of the search interface (e.g. "en").  Useful
               for internationalization.

          ec - list of external search engines to search as well
               (e.g. "SPIRES HEP").
    """
    selected_external_collections_infos = None

    # wash all arguments requiring special care
    try:
        (cc, colls_to_display, colls_to_search) = wash_colls(cc, c, sc) # which colls to search and to display?
    except InvenioWebSearchUnknownCollectionError, exc:
        colname = exc.colname
        if of.startswith("h"):
            page_start(req, of, cc, as, ln, getUid(req),
                       websearch_templates.tmpl_collection_not_found_page_title(colname, ln))
            req.write(websearch_templates.tmpl_collection_not_found_page_body(colname, ln))
            return page_end(req, of, ln)
        elif of == "id":
            return []
        elif of.startswith("x"):
            # Print empty, but valid XML
            print_records_prologue(req, of)
            print_records_epilogue(req, of)
        else:
            return page_end(req, of, ln)

    p = wash_pattern(p)
    f = wash_field(f)
    p1 = wash_pattern(p1)
    f1 = wash_field(f1)
    p2 = wash_pattern(p2)
    f2 = wash_field(f2)
    p3 = wash_pattern(p3)
    f3 = wash_field(f3)
    datetext1, datetext2 = wash_dates(d1, d1y, d1m, d1d, d2, d2y, d2m, d2d)

    _ = gettext_set_language(ln)

    # backwards compatibility: id, idb, sysnb -> recid, recidb, sysno (if applicable)
    if sysnb != "" and sysno == "":
        sysno = sysnb
    if id > 0 and recid == -1:
        recid = id
    if idb > 0 and recidb == -1:
        recidb = idb
    # TODO deduce passed search limiting criterias (if applicable)
    pl, pl_in_url = "", "" # no limits by default
    if action != "browse" and req and req.args: # we do not want to add options while browsing or while calling via command-line
        fieldargs = cgi.parse_qs(req.args)
        for fieldcode in get_fieldcodes():
            if fieldargs.has_key(fieldcode):
                for val in fieldargs[fieldcode]:
                    pl += "+%s:\"%s\" " % (fieldcode, val)
                    pl_in_url += "&amp;%s=%s" % (urllib.quote(fieldcode), urllib.quote(val))
    # deduce recid from sysno argument (if applicable):
    if sysno: # ALEPH SYS number was passed, so deduce DB recID for the record:
        recid = get_mysql_recid_from_aleph_sysno(sysno)
        if recid is None:
            recid = 0 # use recid 0 to indicate that this sysno does not exist
    # deduce collection we are in (if applicable):
    if recid > 0:
        cc = guess_primary_collection_of_a_record(recid)
    # deduce user id (if applicable):
    try:
        uid = getUid(req)
    except:
        uid = 0
    ## 0 - start output
    if recid >= 0: # recid can be 0 if deduced from sysno and if such sysno does not exist
        ## 1 - detailed record display
        title, description, keywords = \
               websearch_templates.tmpl_record_page_header_content(req, recid, ln)

        page_start(req, of, cc, as, ln, uid, title, description, keywords, recid, tab)
        # Default format is hb but we are in detailed -> change 'of'
        if of == "hb":
            of = "hd"
        if record_exists(recid):
            if recidb <= recid: # sanity check
                recidb = recid + 1
            if of == "id":
                return [recidx for recidx in range(recid, recidb) if record_exists(recidx)]
            else:
                print_records(req, range(recid, recidb), -1, -9999, of, ot, ln, search_pattern=p, verbose=verbose, tab=tab)
            if req and of.startswith("h"): # register detailed record page view event
                client_ip_address = str(req.get_remote_host(apache.REMOTE_NOLOOKUP))
                register_page_view_event(recid, uid, client_ip_address)
        else: # record does not exist
            if of == "id":
                return []
            elif of.startswith("x"):
                # Print empty, but valid XML
                print_records_prologue(req, of)
                print_records_epilogue(req, of)
            elif of.startswith("h"):
                print_warning(req, _("Requested record does not seem to exist."))

    elif action == "browse":
        ## 2 - browse needed
        page_start(req, of, cc, as, ln, uid, _("Browse"))
        if of.startswith("h"):
            req.write(create_search_box(cc, colls_to_display, p, f, rg, sf, so, sp, rm, of, ot, as, ln, p1, f1, m1, op1,
                                        p2, f2, m2, op2, p3, f3, m3, sc, pl, d1y, d1m, d1d, d2y, d2m, d2d, dt, jrec, ec, action))
        try:
            if as == 1 or (p1 or p2 or p3):
                browse_pattern(req, colls_to_search, p1, f1, rg, ln)
                browse_pattern(req, colls_to_search, p2, f2, rg, ln)
                browse_pattern(req, colls_to_search, p3, f3, rg, ln)
            else:
                browse_pattern(req, colls_to_search, p, f, rg, ln)
        except:
            if of.startswith("h"):
                req.write(create_error_box(req, verbose=verbose, ln=ln))
            elif of.startswith("x"):
                # Print empty, but valid XML
                print_records_prologue(req, of)
                print_records_epilogue(req, of)
            return page_end(req, of, ln)

    elif rm and p.startswith("recid:"):
        ## 3-ter - similarity search needed
        page_start(req, of, cc, as, ln, uid, _("Search Results"))
        if of.startswith("h"):
            req.write(create_search_box(cc, colls_to_display, p, f, rg, sf, so, sp, rm, of, ot, as, ln, p1, f1, m1, op1,
                                        p2, f2, m2, op2, p3, f3, m3, sc, pl, d1y, d1m, d1d, d2y, d2m, d2d, dt, jrec, ec, action))
        if record_exists(p[6:]) != 1:
            # record does not exist
            if of.startswith("h"):
                print_warning(req, "Requested record does not seem to exist.")
            if of == "id":
                return []
            elif of.startswith("x"):
                # Print empty, but valid XML
                print_records_prologue(req, of)
                print_records_epilogue(req, of)
        else:
            # record well exists, so find similar ones to it
            t1 = os.times()[4]
            results_similar_recIDs, results_similar_relevances, results_similar_relevances_prologue, results_similar_relevances_epilogue, results_similar_comments = \
                                    rank_records(rm, 0, get_collection_reclist(cc), string.split(p), verbose)
            if results_similar_recIDs:
                t2 = os.times()[4]
                cpu_time = t2 - t1
                if of.startswith("h"):
                    req.write(print_search_info(p, f, sf, so, sp, rm, of, ot, cc, len(results_similar_recIDs),
                                                jrec, rg, as, ln, p1, p2, p3, f1, f2, f3, m1, m2, m3, op1, op2,
                                                sc, pl_in_url,
                                                d1y, d1m, d1d, d2y, d2m, d2d, dt, cpu_time))
                    print_warning(req, results_similar_comments)
                    print_records(req, results_similar_recIDs, jrec, rg, of, ot, ln,
                                  results_similar_relevances, results_similar_relevances_prologue, results_similar_relevances_epilogue, search_pattern=p, verbose=verbose)
                elif of=="id":
                    return results_similar_recIDs
                elif of.startswith("x"):
                    print_records(req, results_similar_recIDs, jrec, rg, of, ot, ln,
                                  results_similar_relevances, results_similar_relevances_prologue, results_similar_relevances_epilogue, search_pattern=p, verbose=verbose)
            else:
                # rank_records failed and returned some error message to display:
                if of.startswith("h"):
                    print_warning(req, results_similar_relevances_prologue)
                    print_warning(req, results_similar_relevances_epilogue)
                    print_warning(req, results_similar_comments)
                if of == "id":
                    return []
                elif of.startswith("x"):
                    # Print empty, but valid XML
                    print_records_prologue(req, of)
                    print_records_epilogue(req, of)

    elif p.startswith("cocitedwith:"):  #WAS EXPERIMENTAL
        ## 3-terter - cited by search needed
        page_start(req, of, cc, as, ln, uid, _("Search Results"))
        if of.startswith("h"):
            req.write(create_search_box(cc, colls_to_display, p, f, rg, sf, so, sp, rm, of, ot, as, ln, p1, f1, m1, op1,
                                        p2, f2, m2, op2, p3, f3, m3, sc, pl, d1y, d1m, d1d, d2y, d2m, d2d, dt, jrec, ec, action))
        recID = p[12:]
        if record_exists(recID) != 1:
            # record does not exist
            if of.startswith("h"):
                print_warning(req, "Requested record does not seem to exist.")
            if of == "id":
                return []
            elif of.startswith("x"):
                # Print empty, but valid XML
                print_records_prologue(req, of)
                print_records_epilogue(req, of)
        else:
            # record well exists, so find co-cited ones:
            t1 = os.times()[4]
            results_cocited_recIDs = map(lambda x: x[0], calculate_co_cited_with_list(int(recID)))
            if results_cocited_recIDs:
                t2 = os.times()[4]
                cpu_time = t2 - t1
                if of.startswith("h"):
                    req.write(print_search_info(p, f, sf, so, sp, rm, of, ot, CFG_SITE_NAME, len(results_cocited_recIDs),
                                                jrec, rg, as, ln, p1, p2, p3, f1, f2, f3, m1, m2, m3, op1, op2,
                                                sc, pl_in_url,
                                                d1y, d1m, d1d, d2y, d2m, d2d, dt, cpu_time))
                    print_records(req, results_cocited_recIDs, jrec, rg, of, ot, ln, search_pattern=p, verbose=verbose)
                elif of=="id":
                    return results_cocited_recIDs
                elif of.startswith("x"):
                    print_records(req, results_cocited_recIDs, jrec, rg, of, ot, ln, search_pattern=p, verbose=verbose)

            else:
                # cited rank_records failed and returned some error message to display:
                if of.startswith("h"):
                    print_warning(req, "nothing found")
                if of == "id":
                    return []
                elif of.startswith("x"):
                    # Print empty, but valid XML
                    print_records_prologue(req, of)
                    print_records_epilogue(req, of)
    else:
        ## 3 - common search needed
        page_start(req, of, cc, as, ln, uid, _("Search Results"))
        if of.startswith("h"):
            req.write(create_search_box(cc, colls_to_display, p, f, rg, sf, so, sp, rm, of, ot, as, ln, p1, f1, m1, op1,
                                        p2, f2, m2, op2, p3, f3, m3, sc, pl, d1y, d1m, d1d, d2y, d2m, d2d, dt, jrec, ec, action))
        t1 = os.times()[4]
        results_in_any_collection = HitSet()
        if as == 1 or (p1 or p2 or p3):
            ## 3A - advanced search
            try:
                results_in_any_collection = search_pattern_parenthesised(req, p1, f1, m1, ap=ap, of=of, verbose=verbose, ln=ln)
                if len(results_in_any_collection) == 0:
                    if of.startswith("h"):
                        perform_external_collection_search(req, cc, [p, p1, p2, p3], f, ec, verbose, ln, selected_external_collections_infos)
                    elif of.startswith("x"):
                        # Print empty, but valid XML
                        print_records_prologue(req, of)
                        print_records_epilogue(req, of)
                    return page_end(req, of, ln)
                if p2:
                    results_tmp = search_pattern_parenthesised(req, p2, f2, m2, ap=ap, of=of, verbose=verbose, ln=ln)
                    if op1 == "a": # add
                        results_in_any_collection.intersection_update(results_tmp)
                    elif op1 == "o": # or
                        results_in_any_collection.union_update(results_tmp)
                    elif op1 == "n": # not
                        results_in_any_collection.difference_update(results_tmp)
                    else:
                        if of.startswith("h"):
                            print_warning(req, "Invalid set operation %s." % op1, "Error")
                    if len(results_in_any_collection) == 0:
                        if of.startswith("h"):
                            perform_external_collection_search(req, cc, [p, p1, p2, p3], f, ec, verbose, ln, selected_external_collections_infos)
                        elif of.startswith("x"):
                            # Print empty, but valid XML
                            print_records_prologue(req, of)
                            print_records_epilogue(req, of)
                        return page_end(req, of, ln)
                if p3:
                    results_tmp = search_pattern_parenthesised(req, p3, f3, m3, ap=ap, of=of, verbose=verbose, ln=ln)
                    if op2 == "a": # add
                        results_in_any_collection.intersection_update(results_tmp)
                    elif op2 == "o": # or
                        results_in_any_collection.union_update(results_tmp)
                    elif op2 == "n": # not
                        results_in_any_collection.difference_update(results_tmp)
                    else:
                        if of.startswith("h"):
                            print_warning(req, "Invalid set operation %s." % op2, "Error")
            except:
                if of.startswith("h"):
                    req.write(create_error_box(req, verbose=verbose, ln=ln))
                    perform_external_collection_search(req, cc, [p, p1, p2, p3], f, ec, verbose, ln, selected_external_collections_infos)
                elif of.startswith("x"):
                    # Print empty, but valid XML
                    print_records_prologue(req, of)
                    print_records_epilogue(req, of)

                return page_end(req, of, ln)
        else:
            ## 3B - simple search
            try:
                results_in_any_collection = search_pattern_parenthesised(req, p, f, ap=ap, of=of, verbose=verbose, ln=ln)
            except:
                if of.startswith("h"):
                    req.write(create_error_box(req, verbose=verbose, ln=ln))
                    perform_external_collection_search(req, cc, [p, p1, p2, p3], f, ec, verbose, ln, selected_external_collections_infos)
                return page_end(req, of, ln)

        if len(results_in_any_collection) == 0:
            if of.startswith("h"):
                perform_external_collection_search(req, cc, [p, p1, p2, p3], f, ec, verbose, ln, selected_external_collections_infos)
            elif of.startswith("x"):
                # Print empty, but valid XML
                print_records_prologue(req, of)
                print_records_epilogue(req, of)
            return page_end(req, of, ln)

#             search_cache_key = p+"@"+f+"@"+string.join(colls_to_search,",")
#             if search_cache.has_key(search_cache_key): # is the result in search cache?
#                 results_final = search_cache[search_cache_key]
#             else:
#                 results_final = search_pattern(req, p, f, colls_to_search)
#                 search_cache[search_cache_key] = results_final
#             if len(search_cache) > CFG_WEBSEARCH_SEARCH_CACHE_SIZE: # is the cache full? (sanity cleaning)
#                 search_cache.clear()

        # search stage 4: intersection with collection universe:
        try:
            results_final = intersect_results_with_collrecs(req, results_in_any_collection, colls_to_search, ap, of, verbose, ln)
        except:
            if of.startswith("h"):
                req.write(create_error_box(req, verbose=verbose, ln=ln))
                perform_external_collection_search(req, cc, [p, p1, p2, p3], f, ec, verbose, ln, selected_external_collections_infos)
            return page_end(req, of, ln)

        if results_final == {}:
            if of.startswith("h"):
                perform_external_collection_search(req, cc, [p, p1, p2, p3], f, ec, verbose, ln, selected_external_collections_infos)
            if of.startswith("x"):
                # Print empty, but valid XML
                print_records_prologue(req, of)
                print_records_epilogue(req, of)
            return page_end(req, of, ln)

        # search stage 5: apply search option limits and restrictions:
        if datetext1 != "":
            if verbose and of.startswith("h"):
                print_warning(req, "Search stage 5: applying time etc limits, from %s until %s..." % (datetext1, datetext2))
            try:
                results_final = intersect_results_with_hitset(req,
                                                              results_final,
                                                              search_unit_in_bibrec(datetext1, datetext2, dt),
                                                              ap,
                                                              aptext= _("No match within your time limits, "
                                                                        "discarding this condition..."),
                                                              of=of)
            except:
                if of.startswith("h"):
                    req.write(create_error_box(req, verbose=verbose, ln=ln))
                    perform_external_collection_search(req, cc, [p, p1, p2, p3], f, ec, verbose, ln, selected_external_collections_infos)
                return page_end(req, of, ln)
            if results_final == {}:
                if of.startswith("h"):
                    perform_external_collection_search(req, cc, [p, p1, p2, p3], f, ec, verbose, ln, selected_external_collections_infos)
                return page_end(req, of, ln)



        if pl:
            pl = wash_pattern(pl)
            if verbose and of.startswith("h"):
                print_warning(req, "Search stage 5: applying search pattern limit %s..." % (pl,))
            try:
                results_final = intersect_results_with_hitset(req,
                                                              results_final,
                                                              search_pattern_parenthesised(req, pl, ap=0, ln=ln),
                                                              ap,
                                                              aptext=_("No match within your search limits, "
                                                                       "discarding this condition..."),
                                                              of=of)
            except:
                if of.startswith("h"):
                    req.write(create_error_box(req, verbose=verbose, ln=ln))
                    perform_external_collection_search(req, cc, [p, p1, p2, p3], f, ec, verbose, ln, selected_external_collections_infos)
                return page_end(req, of, ln)
            if results_final == {}:
                if of.startswith("h"):
                    perform_external_collection_search(req, cc, [p, p1, p2, p3], f, ec, verbose, ln, selected_external_collections_infos)
                if of.startswith("x"):
                    # Print empty, but valid XML
                    print_records_prologue(req, of)
                    print_records_epilogue(req, of)
                return page_end(req, of, ln)

        t2 = os.times()[4]
        cpu_time = t2 - t1
        ## search stage 6: display results:
        results_final_nb_total = 0
        results_final_nb = {} # will hold number of records found in each collection
                              # (in simple dict to display overview more easily)
        for coll in results_final.keys():
            results_final_nb[coll] = len(results_final[coll])
            #results_final_nb_total += results_final_nb[coll]

        # Now let us calculate results_final_nb_total more precisely,
        # in order to get the total number of "distinct" hits across
        # searched collections; this is useful because a record might
        # have been attributed to more than one primary collection; so
        # we have to avoid counting it multiple times.  The price to
        # pay for this accuracy of results_final_nb_total is somewhat
        # increased CPU time.
        if results_final.keys() == 1:
            # only one collection; no need to union them
            results_final_for_all_selected_colls = results_final.values()[0]
            results_final_nb_total = results_final_nb.values()[0]
        else:
            # okay, some work ahead to union hits across collections:
            results_final_for_all_selected_colls = HitSet()
            for coll in results_final.keys():
                results_final_for_all_selected_colls.union_update(results_final[coll])
            results_final_nb_total = len(results_final_for_all_selected_colls)

        if results_final_nb_total == 0:
            if of.startswith('h'):
                print_warning(req, "No match found, please enter different search terms.")
            elif of.startswith("x"):
                # Print empty, but valid XML
                print_records_prologue(req, of)
                print_records_epilogue(req, of)
        else:
            # yes, some hits found: good!
            # collection list may have changed due to not-exact-match-found policy so check it out:
            for coll in results_final.keys():
                if coll not in colls_to_search:
                    colls_to_search.append(coll)
            # print results overview:
            if of == "id":
                # we have been asked to return list of recIDs
                recIDs = list(results_final_for_all_selected_colls)
                if sf: # do we have to sort?
                    recIDs = sort_records(req, recIDs, sf, so, sp, verbose, of)
                elif rm: # do we have to rank?
                    results_final_for_all_colls_rank_records_output = rank_records(rm, 0, results_final_for_all_selected_colls,
                                                                                   string.split(p) + string.split(p1) +
                                                                                   string.split(p2) + string.split(p3), verbose)
                    if results_final_for_all_colls_rank_records_output[0]:
                        recIDs = results_final_for_all_colls_rank_records_output[0]
                return recIDs
            elif of.startswith("h"):
                if of not in ['hcs']:
                    req.write(print_results_overview(req, colls_to_search, results_final_nb_total, results_final_nb, cpu_time, ln, ec))
                    selected_external_collections_infos = print_external_results_overview(req, cc, [p, p1, p2, p3], f, ec, verbose, ln)
            # print number of hits found for XML outputs:
            if of.startswith("x"):
                req.write("<!-- Search-Engine-Total-Number-Of-Results: %s -->\n" % results_final_nb_total)
            # print records:
            if of in ['hcs']:
                req.write(summarize_records(results_final_for_all_selected_colls, 'hcs', ln))
            else:
                if len(colls_to_search)>1:
                    cpu_time = -1 # we do not want to have search time printed on each collection
                print_records_prologue(req, of)
                for coll in colls_to_search:
                    if results_final.has_key(coll) and len(results_final[coll]):
                        if of.startswith("h"):
                            req.write(print_search_info(p, f, sf, so, sp, rm, of, ot, coll, results_final_nb[coll],
                                                        jrec, rg, as, ln, p1, p2, p3, f1, f2, f3, m1, m2, m3, op1, op2,
                                                        sc, pl_in_url,
                                                        d1y, d1m, d1d, d2y, d2m, d2d, dt, cpu_time))
                        results_final_recIDs = list(results_final[coll])
                        results_final_relevances = []
                        results_final_relevances_prologue = ""
                        results_final_relevances_epilogue = ""
                        if sf: # do we have to sort?
                            results_final_recIDs = sort_records(req, results_final_recIDs, sf, so, sp, verbose, of)
                        elif rm: # do we have to rank?
                            results_final_recIDs_ranked, results_final_relevances, results_final_relevances_prologue, results_final_relevances_epilogue, results_final_comments = \
                                                         rank_records(rm, 0, results_final[coll],
                                                                      string.split(p) + string.split(p1) +
                                                                      string.split(p2) + string.split(p3), verbose)
                            if of.startswith("h"):
                                print_warning(req, results_final_comments)
                            if results_final_recIDs_ranked:
                                results_final_recIDs = results_final_recIDs_ranked
                            else:
                                # rank_records failed and returned some error message to display:
                                print_warning(req, results_final_relevances_prologue)
                                print_warning(req, results_final_relevances_epilogue)
                        print_records(req, results_final_recIDs, jrec, rg, of, ot, ln,
                                      results_final_relevances,
                                      results_final_relevances_prologue,
                                      results_final_relevances_epilogue,
                                      search_pattern=p,
                                      print_records_prologue_p=False,
                                      print_records_epilogue_p=False,
                                      verbose=verbose)
                        if of.startswith("h"):
                            req.write(print_search_info(p, f, sf, so, sp, rm, of, ot, coll, results_final_nb[coll],
                                                        jrec, rg, as, ln, p1, p2, p3, f1, f2, f3, m1, m2, m3, op1, op2,
                                                        sc, pl_in_url,
                                                        d1y, d1m, d1d, d2y, d2m, d2d, dt, cpu_time, 1))
                print_records_epilogue(req, of)
                if f == "author" and of.startswith("h"):
                    req.write(create_similarly_named_authors_link_box(p, ln))
            # log query:
            try:
                id_query = log_query(req.get_remote_host(), req.args, uid)
                if of.startswith("h") and id_query:
                    if not of in ['hcs']:
                        # display aalert/RSS teaser for non-summary formats:
                        req.write(websearch_templates.tmpl_alert_rss_teaser_box_for_query(id_query, ln=ln))
            except:
                # do not log query if req is None (used by CLI interface)
                pass
            log_query_info("ss", p, f, colls_to_search, results_final_nb_total)

    # External searches
    if of.startswith("h"):
        if not of in ['hcs']:
            perform_external_collection_search(req, cc, [p, p1, p2, p3], f, ec, verbose, ln, selected_external_collections_infos)

    return page_end(req, of, ln)

def perform_request_cache(req, action="show"):
    """Manipulates the search engine cache."""
    global search_cache
    global collection_reclist_cache
    global collection_reclist_cache_timestamp
    global field_i18nname_cache
    global field_i18nname_cache_timestamp
    global collection_i18nname_cache
    global collection_i18nname_cache_timestamp
    req.content_type = "text/html"
    req.send_http_header()
    out = ""
    out += "<h1>Search Cache</h1>"
    # clear cache if requested:
    if action == "clear":
        search_cache = {}
        collection_reclist_cache = create_collection_reclist_cache()
    # show collection reclist cache:
    out += "<h3>Collection reclist cache</h3>"
    out += "- collection table last updated: %s" % get_table_update_time('collection')
    out += "<br />- reclist cache timestamp: %s" % collection_reclist_cache_timestamp
    out += "<br />- reclist cache contents:"
    out += "<blockquote>"
    for coll in collection_reclist_cache.keys():
        if collection_reclist_cache[coll]:
            out += "%s (%d)<br />" % (coll, len(get_collection_reclist(coll)))
    out += "</blockquote>"
    # show search cache:
    out += "<h3>Search Cache</h3>"
    out += "<blockquote>"
    if len(search_cache):
        out += """<table border="=">"""
        out += "<tr><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td></tr>" % \
               ("Pattern", "Field", "Collection", "Number of Hits")
        for search_cache_key in search_cache.keys():
            p, f, c = string.split(search_cache_key, "@", 2)
            # find out about length of cached data:
            l = 0
            for coll in search_cache[search_cache_key]:
                l += len(search_cache[search_cache_key][coll])
            out += "<tr><td>%s</td><td>%s</td><td>%s</td><td>%d</td></tr>" % (p, f, c, l)
        out += "</table>"
    else:
        out += "<p>Search cache is empty."
    out += "</blockquote>"
    out += """<p><a href="%s/search/cache?action=clear">clear cache</a>""" % CFG_SITE_URL
    # show field i18nname cache:
    out += "<h3>Field I18N names cache</h3>"
    out += "- fieldname table last updated: %s" % get_table_update_time('fieldname')
    out += "<br />- i18nname cache timestamp: %s" % field_i18nname_cache_timestamp
    out += "<br />- i18nname cache contents:"
    out += "<blockquote>"
    for field in field_i18nname_cache.keys():
        for ln in field_i18nname_cache[field].keys():
            out += "%s, %s = %s<br />" % (field, ln, field_i18nname_cache[field][ln])
    out += "</blockquote>"
    # show collection i18nname cache:
    out += "<h3>Collection I18N names cache</h3>"
    out += "- collectionname table last updated: %s" % get_table_update_time('collectionname')
    out += "<br />- i18nname cache timestamp: %s" % collection_i18nname_cache_timestamp
    out += "<br />- i18nname cache contents:"
    out += "<blockquote>"
    for coll in collection_i18nname_cache.keys():
        for ln in collection_i18nname_cache[coll].keys():
            out += "%s, %s = %s<br />" % (coll, ln, collection_i18nname_cache[coll][ln])
    out += "</blockquote>"
    req.write("<html>")
    req.write(out)
    req.write("</html>")
    return "\n"

def perform_request_log(req, date=""):
    """Display search log information for given date."""
    req.content_type = "text/html"
    req.send_http_header()
    req.write("<html>")
    req.write("<h1>Search Log</h1>")
    if date: # case A: display stats for a day
        yyyymmdd = string.atoi(date)
        req.write("<p><big><strong>Date: %d</strong></big><p>" % yyyymmdd)
        req.write("""<table border="1">""")
        req.write("<tr><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td></tr>" % ("No.", "Time", "Pattern", "Field", "Collection", "Number of Hits"))
        # read file:
        p = os.popen("grep ^%d %s/search.log" % (yyyymmdd, CFG_LOGDIR), 'r')
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
        yyyymm01 = int(time.strftime("%Y%m01", time.localtime()))
        yyyymmdd = int(time.strftime("%Y%m%d", time.localtime()))
        req.write("""<table border="1">""")
        req.write("<tr><td><strong>%s</strong></td><td><strong>%s</strong></tr>" % ("Day", "Number of Queries"))
        for day in range(yyyymm01, yyyymmdd + 1):
            p = os.popen("grep -c ^%d %s/search.log" % (day, CFG_LOGDIR), 'r')
            for line in p.readlines():
                req.write("""<tr><td>%s</td><td align="right"><a href="%s/search/log?date=%d">%s</a></td></tr>""" % \
                          (day, CFG_SITE_URL, day, line))
            p.close()
        req.write("</table>")
    req.write("</html>")
    return "\n"


def get_values_for_code_dict(recids, tag):
    """ gets values of tag for records, puts them in dictionary that contains their frequency"""
    valuefreqdict = {}
    for recid in recids:
        vals = get_fieldvalues(recid, tag)
        for v in vals:
            if valuefreqdict.has_key(v):
                valuefreqdict[v] = valuefreqdict[v]+1
            else:
                valuefreqdict[v] = 1
    return valuefreqdict

def get_most_popular_values_for_code(recids, tag):
    """returns a sorted tuple list of the popular values for a given tag"""
    valuefreqdict = get_values_for_code_dict(recids, tag)
    tmppairs = []
    for k,v in valuefreqdict.items():
        tmppairs.append((v,k))
    tmppairs.sort()
    tmppairs.reverse()
    #take only the keys and return them
    sortedvalues = []
    for (v,k) in tmppairs:
        sortedvalues.append(k)
    return sortedvalues

def profile(p="", f="", c=CFG_SITE_NAME):
    """Profile search time."""
    import profile
    import pstats
    profile.run("perform_request_search(p='%s',f='%s', c='%s')" % (p, f, c), "perform_request_search_profile")
    p = pstats.Stats("perform_request_search_profile")
    p.strip_dirs().sort_stats("cumulative").print_stats()
    return 0

## test cases:
#print wash_colls(CFG_SITE_NAME,"Library Catalogue", 0)
#print wash_colls("Periodicals & Progress Reports",["Periodicals","Progress Reports"], 0)
#print wash_field("wau")
#print print_record(20,"tm","001,245")
#print create_opft_search_units(None, "PHE-87-13","reportnumber")
#print ":"+wash_pattern("* and % doo * %")+":\n"
#print ":"+wash_pattern("*")+":\n"
#print ":"+wash_pattern("ellis* ell* e*%")+":\n"
#print run_sql("SELECT name,dbquery from collection")
#print get_index_id("author")
#print get_coll_ancestors("Theses")
#print get_coll_sons("Articles & Preprints")
#print get_coll_real_descendants("Articles & Preprints")
#print get_collection_reclist("Theses")
#print log(sys.stdin)
#print search_unit_in_bibrec('2002-12-01','2002-12-12')
#print type(wash_url_argument("-1",'int'))
#print get_nearest_terms_in_bibxxx("ellis", "author", 5, 5)
#print call_bibformat(68, "HB_FLY")
#print create_collection_i18nname_cache()
#print get_fieldvalues(10, "980__a")
#print get_fieldvalues_alephseq_like(10,"001___")
#print get_fieldvalues_alephseq_like(10,"980__a")
#print get_fieldvalues_alephseq_like(10,"foo")
#print get_fieldvalues_alephseq_like(10,"-1")
#print get_fieldvalues_alephseq_like(10,"99")
#print get_fieldvalues_alephseq_like(10,["001", "980"])

## profiling:
#profile("of the this")
#print perform_request_search(p="ellis")
