# -*- coding: utf-8 -*-

## This file is part of Invenio.
## Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012 CERN.
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

# pylint: disable=C0301

"""Invenio Search Engine in mod_python."""

__lastupdated__ = """$Date$"""

__revision__ = "$Id$"

## import general modules:
import cgi
import cStringIO
import copy
import string
import os
import re
import time
import urllib
import urlparse
import zlib
import sys

if sys.hexversion < 0x2040000:
    # pylint: disable=W0622
    from sets import Set as set
    # pylint: enable=W0622

## import Invenio stuff:
from invenio.config import \
     CFG_CERN_SITE, \
     CFG_INSPIRE_SITE, \
     CFG_OAI_ID_FIELD, \
     CFG_WEBCOMMENT_ALLOW_REVIEWS, \
     CFG_WEBSEARCH_CALL_BIBFORMAT, \
     CFG_WEBSEARCH_CREATE_SIMILARLY_NAMED_AUTHORS_LINK_BOX, \
     CFG_WEBSEARCH_FIELDS_CONVERT, \
     CFG_WEBSEARCH_NB_RECORDS_TO_SORT, \
     CFG_WEBSEARCH_SEARCH_CACHE_SIZE, \
     CFG_WEBSEARCH_USE_MATHJAX_FOR_FORMATS, \
     CFG_WEBSEARCH_USE_ALEPH_SYSNOS, \
     CFG_WEBSEARCH_DEF_RECORDS_IN_GROUPS, \
     CFG_WEBSEARCH_FULLTEXT_SNIPPETS, \
     CFG_WEBSEARCH_DISPLAY_NEAREST_TERMS, \
     CFG_BIBUPLOAD_SERIALIZE_RECORD_STRUCTURE, \
     CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG, \
     CFG_BIBRANK_SHOW_DOWNLOAD_GRAPHS, \
     CFG_WEBSEARCH_WILDCARD_LIMIT, \
     CFG_WEBSEARCH_SYNONYM_KBRS, \
     CFG_SITE_LANG, \
     CFG_SITE_NAME, \
     CFG_LOGDIR, \
     CFG_BIBFORMAT_HIDDEN_TAGS, \
     CFG_SITE_URL, \
     CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS, \
     CFG_SOLR_URL, \
     CFG_SITE_RECORD, \
     CFG_WEBSEARCH_PREV_NEXT_HIT_LIMIT, \
     CFG_WEBSEARCH_VIEWRESTRCOLL_POLICY, \
     CFG_BIBSORT_BUCKETS

from invenio.search_engine_config import InvenioWebSearchUnknownCollectionError, InvenioWebSearchWildcardLimitError
from invenio.search_engine_utils import get_fieldvalues
from invenio.bibrecord import create_record
from invenio.bibrank_record_sorter import get_bibrank_methods, is_method_valid, rank_records as rank_records_bibrank
from invenio.bibrank_downloads_similarity import register_page_view_event, calculate_reading_similarity_list
from invenio.bibindex_engine_stemmer import stem
from invenio.bibindex_engine_tokenizer import wash_author_name, author_name_requires_phrase_search
from invenio.bibformat import format_record, format_records, get_output_format_content_type, create_excel
from invenio.bibformat_config import CFG_BIBFORMAT_USE_OLD_BIBFORMAT
from invenio.bibrank_downloads_grapher import create_download_history_graph_and_box
from invenio.bibknowledge import get_kbr_values
from invenio.data_cacher import DataCacher
from invenio.websearch_external_collections import print_external_results_overview, perform_external_collection_search
from invenio.access_control_admin import acc_get_action_id
from invenio.access_control_config import VIEWRESTRCOLL, \
    CFG_ACC_GRANT_AUTHOR_RIGHTS_TO_EMAILS_IN_TAGS
from invenio.websearchadminlib import get_detailed_page_tabs, get_detailed_page_tabs_counts
from invenio.intbitset import intbitset
from invenio.dbquery import DatabaseError, deserialize_via_marshal, InvenioDbQueryWildcardLimitError
from invenio.access_control_engine import acc_authorize_action
from invenio.errorlib import register_exception
from invenio.textutils import encode_for_xml, wash_for_utf8, strip_accents
from invenio.htmlutils import get_mathjax_header
from invenio.htmlutils import nmtoken_from_string

import invenio.template
webstyle_templates = invenio.template.load('webstyle')
webcomment_templates = invenio.template.load('webcomment')

from invenio.bibrank_citation_searcher import calculate_cited_by_list, \
    calculate_co_cited_with_list, get_records_with_num_cites, get_self_cited_by, \
    get_refersto_hitset, get_citedby_hitset
from invenio.bibrank_citation_grapher import create_citation_history_graph_and_box


from invenio.dbquery import run_sql, run_sql_with_limit, \
                            get_table_update_time, Error
from invenio.webuser import getUid, collect_user_info, session_param_set
from invenio.webpage import pageheaderonly, pagefooteronly, create_error_box
from invenio.messages import gettext_set_language
from invenio.search_engine_query_parser import SearchQueryParenthesisedParser, \
    SpiresToInvenioSyntaxConverter

from invenio import webinterface_handler_config as apache
from invenio.solrutils import solr_get_bitset


try:
    import invenio.template
    websearch_templates = invenio.template.load('websearch')
except:
    pass

from invenio.websearch_external_collections import calculate_hosted_collections_results, do_calculate_hosted_collections_results
from invenio.websearch_external_collections_config import CFG_HOSTED_COLLECTION_TIMEOUT_ANTE_SEARCH
from invenio.websearch_external_collections_config import CFG_HOSTED_COLLECTION_TIMEOUT_POST_SEARCH
from invenio.websearch_external_collections_config import CFG_EXTERNAL_COLLECTION_MAXRESULTS

VIEWRESTRCOLL_ID = acc_get_action_id(VIEWRESTRCOLL)

## global vars:
cfg_nb_browse_seen_records = 100 # limit of the number of records to check when browsing certain collection
cfg_nicely_ordered_collection_list = 0 # do we propose collection list nicely ordered or alphabetical?

## precompile some often-used regexp for speed reasons:
re_word = re.compile('[\s]')
re_quotes = re.compile('[\'\"]')
re_doublequote = re.compile('\"')
re_equal = re.compile('\=')
re_logical_and = re.compile('\sand\s', re.I)
re_logical_or = re.compile('\sor\s', re.I)
re_logical_not = re.compile('\snot\s', re.I)
re_operators = re.compile(r'\s([\+\-\|])\s')
re_pattern_wildcards_after_spaces = re.compile(r'(\s)[\*\%]+')
re_pattern_single_quotes = re.compile("'(.*?)'")
re_pattern_double_quotes = re.compile("\"(.*?)\"")
re_pattern_regexp_quotes = re.compile("\/(.*?)\/")
re_pattern_spaces_after_colon = re.compile(r'(:\s+)')
re_pattern_short_words = re.compile(r'([\s\"]\w{1,3})[\*\%]+')
re_pattern_space = re.compile("__SPACE__")
re_pattern_today = re.compile("\$TODAY\$")
re_pattern_parens = re.compile(r'\([^\)]+\s+[^\)]+\)')

class RestrictedCollectionDataCacher(DataCacher):
    def __init__(self):
        def cache_filler():
            ret = []
            try:
                res = run_sql("""SELECT DISTINCT ar.value
                    FROM accROLE_accACTION_accARGUMENT raa JOIN accARGUMENT ar ON raa.id_accARGUMENT = ar.id
                    WHERE ar.keyword = 'collection' AND raa.id_accACTION = %s""", (VIEWRESTRCOLL_ID,))
            except Exception:
                # database problems, return empty cache
                return []
            for coll in res:
                ret.append(coll[0])
            return ret

        def timestamp_verifier():
            return max(get_table_update_time('accROLE_accACTION_accARGUMENT'), get_table_update_time('accARGUMENT'))

        DataCacher.__init__(self, cache_filler, timestamp_verifier)

def collection_restricted_p(collection, recreate_cache_if_needed=True):
    if recreate_cache_if_needed:
        restricted_collection_cache.recreate_cache_if_needed()
    return collection in restricted_collection_cache.cache

try:
    restricted_collection_cache.is_ok_p
except Exception:
    restricted_collection_cache = RestrictedCollectionDataCacher()


def ziplist(*lists):
    """Just like zip(), but returns lists of lists instead of lists of tuples

    Example:
    zip([f1, f2, f3], [p1, p2, p3], [op1, op2, '']) =>
       [(f1, p1, op1), (f2, p2, op2), (f3, p3, '')]
    ziplist([f1, f2, f3], [p1, p2, p3], [op1, op2, '']) =>
       [[f1, p1, op1], [f2, p2, op2], [f3, p3, '']]

    FIXME: This is handy to have, and should live somewhere else, like
           miscutil.really_useful_functions or something.
    XXX: Starting in python 2.6, the same can be achieved (faster) by
         using itertools.izip_longest(); when the minimum recommended Python
         is bumped, we should use that instead.
    """
    def l(*items):
        return list(items)
    return map(l, *lists)


def get_permitted_restricted_collections(user_info, recreate_cache_if_needed=True):
    """Return a list of collection that are restricted but for which the user
    is authorized."""
    if recreate_cache_if_needed:
        restricted_collection_cache.recreate_cache_if_needed()
    ret = []
    for collection in restricted_collection_cache.cache:
        if acc_authorize_action(user_info, 'viewrestrcoll', collection=collection)[0] == 0:
            ret.append(collection)
    return ret

def get_all_restricted_recids():
    """
    Return the set of all the restricted recids, i.e. the ids of those records
    which belong to at least one restricted collection.
    """
    ret = intbitset()
    for collection in restricted_collection_cache.cache:
        ret |= get_collection_reclist(collection)
    return ret

def get_restricted_collections_for_recid(recid, recreate_cache_if_needed=True):
    """
    Return the list of restricted collection names to which recid belongs.
    """
    if recreate_cache_if_needed:
        restricted_collection_cache.recreate_cache_if_needed()
        collection_reclist_cache.recreate_cache_if_needed()
    return [collection for collection in restricted_collection_cache.cache if recid in get_collection_reclist(collection, recreate_cache_if_needed=False)]

def is_user_owner_of_record(user_info, recid):
    """
    Check if the user is owner of the record, i.e. he is the submitter
    and/or belongs to a owner-like group authorized to 'see' the record.

    @param user_info: the user_info dictionary that describe the user.
    @type user_info: user_info dictionary
    @param recid: the record identifier.
    @type recid: positive integer
    @return: True if the user is 'owner' of the record; False otherwise
    @rtype: bool
    """
    authorized_emails_or_group = []
    for tag in CFG_ACC_GRANT_AUTHOR_RIGHTS_TO_EMAILS_IN_TAGS:
        authorized_emails_or_group.extend(get_fieldvalues(recid, tag))
    for email_or_group in authorized_emails_or_group:
        if email_or_group in user_info['group']:
            return True
        email = email_or_group.strip().lower()
        if user_info['email'].strip().lower() == email:
            return True
    return False

def check_user_can_view_record(user_info, recid):
    """
    Check if the user is authorized to view the given recid. The function
    grants access in two cases: either user has author rights on this
    record, or he has view rights to the primary collection this record
    belongs to.

    @param user_info: the user_info dictionary that describe the user.
    @type user_info: user_info dictionary
    @param recid: the record identifier.
    @type recid: positive integer
    @return: (0, ''), when authorization is granted, (>0, 'message') when
    authorization is not granted
    @rtype: (int, string)
    """
    policy = CFG_WEBSEARCH_VIEWRESTRCOLL_POLICY.strip().upper()
    if isinstance(recid, str):
        recid = int(recid)
    if record_public_p(recid):
        ## The record is already known to be public.
        return (0, '')
    ## At this point, either webcoll has not yet run or there are some
    ## restricted collections. Let's see first if the user own the record.
    if is_user_owner_of_record(user_info, recid):
        ## Perfect! It's authorized then!
        return (0, '')
    restricted_collections = get_restricted_collections_for_recid(recid, recreate_cache_if_needed=False)
    if restricted_collections:
        ## If there are restricted collections the user must be authorized to all/any of them (depending on the policy)
        auth_code, auth_msg = 0, ''
        for collection in get_restricted_collections_for_recid(recid, recreate_cache_if_needed=False):
            (auth_code, auth_msg) = acc_authorize_action(user_info, VIEWRESTRCOLL, collection=collection)
            if auth_code and policy != 'ANY':
                ## Ouch! the user is not authorized to this collection
                return (auth_code, auth_msg)
            elif auth_code == 0 and policy == 'ANY':
                ## Good! At least one collection is authorized
                return (0, '')
        ## Depending on the policy, the user will be either authorized or not
        return auth_code, auth_msg
    if is_record_in_any_collection(recid, recreate_cache_if_needed=False):
        ## the record is not in any restricted collection
        return (0, '')
    elif record_exists(recid) > 0:
        ## We are in the case where webcoll has not run.
        ## Let's authorize SUPERADMIN
        (auth_code, auth_msg) = acc_authorize_action(user_info, VIEWRESTRCOLL, collection=None)
        if auth_code == 0:
            return (0, '')
        else:
            ## Too bad. Let's print a nice message:
            return (1, """The record you are trying to access has just been
submitted to the system and needs to be assigned to the
proper collections. It is currently restricted for security reasons
until the assignment will be fully completed. Please come back later to
properly access this record.""")
    else:
        ## The record either does not exists or has been deleted.
        ## Let's handle these situations outside of this code.
        return (0, '')

class IndexStemmingDataCacher(DataCacher):
    """
    Provides cache for stemming information for word/phrase indexes.
    This class is not to be used directly; use function
    get_index_stemming_language() instead.
    """
    def __init__(self):
        def cache_filler():
            try:
                res = run_sql("""SELECT id, stemming_language FROM idxINDEX""")
            except DatabaseError:
                # database problems, return empty cache
                return {}
            return dict(res)

        def timestamp_verifier():
            return get_table_update_time('idxINDEX')

        DataCacher.__init__(self, cache_filler, timestamp_verifier)

try:
    index_stemming_cache.is_ok_p
except Exception:
    index_stemming_cache = IndexStemmingDataCacher()

def get_index_stemming_language(index_id, recreate_cache_if_needed=True):
    """Return stemming langugage for given index."""
    if recreate_cache_if_needed:
        index_stemming_cache.recreate_cache_if_needed()
    return index_stemming_cache.cache[index_id]

class CollectionRecListDataCacher(DataCacher):
    """
    Provides cache for collection reclist hitsets.  This class is not
    to be used directly; use function get_collection_reclist() instead.
    """
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

        def timestamp_verifier():
            return get_table_update_time('collection')

        DataCacher.__init__(self, cache_filler, timestamp_verifier)

try:
    if not collection_reclist_cache.is_ok_p:
        raise Exception
except Exception:
    collection_reclist_cache = CollectionRecListDataCacher()

def get_collection_reclist(coll, recreate_cache_if_needed=True):
    """Return hitset of recIDs that belong to the collection 'coll'."""
    if recreate_cache_if_needed:
        collection_reclist_cache.recreate_cache_if_needed()
    if not collection_reclist_cache.cache[coll]:
        # not yet it the cache, so calculate it and fill the cache:
        set = intbitset()
        query = "SELECT nbrecs,reclist FROM collection WHERE name=%s"
        res = run_sql(query, (coll, ), 1)
        if res:
            try:
                set = intbitset(res[0][1])
            except:
                pass
        collection_reclist_cache.cache[coll] = set
    # finally, return reclist:
    return collection_reclist_cache.cache[coll]

def get_available_output_formats(visible_only=False):
    """
    Return the list of available output formats.  When visible_only is
    True, returns only those output formats that have visibility flag
    set to 1.
    """

    formats = []
    query = "SELECT code,name FROM format"
    if visible_only:
        query += " WHERE visibility='1'"
    query += " ORDER BY name ASC"
    res = run_sql(query)
    if res:
        # propose found formats:
        for code, name in res:
            formats.append({ 'value' : code,
                             'text' : name
                           })
    else:
        formats.append({'value' : 'hb',
                        'text' : "HTML brief"
                       })
    return formats

class SearchResultsCache(DataCacher):
    """
    Provides temporary lazy cache for Search Results.
    Useful when users click on `next page'.
    """
    def __init__(self):
        def cache_filler():
            return {}
        def timestamp_verifier():
            return '1970-01-01 00:00:00' # lazy cache is always okay;
                                         # its filling is governed by
                                         # CFG_WEBSEARCH_SEARCH_CACHE_SIZE
        DataCacher.__init__(self, cache_filler, timestamp_verifier)

try:
    if not search_results_cache.is_ok_p:
        raise Exception
except Exception:
    search_results_cache = SearchResultsCache()

class CollectionI18nNameDataCacher(DataCacher):
    """
    Provides cache for I18N collection names.  This class is not to be
    used directly; use function get_coll_i18nname() instead.
    """
    def __init__(self):
        def cache_filler():
            ret = {}
            try:
                res = run_sql("SELECT c.name,cn.ln,cn.value FROM collectionname AS cn, collection AS c WHERE cn.id_collection=c.id AND cn.type='ln'") # ln=long name
            except Exception:
                # database problems
                return {}
            for c, ln, i18nname in res:
                if i18nname:
                    if not ret.has_key(c):
                        ret[c] = {}
                    ret[c][ln] = i18nname
            return ret

        def timestamp_verifier():
            return get_table_update_time('collectionname')

        DataCacher.__init__(self, cache_filler, timestamp_verifier)

try:
    if not collection_i18nname_cache.is_ok_p:
        raise Exception
except Exception:
    collection_i18nname_cache = CollectionI18nNameDataCacher()

def get_coll_i18nname(c, ln=CFG_SITE_LANG, verify_cache_timestamp=True):
    """
    Return nicely formatted collection name (of the name type `ln'
    (=long name)) for collection C in language LN.

    This function uses collection_i18nname_cache, but it verifies
    whether the cache is up-to-date first by default.  This
    verification step is performed by checking the DB table update
    time.  So, if you call this function 1000 times, it can get very
    slow because it will do 1000 table update time verifications, even
    though collection names change not that often.

    Hence the parameter VERIFY_CACHE_TIMESTAMP which, when set to
    False, will assume the cache is already up-to-date.  This is
    useful namely in the generation of collection lists for the search
    results page.
    """
    if verify_cache_timestamp:
        collection_i18nname_cache.recreate_cache_if_needed()
    out = c
    try:
        out = collection_i18nname_cache.cache[c][ln]
    except KeyError:
        pass # translation in LN does not exist
    return out

class FieldI18nNameDataCacher(DataCacher):
    """
    Provides cache for I18N field names.  This class is not to be used
    directly; use function get_field_i18nname() instead.
    """
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

        def timestamp_verifier():
            return get_table_update_time('fieldname')

        DataCacher.__init__(self, cache_filler, timestamp_verifier)

try:
    if not field_i18nname_cache.is_ok_p:
        raise Exception
except Exception:
    field_i18nname_cache = FieldI18nNameDataCacher()

def get_field_i18nname(f, ln=CFG_SITE_LANG, verify_cache_timestamp=True):
    """
    Return nicely formatted field name (of type 'ln', 'long name') for
    field F in language LN.

    If VERIFY_CACHE_TIMESTAMP is set to True, then verify DB timestamp
    and field I18N name cache timestamp and refresh cache from the DB
    if needed.  Otherwise don't bother checking DB timestamp and
    return the cached value.  (This is useful when get_field_i18nname
    is called inside a loop.)
    """
    if verify_cache_timestamp:
        field_i18nname_cache.recreate_cache_if_needed()
    out = f
    try:
        out = field_i18nname_cache.cache[f][ln]
    except KeyError:
        pass # translation in LN does not exist
    return out

def get_alphabetically_ordered_collection_list(level=0, ln=CFG_SITE_LANG):
    """Returns nicely ordered (score respected) list of collections, more exactly list of tuples
       (collection name, printable collection name).
       Suitable for create_search_box()."""
    out = []
    res = run_sql("SELECT id,name FROM collection ORDER BY name ASC")
    for c_id, c_name in res:
        # make a nice printable name (e.g. truncate c_printable for
        # long collection names in given language):
        c_printable_fullname = get_coll_i18nname(c_name, ln, False)
        c_printable = wash_index_term(c_printable_fullname, 30, False)
        if c_printable != c_printable_fullname:
            c_printable = c_printable + "..."
        if level:
            c_printable = " " + level * '-' + " " + c_printable
        out.append([c_name, c_printable])
    return out

def get_nicely_ordered_collection_list(collid=1, level=0, ln=CFG_SITE_LANG):
    """Returns nicely ordered (score respected) list of collections, more exactly list of tuples
       (collection name, printable collection name).
       Suitable for create_search_box()."""
    colls_nicely_ordered = []
    res = run_sql("""SELECT c.name,cc.id_son FROM collection_collection AS cc, collection AS c
                     WHERE c.id=cc.id_son AND cc.id_dad=%s ORDER BY score DESC""", (collid, ))
    for c, cid in res:
        # make a nice printable name (e.g. truncate c_printable for
        # long collection names in given language):
        c_printable_fullname = get_coll_i18nname(c, ln, False)
        c_printable = wash_index_term(c_printable_fullname, 30, False)
        if c_printable != c_printable_fullname:
            c_printable = c_printable + "..."
        if level:
            c_printable = " " + level * '-' + " " + c_printable
        colls_nicely_ordered.append([c, c_printable])
        colls_nicely_ordered  = colls_nicely_ordered + get_nicely_ordered_collection_list(cid, level+1, ln=ln)
    return colls_nicely_ordered

def get_index_id_from_field(field):
    """
    Return index id with name corresponding to FIELD, or the first
    index id where the logical field code named FIELD is indexed.

    Return zero in case there is no index defined for this field.

    Example: field='author', output=4.
    """
    out = 0
    if not field:
        field = 'global' # empty string field means 'global' index (field 'anyfield')

    # first look in the index table:
    res = run_sql("""SELECT id FROM idxINDEX WHERE name=%s""", (field,))
    if res:
        out = res[0][0]
        return out

    # not found in the index table, now look in the field table:
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
            words[word] = 1
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

    # FIXME: quick hack for the journal index
    if f == 'journal':
        opfts.append(['+', p, f, 'w'])
        return opfts

    ## check arguments: is desired matching type set?
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
                print_warning(req, "Matching type '%s' is not implemented yet." % cgi.escape(m), "Warning")
            opfts.append(['+', "%" + p + "%", f, 'w'])
    else:
        ## B - matching type is not known: let us try to determine it by some heuristics
        if f and p[0] == '"' and p[-1] == '"':
            ## B0 - does 'p' start and end by double quote, and is 'f' defined? => doing ACC search
            opfts.append(['+', p[1:-1], f, 'a'])
        elif f in ('author', 'firstauthor', 'exactauthor', 'exactfirstauthor') and author_name_requires_phrase_search(p):
            ## B1 - do we search in author, and does 'p' contain space/comma/dot/etc?
            ## => doing washed ACC search
            opfts.append(['+', p, f, 'a'])
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
            # and spaces after colon as well:
            p = re_pattern_spaces_after_colon.sub(lambda x: string.replace(x.group(1), ' ', '__SPACE__'), p)
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
                    fi = wash_field(fi)
                    # test whether fi is a real index code or a MARC-tag defined code:
                    if fi in get_fieldcodes() or '00' <= fi[:2] <= '99':
                        pass
                    else:
                        # it is not, so join it back:
                        fi, pi = f, fi + ":" + pi
                else:
                    fi, pi = f, pi
                # wash 'fi' argument:
                fi = wash_field(fi)
                # wash 'pi' argument:
                pi = pi.strip() # strip eventual spaces
                if re_quotes.match(pi):
                    # B3a - quotes are found => do ACC search (phrase search)
                    if pi[0] == '"' and pi[-1] == '"':
                        pi = string.replace(pi, '"', '') # remove quote signs
                        opfts.append([oi, pi, fi, 'a'])
                    elif pi[0] == "'" and pi[-1] == "'":
                        pi = string.replace(pi, "'", "") # remove quote signs
                        opfts.append([oi, "%" + pi + "%", fi, 'a'])
                    else: # unbalanced quotes, so fall back to WRD query:
                        opfts.append([oi, pi, fi, 'w'])
                elif pi.startswith('/') and pi.endswith('/'):
                    # B3b - pi has slashes around => do regexp search
                    opfts.append([oi, pi[1:-1], fi, 'r'])
                elif fi and len(fi) > 1 and str(fi[0]).isdigit() and str(fi[1]).isdigit():
                    # B3c - fi exists and starts by two digits => do ACC search
                    opfts.append([oi, pi, fi, 'a'])
                elif fi and not get_index_id_from_field(fi) and get_field_name(fi):
                    # B3d - logical field fi exists but there is no WRD index for fi => try ACC search
                    opfts.append([oi, pi, fi, 'a'])
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

    ## replace old logical field names if applicable:
    if CFG_WEBSEARCH_FIELDS_CONVERT:
        opfts = [[o,p,wash_field(f),t] for o,p,f,t in opfts]

    ## return search units:
    return opfts

def page_start(req, of, cc, aas, ln, uid, title_message=None,
               description='', keywords='', recID=-1, tab='', p=''):
    """
    Start page according to given output format.

    @param title_message: title of the page, not escaped for HTML
    @param description: description of the page, not escaped for HTML
    @param keywords: keywords of the page, not escaped for HTML
    """
    _ = gettext_set_language(ln)

    if not req or isinstance(req, cStringIO.OutputType):
        return # we were called from CLI

    if not title_message:
        title_message = _("Search Results")

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
            keywords = "%s, WebSearch, %s" % (get_coll_i18nname(CFG_SITE_NAME, ln, False), get_coll_i18nname(cc, ln, False))

        ## generate RSS URL:
        argd = {}
        if req.args:
            argd = cgi.parse_qs(req.args)
        rssurl = websearch_templates.build_rss_url(argd)

        ## add MathJax if displaying single records (FIXME: find
        ## eventual better place to this code)
        if of.lower() in CFG_WEBSEARCH_USE_MATHJAX_FOR_FORMATS:
            metaheaderadd = get_mathjax_header(req.is_https())
        else:
            metaheaderadd = ''

        ## generate navtrail:
        navtrail = create_navtrail_links(cc, aas, ln)
        if navtrail != '':
            navtrail += ' &gt; '
        if (tab != '' or ((of != '' or of.lower() != 'hd') and of != 'hb')) and \
               recID != -1:
            # If we are not in information tab in HD format, customize
            # the nav. trail to have a link back to main record. (Due
            # to the way perform_request_search() works, hb
            # (lowercase) is equal to hd)
            navtrail += ' <a class="navtrail" href="%s/%s/%s">%s</a>' % \
                            (CFG_SITE_URL, CFG_SITE_RECORD, recID, cgi.escape(title_message))
            if (of != '' or of.lower() != 'hd') and of != 'hb':
                # Export
                format_name = of
                query = "SELECT name FROM format WHERE code=%s"
                res = run_sql(query, (of,))
                if res:
                    format_name = res[0][0]
                navtrail += ' &gt; ' + format_name
            else:
                # Discussion, citations, etc. tabs
                tab_label = get_detailed_page_tabs(cc, ln=ln)[tab]['label']
                navtrail += ' &gt; ' + _(tab_label)
        else:
            navtrail += cgi.escape(title_message)

        if p:
            # we are serving search/browse results pages, so insert pattern:
            navtrail += ": " + cgi.escape(p)
            title_message = p + " - " + title_message

        body_css_classes = []
        if cc:
            # we know the collection, lets allow page styles based on cc

            #collection names may not satisfy rules for css classes which
            #are something like:  -?[_a-zA-Z]+[_a-zA-Z0-9-]*
            #however it isn't clear what we should do about cases with
            #numbers, so we leave them to fail.  Everything else becomes "_"

            css = nmtoken_from_string(cc).replace('.','_').replace('-','_').replace(':','_')
            body_css_classes.append(css)

        ## finally, print page header:
        req.write(pageheaderonly(req=req, title=title_message,
                                 navtrail=navtrail,
                                 description=description,
                                 keywords=keywords,
                                 metaheaderadd=metaheaderadd,
                                 uid=uid,
                                 language=ln,
                                 navmenuid='search',
                                 navtrail_append_title_p=0,
                                 rssurl=rssurl,
                                 body_css_classes=body_css_classes))
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
    return

def create_page_title_search_pattern_info(p, p1, p2, p3):
    """Create the search pattern bit for the page <title> web page
    HTML header.  Basically combine p and (p1,p2,p3) together so that
    the page header may be filled whether we are in the Simple Search
    or Advanced Search interface contexts."""
    out = ""
    if p:
        out = p
    else:
        out = p1
        if p2:
            out += ' ' + p2
        if p3:
            out += ' ' + p3
    return out

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
    # trailing space in May distinguishes short/long form of the month name
    for mm, month in [(1, _("January")), (2, _("February")), (3, _("March")), (4, _("April")), \
                      (5, _("May ")), (6, _("June")), (7, _("July")), (8, _("August")), \
                      (9, _("September")), (10, _("October")), (11, _("November")), (12, _("December"))]:
        box += """<option value="%02d"%s>%s""" % (mm, is_selected(mm, selected_month), month.strip())
    box += """</select>"""
    # year
    box += """<select name="%sy">""" % name
    box += """<option value="">%s""" % _("any year")
    this_year = int(time.strftime("%Y", time.localtime()))
    for year in range(this_year-20, this_year+1):
        box += """<option value="%d"%s>%d""" % (year, is_selected(year, selected_year), year)
    box += """</select>"""
    return box

def create_search_box(cc, colls, p, f, rg, sf, so, sp, rm, of, ot, aas,
                      ln, p1, f1, m1, op1, p2, f2, m2, op2, p3, f3,
                      m3, sc, pl, d1y, d1m, d1d, d2y, d2m, d2d, dt, jrec, ec,
                      action=""):

    """Create search box for 'search again in the results page' functionality."""

    # load the right message language
    _ = gettext_set_language(ln)

    # some computations
    cc_intl = get_coll_i18nname(cc, ln, False)
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
                              'text' : '*** %s ***' % _("any public collection")
                            })
                # this field is used to remove the current collection from the ones to be searched.
                temp.append({ 'value' : '',
                              'text' : '*** %s ***' % _("remove this collection")
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
    else: # we searched in CFG_SITE_NAME, so print 'any public collection' heading
        coll_selects.append([{ 'value' : CFG_SITE_NAME,
                               'text' : '*** %s ***' % _("any public collection")
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

    formats = get_available_output_formats(visible_only=True)

    # show collections in the search box? (not if there is only one
    # collection defined, and not if we are in light search)
    show_colls = True
    show_title = True
    if len(collection_reclist_cache.cache.keys()) == 1 or \
           aas == -1:
        show_colls = False
        show_title = False

    if cc == CFG_SITE_NAME:
        show_title = False

    if CFG_INSPIRE_SITE:
        show_title = False

    return websearch_templates.tmpl_search_box(
             ln = ln,
             aas = aas,
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
             show_colls = show_colls,
             show_title = show_title,
           )

def create_navtrail_links(cc=CFG_SITE_NAME, aas=0, ln=CFG_SITE_LANG, self_p=1, tab=''):
    """Creates navigation trail links, i.e. links to collection
    ancestors (except Home collection).  If aas==1, then links to
    Advanced Search interfaces; otherwise Simple Search.
    """

    dads = []
    for dad in get_coll_ancestors(cc):
        if dad != CFG_SITE_NAME: # exclude Home collection
            dads.append ((dad, get_coll_i18nname(dad, ln, False)))

    if self_p and cc != CFG_SITE_NAME:
        dads.append((cc, get_coll_i18nname(cc, ln, False)))

    return websearch_templates.tmpl_navtrail_links(
        aas=aas, ln=ln, dads=dads)

def get_searchwithin_fields(ln='en', colID=None):
    """Retrieves the fields name used in the 'search within' selection box for the collection ID colID."""
    res = None
    if colID:
        res = run_sql("""SELECT f.code,f.name FROM field AS f, collection_field_fieldvalue AS cff
                                 WHERE cff.type='sew' AND cff.id_collection=%s AND cff.id_field=f.id
                              ORDER BY cff.score DESC, f.name ASC""", (colID,))
    if not res:
        res = run_sql("SELECT code,name FROM field ORDER BY name ASC")
    fields = [{
                'value' : '',
                'text' : get_field_i18nname("any field", ln, False)
              }]
    for field_code, field_name in res:
        if field_code and field_code != "anyfield":
            fields.append({ 'value' : field_code,
                            'text' : get_field_i18nname(field_name, ln, False)
                          })
    return fields

def get_sortby_fields(ln='en', colID=None):
    """Retrieves the fields name used in the 'sort by' selection box for the collection ID colID."""
    _ = gettext_set_language(ln)
    res = None
    if colID:
        res = run_sql("""SELECT DISTINCT(f.code),f.name FROM field AS f, collection_field_fieldvalue AS cff
                                 WHERE cff.type='soo' AND cff.id_collection=%s AND cff.id_field=f.id
                              ORDER BY cff.score DESC, f.name ASC""", (colID,))
    if not res:
        # no sort fields defined for this colID, try to take Home collection:
        res = run_sql("""SELECT DISTINCT(f.code),f.name FROM field AS f, collection_field_fieldvalue AS cff
                                 WHERE cff.type='soo' AND cff.id_collection=%s AND cff.id_field=f.id
                                 ORDER BY cff.score DESC, f.name ASC""", (1,))
    if not res:
        # no sort fields defined for the Home collection, take all sort fields defined wherever they are:
        res = run_sql("""SELECT DISTINCT(f.code),f.name FROM field AS f, collection_field_fieldvalue AS cff
                                 WHERE cff.type='soo' AND cff.id_field=f.id
                                 ORDER BY cff.score DESC, f.name ASC""",)
    fields = [{
                'value' : '',
                'text' : _("latest first")
              }]
    for field_code, field_name in res:
        if field_code and field_code != "anyfield":
            fields.append({ 'value' : field_code,
                            'text' : get_field_i18nname(field_name, ln, False)
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

def wash_colls(cc, c, split_colls=0, verbose=0):
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
    # list to hold the hosted collections to be searched and displayed
    hosted_colls_out = []
    debug = ""

    if verbose:
        debug += "<br />"
        debug += "<br />1) --- initial parameters ---"
        debug += "<br />cc : %s" % cc
        debug += "<br />c : %s" % c
        debug += "<br />"

    # check what type is 'cc':
    if type(cc) is list:
        for ci in cc:
            if collection_reclist_cache.cache.has_key(ci):
                # yes this collection is real, so use it:
                cc = ci
                break
    else:
        # check once if cc is real:
        if not collection_reclist_cache.cache.has_key(cc):
            if cc:
                raise InvenioWebSearchUnknownCollectionError(cc)
            else:
                cc = CFG_SITE_NAME # cc is not set, so replace it with Home collection

    # check type of 'c' argument:
    if type(c) is list:
        colls = c
    else:
        colls = [c]

    if verbose:
        debug += "<br />2) --- after check for the integrity of cc and the being or not c a list ---"
        debug += "<br />cc : %s" % cc
        debug += "<br />c : %s" % c
        debug += "<br />"

    # remove all 'unreal' collections:
    colls_real = []
    for coll in colls:
        if collection_reclist_cache.cache.has_key(coll):
            colls_real.append(coll)
        else:
            if coll:
                raise InvenioWebSearchUnknownCollectionError(coll)
    colls = colls_real

    if verbose:
        debug += "<br />3) --- keeping only the real colls of c ---"
        debug += "<br />colls : %s" % colls
        debug += "<br />"

    # check if some real collections remain:
    if len(colls)==0:
        colls = [cc]

    if verbose:
        debug += "<br />4) --- in case no colls were left we use cc directly ---"
        debug += "<br />colls : %s" % colls
        debug += "<br />"

    # then let us check the list of non-restricted "real" sons of 'cc' and compare it to 'coll':
    res = run_sql("""SELECT c.name FROM collection AS c,
                                        collection_collection AS cc,
                                        collection AS ccc
                     WHERE c.id=cc.id_son AND cc.id_dad=ccc.id
                       AND ccc.name=%s AND cc.type='r'""", (cc,))

    # list that holds all the non restricted sons of cc that are also not hosted collections
    l_cc_nonrestricted_sons_and_nonhosted_colls = []
    res_hosted = run_sql("""SELECT c.name FROM collection AS c,
                         collection_collection AS cc,
                         collection AS ccc
                         WHERE c.id=cc.id_son AND cc.id_dad=ccc.id
                         AND ccc.name=%s AND cc.type='r'
                         AND (c.dbquery NOT LIKE 'hostedcollection:%%' OR c.dbquery IS NULL)""", (cc,))
    for row_hosted in res_hosted:
        l_cc_nonrestricted_sons_and_nonhosted_colls.append(row_hosted[0])
    l_cc_nonrestricted_sons_and_nonhosted_colls.sort()

    l_cc_nonrestricted_sons = []
    l_c = colls[:]
    for row in res:
        if not collection_restricted_p(row[0]):
            l_cc_nonrestricted_sons.append(row[0])
    l_c.sort()
    l_cc_nonrestricted_sons.sort()
    if l_cc_nonrestricted_sons == l_c:
        colls_out_for_display = [cc] # yep, washing permitted, it is sufficient to display 'cc'
    # the following elif is a hack that preserves the above funcionality when we start searching from
    # the frontpage with some hosted collections deselected (either by default or manually)
    elif set(l_cc_nonrestricted_sons_and_nonhosted_colls).issubset(set(l_c)):
        colls_out_for_display = colls
        split_colls = 0
    else:
        colls_out_for_display = colls # nope, we need to display all 'colls' successively

    # remove duplicates:
    #colls_out_for_display_nondups=filter(lambda x, colls_out_for_display=colls_out_for_display: colls_out_for_display[x-1] not in colls_out_for_display[x:], range(1, len(colls_out_for_display)+1))
    #colls_out_for_display = map(lambda x, colls_out_for_display=colls_out_for_display:colls_out_for_display[x-1], colls_out_for_display_nondups)
    #colls_out_for_display = list(set(colls_out_for_display))
    #remove duplicates while preserving the order
    set_out = set()
    colls_out_for_display = [coll for coll in colls_out_for_display if coll not in set_out and not set_out.add(coll)]

    if verbose:
        debug += "<br />5) --- decide whether colls_out_for_diplay should be colls or is it sufficient for it to be cc; remove duplicates ---"
        debug += "<br />colls_out_for_display : %s" % colls_out_for_display
        debug += "<br />"

    # FIXME: The below quoted part of the code has been commented out
    # because it prevents searching in individual restricted daughter
    # collections when both parent and all its public daughter
    # collections were asked for, in addition to some restricted
    # daughter collections.  The removal was introduced for hosted
    # collections, so we may want to double check in this context.

    # the following piece of code takes care of removing collections whose ancestors are going to be searched anyway
    # list to hold the collections to be removed
    #colls_to_be_removed = []
    # first calculate the collections that can safely be removed
    #for coll in colls_out_for_display:
    #    for ancestor in get_coll_ancestors(coll):
    #        #if ancestor in colls_out_for_display: colls_to_be_removed.append(coll)
    #        if ancestor in colls_out_for_display and not is_hosted_collection(coll): colls_to_be_removed.append(coll)
    # secondly remove the collections
    #for coll in colls_to_be_removed:
    #    colls_out_for_display.remove(coll)

    if verbose:
        debug += "<br />6) --- remove collections that have ancestors about to be search, unless they are hosted ---"
        debug += "<br />colls_out_for_display : %s" % colls_out_for_display
        debug += "<br />"

    # calculate the hosted collections to be searched.
    if colls_out_for_display == [cc]:
        if is_hosted_collection(cc):
            hosted_colls_out.append(cc)
        else:
            for coll in get_coll_sons(cc):
                if is_hosted_collection(coll):
                    hosted_colls_out.append(coll)
    else:
        for coll in colls_out_for_display:
            if is_hosted_collection(coll):
                hosted_colls_out.append(coll)

    if verbose:
        debug += "<br />7) --- calculate the hosted_colls_out ---"
        debug += "<br />hosted_colls_out : %s" % hosted_colls_out
        debug += "<br />"

    # second, let us decide on collection splitting:
    if split_colls == 0:
        # type A - no sons are wanted
        colls_out = colls_out_for_display
    else:
        # type B - sons (first-level descendants) are wanted
        for coll in colls_out_for_display:
            coll_sons = get_coll_sons(coll)
            if coll_sons == []:
                colls_out.append(coll)
            else:
                for coll_son in coll_sons:
                    if not is_hosted_collection(coll_son):
                        colls_out.append(coll_son)
            #else:
            #    colls_out = colls_out + coll_sons

    # remove duplicates:
    #colls_out_nondups=filter(lambda x, colls_out=colls_out: colls_out[x-1] not in colls_out[x:], range(1, len(colls_out)+1))
    #colls_out = map(lambda x, colls_out=colls_out:colls_out[x-1], colls_out_nondups)
    #colls_out = list(set(colls_out))
    #remove duplicates while preserving the order
    set_out = set()
    colls_out = [coll for coll in colls_out if coll not in set_out and not set_out.add(coll)]


    if verbose:
        debug += "<br />8) --- calculate the colls_out; remove duplicates ---"
        debug += "<br />colls_out : %s" % colls_out
        debug += "<br />"

    # remove the hosted collections from the collections to be searched
    if hosted_colls_out:
        for coll in hosted_colls_out:
            try:
                colls_out.remove(coll)
            except ValueError:
                # in case coll was not found in colls_out
                pass

    if verbose:
        debug += "<br />9) --- remove the hosted_colls from the colls_out ---"
        debug += "<br />colls_out : %s" % colls_out

    return (cc, colls_out_for_display, colls_out, hosted_colls_out, debug)

def wash_index_term(term, max_char_length=50, lower_term=True):
    """
    Return washed form of the index term TERM that would be suitable
    for storing into idxWORD* tables.  I.e., lower the TERM if
    LOWER_TERM is True, and truncate it safely to MAX_CHAR_LENGTH
    UTF-8 characters (meaning, in principle, 4*MAX_CHAR_LENGTH bytes).

    The function works by an internal conversion of TERM, when needed,
    from its input Python UTF-8 binary string format into Python
    Unicode format, and then truncating it safely to the given number
    of UTF-8 characters, without possible mis-truncation in the middle
    of a multi-byte UTF-8 character that could otherwise happen if we
    would have been working with UTF-8 binary representation directly.

    Note that MAX_CHAR_LENGTH corresponds to the length of the term
    column in idxINDEX* tables.
    """
    if lower_term:
        washed_term = unicode(term, 'utf-8').lower()
    else:
        washed_term = unicode(term, 'utf-8')
    if len(washed_term) <= max_char_length:
        # no need to truncate the term, because it will fit
        # nicely even if it uses four-byte UTF-8 characters
        return washed_term.encode('utf-8')
    else:
        # truncate the term in a safe position:
        return washed_term[:max_char_length].encode('utf-8')

def lower_index_term(term):
    """
    Return safely lowered index term TERM.  This is done by converting
    to UTF-8 first, because standard Python lower() function is not
    UTF-8 safe.  To be called by both the search engine and the
    indexer when appropriate (e.g. before stemming).

    In case of problems with UTF-8 compliance, this function raises
    UnicodeDecodeError, so the client code may want to catch it.
    """
    return unicode(term, 'utf-8').lower().encode('utf-8')


def get_synonym_terms(term, kbr_name, match_type):
    """
    Return list of synonyms for TERM by looking in KBR_NAME in
    MATCH_TYPE style.

    @param term: search-time term or index-time term
    @type term: str
    @param kbr_name: knowledge base name
    @type kbr_name: str
    @param match_type: specifies how the term matches against the KBR
        before doing the lookup.  Could be `exact' (default),
        'leading_to_comma', `leading_to_number'.
    @type match_type: str
    @return: list of term synonyms
    @rtype: list of strings
    """
    dterms = {}
    ## exact match is default:
    term_for_lookup = term
    term_remainder = ''
    ## but maybe match different term:
    if match_type == 'leading_to_comma':
        mmm = re.match(r'^(.*?)(\s*,.*)$', term)
        if mmm:
            term_for_lookup = mmm.group(1)
            term_remainder = mmm.group(2)
    elif match_type == 'leading_to_number':
        mmm = re.match(r'^(.*?)(\s*\d.*)$', term)
        if mmm:
            term_for_lookup = mmm.group(1)
            term_remainder = mmm.group(2)
    ## FIXME: workaround: escaping SQL wild-card signs, since KBR's
    ## exact search is doing LIKE query, so would match everything:
    term_for_lookup = term_for_lookup.replace('%', '\%')
    ## OK, now find synonyms:
    for kbr_values in get_kbr_values(kbr_name,
                                     searchkey=term_for_lookup,
                                     searchtype='e'):
        for kbr_value in kbr_values:
            dterms[kbr_value + term_remainder] = 1
    ## return list of term synonyms:
    return dterms.keys()


def wash_output_format(format):
    """Wash output format FORMAT.  Currently only prevents input like
    'of=9' for backwards-compatible format that prints certain fields
    only.  (for this task, 'of=tm' is preferred)"""
    if str(format[0:3]).isdigit() and len(format) != 6:
        # asked to print MARC tags, but not enough digits,
        # so let's switch back to HTML brief default
        return 'hb'
    else:
        return format

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
    # replace spaces within quotes by __SPACE__ temporarily:
    p = re_pattern_single_quotes.sub(lambda x: "'"+string.replace(x.group(1), ' ', '__SPACE__')+"'", p)
    p = re_pattern_double_quotes.sub(lambda x: "\""+string.replace(x.group(1), ' ', '__SPACE__')+"\"", p)
    p = re_pattern_regexp_quotes.sub(lambda x: "/"+string.replace(x.group(1), ' ', '__SPACE__')+"/", p)
    # get rid of unquoted wildcards after spaces:
    p = re_pattern_wildcards_after_spaces.sub("\\1", p)
    # get rid of extremely short words (1-3 letters with wildcards):
    #p = re_pattern_short_words.sub("\\1", p)
    # replace back __SPACE__ by spaces:
    p = re_pattern_space.sub(" ", p)
    # replace special terms:
    p = re_pattern_today.sub(time.strftime("%Y-%m-%d", time.localtime()), p)
    # remove unnecessary whitespace:
    p = string.strip(p)
    # remove potentially wrong UTF-8 characters:
    p = wash_for_utf8(p)
    return p

def wash_field(f):
    """Wash field passed by URL."""
    if f:
        # get rid of unnecessary whitespace and make it lowercase
        # (e.g. Author -> author) to better suit iPhone etc input
        # mode:
        f = f.strip().lower()
    # wash legacy 'f' field names, e.g. replace 'wau' or `au' by
    # 'author', if applicable:
    if CFG_WEBSEARCH_FIELDS_CONVERT:
        f = CFG_WEBSEARCH_FIELDS_CONVERT.get(f, f)
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

def is_hosted_collection(coll):
    """Check if the given collection is a hosted one; i.e. its dbquery starts with hostedcollection:
    Returns True if it is, False if it's not or if the result is empty or if the query failed"""

    res = run_sql("SELECT dbquery FROM collection WHERE name=%s", (coll, ))
    try:
        return res[0][0].startswith("hostedcollection:")
    except:
        return False

def get_colID(c):
    "Return collection ID for collection name C.  Return None if no match found."
    colID = None
    res = run_sql("SELECT id FROM collection WHERE name=%s", (c,), 1)
    if res:
        colID = res[0][0]
    return colID

def get_coll_normalised_name(c):
    """Returns normalised collection name (case sensitive) for collection name
       C (case insensitive).
       Returns None if no match found."""
    try:
        return run_sql("SELECT name FROM collection WHERE name=%s", (c,))[0][0]
    except:
        return None

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
    query += " ORDER BY cc.score DESC"
    res = run_sql(query, (type, coll))
    for name in res:
        if not public_only or not collection_restricted_p(name[0]):
            coll_sons.append(name[0])
    return coll_sons

def get_coll_real_descendants(coll, type='_', get_hosted_colls=True):
    """Return a list of all descendants of collection 'coll' that are defined by a 'dbquery'.
       IOW, we need to decompose compound collections like "A & B" into "A" and "B" provided
       that "A & B" has no associated database query defined.
    """
    coll_sons = []
    res = run_sql("""SELECT c.name,c.dbquery FROM collection AS c
                     LEFT JOIN collection_collection AS cc ON c.id=cc.id_son
                     LEFT JOIN collection AS ccc ON ccc.id=cc.id_dad
                     WHERE ccc.name=%s AND cc.type LIKE %s ORDER BY cc.score DESC""",
                  (coll, type,))
    for name, dbquery in res:
        if dbquery: # this is 'real' collection, so return it:
            if get_hosted_colls:
                coll_sons.append(name)
            else:
                if not dbquery.startswith("hostedcollection:"):
                    coll_sons.append(name)
        else: # this is 'composed' collection, so recurse:
            coll_sons.extend(get_coll_real_descendants(name))
    return coll_sons

def browse_pattern(req, colls, p, f, rg, ln=CFG_SITE_LANG):
    """Browse either biliographic phrases or words indexes, and display it."""

    # load the right message language
    _ = gettext_set_language(ln)

    ## is p enclosed in quotes? (coming from exact search)
    if p.startswith('"') and p.endswith('"'):
        p = p[1:-1]

    p_orig = p
    ## okay, "real browse" follows:
    ## FIXME: the maths in the get_nearest_terms_in_bibxxx is just a test

    if not f and string.find(p, ":") > 0: # does 'p' contain ':'?
        f, p = string.split(p, ":", 1)

    ## do we search in words indexes?
    if not f:
        return browse_in_bibwords(req, p, f)

    index_id = get_index_id_from_field(f)
    if index_id != 0:
        coll = intbitset()
        for coll_name in colls:
            coll |= get_collection_reclist(coll_name)
        browsed_phrases_in_colls = get_nearest_terms_in_idxphrase_with_collection(p, index_id, rg/2, rg/2, coll)
    else:
        browsed_phrases = get_nearest_terms_in_bibxxx(p, f, (rg+1)/2+1, (rg-1)/2+1)
        while not browsed_phrases:
            # try again and again with shorter and shorter pattern:
            try:
                p = p[:-1]
                browsed_phrases = get_nearest_terms_in_bibxxx(p, f, (rg+1)/2+1, (rg-1)/2+1)
            except:
                # probably there are no hits at all:
                req.write(_("No values found."))
                return

        ## try to check hits in these particular collection selection:
        browsed_phrases_in_colls = []
        if 0:
            for phrase in browsed_phrases:
                phrase_hitset = intbitset()
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
            fn=get_field_i18nname(get_field_name(f) or f, ln, False),
            ln=ln,
            browsed_phrases_in_colls=browsed_phrases_in_colls,
            colls=colls,
            rg=rg,
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

def search_pattern(req=None, p=None, f=None, m=None, ap=0, of="id", verbose=0, ln=CFG_SITE_LANG, display_nearest_terms_box=True, wl=0):
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

    hitset_empty = intbitset()
    # sanity check:
    if not p:
        hitset_full = intbitset(trailing_bits=1)
        hitset_full.discard(0)
        # no pattern, so return all universe
        return hitset_full
    # search stage 1: break up arguments into basic search units:
    if verbose and of.startswith("h"):
        t1 = os.times()[4]
    basic_search_units = create_basic_search_units(req, p, f, m, of)
    if verbose and of.startswith("h"):
        t2 = os.times()[4]
        print_warning(req, "Search stage 1: basic search units are: %s" % cgi.escape(repr(basic_search_units)))
        print_warning(req, "Search stage 1: execution took %.2f seconds." % (t2 - t1))
    # search stage 2: do search for each search unit and verify hit presence:
    if verbose and of.startswith("h"):
        t1 = os.times()[4]
    basic_search_units_hitsets = []
    #prepare hiddenfield-related..
    myhiddens = CFG_BIBFORMAT_HIDDEN_TAGS
    can_see_hidden = False
    if req:
        user_info = collect_user_info(req)
        can_see_hidden = (acc_authorize_action(user_info, 'runbibedit')[0] == 0)
    if can_see_hidden:
        myhiddens = []

    if CFG_INSPIRE_SITE and of.startswith('h'):
        # fulltext/caption search warnings for INSPIRE:
        fields_to_be_searched = [f for o,p,f,m in basic_search_units]
        if 'fulltext' in fields_to_be_searched:
            print_warning(req, _("Warning: full-text search is only available for a subset of papers mostly from %(x_range_from_year)s-%(x_range_to_year)s.") % \
                          {'x_range_from_year': '2006',
                           'x_range_to_year': '2012'})
        elif 'caption' in fields_to_be_searched:
            print_warning(req, _("Warning: figure caption search is only available for a subset of papers mostly from %(x_range_from_year)s-%(x_range_to_year)s.") % \
                          {'x_range_from_year': '2008',
                           'x_range_to_year': '2012'})

    for idx_unit in xrange(len(basic_search_units)):
        bsu_o, bsu_p, bsu_f, bsu_m = basic_search_units[idx_unit]
        if bsu_f and len(bsu_f) < 2:
            if of.startswith("h"):
                print_warning(req, _("There is no index %s.  Searching for %s in all fields." % (bsu_f, bsu_p)))
            bsu_f = ''
            bsu_m = 'w'
            if of.startswith("h") and verbose:
                print_warning(req, _('Instead searching %s.' % str([bsu_o, bsu_p, bsu_f, bsu_m])))
        try:
            basic_search_unit_hitset = search_unit(bsu_p, bsu_f, bsu_m, wl)
        except InvenioWebSearchWildcardLimitError, excp:
            basic_search_unit_hitset = excp.res
            if of.startswith("h"):
                print_warning(req, _("Search term too generic, displaying only partial results..."))
        # FIXME: print warning if we use native full-text indexing
        if bsu_f == 'fulltext' and bsu_m != 'w' and of.startswith('h') and not CFG_SOLR_URL:
            print_warning(req, _("No phrase index available for fulltext yet, looking for word combination..."))
        #check that the user is allowed to search with this tag
        #if he/she tries it
        if bsu_f and len(bsu_f) > 1 and bsu_f[0].isdigit() and bsu_f[1].isdigit():
            for htag in myhiddens:
                ltag = len(htag)
                samelenfield = bsu_f[0:ltag]
                if samelenfield == htag: #user searches by a hidden tag
                    #we won't show you anything..
                    basic_search_unit_hitset = intbitset()
                    if verbose >= 9 and of.startswith("h"):
                        print_warning(req, "Pattern %s hitlist omitted since \
                                            it queries in a hidden tag %s" %
                                      (repr(bsu_p), repr(myhiddens)))
                    display_nearest_terms_box=False #..and stop spying, too.
        if verbose >= 9 and of.startswith("h"):
            print_warning(req, "Search stage 1: pattern %s gave hitlist %s" % (cgi.escape(bsu_p), basic_search_unit_hitset))
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
            if re.search(r'[^a-zA-Z0-9\s\:]', bsu_p) and bsu_f != 'refersto' and bsu_f != 'citedby':
                if bsu_p.startswith('"') and bsu_p.endswith('"'): # is it ACC query?
                    bsu_pn = re.sub(r'[^a-zA-Z0-9\s\:]+', "*", bsu_p)
                else: # it is WRD query
                    bsu_pn = re.sub(r'[^a-zA-Z0-9\s\:]+', " ", bsu_p)
                if verbose and of.startswith('h') and req:
                    print_warning(req, "Trying (%s,%s,%s)" % (cgi.escape(bsu_pn), cgi.escape(bsu_f), cgi.escape(bsu_m)))
                basic_search_unit_hitset = search_pattern(req=None, p=bsu_pn, f=bsu_f, m=bsu_m, of="id", ln=ln, wl=wl)
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
                    if of.startswith('h') and display_nearest_terms_box:
                        if req:
                            if bsu_f == "recid":
                                print_warning(req, _("Requested record does not seem to exist."))
                            else:
                                print_warning(req, create_nearest_terms_box(req.argd, bsu_p, bsu_f, bsu_m, ln=ln))
                    return hitset_empty
            else:
                # stage 2-3: no hits found either, propose nearest indexed terms:
                if of.startswith('h') and display_nearest_terms_box:
                    if req:
                        if bsu_f == "recid":
                            print_warning(req, _("Requested record does not seem to exist."))
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
    hitset_in_any_collection = intbitset(trailing_bits=1)
    hitset_in_any_collection.discard(0)
    for idx_unit in xrange(len(basic_search_units)):
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
                print_warning(req, "Invalid set operation %s." % cgi.escape(this_unit_operation), "Error")
    if len(hitset_in_any_collection) == 0:
        # no hits found, propose alternative boolean query:
        if of.startswith('h') and display_nearest_terms_box:
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

def search_pattern_parenthesised(req=None, p=None, f=None, m=None, ap=0, of="id", verbose=0, ln=CFG_SITE_LANG, display_nearest_terms_box=True, wl=0):
    """Search for complex pattern 'p' containing parenthesis within field 'f' according to
       matching type 'm'.  Return hitset of recIDs.

       For more details on the parameters see 'search_pattern'
    """
    _ = gettext_set_language(ln)
    spires_syntax_converter = SpiresToInvenioSyntaxConverter()
    spires_syntax_query = False

    # if the pattern uses SPIRES search syntax, convert it to Invenio syntax
    if spires_syntax_converter.is_applicable(p):
        spires_syntax_query = True
        p = spires_syntax_converter.convert_query(p)

    # sanity check: do not call parenthesised parser for search terms
    # like U(1):
    if not re_pattern_parens.search(p):
        return search_pattern(req, p, f, m, ap, of, verbose, ln, display_nearest_terms_box=display_nearest_terms_box, wl=wl)

    # Try searching with parentheses
    try:
        parser = SearchQueryParenthesisedParser()

        # get a hitset with all recids
        result_hitset = intbitset(trailing_bits=1)

        # parse the query. The result is list of [op1, expr1, op2, expr2, ..., opN, exprN]
        parsing_result = parser.parse_query(p)
        if verbose  and of.startswith("h"):
            print_warning(req, "Search stage 1: search_pattern_parenthesised() searched %s." % repr(p))
            print_warning(req, "Search stage 1: search_pattern_parenthesised() returned %s." % repr(parsing_result))

        # go through every pattern
        # calculate hitset for it
        # combine pattern's hitset with the result using the corresponding operator
        for index in xrange(0, len(parsing_result)-1, 2 ):
            current_operator = parsing_result[index]
            current_pattern = parsing_result[index+1]

            if CFG_INSPIRE_SITE and spires_syntax_query:
                # setting ap=0 to turn off approximate matching for 0 results.
                # Doesn't work well in combinations.
                # FIXME: The right fix involves collecting statuses for each
                #        hitset, then showing a nearest terms box exactly once,
                #        outside this loop.
                ap = 0
                display_nearest_terms_box=False

            # obtain a hitset for the current pattern
            current_hitset = search_pattern(req, current_pattern, f, m, ap, of, verbose, ln, display_nearest_terms_box=display_nearest_terms_box, wl=wl)

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
    except SyntaxError:

        print_warning(req, _("Search syntax misunderstood. Ignoring all parentheses in the query. If this doesn't help, please check your search and try again."))

        # remove the parentheses in the query. Current implementation removes all the parentheses,
        # but it could be improved to romove only these that are not inside quotes
        p = p.replace('(', ' ')
        p = p.replace(')', ' ')

        return search_pattern(req, p, f, m, ap, of, verbose, ln, display_nearest_terms_box=display_nearest_terms_box, wl=wl)


def search_unit(p, f=None, m=None, wl=0):
    """Search for basic search unit defined by pattern 'p' and field
       'f' and matching type 'm'.  Return hitset of recIDs.

       All the parameters are assumed to have been previously washed.
       'p' is assumed to be already a ``basic search unit'' so that it
       is searched as such and is not broken up in any way.  Only
       wildcard and span queries are being detected inside 'p'.

       If CFG_WEBSEARCH_SYNONYM_KBRS is set and we are searching in
       one of the indexes that has defined runtime synonym knowledge
       base, then look up there and automatically enrich search
       results with results for synonyms.

       In case the wildcard limit (wl) is greater than 0 and this limit
       is reached an InvenioWebSearchWildcardLimitError will be raised.
       In case you want to call this function with no limit for the
       wildcard queries, wl should be 0.

       This function is suitable as a low-level API.
    """

    ## create empty output results set:
    hitset = intbitset()
    if not p: # sanity checking
        return hitset

    ## eventually look up runtime synonyms:
    hitset_synonyms = intbitset()
    if CFG_WEBSEARCH_SYNONYM_KBRS.has_key(f):
        for p_synonym in get_synonym_terms(p,
                             CFG_WEBSEARCH_SYNONYM_KBRS[f][0],
                             CFG_WEBSEARCH_SYNONYM_KBRS[f][1]):
            if p_synonym != p:
                hitset_synonyms |= search_unit(p_synonym, f, m, wl)

    ## look up hits:
    if CFG_SOLR_URL and f == 'fulltext':
        # redirect to Solr/Lucene
        try:
            return search_unit_in_solr(p, f, m)
        except:
            # There were troubles with getting full-text search
            # results from Solr. Let us alert the admin of these
            # problems and let us simply return empty results to the
            # end user.
            register_exception(alert_admin=True)
            return hitset
    if f == 'datecreated':
        hitset = search_unit_in_bibrec(p, p, 'c')
    elif f == 'datemodified':
        hitset = search_unit_in_bibrec(p, p, 'm')
    elif f == 'refersto':
        # we are doing search by the citation count
        hitset = search_unit_refersto(p)
    elif f == 'citedby':
        # we are doing search by the citation count
        hitset = search_unit_citedby(p)
    elif m == 'a' or m == 'r':
        # we are doing either phrase search or regexp search
        if f == 'fulltext':
            # FIXME: workaround for not having phrase index yet
            return search_pattern(None, p, f, 'w')
        index_id = get_index_id_from_field(f)
        if index_id != 0:
            hitset = search_unit_in_idxphrases(p, f, m, wl)
        else:
            hitset = search_unit_in_bibxxx(p, f, m, wl)
    elif p.startswith("cited:"):
        # we are doing search by the citation count
        hitset = search_unit_by_times_cited(p[6:])
    else:
        # we are doing bibwords search by default
        hitset = search_unit_in_bibwords(p, f, m, wl=wl)

    ## merge synonym results and return total:
    hitset |= hitset_synonyms
    return hitset

def search_unit_in_bibwords(word, f, m=None, decompress=zlib.decompress, wl=0):
    """Searches for 'word' inside bibwordsX table for field 'f' and returns hitset of recIDs."""
    set = intbitset() # will hold output result set
    set_used = 0 # not-yet-used flag, to be able to circumvent set operations
    limit_reached = 0 # flag for knowing if the query limit has been reached

    # if no field is specified, search in the global index.
    f = f or 'anyfield'
    index_id = get_index_id_from_field(f)
    if index_id:
        bibwordsX = "idxWORD%02dF" % index_id
        stemming_language = get_index_stemming_language(index_id)
    else:
        return intbitset() # word index f does not exist

    # wash 'word' argument and run query:
    if f == 'authorcount' and word.endswith('+'):
        # field count query of the form N+ so transform N+ to N->99999:
        word = word[:-1] + '->99999'
    word = string.replace(word, '*', '%') # we now use '*' as the truncation character
    words = string.split(word, "->", 1) # check for span query
    if len(words) == 2:
        word0 = re_word.sub('', words[0])
        word1 = re_word.sub('', words[1])
        if stemming_language:
            word0 = lower_index_term(word0)
            word1 = lower_index_term(word1)
            word0 = stem(word0, stemming_language)
            word1 = stem(word1, stemming_language)
        word0_washed = wash_index_term(word0)
        word1_washed = wash_index_term(word1)
        if f == 'authorcount':
            # field count query; convert to integers in order
            # to have numerical behaviour for 'BETWEEN n1 AND n2' query
            try:
                word0_washed = int(word0_washed)
                word1_washed = int(word1_washed)
            except ValueError:
                pass
        try:
            res = run_sql_with_limit("SELECT term,hitlist FROM %s WHERE term BETWEEN %%s AND %%s" % bibwordsX,
                          (word0_washed, word1_washed), wildcard_limit = wl)
        except InvenioDbQueryWildcardLimitError, excp:
            res = excp.res
            limit_reached = 1 # set the limit reached flag to true
    else:
        if f == 'journal':
            pass # FIXME: quick hack for the journal index
        else:
            word = re_word.sub('', word)
        if stemming_language:
            word = lower_index_term(word)
            word = stem(word, stemming_language)
        if string.find(word, '%') >= 0: # do we have wildcard in the word?
            if f == 'journal':
                # FIXME: quick hack for the journal index
                # FIXME: we can run a sanity check here for all indexes
                res = ()
            else:
                try:
                    res = run_sql_with_limit("SELECT term,hitlist FROM %s WHERE term LIKE %%s" % bibwordsX,
                                  (wash_index_term(word),), wildcard_limit = wl)
                except InvenioDbQueryWildcardLimitError, excp:
                    res = excp.res
                    limit_reached = 1 # set the limit reached flag to true
        else:
            res = run_sql("SELECT term,hitlist FROM %s WHERE term=%%s" % bibwordsX,
                          (wash_index_term(word),))
    # fill the result set:
    for word, hitlist in res:
        hitset_bibwrd = intbitset(hitlist)
        # add the results:
        if set_used:
            set.union_update(hitset_bibwrd)
        else:
            set = hitset_bibwrd
            set_used = 1
    #check to see if the query limit was reached
    if limit_reached:
        #raise an exception, so we can print a nice message to the user
        raise InvenioWebSearchWildcardLimitError(set)
    # okay, return result set:
    return set

def search_unit_in_idxphrases(p, f, type, wl=0):
    """Searches for phrase 'p' inside idxPHRASE*F table for field 'f' and returns hitset of recIDs found.
    The search type is defined by 'type' (e.g. equals to 'r' for a regexp search)."""
    # call word search method in some cases:
    if f == 'authorcount':
        return search_unit_in_bibwords(p, f, wl=wl)
    set = intbitset() # will hold output result set
    set_used = 0 # not-yet-used flag, to be able to circumvent set operations
    limit_reached = 0 # flag for knowing if the query limit has been reached
    use_query_limit = False # flag for knowing if to limit the query results or not
    # deduce in which idxPHRASE table we will search:
    idxphraseX = "idxPHRASE%02dF" % get_index_id_from_field("anyfield")
    if f:
        index_id = get_index_id_from_field(f)
        if index_id:
            idxphraseX = "idxPHRASE%02dF" % index_id
        else:
            return intbitset() # phrase index f does not exist
    # detect query type (exact phrase, partial phrase, regexp):
    if type == 'r':
        query_addons = "REGEXP %s"
        query_params = (p,)
        use_query_limit = True
    else:
        p = string.replace(p, '*', '%') # we now use '*' as the truncation character
        ps = string.split(p, "->", 1) # check for span query:
        if len(ps) == 2 and not (ps[0].endswith(' ') or ps[1].startswith(' ')):
            query_addons = "BETWEEN %s AND %s"
            query_params = (ps[0], ps[1])
            use_query_limit = True
        else:
            if string.find(p, '%') > -1:
                query_addons = "LIKE %s"
                query_params = (p,)
                use_query_limit = True
            else:
                query_addons = "= %s"
                query_params = (p,)

    # special washing for fuzzy author index:
    if f in ('author', 'firstauthor', 'exactauthor', 'exactfirstauthor'):
        query_params_washed = ()
        for query_param in query_params:
            query_params_washed += (wash_author_name(query_param),)
        query_params = query_params_washed
    # perform search:
    if use_query_limit:
        try:
            res = run_sql_with_limit("SELECT term,hitlist FROM %s WHERE term %s" % (idxphraseX, query_addons),
                      query_params, wildcard_limit=wl)
        except InvenioDbQueryWildcardLimitError, excp:
            res = excp.res
            limit_reached = 1 # set the limit reached flag to true
    else:
        res = run_sql("SELECT term,hitlist FROM %s WHERE term %s" % (idxphraseX, query_addons), query_params)
    # fill the result set:
    for word, hitlist in res:
        hitset_bibphrase = intbitset(hitlist)
        # add the results:
        if set_used:
            set.union_update(hitset_bibphrase)
        else:
            set = hitset_bibphrase
            set_used = 1
    #check to see if the query limit was reached
    if limit_reached:
        #raise an exception, so we can print a nice message to the user
        raise InvenioWebSearchWildcardLimitError(set)
    # okay, return result set:
    return set

def search_unit_in_bibxxx(p, f, type, wl=0):
    """Searches for pattern 'p' inside bibxxx tables for field 'f' and returns hitset of recIDs found.
    The search type is defined by 'type' (e.g. equals to 'r' for a regexp search)."""

    # call word search method in some cases:
    if f == 'journal' or f == 'authorcount':
        return search_unit_in_bibwords(p, f, wl=wl)
    p_orig = p # saving for eventual future 'no match' reporting
    limit_reached = 0 # flag for knowing if the query limit has been reached
    use_query_limit = False  # flag for knowing if to limit the query results or not
    query_addons = "" # will hold additional SQL code for the query
    query_params = () # will hold parameters for the query (their number may vary depending on TYPE argument)
    # wash arguments:
    f = string.replace(f, '*', '%') # replace truncation char '*' in field definition
    if type == 'r':
        query_addons = "REGEXP %s"
        query_params = (p,)
        use_query_limit = True
    else:
        p = string.replace(p, '*', '%') # we now use '*' as the truncation character
        ps = string.split(p, "->", 1) # check for span query:
        if len(ps) == 2 and not (ps[0].endswith(' ') or ps[1].startswith(' ')):
            query_addons = "BETWEEN %s AND %s"
            query_params = (ps[0], ps[1])
            use_query_limit = True
        else:
            if string.find(p, '%') > -1:
                query_addons = "LIKE %s"
                query_params = (p,)
                use_query_limit = True
            else:
                query_addons = "= %s"
                query_params = (p,)
    # construct 'tl' which defines the tag list (MARC tags) to search in:
    tl = []
    if len(f) >= 2 and str(f[0]).isdigit() and str(f[1]).isdigit():
        tl.append(f) # 'f' seems to be okay as it starts by two digits
    else:
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
            if query_addons.find('BETWEEN') > -1 or query_addons.find('=') > -1:
                # verify that the params are integers (to avoid returning record 123 when searching for 123foo)
                try:
                    query_params = tuple(int(param) for param in query_params)
                except ValueError:
                    return intbitset()
            if use_query_limit:
                try:
                    res = run_sql_with_limit("SELECT id FROM bibrec WHERE id %s" % query_addons,
                              query_params, wildcard_limit=wl)
                except InvenioDbQueryWildcardLimitError, excp:
                    res = excp.res
                    limit_reached = 1 # set the limit reached flag to true
            else:
                res = run_sql("SELECT id FROM bibrec WHERE id %s" % query_addons,
                              query_params)
        else:
            query = "SELECT bibx.id_bibrec FROM %s AS bx LEFT JOIN %s AS bibx ON bx.id=bibx.id_bibxxx WHERE bx.value %s" % \
                    (bx, bibx, query_addons)
            if len(t) != 6 or t[-1:]=='%':
                # wildcard query, or only the beginning of field 't'
                # is defined, so add wildcard character:
                query += " AND bx.tag LIKE %s"
                query_params_and_tag = query_params + (t + '%',)
            else:
                # exact query for 't':
                query += " AND bx.tag=%s"
                query_params_and_tag = query_params + (t,)
            if use_query_limit:
                try:
                    res = run_sql_with_limit(query, query_params_and_tag, wildcard_limit=wl)
                except InvenioDbQueryWildcardLimitError, excp:
                    res = excp.res
                    limit_reached = 1 # set the limit reached flag to true
            else:
                res = run_sql(query, query_params_and_tag)
        # fill the result set:
        for id_bibrec in res:
            if id_bibrec[0]:
                l.append(id_bibrec[0])
    # check no of hits found:
    nb_hits = len(l)
    # okay, return result set:
    set = intbitset(l)
    #check to see if the query limit was reached
    if limit_reached:
        #raise an exception, so we can print a nice message to the user
        raise InvenioWebSearchWildcardLimitError(set)
    return set

def search_unit_in_solr(p, f=None, m=None):
    """
    Query the Solr full-text index and return an intbitset corresponding
    to the result.  Parameters (p,f,m) are usual search unit ones.
    """
    if m and (m == 'a' or m == 'r'): # phrase/regexp query
        if p.startswith('%') and p.endswith('%'):
            p = p[1:-1] # fix for partial phrase
        p = '"' + p + '"'
    return solr_get_bitset(p, CFG_SOLR_URL)

def search_unit_in_bibrec(datetext1, datetext2, type='c'):
    """
    Return hitset of recIDs found that were either created or modified
    (according to 'type' arg being 'c' or 'm') from datetext1 until datetext2, inclusive.
    Does not pay attention to pattern, collection, anything.  Useful
    to intersect later on with the 'real' query.
    """
    set = intbitset()
    if type.startswith("m"):
        type = "modification_date"
    else:
        type = "creation_date" # by default we are searching for creation dates

    parts = datetext1.split('->')
    if len(parts) > 1 and datetext1 == datetext2:
        datetext1 = parts[0]
        datetext2 = parts[1]

    if datetext1 == datetext2:
        res = run_sql("SELECT id FROM bibrec WHERE %s LIKE %%s" % (type,),
                      (datetext1 + '%',))
    else:
        res = run_sql("SELECT id FROM bibrec WHERE %s>=%%s AND %s<=%%s" % (type, type),
                      (datetext1, datetext2))
    for row in res:
        set += row[0]
    return set

def search_unit_by_times_cited(p):
    """
    Return histset of recIDs found that are cited P times.
    Usually P looks like '10->23'.
    """
    numstr = '"'+p+'"'
    #this is sort of stupid but since we may need to
    #get the records that do _not_ have cites, we have to
    #know the ids of all records, too
    #but this is needed only if bsu_p is 0 or 0 or 0->0
    allrecs = []
    if p == 0 or p == "0" or \
       p.startswith("0->") or p.endswith("->0"):
        allrecs = intbitset(run_sql("SELECT id FROM bibrec"))
    return get_records_with_num_cites(numstr, allrecs)

def search_unit_refersto(query):
    """
    Search for records satisfying the query (e.g. author:ellis) and
    return list of records referred to by these records.
    """
    if query:
        ahitset = search_pattern(p=query)
        if ahitset:
            return get_refersto_hitset(ahitset)
        else:
            return intbitset([])
    else:
        return intbitset([])

def search_unit_citedby(query):
    """
    Search for records satisfying the query (e.g. author:ellis) and
    return list of records cited by these records.
    """
    if query:
        ahitset = search_pattern(p=query)
        if ahitset:
            return get_citedby_hitset(ahitset)
        else:
            return intbitset([])
    else:
        return intbitset([])

def intersect_results_with_collrecs(req, hitset_in_any_collection, colls, ap=0, of="hb", verbose=0, ln=CFG_SITE_LANG, display_nearest_terms_box=True):
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
            if of.startswith("h") and display_nearest_terms_box:
                url = websearch_templates.build_search_url(req.argd, cc=CFG_SITE_NAME, c=[])
                print_warning(req, _("No match found in collection %(x_collection)s. Other public collections gave %(x_url_open)s%(x_nb_hits)d hits%(x_url_close)s.") %\
                              {'x_collection': '<em>' + string.join([get_coll_i18nname(coll, ln, False) for coll in colls], ', ') + '</em>',
                               'x_url_open': '<a class="nearestterms" href="%s">' % (url),
                               'x_nb_hits': len(results_in_Home),
                               'x_url_close': '</a>'})
            results = {}
        else:
            # no hits found in Home, recommend different search terms:
            if of.startswith("h") and display_nearest_terms_box:
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

    if not CFG_WEBSEARCH_DISPLAY_NEAREST_TERMS:
        return _("Your search did not match any records.  Please try again.")
    nearest_terms = []
    if not p: # sanity check
        p = "."
    if p.startswith('%') and p.endswith('%'):
        p = p[1:-1] # fix for partial phrase
    index_id = get_index_id_from_field(f)
    if f == 'fulltext':
        if CFG_SOLR_URL:
            return _("No match found, please enter different search terms.")
        else:
            # FIXME: workaround for not having native phrase index yet
            t = 'w'
    # special indexes:
    if f == 'refersto':
        return _("There are no records referring to %s.") % cgi.escape(p)
    if f == 'citedby':
        return _("There are no records cited by %s.") % cgi.escape(p)
    # look for nearest terms:
    if t == 'w':
        nearest_terms = get_nearest_terms_in_bibwords(p, f, n, n)
        if not nearest_terms:
            return _("No word index is available for %s.") % \
                   ('<em>' + cgi.escape(get_field_i18nname(get_field_name(f) or f, ln, False)) + '</em>')
    else:
        nearest_terms = []
        if index_id:
            nearest_terms = get_nearest_terms_in_idxphrase(p, index_id, n, n)
        if f == 'datecreated' or f == 'datemodified':
            nearest_terms = get_nearest_terms_in_bibrec(p, f, n, n)
        if not nearest_terms:
            nearest_terms = get_nearest_terms_in_bibxxx(p, f, n, n)
        if not nearest_terms:
            return _("No phrase index is available for %s.") % \
                   ('<em>' + cgi.escape(get_field_i18nname(get_field_name(f) or f, ln, False)) + '</em>')

    terminfo = []
    for term in nearest_terms:
        if t == 'w':
            hits = get_nbhits_in_bibwords(term, f)
        else:
            if index_id:
                hits = get_nbhits_in_idxphrases(term, f)
            elif f == 'datecreated' or f == 'datemodified':
                hits = get_nbhits_in_bibrec(term, f)
            else:
                hits = get_nbhits_in_bibxxx(term, f)

        argd = {}
        argd.update(urlargd)

        # check which fields contained the requested parameter, and replace it.
        for (px, fx) in ('p', 'f'), ('p1', 'f1'), ('p2', 'f2'), ('p3', 'f3'):
            if px in argd:
                argd_px = argd[px]
                if t == 'w':
                    # p was stripped of accents, to do the same:
                    argd_px = strip_accents(argd_px)
                #argd[px] = string.replace(argd_px, p, term, 1)
                #we need something similar, but case insensitive
                pattern_index = string.find(argd_px.lower(), p.lower())
                if pattern_index > -1:
                    argd[px] = argd_px[:pattern_index] + term + argd_px[pattern_index+len(p):]
                    break
                #this is doing exactly the same as:
                #argd[px] = re.sub('(?i)' + re.escape(p), term, argd_px, 1)
                #but is ~4x faster (2us vs. 8.25us)
        terminfo.append((term, hits, argd))

    intro = ""
    if intro_text_p: # add full leading introductory text
        if f:
            intro = _("Search term %(x_term)s inside index %(x_index)s did not match any record. Nearest terms in any collection are:") % \
                     {'x_term': "<em>" + cgi.escape(p.startswith("%") and p.endswith("%") and p[1:-1] or p) + "</em>",
                      'x_index': "<em>" + cgi.escape(get_field_i18nname(get_field_name(f) or f, ln, False)) + "</em>"}
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

def get_nearest_terms_in_idxphrase(p, index_id, n_below, n_above):
    """Browse (-n_above, +n_below) closest bibliographic phrases
       for the given pattern p in the given field idxPHRASE table,
       regardless of collection.
       Return list of [phrase1, phrase2, ... , phrase_n]."""
    if CFG_INSPIRE_SITE and index_id in (3, 15): # FIXME: workaround due to new fuzzy index
        return [p,]
    idxphraseX = "idxPHRASE%02dF" % index_id
    res_above = run_sql("SELECT term FROM %s WHERE term<%%s ORDER BY term DESC LIMIT %%s" % idxphraseX, (p, n_above))
    res_above = map(lambda x: x[0], res_above)
    res_above.reverse()

    res_below = run_sql("SELECT term FROM %s WHERE term>=%%s ORDER BY term ASC LIMIT %%s" % idxphraseX, (p, n_below))
    res_below = map(lambda x: x[0], res_below)

    return res_above + res_below

def get_nearest_terms_in_idxphrase_with_collection(p, index_id, n_below, n_above, collection):
    """Browse (-n_above, +n_below) closest bibliographic phrases
       for the given pattern p in the given field idxPHRASE table,
       considering the collection (intbitset).
       Return list of [(phrase1, hitset), (phrase2, hitset), ... , (phrase_n, hitset)]."""
    idxphraseX = "idxPHRASE%02dF" % index_id
    res_above = run_sql("SELECT term,hitlist FROM %s WHERE term<%%s ORDER BY term DESC LIMIT %%s" % idxphraseX, (p, n_above * 3))
    res_above = [(term, intbitset(hitlist) & collection) for term, hitlist in res_above]
    res_above = [(term, len(hitlist)) for term, hitlist in res_above if hitlist]

    res_below = run_sql("SELECT term,hitlist FROM %s WHERE term>=%%s ORDER BY term ASC LIMIT %%s" % idxphraseX, (p, n_below * 3))
    res_below = [(term, intbitset(hitlist) & collection) for term, hitlist in res_below]
    res_below = [(term, len(hitlist)) for term, hitlist in res_below if hitlist]

    res_above.reverse()
    return res_above[-n_above:] + res_below[:n_below]


def get_nearest_terms_in_bibxxx(p, f, n_below, n_above):
    """Browse (-n_above, +n_below) closest bibliographic phrases
       for the given pattern p in the given field f, regardless
       of collection.
       Return list of [phrase1, phrase2, ... , phrase_n]."""
    ## determine browse field:
    if not f and string.find(p, ":") > 0: # does 'p' contain ':'?
        f, p = string.split(p, ":", 1)

    # FIXME: quick hack for the journal index
    if f == 'journal':
        return get_nearest_terms_in_bibwords(p, f, n_below, n_above)

    ## We are going to take max(n_below, n_above) as the number of
    ## values to ferch from bibXXx.  This is needed to work around
    ## MySQL UTF-8 sorting troubles in 4.0.x.  Proper solution is to
    ## use MySQL 4.1.x or our own idxPHRASE in the future.

    index_id = get_index_id_from_field(f)
    if index_id:
        return get_nearest_terms_in_idxphrase(p, index_id, n_below, n_above)

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

def get_nearest_terms_in_bibrec(p, f, n_below, n_above):
    """Return list of nearest terms and counts from bibrec table.
    p is usually a date, and f either datecreated or datemodified.

    Note: below/above count is very approximative, not really respected.
    """
    col = 'creation_date'
    if f == 'datemodified':
        col = 'modification_date'
    res_above = run_sql("""SELECT DATE_FORMAT(%s,'%%%%Y-%%%%m-%%%%d %%%%H:%%%%i:%%%%s')
                             FROM bibrec WHERE %s < %%s
                            ORDER BY %s DESC LIMIT %%s""" % (col, col, col),
                        (p, n_above))
    res_below = run_sql("""SELECT DATE_FORMAT(%s,'%%%%Y-%%%%m-%%%%d %%%%H:%%%%i:%%%%s')
                             FROM bibrec WHERE %s > %%s
                            ORDER BY %s ASC LIMIT %%s""" % (col, col, col),
                        (p, n_below))
    out = set([])
    for row in res_above:
        out.add(row[0])
    for row in res_below:
        out.add(row[0])
    out_list = list(out)
    out_list.sort()
    return list(out_list)

def get_nbhits_in_bibrec(term, f):
    """Return number of hits in bibrec table.  term is usually a date,
    and f is either 'datecreated' or 'datemodified'."""
    col = 'creation_date'
    if f == 'datemodified':
        col = 'modification_date'
    res = run_sql("SELECT COUNT(*) FROM bibrec WHERE %s LIKE %%s" % (col,),
                  (term + '%',))
    return res[0][0]

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
            out += len(intbitset(hitlist[0]))
    return out

def get_nbhits_in_idxphrases(word, f):
    """Return number of hits for word 'word' inside phrase index for field 'f'."""
    out = 0
    # deduce into which bibwordsX table we will search:
    idxphraseX = "idxPHRASE%02dF" % get_index_id_from_field("anyfield")
    if f:
        index_id = get_index_id_from_field(f)
        if index_id:
            idxphraseX = "idxPHRASE%02dF" % index_id
        else:
            return 0
    if word:
        res = run_sql("SELECT hitlist FROM %s WHERE term=%%s" % idxphraseX,
                      (word,))
        for hitlist in res:
            out += len(intbitset(hitlist[0]))
    return out

def get_nbhits_in_bibxxx(p, f):
    """Return number of hits for word 'word' inside words index for field 'f'."""
    ## determine browse field:
    if not f and string.find(p, ":") > 0: # does 'p' contain ':'?
        f, p = string.split(p, ":", 1)

    # FIXME: quick hack for the journal index
    if f == 'journal':
        return get_nbhits_in_bibwords(p, f)

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
    """Return primary collection name a record recid belongs to, by
       testing 980 identifier.
       May lead to bad guesses when a collection is defined dynamically
       via dbquery.
       In that case, return 'CFG_SITE_NAME'."""
    out = CFG_SITE_NAME
    dbcollids = get_fieldvalues(recID, "980__a")
    for dbcollid in dbcollids:
        variants = ("collection:" + dbcollid,
                    'collection:"' + dbcollid + '"',
                    "980__a:" + dbcollid,
                    '980__a:"' + dbcollid + '"',
                    '980:' + dbcollid ,
                    '980:"' + dbcollid + '"')
        res = run_sql("SELECT name FROM collection WHERE dbquery IN (%s,%s,%s,%s,%s,%s)", variants)
        if res:
            out = res[0][0]
            break
    if CFG_CERN_SITE:
        # dirty hack for ATLAS collections at CERN:
        if out in ('ATLAS Communications', 'ATLAS Internal Notes'):
            for alternative_collection in ('ATLAS Communications Physics',
                                           'ATLAS Communications General',
                                           'ATLAS Internal Notes Physics',
                                           'ATLAS Internal Notes General',):
                if recID in get_collection_reclist(alternative_collection):
                    out = alternative_collection
                    break
    return out

_re_collection_url = re.compile('/collection/(.+)')
def guess_collection_of_a_record(recID, referer=None, recreate_cache_if_needed=True):
    """Return collection name a record recid belongs to, by first testing
       the referer URL if provided and otherwise returning the
       primary collection."""
    if referer:
        dummy, hostname, path, dummy, query, dummy = urlparse.urlparse(referer)
        #requests can come from different invenio installations, with different collections
        if CFG_SITE_URL.find(hostname) < 0:
            return guess_primary_collection_of_a_record(recID)
        g = _re_collection_url.match(path)
        if g:
            name = urllib.unquote_plus(g.group(1))
            #check if this collection actually exist (also normalize the name if case-insensitive)
            name = get_coll_normalised_name(name)
            if name and recID in get_collection_reclist(name):
                return name
        elif path.startswith('/search'):
            if recreate_cache_if_needed:
                collection_reclist_cache.recreate_cache_if_needed()
            query = cgi.parse_qs(query)
            for name in query.get('cc', []) + query.get('c', []):
                name = get_coll_normalised_name(name)
                if name and recID in get_collection_reclist(name, recreate_cache_if_needed=False):
                    return name
    return guess_primary_collection_of_a_record(recID)

def is_record_in_any_collection(recID, recreate_cache_if_needed=True):
    """Return True if the record belongs to at least one collection. This is a
    good, although not perfect, indicator to guess if webcoll has already run
    after this record has been entered into the system.
    """
    if recreate_cache_if_needed:
        collection_reclist_cache.recreate_cache_if_needed()
    for name in collection_reclist_cache.cache.keys():
        if recID in get_collection_reclist(name, recreate_cache_if_needed=False):
            return True
    return False

def get_all_collections_of_a_record(recID, recreate_cache_if_needed=True):
    """Return all the collection names a record belongs to.
    Note this function is O(n_collections)."""
    ret = []
    if recreate_cache_if_needed:
        collection_reclist_cache.recreate_cache_if_needed()
    for name in collection_reclist_cache.cache.keys():
        if recID in get_collection_reclist(name, recreate_cache_if_needed=False):
            ret.append(name)
    return ret

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

def get_field_name(code):
    """Return the corresponding field_name given the field code.
    e.g. reportnumber -> report number."""
    res = run_sql("SELECT name FROM field WHERE code=%s", (code, ))
    if res:
        return res[0][0]
    else:
        return ""

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

def get_fieldvalues_alephseq_like(recID, tags_in, can_see_hidden=False):
    """Return buffer of ALEPH sequential-like textual format with fields found
       in the list TAGS_IN for record RECID.

       If can_see_hidden is True, just print everything.  Otherwise hide fields
       from CFG_BIBFORMAT_HIDDEN_TAGS.
    """

    out = ""
    if type(tags_in) is not list:
        tags_in = [tags_in,]
    if len(tags_in) == 1 and len(tags_in[0]) == 6:
        ## case A: one concrete subfield asked, so print its value if found
        ##         (use with care: can mislead if field has multiple occurrences)
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
                    "WHERE bb.id_bibrec=%%s AND b.id=bb.id_bibxxx AND b.tag LIKE %%s"\
                    "ORDER BY bb.field_number, b.tag ASC" % (bx, bibx)
            res = run_sql(query, (recID, str(tag)+'%'))
            # go through fields:
            field_number_old = -999
            field_old = ""
            for row in res:
                field, value, field_number = row[0], row[1], row[2]
                ind1, ind2 = field[3], field[4]
                printme = True
                #check the stuff in hiddenfields
                if not can_see_hidden:
                    for htag in CFG_BIBFORMAT_HIDDEN_TAGS:
                        ltag = len(htag)
                        samelenfield = field[0:ltag]
                        if samelenfield == htag:
                            printme = False
                if ind1 == "_":
                    ind1 = ""
                if ind2 == "_":
                    ind2 = ""
                # print field tag
                if printme:
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

def get_merged_recid(recID):
    """ Return the record ID of the record with
    which the given record has been merged.
    @param recID: deleted record recID
    @type recID: int
    @return: merged record recID
    @rtype: int
    """
    merged_recid = get_fieldvalues(recID, "970__d")
    if merged_recid:
        return int(merged_recid[0])

def record_exists(recID):
    """Return 1 if record RECID exists.
       Return 0 if it doesn't exist.
       Return -1 if it exists but is marked as deleted.
    """
    out = 0
    res = run_sql("SELECT id FROM bibrec WHERE id=%s", (recID,), 1)
    if res:
        try: # if recid is '123foo', mysql will return id=123, and we don't want that
            recID = int(recID)
        except ValueError:
            return 0
        # record exists; now check whether it isn't marked as deleted:
        dbcollids = get_fieldvalues(recID, "980__%")
        if ("DELETED" in dbcollids) or (CFG_CERN_SITE and "DUMMY" in dbcollids):
            out = -1 # exists, but marked as deleted
        else:
            out = 1 # exists fine
    return out

def record_empty(recID):
    """
    Is this record empty, e.g. has only 001, waiting for integration?

    @param recID: the record identifier.
    @type recID: int
    @return: 1 if the record is empty, 0 otherwise.
    @rtype: int
    """
    record = get_record(recID)
    if record is None or len(record) < 2:
        return 1
    else:
        return 0

def record_public_p(recID, recreate_cache_if_needed=True):
    """Return 1 if the record is public, i.e. if it can be found in the Home collection.
       Return 0 otherwise.
    """
    return recID in get_collection_reclist(CFG_SITE_NAME, recreate_cache_if_needed=recreate_cache_if_needed)

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

def print_warning(req, msg, msg_type='', prologue='<br />', epilogue='<br />'):
    "Prints warning message and flushes output."
    if req and msg:
        req.write(websearch_templates.tmpl_print_warning(
                   msg = msg,
                   type = msg_type,
                   prologue = prologue,
                   epilogue = epilogue,
                 ))
        return

def print_search_info(p, f, sf, so, sp, rm, of, ot, collection=CFG_SITE_NAME, nb_found=-1, jrec=1, rg=10,
                      aas=0, ln=CFG_SITE_LANG, p1="", p2="", p3="", f1="", f2="", f3="", m1="", m2="", m3="", op1="", op2="",
                      sc=1, pl_in_url="",
                      d1y=0, d1m=0, d1d=0, d2y=0, d2m=0, d2d=0, dt="",
                      cpu_time=-1, middle_only=0):
    """Prints stripe with the information on 'collection' and 'nb_found' results and CPU time.
       Also, prints navigation links (beg/next/prev/end) inside the results set.
       If middle_only is set to 1, it will only print the middle box information (beg/netx/prev/end/etc) links.
       This is suitable for displaying navigation links at the bottom of the search results page."""

    # sanity check:
    if jrec < 1:
        jrec = 1
    if jrec > nb_found:
        jrec = max(nb_found-rg+1, 1)

    return websearch_templates.tmpl_print_search_info(
             ln = ln,
             collection = collection,
             aas = aas,
             collection_name = get_coll_i18nname(collection, ln, False),
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

def print_hosted_search_info(p, f, sf, so, sp, rm, of, ot, collection=CFG_SITE_NAME, nb_found=-1, jrec=1, rg=10,
                      aas=0, ln=CFG_SITE_LANG, p1="", p2="", p3="", f1="", f2="", f3="", m1="", m2="", m3="", op1="", op2="",
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

    return websearch_templates.tmpl_print_hosted_search_info(
             ln = ln,
             collection = collection,
             aas = aas,
             collection_name = get_coll_i18nname(collection, ln, False),
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

def print_results_overview(colls, results_final_nb_total, results_final_nb, cpu_time, ln=CFG_SITE_LANG, ec=[], hosted_colls_potential_results_p=False):
    """Prints results overview box with links to particular collections below."""

    out = ""
    new_colls = []
    for coll in colls:
        new_colls.append({
                          'id': get_colID(coll),
                          'code': coll,
                          'name': get_coll_i18nname(coll, ln, False),
                         })

    return websearch_templates.tmpl_print_results_overview(
             ln = ln,
             results_final_nb_total = results_final_nb_total,
             results_final_nb = results_final_nb,
             cpu_time = cpu_time,
             colls = new_colls,
             ec = ec,
             hosted_colls_potential_results_p = hosted_colls_potential_results_p,
           )

def print_hosted_results(url_and_engine, ln=CFG_SITE_LANG, of=None, req=None, no_records_found=False, search_timed_out=False, limit=CFG_EXTERNAL_COLLECTION_MAXRESULTS):
    """Prints the full results of a hosted collection"""

    if of.startswith("h"):
        if no_records_found:
            return "<br />No results found."
        if search_timed_out:
            return "<br />The search engine did not respond in time."

    return websearch_templates.tmpl_print_hosted_results(
        url_and_engine=url_and_engine,
        ln=ln,
        of=of,
        req=req,
        limit=limit
        )

class BibSortDataCacher(DataCacher):
    """
    Cache holding all structures created by bibsort
    (   _data, data_dict).
    """
    def __init__(self, method_name):
        self.method_name = method_name
        self.method_id = 0
        try:
            res = run_sql("""SELECT id from bsrMETHOD where name = %s""", (self.method_name,))
        except:
            self.method_id = 0
        if res and res[0]:
            self.method_id = res[0][0]
        else:
            self.method_id = 0

        def cache_filler():
            method_id = self.method_id
            alldicts = {}
            if self.method_id == 0:
                return {}
            try:
                res_data = run_sql("""SELECT data_dict_ordered from bsrMETHODDATA \
                                   where id_bsrMETHOD = %s""", (method_id,))
                res_buckets = run_sql("""SELECT bucket_no, bucket_data from bsrMETHODDATABUCKET\
                                      where id_bsrMETHOD = %s""", (method_id,))
            except Exception:
                # database problems, return empty cache
                return {}
            try:
                data_dict_ordered = deserialize_via_marshal(res_data[0][0])
            except:
                data_dict_ordered= {}
            alldicts['data_dict_ordered'] = data_dict_ordered # recid: weight

            if not res_buckets:
                alldicts['bucket_data'] = {}
                return alldicts

            for row in res_buckets:
                bucket_no = row[0]
                try:
                    bucket_data = intbitset(row[1])
                except:
                    bucket_data = intbitset([])
                alldicts.setdefault('bucket_data', {})[bucket_no] = bucket_data

            return alldicts

        def timestamp_verifier():
            method_id = self.method_id
            res = run_sql("""SELECT last_updated from bsrMETHODDATA where id_bsrMETHOD = %s""", (method_id,))
            try:
                update_time_methoddata = str(res[0][0])
            except IndexError:
                update_time_methoddata = '1970-01-01 00:00:00'
            res = run_sql("""SELECT max(last_updated) from bsrMETHODDATABUCKET where id_bsrMETHOD = %s""", (method_id,))
            try:
                update_time_buckets = str(res[0][0])
            except IndexError:
                update_time_buckets = '1970-01-01 00:00:00'
            return max(update_time_methoddata, update_time_buckets)

        DataCacher.__init__(self, cache_filler, timestamp_verifier)

def get_sorting_methods():
    if not CFG_BIBSORT_BUCKETS: # we do not want to use buckets
        return {}
    try: # make sure the method has some data
        res = run_sql("""SELECT m.name, m.definition FROM bsrMETHOD m, bsrMETHODDATA md WHERE m.id = md.id_bsrMETHOD""")
    except:
        return {}
    return dict(res)

sorting_methods = get_sorting_methods()
cache_sorted_data = {}
for sorting_method in sorting_methods:
    try:
        cache_sorted_data[sorting_method].is_ok_p
    except Exception:
        cache_sorted_data[sorting_method] = BibSortDataCacher(sorting_method)


def get_tags_form_sort_fields(sort_fields):
    """Given a list of sort_fields, return the tags associated with it and
    also the name of the field that has no tags associated, to be able to
    display a message to the user."""
    tags = []
    if not sort_fields:
        return [], ''
    for sort_field in sort_fields:
        if sort_field and str(sort_field[0:2]).isdigit():
            # sort_field starts by two digits, so this is probably a MARC tag already
            tags.append(sort_field)
        else:
            # let us check the 'field' table
            field_tags = get_field_tags(sort_field)
            if field_tags:
                tags.extend(field_tags)
            else:
                return [], sort_field
    return tags, ''


def rank_records(req, rank_method_code, rank_limit_relevance, hitset_global, pattern=None, verbose=0, sort_order='d', of='hb', ln=CFG_SITE_LANG, rg=None, jrec=None):
    """Initial entry point for ranking records, acts like a dispatcher.
       (i) rank_method_code is in bsrMETHOD, bibsort buckets can be used;
       (ii)rank_method_code is not in bsrMETHOD, use bibrank;
    """

    if CFG_BIBSORT_BUCKETS and sorting_methods:
        for sort_method in sorting_methods:
            definition = sorting_methods[sort_method]
            if definition.startswith('RNK') and \
            definition.replace('RNK:','').strip().lower() == string.lower(rank_method_code):
                (solution_recs, solution_scores) = sort_records_bibsort(req, hitset_global, sort_method, '', sort_order, verbose, of, ln, rg, jrec, 'r')
                #return (solution_recs, solution_scores, '', '', '')
                comment = ''
                if verbose > 0:
                    comment = 'find_citations retlist %s' %[[solution_recs[i], solution_scores[i]] for i in range(len(solution_recs))]
                return (solution_recs, solution_scores, '(', ')', comment)
    return rank_records_bibrank(rank_method_code, rank_limit_relevance, hitset_global, pattern, verbose)


def sort_records(req, recIDs, sort_field='', sort_order='d', sort_pattern='', verbose=0, of='hb', ln=CFG_SITE_LANG, rg=None, jrec=None):
    """Initial entry point for sorting records, acts like a dispatcher.
       (i) sort_field is in the bsrMETHOD, and thus, the BibSort has sorted the data for this field, so we can use the cache;
       (ii)sort_field is not in bsrMETHOD, and thus, the cache does not contain any information regarding this sorting method"""

    _ = gettext_set_language(ln)

    #we should return sorted records up to irec_max(exclusive)
    dummy, irec_max = get_interval_for_records_to_sort(len(recIDs), jrec, rg)
    #calculate the min index on the reverted list
    index_min = max(len(recIDs) - irec_max, 0) #just to be sure that the min index is not negative

    #bibsort does not handle sort_pattern for now, use bibxxx
    if sort_pattern:
        return sort_records_bibxxx(req, recIDs, None, sort_field, sort_order, sort_pattern, verbose, of, ln, rg, jrec)

    use_sorting_buckets = True

    if not CFG_BIBSORT_BUCKETS or not sorting_methods: #ignore the use of buckets, use old fashion sorting
        use_sorting_buckets = False

    if not sort_field:
        if use_sorting_buckets:
            return sort_records_bibsort(req, recIDs, 'latest first', sort_field, sort_order, verbose, of, ln, rg, jrec)
        else:
            return recIDs[index_min:]

    sort_fields = string.split(sort_field, ",")
    if len(sort_fields) == 1:
        # we have only one sorting_field, check if it is treated by BibSort
        for sort_method in sorting_methods:
            definition = sorting_methods[sort_method]
            if use_sorting_buckets and \
               ((definition.startswith('FIELD') and \
                definition.replace('FIELD:','').strip().lower() == string.lower(sort_fields[0])) or \
                sort_method == sort_fields[0]):
                #use BibSort
                return sort_records_bibsort(req, recIDs, sort_method, sort_field, sort_order, verbose, of, ln, rg, jrec)
    #deduce sorting MARC tag out of the 'sort_field' argument:
    tags, error_field = get_tags_form_sort_fields(sort_fields)
    if error_field:
        if use_sorting_buckets:
            return sort_records_bibsort(req, recIDs, 'latest first', sort_field, sort_order, verbose, of, ln, rg, jrec)
        else:
            if of.startswith('h'):
                print_warning(req, _("Sorry, %s does not seem to be a valid sort option. The records will not be sorted.") % cgi.escape(error_field), "Error")
            return recIDs[index_min:]
    if tags:
        for sort_method in sorting_methods:
            definition = sorting_methods[sort_method]
            if definition.startswith('MARC') \
                    and definition.replace('MARC:','').strip().split(',') == tags \
                    and use_sorting_buckets:
                #this list of tags have a designated method in BibSort, so use it
                return sort_records_bibsort(req, recIDs, sort_method, sort_field, sort_order, verbose, of, ln, rg, jrec)
        #we do not have this sort_field in BibSort tables -> do the old fashion sorting
        return sort_records_bibxxx(req, recIDs, tags, sort_field, sort_order, sort_pattern, verbose, of, ln, rg, jrec)

    return recIDs[index_min:]


def sort_records_bibsort(req, recIDs, sort_method, sort_field='', sort_order='d', verbose=0, of='hb', ln=CFG_SITE_LANG, rg=None, jrec=None, sort_or_rank = 's'):
    """This function orders the recIDs list, based on a sorting method(sort_field) using the BibSortDataCacher for speed"""

    _ = gettext_set_language(ln)

    #sanity check
    if sort_method not in sorting_methods:
        if sort_or_rank == 'r':
            return rank_records_bibrank(sort_method, 0, recIDs, None, verbose)
        else:
            return sort_records_bibxxx(req, recIDs, None, sort_field, sort_order, '', verbose, of, ln, rg, jrec)

    if verbose >= 3 and of.startswith('h'):
        print_warning(req, "Sorting (using BibSort cache) by method %s (definition %s)." \
                      % (cgi.escape(repr(sort_method)), cgi.escape(repr(sorting_methods[sort_method]))))

    #we should return sorted records up to irec_max(exclusive)
    dummy, irec_max = get_interval_for_records_to_sort(len(recIDs), jrec, rg)
    solution = intbitset([])
    input_recids = intbitset(recIDs)
    cache_sorted_data[sort_method].recreate_cache_if_needed()
    sort_cache = cache_sorted_data[sort_method].cache
    bucket_numbers = sort_cache['bucket_data'].keys()
    #check if all buckets have been constructed
    if len(bucket_numbers) != CFG_BIBSORT_BUCKETS:
        if verbose > 3 and of.startswith('h'):
            print_warning(req, "Not all buckets have been constructed.. switching to old fashion sorting.")
        if sort_or_rank == 'r':
            return rank_records_bibrank(sort_method, 0, recIDs, None, verbose)
        else:
            return sort_records_bibxxx(req, recIDs, None, sort_field, sort_order, '', verbose, of, ln, rg, jrec)

    if sort_order == 'd':
        bucket_numbers.reverse()
    for bucket_no in bucket_numbers:
        solution.union_update(input_recids & sort_cache['bucket_data'][bucket_no])
        if len(solution) >= irec_max:
            break
    dict_solution = {}
    missing_records = []
    for recid in solution:
        try:
            dict_solution[recid] = sort_cache['data_dict_ordered'][recid]
        except KeyError:
            #recid is in buckets, but not in the bsrMETHODDATA,
            #maybe because the value has been deleted, but the change has not yet been propagated to the buckets
            missing_records.append(recid)
    #check if there are recids that are not in any bucket -> to be added at the end/top, ordered by insertion date
    if len(solution) < irec_max:
        #some records have not been yet inserted in the bibsort structures
        #or, some records have no value for the sort_method
        missing_records = sorted(missing_records + list(input_recids.difference(solution)))
    #the records need to be sorted in reverse order for the print record function
    #the return statement should be equivalent with the following statements
    #(these are clearer, but less efficient, since they revert the same list twice)
    #sorted_solution = (missing_records + sorted(dict_solution, key=dict_solution.__getitem__, reverse=sort_order=='d'))[:irec_max]
    #sorted_solution.reverse()
    #return sorted_solution
    if sort_method.strip().lower().startswith('latest') and sort_order == 'd':
        # if we want to sort the records on their insertion date, add the mission records at the top
        solution = sorted(dict_solution, key=dict_solution.__getitem__, reverse=sort_order=='a') + missing_records
    else:
        solution = missing_records + sorted(dict_solution, key=dict_solution.__getitem__, reverse=sort_order=='a')
    #calculate the min index on the reverted list
    index_min = max(len(solution) - irec_max, 0) #just to be sure that the min index is not negative
    #return all the records up to irec_max, but on the reverted list
    if sort_or_rank == 'r':
        # we need the recids, with values
        return (solution[index_min:], [dict_solution.get(record, 0) for record in solution[index_min:]])
    else:
        return solution[index_min:]


def sort_records_bibxxx(req, recIDs, tags, sort_field='', sort_order='d', sort_pattern='', verbose=0, of='hb', ln=CFG_SITE_LANG, rg=None, jrec=None):
    """OLD FASHION SORTING WITH NO CACHE, for sort fields that are not run in BibSort
       Sort records in 'recIDs' list according sort field 'sort_field' in order 'sort_order'.
       If more than one instance of 'sort_field' is found for a given record, try to choose that that is given by
       'sort pattern', for example "sort by report number that starts by CERN-PS".
       Note that 'sort_field' can be field code like 'author' or MARC tag like '100__a' directly."""

    _ = gettext_set_language(ln)

    #we should return sorted records up to irec_max(exclusive)
    dummy, irec_max = get_interval_for_records_to_sort(len(recIDs), jrec, rg)
    #calculate the min index on the reverted list
    index_min = max(len(recIDs) - irec_max, 0) #just to be sure that the min index is not negative

    ## check arguments:
    if not sort_field:
        return recIDs[index_min:]
    if len(recIDs) > CFG_WEBSEARCH_NB_RECORDS_TO_SORT:
        if of.startswith('h'):
            print_warning(req, _("Sorry, sorting is allowed on sets of up to %d records only. Using default sort order.") % CFG_WEBSEARCH_NB_RECORDS_TO_SORT, "Warning")
        return recIDs[index_min:]

    recIDs_dict = {}
    recIDs_out = []

    if not tags:
        # tags have not been camputed yet
        sort_fields = string.split(sort_field, ",")
        tags, error_field = get_tags_form_sort_fields(sort_fields)
        if error_field:
            if of.startswith('h'):
                print_warning(req, _("Sorry, %s does not seem to be a valid sort option. The records will not be sorted.") % cgi.escape(error_field), "Error")
            return recIDs[index_min:]
    if verbose >= 3 and of.startswith('h'):
        print_warning(req, "Sorting by tags %s." % cgi.escape(repr(tags)))
        if sort_pattern:
            print_warning(req, "Sorting preferentially by %s." % cgi.escape(sort_pattern))

    ## check if we have sorting tag defined:
    if tags:
        # fetch the necessary field values:
        for recID in recIDs:
            val = "" # will hold value for recID according to which sort
            vals = [] # will hold all values found in sorting tag for recID
            for tag in tags:
                if CFG_CERN_SITE and tag == '773__c':
                    # CERN hack: journal sorting
                    # 773__c contains page numbers, e.g. 3-13, and we want to sort by 3, and numerically:
                    vals.extend(["%050s" % x.split("-",1)[0] for x in get_fieldvalues(recID, tag)])
                else:
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
        # return only up to the maximum that we need to sort
        if len(recIDs_out) != len(recIDs):
            dummy, irec_max = get_interval_for_records_to_sort(len(recIDs_out), jrec, rg)
            index_min = max(len(recIDs_out) - irec_max, 0) #just to be sure that the min index is not negative
        return recIDs_out[index_min:]
    else:
        # good, no sort needed
        return recIDs[index_min:]


def get_interval_for_records_to_sort(nb_found, jrec=None, rg=None):
    """calculates in which interval should the sorted records be
    a value of 'rg=-9999' means to print all records: to be used with care."""

    if not jrec:
        jrec = 1

    if not rg:
        #return all
        return jrec-1, nb_found

    if rg == -9999: # print all records
        rg = nb_found
    else:
        rg = abs(rg)
    if jrec < 1: # sanity checks
        jrec = 1
    if jrec > nb_found:
        jrec = max(nb_found-rg+1, 1)

    # will sort records from irec_min to irec_max excluded
    irec_min = jrec - 1
    irec_max = irec_min + rg
    if irec_min < 0:
        irec_min = 0
    if irec_max > nb_found:
        irec_max = nb_found

    return irec_min, irec_max

def print_records(req, recIDs, jrec=1, rg=10, format='hb', ot='', ln=CFG_SITE_LANG, relevances=[], relevances_prologue="(", relevances_epilogue="%%)", decompress=zlib.decompress, search_pattern='', print_records_prologue_p=True, print_records_epilogue_p=True, verbose=0, tab='', sf='', so='d', sp='', rm=''):
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

    'sf' is sort field and 'rm' is ranking method that are passed here
    only for proper linking purposes: e.g. when a certain ranking
    method or a certain sort field was selected, keep it selected in
    any dynamic search links that may be printed.
    """

    # load the right message language
    _ = gettext_set_language(ln)

    # sanity checking:
    if req is None:
        return

    # get user_info (for formatting based on user)
    if isinstance(req, cStringIO.OutputType):
        user_info = {}
    else:
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
                                 user_info=user_info, verbose=verbose, sf=sf, so=so, sp=sp, rm=rm)
                req.write(x)
                if x:
                    req.write('\n')
        elif format == 'excel':
            recIDs_to_print = [recIDs[x] for x in range(irec_max, irec_min, -1)]
            create_excel(recIDs=recIDs_to_print, req=req, ln=ln, ot=ot)
        else:
            # we are doing HTML output:
            if format == 'hp' or format.startswith("hb_") or format.startswith("hd_"):
                # portfolio and on-the-fly formats:
                for irec in range(irec_max, irec_min, -1):
                    req.write(print_record(recIDs[irec], format, ot, ln, search_pattern=search_pattern,
                                           user_info=user_info, verbose=verbose, sf=sf, so=so, sp=sp, rm=rm))
            elif format.startswith("hb"):
                # HTML brief format:

                display_add_to_basket = True
                if user_info:
                    if user_info['email'] == 'guest':
                        if CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS > 4:
                            display_add_to_basket = False
                    else:
                        if not user_info['precached_usebaskets']:
                            display_add_to_basket = False
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
                                                  user_info=user_info, verbose=verbose, sf=sf, so=so, sp=sp, rm=rm)

                    req.write(websearch_templates.tmpl_record_format_htmlbrief_body(
                        ln = ln,
                        recid = recid,
                        row_number = row_number,
                        relevance = relevance,
                        record = record,
                        relevances_prologue = relevances_prologue,
                        relevances_epilogue = relevances_epilogue,
                        display_add_to_basket = display_add_to_basket
                        ))

                req.write(websearch_templates.tmpl_record_format_htmlbrief_footer(
                    ln = ln,
                    display_add_to_basket = display_add_to_basket))

            elif format.startswith("hd"):
                # HTML detailed format:
                for irec in range(irec_max, irec_min, -1):
                    merged_recid = get_merged_recid(recIDs[irec])
                    if record_exists(recIDs[irec]) == -1 and not merged_recid:
                        print_warning(req, _("The record has been deleted."))
                        continue
                    if merged_recid:
                        recIDs[irec] = merged_recid
                    unordered_tabs = get_detailed_page_tabs(get_colID(guess_primary_collection_of_a_record(recIDs[irec])),
                                                            recIDs[irec], ln=ln)
                    ordered_tabs_id = [(tab_id, values['order']) for (tab_id, values) in unordered_tabs.iteritems()]
                    ordered_tabs_id.sort(lambda x,y: cmp(x[1],y[1]))

                    link_ln = ''

                    if ln != CFG_SITE_LANG:
                        link_ln = '?ln=%s' % ln

                    recid = recIDs[irec]
                    recid_to_display = recid  # Record ID used to build the URL.
                    if CFG_WEBSEARCH_USE_ALEPH_SYSNOS:
                        try:
                            recid_to_display = get_fieldvalues(recid,
                                    CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG)[0]
                        except IndexError:
                            # No external sysno is available, keep using
                            # internal recid.
                            pass

                    tabs = [(unordered_tabs[tab_id]['label'], \
                             '%s/%s/%s/%s%s' % (CFG_SITE_URL, CFG_SITE_RECORD, recid_to_display, tab_id, link_ln), \
                             tab_id == tab,
                             unordered_tabs[tab_id]['enabled']) \
                            for (tab_id, order) in ordered_tabs_id
                            if unordered_tabs[tab_id]['visible'] == True]

                    tabs_counts = get_detailed_page_tabs_counts(recid)
                    citedbynum = tabs_counts['Citations']
                    references = tabs_counts['References']
                    discussions = tabs_counts['Discussions']

                    # load content
                    if tab == 'usage':
                        req.write(webstyle_templates.detailed_record_container_top(recIDs[irec],
                                                     tabs,
                                                     ln,
                                                     citationnum=citedbynum,
                                                     referencenum=references,
                                                     discussionnum=discussions))
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
                        req.write(content)
                        req.write(webstyle_templates.detailed_record_container_bottom(recIDs[irec],
                                                                                      tabs,
                                                                                      ln))
                    elif tab == 'citations':
                        recid = recIDs[irec]
                        req.write(webstyle_templates.detailed_record_container_top(recid,
                                                     tabs,
                                                     ln,
                                                     citationnum=citedbynum,
                                                     referencenum=references,
                                                     discussionnum=discussions))
                        req.write(websearch_templates.tmpl_detailed_record_citations_prologue(recid, ln))

                        # Citing
                        citinglist = calculate_cited_by_list(recid)
                        req.write(websearch_templates.tmpl_detailed_record_citations_citing_list(recid,
                                                                                                 ln,
                                                                                                 citinglist,
                                                                                                 sf=sf,
                                                                                                 so=so,
                                                                                                 sp=sp,
                                                                                                 rm=rm))
                        # Self-cited
                        selfcited = get_self_cited_by(recid)
                        req.write(websearch_templates.tmpl_detailed_record_citations_self_cited(recid,
                                  ln, selfcited=selfcited, citinglist=citinglist))
                        # Co-cited
                        s = calculate_co_cited_with_list(recid)
                        cociting = None
                        if s:
                            cociting = s
                        req.write(websearch_templates.tmpl_detailed_record_citations_co_citing(recid,
                                                                                               ln,
                                                                                               cociting=cociting))
                        # Citation history, if needed
                        citationhistory = None
                        if citinglist:
                            citationhistory = create_citation_history_graph_and_box(recid, ln)
                        #debug
                        if verbose > 3:
                            print_warning(req, "Citation graph debug: " + \
                                          str(len(citationhistory)))

                        req.write(websearch_templates.tmpl_detailed_record_citations_citation_history(recid, ln, citationhistory))
                        req.write(websearch_templates.tmpl_detailed_record_citations_epilogue(recid, ln))
                        req.write(webstyle_templates.detailed_record_container_bottom(recid,
                                                                                      tabs,
                                                                                      ln))
                    elif tab == 'references':
                        req.write(webstyle_templates.detailed_record_container_top(recIDs[irec],
                                                     tabs,
                                                     ln,
                                                     citationnum=citedbynum,
                                                     referencenum=references,
                                                     discussionnum=discussions))

                        req.write(format_record(recIDs[irec], 'HDREF', ln=ln, user_info=user_info, verbose=verbose))
                        req.write(webstyle_templates.detailed_record_container_bottom(recIDs[irec],
                                                                                      tabs,
                                                                                      ln))
                    elif tab == 'keywords':
                        import bibclassify_webinterface
                        recid = recIDs[irec]
                        bibclassify_webinterface.main_page(req, recid, tabs, ln, webstyle_templates)
                    elif tab == 'plots':
                        req.write(webstyle_templates.detailed_record_container_top(recIDs[irec],
                                                                                   tabs,
                                                                                   ln))
                        content = websearch_templates.tmpl_record_plots(recID=recIDs[irec],
                                                                         ln=ln)
                        req.write(content)
                        req.write(webstyle_templates.detailed_record_container_bottom(recIDs[irec],
                                                                                      tabs,
                                                                                      ln))

                    else:
                        # Metadata tab
                        req.write(webstyle_templates.detailed_record_container_top(recIDs[irec],
                                                     tabs,
                                                     ln,
                                                     show_short_rec_p=False,
                                                     citationnum=citedbynum, referencenum=references,
                                                     discussionnum=discussions))

                        creationdate = None
                        modificationdate = None
                        if record_exists(recIDs[irec]) == 1:
                            creationdate = get_creation_date(recIDs[irec])
                            modificationdate = get_modification_date(recIDs[irec])

                        content = print_record(recIDs[irec], format, ot, ln,
                                               search_pattern=search_pattern,
                                               user_info=user_info, verbose=verbose,
                                               sf=sf, so=so, sp=sp, rm=rm)
                        content = websearch_templates.tmpl_detailed_record_metadata(
                            recID = recIDs[irec],
                            ln = ln,
                            format = format,
                            creationdate = creationdate,
                            modificationdate = modificationdate,
                            content = content)
                        # display of the next-hit/previous-hit/back-to-search links
                        # on the detailed record pages
                        content += websearch_templates.tmpl_display_back_to_search(req,
                                                                                   recIDs[irec],
                                                                                   ln)
                        req.write(content)
                        req.write(webstyle_templates.detailed_record_container_bottom(recIDs[irec],
                                                                                      tabs,
                                                                                      ln,
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
                                           user_info=user_info, verbose=verbose,
                                           sf=sf, so=so, sp=sp, rm=rm))

    else:
        print_warning(req, _("Use different search terms."))

def print_records_prologue(req, format, cc=None):
    """
    Print the appropriate prologue for list of records in the given
    format.
    """
    prologue = "" # no prologue needed for HTML or Text formats
    if format.startswith('xm'):
        prologue = websearch_templates.tmpl_xml_marc_prologue()
    elif format.startswith('xn'):
        prologue = websearch_templates.tmpl_xml_nlm_prologue()
    elif format.startswith('xw'):
        prologue = websearch_templates.tmpl_xml_refworks_prologue()
    elif format.startswith('xr'):
        prologue = websearch_templates.tmpl_xml_rss_prologue(cc=cc)
    elif format.startswith('xe'):
        prologue = websearch_templates.tmpl_xml_endnote_prologue()
    elif format.startswith('xo'):
        prologue = websearch_templates.tmpl_xml_mods_prologue()
    elif format.startswith('xp'):
        prologue = websearch_templates.tmpl_xml_podcast_prologue(cc=cc)
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
    elif format.startswith('xw'):
        epilogue = websearch_templates.tmpl_xml_refworks_epilogue()
    elif format.startswith('xr'):
        epilogue = websearch_templates.tmpl_xml_rss_epilogue()
    elif format.startswith('xe'):
        epilogue = websearch_templates.tmpl_xml_endnote_epilogue()
    elif format.startswith('xo'):
        epilogue = websearch_templates.tmpl_xml_mods_epilogue()
    elif format.startswith('xp'):
        epilogue = websearch_templates.tmpl_xml_podcast_epilogue()
    elif format.startswith('x'):
        epilogue = websearch_templates.tmpl_xml_default_epilogue()
    req.write(epilogue)

def get_record(recid):
    """Directly the record object corresponding to the recid."""
    if CFG_BIBUPLOAD_SERIALIZE_RECORD_STRUCTURE:
        value = run_sql("SELECT value FROM bibfmt WHERE id_bibrec=%s AND FORMAT='recstruct'",  (recid, ))
        if value:
            try:
                return deserialize_via_marshal(value[0][0])
            except:
                ### In case of corruption, let's rebuild it!
                pass
    return create_record(print_record(recid, 'xm'))[0]

def print_record(recID, format='hb', ot='', ln=CFG_SITE_LANG, decompress=zlib.decompress,
                 search_pattern=None, user_info=None, verbose=0, sf='', so='d', sp='', rm=''):
    """
    Prints record 'recID' formatted according to 'format'.

    'sf' is sort field and 'rm' is ranking method that are passed here
    only for proper linking purposes: e.g. when a certain ranking
    method or a certain sort field was selected, keep it selected in
    any dynamic search links that may be printed.
    """
    if format == 'recstruct':
        return get_record(recID)

    _ = gettext_set_language(ln)

    display_claim_this_paper = False

    try:
        display_claim_this_paper = user_info["precached_viewclaimlink"]
    except (KeyError, TypeError):
        display_claim_this_paper = False
    #check from user information if the user has the right to see hidden fields/tags in the
    #records as well
    can_see_hidden = (acc_authorize_action(user_info, 'runbibedit')[0] == 0)

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

        merged_recid = get_merged_recid(recID)
        if record_exist_p == -1 and not merged_recid and get_output_format_content_type(format) == 'text/html':
            # HTML output displays a default value for deleted records.
            # Other format have to deal with it.
            out += _("The record has been deleted.")
        else:
            if merged_recid:
                recID = merged_recid
            out += call_bibformat(recID, format, ln, search_pattern=search_pattern,
                                  user_info=user_info, verbose=verbose)

            # at the end of HTML brief mode, print the "Detailed record" functionality:
            if format.lower().startswith('hb') and \
                   format.lower() != 'hb_p':
                out += websearch_templates.tmpl_print_record_brief_links(ln=ln,
                                                                         recID=recID,
                                                                         sf=sf,
                                                                         so=so,
                                                                         sp=sp,
                                                                         rm=rm,
                                                                         display_claim_link=display_claim_this_paper)
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
        query = "SELECT value FROM bibfmt WHERE id_bibrec=%s AND format=%s"
        res = run_sql(query, (recID, format), 1)
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
                        "WHERE bb.id_bibrec=%s AND b.id=bb.id_bibxxx AND b.tag LIKE '00%%' "\
                        "ORDER BY bb.field_number, b.tag ASC"
                res = run_sql(query, (recID, ))
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
                                "WHERE bb.id_bibrec=%%s AND b.id=bb.id_bibxxx AND b.tag LIKE %%s"\
                                "ORDER BY bb.field_number, b.tag ASC" % (bx, bibx)
                        res = run_sql(query, (recID, str(digit1)+str(digit2)+'%'))
                        field_number_old = -999
                        field_old = ""
                        for row in res:
                            field, value, field_number = row[0], row[1], row[2]
                            ind1, ind2 = field[3], field[4]
                            if ind1 == "_" or ind1 == "":
                                ind1 = " "
                            if ind2 == "_" or ind2 == "":
                                ind2 = " "
                            # print field tag, unless hidden
                            printme = True
                            if not can_see_hidden:
                                for htag in CFG_BIBFORMAT_HIDDEN_TAGS:
                                    ltag = len(htag)
                                    samelenfield = field[0:ltag]
                                    if samelenfield == htag:
                                        printme = False

                            if printme:
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
                if f.split('.') == 'png':
                    continue
                out += "        <identifier>%s</identifier>\n" % encode_for_xml(f)

            for f in get_fieldvalues(recID, "520__a"):
                out += "        <description>%s</description>\n" % encode_for_xml(f)

            out += "        <date>%s</date>\n" % get_creation_date(recID)
        out += "    </dc>\n"

    elif len(format) == 6 and str(format[0:3]).isdigit():
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
            out += get_fieldvalues_alephseq_like(recID, ["001", CFG_OAI_ID_FIELD, "980"], can_see_hidden)
        else:
            out += get_fieldvalues_alephseq_like(recID, ot, can_see_hidden)

    elif format == "hm":
        if record_exist_p == -1:
            out += "\n<pre>" + cgi.escape(get_fieldvalues_alephseq_like(recID, ["001", CFG_OAI_ID_FIELD, "980"], can_see_hidden)) + "</pre>"
        else:
            out += "\n<pre>" + cgi.escape(get_fieldvalues_alephseq_like(recID, ot, can_see_hidden)) + "</pre>"

    elif format.startswith("h") and ot:
        ## user directly asked for some tags to be displayed only
        if record_exist_p == -1:
            out += "\n<pre>" + get_fieldvalues_alephseq_like(recID, ["001", CFG_OAI_ID_FIELD, "980"], can_see_hidden) + "</pre>"
        else:
            out += "\n<pre>" + get_fieldvalues_alephseq_like(recID, ot, can_see_hidden) + "</pre>"

    elif format == "hd":
        # HTML detailed format
        if record_exist_p == -1:
            out += _("The record has been deleted.")
        else:
            # look for detailed format existence:
            query = "SELECT value FROM bibfmt WHERE id_bibrec=%s AND format=%s"
            res = run_sql(query, (recID, format), 1)
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
                    out += "<strong>%s %d</strong>" % (get_field_i18nname("record ID", ln, False), recID)
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
            query = "SELECT value FROM bibfmt WHERE id_bibrec=%s AND format=%s"
            res = run_sql(query, (recID, format))
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
                out += websearch_templates.tmpl_print_record_brief_links(ln=ln,
                                                                         recID=recID,
                                                                         sf=sf,
                                                                         so=so,
                                                                         sp=sp,
                                                                         rm=rm,
                                                                         display_claim_link=display_claim_this_paper)

    # print record closing tags, if needed:
    if format == "marcxml" or format == "oai_dc":
        out += "   </metadata>\n"
        out += "  </record>\n"

    return out

def call_bibformat(recID, format="HD", ln=CFG_SITE_LANG, search_pattern=None, user_info=None, verbose=0):
    """
    Calls BibFormat and returns formatted record.

    BibFormat will decide by itself if old or new BibFormat must be used.
    """

    from invenio.bibformat_utils import get_pdf_snippets

    keywords = []
    if search_pattern is not None:
        units = create_basic_search_units(None, str(search_pattern), None)
        keywords = [unit[1] for unit in units if (unit[0] != '-' and unit[2] in [None, 'fulltext'])]

    out = format_record(recID,
                         of=format,
                         ln=ln,
                         search_pattern=keywords,
                         user_info=user_info,
                         verbose=verbose)

    if CFG_WEBSEARCH_FULLTEXT_SNIPPETS and user_info and \
           'fulltext' in user_info['uri']:
        # check snippets only if URL contains fulltext
        # FIXME: make it work for CLI too, via new function arg
        if keywords:
            snippets = get_pdf_snippets(recID, keywords)
            if snippets:
                out += snippets

    return out

def log_query(hostname, query_args, uid=-1):
    """
    Log query into the query and user_query tables.
    Return id_query or None in case of problems.
    """
    id_query = None
    if uid >= 0:
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

### CALLABLES

def perform_request_search(req=None, cc=CFG_SITE_NAME, c=None, p="", f="", rg=CFG_WEBSEARCH_DEF_RECORDS_IN_GROUPS, sf="", so="d", sp="", rm="", of="id", ot="", aas=0,
                           p1="", f1="", m1="", op1="", p2="", f2="", m2="", op2="", p3="", f3="", m3="", sc=0, jrec=0,
                           recid=-1, recidb=-1, sysno="", id=-1, idb=-1, sysnb="", action="", d1="",
                           d1y=0, d1m=0, d1d=0, d2="", d2y=0, d2m=0, d2d=0, dt="", verbose=0, ap=0, ln=CFG_SITE_LANG, ec=None, tab="", wl=0):
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

         aas - advanced search ("0" means no, "1" means yes).  Whether
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
               migrate to Invenio from another system, and store your
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

          wl - wildcard limit (ex: 100) the wildcard queries will be
               limited at 100 results
    """

    selected_external_collections_infos = None

    # wash output format:
    of = wash_output_format(of)

    # raise an exception when trying to print out html from the cli
    if of.startswith("h"):
        assert req

    # for every search engine request asking for an HTML output, we
    # first regenerate cache of collection and field I18N names if
    # needed; so that later we won't bother checking timestamps for
    # I18N names at all:
    if of.startswith("h"):
        collection_i18nname_cache.recreate_cache_if_needed()
        field_i18nname_cache.recreate_cache_if_needed()

    # wash all arguments requiring special care
    try:
        (cc, colls_to_display, colls_to_search, hosted_colls, wash_colls_debug) = wash_colls(cc, c, sc, verbose) # which colls to search and to display?
    except InvenioWebSearchUnknownCollectionError, exc:
        colname = exc.colname
        if of.startswith("h"):
            page_start(req, of, cc, aas, ln, getUid(req),
                       websearch_templates.tmpl_collection_not_found_page_title(colname, ln))
            req.write(websearch_templates.tmpl_collection_not_found_page_body(colname, ln))
            return page_end(req, of, ln)
        elif of == "id":
            return []
        elif of.startswith("x"):
            # Print empty, but valid XML
            print_records_prologue(req, of)
            print_records_epilogue(req, of)
            return page_end(req, of, ln)
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

    # wash ranking method:
    if not is_method_valid(None, rm):
        rm = ""

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
    if action != "browse" and req and not isinstance(req, cStringIO.OutputType) \
           and req.args: # we do not want to add options while browsing or while calling via command-line
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
        referer = None
        if req:
            referer = req.headers_in.get('Referer')
        cc = guess_collection_of_a_record(recid, referer)
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

        if req is not None and not req.header_only:
            page_start(req, of, cc, aas, ln, uid, title, description, keywords, recid, tab)

        # Default format is hb but we are in detailed -> change 'of'
        if of == "hb":
            of = "hd"
        if record_exists(recid):
            if recidb <= recid: # sanity check
                recidb = recid + 1
            if of == "id":
                return [recidx for recidx in range(recid, recidb) if record_exists(recidx)]
            else:
                print_records(req, range(recid, recidb), -1, -9999, of, ot, ln, search_pattern=p, verbose=verbose, tab=tab, sf=sf, so=so, sp=sp, rm=rm)
            if req and of.startswith("h"): # register detailed record page view event
                client_ip_address = str(req.remote_ip)
                register_page_view_event(recid, uid, client_ip_address)
        else: # record does not exist
            if of == "id":
                return []
            elif of.startswith("x"):
                # Print empty, but valid XML
                print_records_prologue(req, of)
                print_records_epilogue(req, of)
            elif of.startswith("h"):
                if req.header_only:
                    raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND
                else:
                    print_warning(req, _("Requested record does not seem to exist."))

    elif action == "browse":
        ## 2 - browse needed
        of = 'hb'
        page_start(req, of, cc, aas, ln, uid, _("Browse"), p=create_page_title_search_pattern_info(p, p1, p2, p3))
        req.write(create_search_box(cc, colls_to_display, p, f, rg, sf, so, sp, rm, of, ot, aas, ln, p1, f1, m1, op1,
                                    p2, f2, m2, op2, p3, f3, m3, sc, pl, d1y, d1m, d1d, d2y, d2m, d2d, dt, jrec, ec, action))
        try:
            if aas == 1 or (p1 or p2 or p3):
                browse_pattern(req, colls_to_search, p1, f1, rg, ln)
                browse_pattern(req, colls_to_search, p2, f2, rg, ln)
                browse_pattern(req, colls_to_search, p3, f3, rg, ln)
            else:
                browse_pattern(req, colls_to_search, p, f, rg, ln)
        except:
            register_exception(req=req, alert_admin=True)
            if of.startswith("h"):
                req.write(create_error_box(req, verbose=verbose, ln=ln))
            elif of.startswith("x"):
                # Print empty, but valid XML
                print_records_prologue(req, of)
                print_records_epilogue(req, of)
            return page_end(req, of, ln)

    elif rm and p.startswith("recid:"):
        ## 3-ter - similarity search (or old-style citation search) needed
        if req and not req.header_only:
            page_start(req, of, cc, aas, ln, uid, _("Search Results"), p=create_page_title_search_pattern_info(p, p1, p2, p3))
        if of.startswith("h"):
            req.write(create_search_box(cc, colls_to_display, p, f, rg, sf, so, sp, rm, of, ot, aas, ln, p1, f1, m1, op1,
                                        p2, f2, m2, op2, p3, f3, m3, sc, pl, d1y, d1m, d1d, d2y, d2m, d2d, dt, jrec, ec, action))
        if record_exists(p[6:]) != 1:
            # record does not exist
            if of.startswith("h"):
                if req.header_only:
                    raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND
                else:
                    print_warning(req, _("Requested record does not seem to exist."))
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
                                    rank_records_bibrank(rm, 0, get_collection_reclist(cc), string.split(p), verbose)
            if results_similar_recIDs:
                t2 = os.times()[4]
                cpu_time = t2 - t1
                if of.startswith("h"):
                    req.write(print_search_info(p, f, sf, so, sp, rm, of, ot, cc, len(results_similar_recIDs),
                                                jrec, rg, aas, ln, p1, p2, p3, f1, f2, f3, m1, m2, m3, op1, op2,
                                                sc, pl_in_url,
                                                d1y, d1m, d1d, d2y, d2m, d2d, dt, cpu_time))
                    print_warning(req, results_similar_comments)
                    print_records(req, results_similar_recIDs, jrec, rg, of, ot, ln,
                                  results_similar_relevances, results_similar_relevances_prologue, results_similar_relevances_epilogue, search_pattern=p, verbose=verbose, sf=sf, so=so, sp=sp, rm=rm)
                elif of=="id":
                    return results_similar_recIDs
                elif of.startswith("x"):
                    print_records(req, results_similar_recIDs, jrec, rg, of, ot, ln,
                                  results_similar_relevances, results_similar_relevances_prologue, results_similar_relevances_epilogue, search_pattern=p, verbose=verbose, sf=sf, so=so, sp=sp, rm=rm)
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
        page_start(req, of, cc, aas, ln, uid, _("Search Results"), p=create_page_title_search_pattern_info(p, p1, p2, p3))
        if of.startswith("h"):
            req.write(create_search_box(cc, colls_to_display, p, f, rg, sf, so, sp, rm, of, ot, aas, ln, p1, f1, m1, op1,
                                        p2, f2, m2, op2, p3, f3, m3, sc, pl, d1y, d1m, d1d, d2y, d2m, d2d, dt, jrec, ec, action))
        recID = p[12:]
        if record_exists(recID) != 1:
            # record does not exist
            if of.startswith("h"):
                print_warning(req, _("Requested record does not seem to exist."))
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
                                                jrec, rg, aas, ln, p1, p2, p3, f1, f2, f3, m1, m2, m3, op1, op2,
                                                sc, pl_in_url,
                                                d1y, d1m, d1d, d2y, d2m, d2d, dt, cpu_time))
                    print_records(req, results_cocited_recIDs, jrec, rg, of, ot, ln, search_pattern=p, verbose=verbose, sf=sf, so=so, sp=sp, rm=rm)
                elif of=="id":
                    return results_cocited_recIDs
                elif of.startswith("x"):
                    print_records(req, results_cocited_recIDs, jrec, rg, of, ot, ln, search_pattern=p, verbose=verbose, sf=sf, so=so, sp=sp, rm=rm)

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
        query_in_cache = False
        query_representation_in_cache = repr((p,f,colls_to_search, wl))
        page_start(req, of, cc, aas, ln, uid, p=create_page_title_search_pattern_info(p, p1, p2, p3))

        if of.startswith("h") and verbose and wash_colls_debug:
            print_warning(req, "wash_colls debugging info : %s" % wash_colls_debug)

        # search into the hosted collections only if the output format is html or xml
        if hosted_colls and (of.startswith("h") or of.startswith("x")) and not p.startswith("recid:"):

            # hosted_colls_results : the hosted collections' searches that did not timeout
            # hosted_colls_timeouts : the hosted collections' searches that timed out and will be searched later on again
            (hosted_colls_results, hosted_colls_timeouts) = calculate_hosted_collections_results(req, [p, p1, p2, p3], f, hosted_colls, verbose, ln, CFG_HOSTED_COLLECTION_TIMEOUT_ANTE_SEARCH)

            # successful searches
            if hosted_colls_results:
                hosted_colls_true_results = []
                for result in hosted_colls_results:
                    # if the number of results is None or 0 (or False) then just do nothing
                    if result[1] == None or result[1] == False:
                        # these are the searches the returned no or zero results
                        if verbose:
                            print_warning(req, "Hosted collections (perform_search_request): %s returned no results" % result[0][1].name)
                    else:
                        # these are the searches that actually returned results on time
                        hosted_colls_true_results.append(result)
                        if verbose:
                            print_warning(req, "Hosted collections (perform_search_request): %s returned %s results in %s seconds" % (result[0][1].name, result[1], result[2]))
            else:
                if verbose:
                    print_warning(req, "Hosted collections (perform_search_request): there were no hosted collections results to be printed at this time")
            if hosted_colls_timeouts:
                if verbose:
                    for timeout in hosted_colls_timeouts:
                        print_warning(req, "Hosted collections (perform_search_request): %s timed out and will be searched again later" % timeout[0][1].name)
        # we need to know for later use if there were any hosted collections to be searched even if they weren't in the end
        elif hosted_colls and ((not (of.startswith("h") or of.startswith("x"))) or p.startswith("recid:")):
            (hosted_colls_results, hosted_colls_timeouts) = (None, None)
        else:
            if verbose:
                print_warning(req, "Hosted collections (perform_search_request): there were no hosted collections to be searched")

        ## let's define some useful boolean variables:
        # True means there are actual or potential hosted collections results to be printed
        hosted_colls_actual_or_potential_results_p = not (not hosted_colls or not ((hosted_colls_results and hosted_colls_true_results) or hosted_colls_timeouts))

        # True means there are hosted collections timeouts to take care of later
        # (useful for more accurate printing of results later)
        hosted_colls_potential_results_p = not (not hosted_colls or not hosted_colls_timeouts)

        # True means we only have hosted collections to deal with
        only_hosted_colls_actual_or_potential_results_p = not colls_to_search and hosted_colls_actual_or_potential_results_p

        if of.startswith("h"):
            req.write(create_search_box(cc, colls_to_display, p, f, rg, sf, so, sp, rm, of, ot, aas, ln, p1, f1, m1, op1,
                                        p2, f2, m2, op2, p3, f3, m3, sc, pl, d1y, d1m, d1d, d2y, d2m, d2d, dt, jrec, ec, action))
        t1 = os.times()[4]
        results_in_any_collection = intbitset()
        if aas == 1 or (p1 or p2 or p3):
            ## 3A - advanced search
            try:
                results_in_any_collection = search_pattern_parenthesised(req, p1, f1, m1, ap=ap, of=of, verbose=verbose, ln=ln, wl=wl)
                if len(results_in_any_collection) == 0:
                    if of.startswith("h"):
                        perform_external_collection_search(req, cc, [p, p1, p2, p3], f, ec, verbose, ln, selected_external_collections_infos)
                    elif of.startswith("x"):
                        # Print empty, but valid XML
                        print_records_prologue(req, of)
                        print_records_epilogue(req, of)
                    return page_end(req, of, ln)
                if p2:
                    results_tmp = search_pattern_parenthesised(req, p2, f2, m2, ap=ap, of=of, verbose=verbose, ln=ln, wl=wl)
                    if op1 == "a": # add
                        results_in_any_collection.intersection_update(results_tmp)
                    elif op1 == "o": # or
                        results_in_any_collection.union_update(results_tmp)
                    elif op1 == "n": # not
                        results_in_any_collection.difference_update(results_tmp)
                    else:
                        if of.startswith("h"):
                            print_warning(req, "Invalid set operation %s." % cgi.escape(op1), "Error")
                    if len(results_in_any_collection) == 0:
                        if of.startswith("h"):
                            perform_external_collection_search(req, cc, [p, p1, p2, p3], f, ec, verbose, ln, selected_external_collections_infos)
                        elif of.startswith("x"):
                            # Print empty, but valid XML
                            print_records_prologue(req, of)
                            print_records_epilogue(req, of)
                        return page_end(req, of, ln)
                if p3:
                    results_tmp = search_pattern_parenthesised(req, p3, f3, m3, ap=ap, of=of, verbose=verbose, ln=ln, wl=wl)
                    if op2 == "a": # add
                        results_in_any_collection.intersection_update(results_tmp)
                    elif op2 == "o": # or
                        results_in_any_collection.union_update(results_tmp)
                    elif op2 == "n": # not
                        results_in_any_collection.difference_update(results_tmp)
                    else:
                        if of.startswith("h"):
                            print_warning(req, "Invalid set operation %s." % cgi.escape(op2), "Error")
            except:
                register_exception(req=req, alert_admin=True)
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
            if search_results_cache.cache.has_key(query_representation_in_cache):
                # query is not in the cache already, so reuse it:
                query_in_cache = True
                results_in_any_collection = search_results_cache.cache[query_representation_in_cache]
                if verbose and of.startswith("h"):
                    print_warning(req, "Search stage 0: query found in cache, reusing cached results.")
            else:
                try:
                    # added the display_nearest_terms_box parameter to avoid printing out the "Nearest terms in any collection"
                    # recommendations when there are results only in the hosted collections. Also added the if clause to avoid
                    # searching in case we know we only have actual or potential hosted collections results
                    if not only_hosted_colls_actual_or_potential_results_p:
                        results_in_any_collection = search_pattern_parenthesised(req, p, f, ap=ap, of=of, verbose=verbose, ln=ln, display_nearest_terms_box=not hosted_colls_actual_or_potential_results_p, wl=wl)
                except:
                    register_exception(req=req, alert_admin=True)
                    if of.startswith("h"):
                        req.write(create_error_box(req, verbose=verbose, ln=ln))
                        perform_external_collection_search(req, cc, [p, p1, p2, p3], f, ec, verbose, ln, selected_external_collections_infos)
                    return page_end(req, of, ln)

        if len(results_in_any_collection) == 0 and not hosted_colls_actual_or_potential_results_p:
            if of.startswith("h"):
                perform_external_collection_search(req, cc, [p, p1, p2, p3], f, ec, verbose, ln, selected_external_collections_infos)
            elif of.startswith("x"):
                # Print empty, but valid XML
                print_records_prologue(req, of)
                print_records_epilogue(req, of)
            return page_end(req, of, ln)

        # store this search query results into search results cache if needed:
        if CFG_WEBSEARCH_SEARCH_CACHE_SIZE and not query_in_cache:
            if len(search_results_cache.cache) > CFG_WEBSEARCH_SEARCH_CACHE_SIZE:
                search_results_cache.clear()
            search_results_cache.cache[query_representation_in_cache] = results_in_any_collection
            if verbose and of.startswith("h"):
                print_warning(req, "Search stage 3: storing query results in cache.")

        # search stage 4: intersection with collection universe:
        try:
            # added the display_nearest_terms_box parameter to avoid printing out the "Nearest terms in any collection"
            # recommendations when there results only in the hosted collections. Also added the if clause to avoid
            # searching in case we know since the last stage that we have no results in any collection
            if len(results_in_any_collection) != 0:
                results_final = intersect_results_with_collrecs(req, results_in_any_collection, colls_to_search, ap, of, verbose, ln, display_nearest_terms_box=not hosted_colls_actual_or_potential_results_p)
            else:
                results_final = {}
        except:
            register_exception(req=req, alert_admin=True)
            if of.startswith("h"):
                req.write(create_error_box(req, verbose=verbose, ln=ln))
                perform_external_collection_search(req, cc, [p, p1, p2, p3], f, ec, verbose, ln, selected_external_collections_infos)
            return page_end(req, of, ln)

        if results_final == {} and not hosted_colls_actual_or_potential_results_p:
            if of.startswith("h"):
                perform_external_collection_search(req, cc, [p, p1, p2, p3], f, ec, verbose, ln, selected_external_collections_infos)
            if of.startswith("x"):
                # Print empty, but valid XML
                print_records_prologue(req, of)
                print_records_epilogue(req, of)
            return page_end(req, of, ln)

        # search stage 5: apply search option limits and restrictions:
        if datetext1 != "" and results_final != {}:
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
                register_exception(req=req, alert_admin=True)
                if of.startswith("h"):
                    req.write(create_error_box(req, verbose=verbose, ln=ln))
                    perform_external_collection_search(req, cc, [p, p1, p2, p3], f, ec, verbose, ln, selected_external_collections_infos)
                return page_end(req, of, ln)
            if results_final == {} and not hosted_colls_actual_or_potential_results_p:
                if of.startswith("h"):
                    perform_external_collection_search(req, cc, [p, p1, p2, p3], f, ec, verbose, ln, selected_external_collections_infos)
                #if of.startswith("x"):
                #    # Print empty, but valid XML
                #    print_records_prologue(req, of)
                #    print_records_epilogue(req, of)
                return page_end(req, of, ln)

        if pl and results_final != {}:
            pl = wash_pattern(pl)
            if verbose and of.startswith("h"):
                print_warning(req, "Search stage 5: applying search pattern limit %s..." % cgi.escape(pl))
            try:
                results_final = intersect_results_with_hitset(req,
                                                              results_final,
                                                              search_pattern_parenthesised(req, pl, ap=0, ln=ln, wl=wl),
                                                              ap,
                                                              aptext=_("No match within your search limits, "
                                                                       "discarding this condition..."),
                                                              of=of)
            except:
                register_exception(req=req, alert_admin=True)
                if of.startswith("h"):
                    req.write(create_error_box(req, verbose=verbose, ln=ln))
                    perform_external_collection_search(req, cc, [p, p1, p2, p3], f, ec, verbose, ln, selected_external_collections_infos)
                return page_end(req, of, ln)
            if results_final == {} and not hosted_colls_actual_or_potential_results_p:
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
            results_final_for_all_selected_colls = intbitset()
            for coll in results_final.keys():
                results_final_for_all_selected_colls.union_update(results_final[coll])
            results_final_nb_total = len(results_final_for_all_selected_colls)

        #if hosted_colls and (of.startswith("h") or of.startswith("x")):
        if hosted_colls_actual_or_potential_results_p:
            if hosted_colls_results:
                for result in hosted_colls_true_results:
                    colls_to_search.append(result[0][1].name)
                    results_final_nb[result[0][1].name] = result[1]
                    results_final_nb_total += result[1]
                    cpu_time += result[2]
            if hosted_colls_timeouts:
                for timeout in hosted_colls_timeouts:
                    colls_to_search.append(timeout[1].name)
                    # use -963 as a special number to identify the collections that timed out
                    results_final_nb[timeout[1].name] = -963

        # we continue past this point only if there is a hosted collection that has timed out and might offer potential results
        if results_final_nb_total ==0 and not hosted_colls_potential_results_p:
            if of.startswith("h"):
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
                if rm: # do we have to rank?
                    results_final_for_all_colls_rank_records_output = rank_records(req, rm, 0, results_final_for_all_selected_colls,
                                                                                   string.split(p) + string.split(p1) +
                                                                                   string.split(p2) + string.split(p3), verbose, so, of, ln, rg, jrec)
                    if results_final_for_all_colls_rank_records_output[0]:
                        recIDs = results_final_for_all_colls_rank_records_output[0]
                elif sf or (CFG_BIBSORT_BUCKETS and sorting_methods): # do we have to sort?
                    recIDs = sort_records(req, recIDs, sf, so, sp, verbose, of, ln, rg, jrec)
                return recIDs
            elif of.startswith("h"):
                if of not in ['hcs']:
                    # added the hosted_colls_potential_results_p parameter to help print out the overview more accurately
                    req.write(print_results_overview(colls_to_search, results_final_nb_total, results_final_nb, cpu_time, ln, ec, hosted_colls_potential_results_p=hosted_colls_potential_results_p))
                    selected_external_collections_infos = print_external_results_overview(req, cc, [p, p1, p2, p3], f, ec, verbose, ln)
            # print number of hits found for XML outputs:
            if of.startswith("x"):
                req.write("<!-- Search-Engine-Total-Number-Of-Results: %s -->\n" % results_final_nb_total)
            # print records:
            if of in ['hcs']:
                # feed the current search to be summarized:
                from invenio.search_engine_summarizer import summarize_records
                search_p = p
                search_f = f
                if not p and (aas == 1 or p1 or p2 or p3):
                    op_d = {'n': ' and not ', 'a': ' and ', 'o': ' or ', '': ''}
                    triples = ziplist([f1, f2, f3], [p1, p2, p3], [op1, op2, ''])
                    triples_len = len(triples)
                    for i in range(triples_len):
                        fi, pi, oi = triples[i]                       # e.g.:
                        if i < triples_len-1 and not triples[i+1][1]: # if p2 empty
                            triples[i+1][0] = ''                      #   f2 must be too
                            oi = ''                                   #   and o1
                        if ' ' in pi:
                            pi = '"'+pi+'"'
                        if fi:
                            fi = fi + ':'
                        search_p += fi + pi + op_d[oi]
                    search_f = ''
                summarize_records(results_final_for_all_selected_colls, 'hcs', ln, search_p, search_f, req)
            else:
                if len(colls_to_search)>1:
                    cpu_time = -1 # we do not want to have search time printed on each collection
                print_records_prologue(req, of, cc=cc)
                results_final_colls = []
                wlqh_results_overlimit = 0
                for coll in colls_to_search:
                    if results_final.has_key(coll) and len(results_final[coll]):
                        if of.startswith("h"):
                            req.write(print_search_info(p, f, sf, so, sp, rm, of, ot, coll, results_final_nb[coll],
                                                        jrec, rg, aas, ln, p1, p2, p3, f1, f2, f3, m1, m2, m3, op1, op2,
                                                        sc, pl_in_url,
                                                        d1y, d1m, d1d, d2y, d2m, d2d, dt, cpu_time))
                        results_final_recIDs = list(results_final[coll])
                        results_final_relevances = []
                        results_final_relevances_prologue = ""
                        results_final_relevances_epilogue = ""
                        if rm: # do we have to rank?
                            results_final_recIDs_ranked, results_final_relevances, results_final_relevances_prologue, results_final_relevances_epilogue, results_final_comments = \
                                                         rank_records(req, rm, 0, results_final[coll],
                                                                      string.split(p) + string.split(p1) +
                                                                      string.split(p2) + string.split(p3), verbose, so, of, ln, rg, jrec)
                            if of.startswith("h"):
                                print_warning(req, results_final_comments)
                            if results_final_recIDs_ranked:
                                results_final_recIDs = results_final_recIDs_ranked
                            else:
                                # rank_records failed and returned some error message to display:
                                print_warning(req, results_final_relevances_prologue)
                                print_warning(req, results_final_relevances_epilogue)
                        elif sf or (CFG_BIBSORT_BUCKETS and sorting_methods): # do we have to sort?
                            results_final_recIDs = sort_records(req, results_final_recIDs, sf, so, sp, verbose, of, ln, rg, jrec)

                        if len(results_final_recIDs) < CFG_WEBSEARCH_PREV_NEXT_HIT_LIMIT:
                            results_final_colls.append(results_final_recIDs)
                        else:
                            wlqh_results_overlimit = 1

                        print_records(req, results_final_recIDs, jrec, rg, of, ot, ln,
                                      results_final_relevances,
                                      results_final_relevances_prologue,
                                      results_final_relevances_epilogue,
                                      search_pattern=p,
                                      print_records_prologue_p=False,
                                      print_records_epilogue_p=False,
                                      verbose=verbose,
                                      sf=sf,
                                      so=so,
                                      sp=sp,
                                      rm=rm)

                        if of.startswith("h"):
                            req.write(print_search_info(p, f, sf, so, sp, rm, of, ot, coll, results_final_nb[coll],
                                                        jrec, rg, aas, ln, p1, p2, p3, f1, f2, f3, m1, m2, m3, op1, op2,
                                                        sc, pl_in_url,
                                                        d1y, d1m, d1d, d2y, d2m, d2d, dt, cpu_time, 1))

                if req and not isinstance(req, cStringIO.OutputType):
                    # store the last search results page
                    session_param_set(req, 'websearch-last-query', req.unparsed_uri)
                    if wlqh_results_overlimit:
                        results_final_colls = None
                    # store list of results if user wants to display hits
                    # in a single list, or store list of collections of records
                    # if user displays hits split by collections:
                    session_param_set(req, 'websearch-last-query-hits', results_final_colls)

                #if hosted_colls and (of.startswith("h") or of.startswith("x")):
                if hosted_colls_actual_or_potential_results_p:
                    if hosted_colls_results:
                        # TODO: add a verbose message here
                        for result in hosted_colls_true_results:
                            if of.startswith("h"):
                                req.write(print_hosted_search_info(p, f, sf, so, sp, rm, of, ot, result[0][1].name, results_final_nb[result[0][1].name],
                                                            jrec, rg, aas, ln, p1, p2, p3, f1, f2, f3, m1, m2, m3, op1, op2,
                                                            sc, pl_in_url,
                                                            d1y, d1m, d1d, d2y, d2m, d2d, dt, cpu_time))
                            req.write(print_hosted_results(url_and_engine=result[0], ln=ln, of=of, req=req, limit=rg))
                            if of.startswith("h"):
                                req.write(print_hosted_search_info(p, f, sf, so, sp, rm, of, ot, result[0][1].name, results_final_nb[result[0][1].name],
                                                            jrec, rg, aas, ln, p1, p2, p3, f1, f2, f3, m1, m2, m3, op1, op2,
                                                            sc, pl_in_url,
                                                            d1y, d1m, d1d, d2y, d2m, d2d, dt, cpu_time, 1))
                    if hosted_colls_timeouts:
                        # TODO: add a verbose message here
                        # TODO: check if verbose messages still work when dealing with (re)calculations of timeouts
                        (hosted_colls_timeouts_results, hosted_colls_timeouts_timeouts) = do_calculate_hosted_collections_results(req, ln, None, verbose, None, hosted_colls_timeouts, CFG_HOSTED_COLLECTION_TIMEOUT_POST_SEARCH)
                        if hosted_colls_timeouts_results:
                            for result in hosted_colls_timeouts_results:
                                if result[1] == None or result[1] == False:
                                    ## these are the searches the returned no or zero results
                                    ## also print a nearest terms box, in case this is the only
                                    ## collection being searched and it returns no results?
                                    if of.startswith("h"):
                                        req.write(print_hosted_search_info(p, f, sf, so, sp, rm, of, ot, result[0][1].name, -963,
                                                                    jrec, rg, aas, ln, p1, p2, p3, f1, f2, f3, m1, m2, m3, op1, op2,
                                                                    sc, pl_in_url,
                                                                    d1y, d1m, d1d, d2y, d2m, d2d, dt, cpu_time))
                                        req.write(print_hosted_results(url_and_engine=result[0], ln=ln, of=of, req=req, no_records_found=True, limit=rg))
                                        req.write(print_hosted_search_info(p, f, sf, so, sp, rm, of, ot, result[0][1].name, -963,
                                                                    jrec, rg, aas, ln, p1, p2, p3, f1, f2, f3, m1, m2, m3, op1, op2,
                                                                    sc, pl_in_url,
                                                                    d1y, d1m, d1d, d2y, d2m, d2d, dt, cpu_time, 1))
                                else:
                                    # these are the searches that actually returned results on time
                                    if of.startswith("h"):
                                        req.write(print_hosted_search_info(p, f, sf, so, sp, rm, of, ot, result[0][1].name, result[1],
                                                                    jrec, rg, aas, ln, p1, p2, p3, f1, f2, f3, m1, m2, m3, op1, op2,
                                                                    sc, pl_in_url,
                                                                    d1y, d1m, d1d, d2y, d2m, d2d, dt, cpu_time))
                                    req.write(print_hosted_results(url_and_engine=result[0], ln=ln, of=of, req=req, limit=rg))
                                    if of.startswith("h"):
                                        req.write(print_hosted_search_info(p, f, sf, so, sp, rm, of, ot, result[0][1].name, result[1],
                                                                    jrec, rg, aas, ln, p1, p2, p3, f1, f2, f3, m1, m2, m3, op1, op2,
                                                                    sc, pl_in_url,
                                                                    d1y, d1m, d1d, d2y, d2m, d2d, dt, cpu_time, 1))
                        if hosted_colls_timeouts_timeouts:
                            for timeout in hosted_colls_timeouts_timeouts:
                                if of.startswith("h"):
                                    req.write(print_hosted_search_info(p, f, sf, so, sp, rm, of, ot, timeout[1].name, -963,
                                                                jrec, rg, aas, ln, p1, p2, p3, f1, f2, f3, m1, m2, m3, op1, op2,
                                                                sc, pl_in_url,
                                                                d1y, d1m, d1d, d2y, d2m, d2d, dt, cpu_time))
                                    req.write(print_hosted_results(url_and_engine=timeout[0], ln=ln, of=of, req=req, search_timed_out=True, limit=rg))
                                    req.write(print_hosted_search_info(p, f, sf, so, sp, rm, of, ot, timeout[1].name, -963,
                                                                jrec, rg, aas, ln, p1, p2, p3, f1, f2, f3, m1, m2, m3, op1, op2,
                                                                sc, pl_in_url,
                                                                d1y, d1m, d1d, d2y, d2m, d2d, dt, cpu_time, 1))

                print_records_epilogue(req, of)
                if f == "author" and of.startswith("h"):
                    req.write(create_similarly_named_authors_link_box(p, ln))

            # log query:
            try:
                id_query = log_query(req.remote_host, req.args, uid)
                if of.startswith("h") and id_query:
                    if not of in ['hcs']:
                        # display alert/RSS teaser for non-summary formats:
                        user_info = collect_user_info(req)
                        display_email_alert_part = True
                        if user_info:
                            if user_info['email'] == 'guest':
                                if CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS > 4:
                                    display_email_alert_part = False
                            else:
                                if not user_info['precached_usealerts']:
                                    display_email_alert_part = False
                        req.write(websearch_templates.tmpl_alert_rss_teaser_box_for_query(id_query, \
                                             ln=ln, display_email_alert_part=display_email_alert_part))
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
    req.content_type = "text/html"
    req.send_http_header()
    req.write("<html>")
    out = ""
    out += "<h1>Search Cache</h1>"
    # clear cache if requested:
    if action == "clear":
        search_results_cache.clear()
    req.write(out)
    # show collection reclist cache:
    out = "<h3>Collection reclist cache</h3>"
    out += "- collection table last updated: %s" % get_table_update_time('collection')
    out += "<br />- reclist cache timestamp: %s" % collection_reclist_cache.timestamp
    out += "<br />- reclist cache contents:"
    out += "<blockquote>"
    for coll in collection_reclist_cache.cache.keys():
        if collection_reclist_cache.cache[coll]:
            out += "%s (%d)<br />" % (coll, len(collection_reclist_cache.cache[coll]))
    out += "</blockquote>"
    req.write(out)
    # show search results cache:
    out = "<h3>Search Cache</h3>"
    out += "- search cache usage: %d queries cached (max. ~%d)" % \
           (len(search_results_cache.cache), CFG_WEBSEARCH_SEARCH_CACHE_SIZE)
    if len(search_results_cache.cache):
        out += "<br />- search cache contents:"
        out += "<blockquote>"
        for query, hitset in search_results_cache.cache.items():
            out += "<br />%s ... %s" % (query, hitset)
        out += """<p><a href="%s/search/cache?action=clear">clear search results cache</a>""" % CFG_SITE_URL
        out += "</blockquote>"
    req.write(out)
    # show field i18nname cache:
    out = "<h3>Field I18N names cache</h3>"
    out += "- fieldname table last updated: %s" % get_table_update_time('fieldname')
    out += "<br />- i18nname cache timestamp: %s" % field_i18nname_cache.timestamp
    out += "<br />- i18nname cache contents:"
    out += "<blockquote>"
    for field in field_i18nname_cache.cache.keys():
        for ln in field_i18nname_cache.cache[field].keys():
            out += "%s, %s = %s<br />" % (field, ln, field_i18nname_cache.cache[field][ln])
    out += "</blockquote>"
    req.write(out)
    # show collection i18nname cache:
    out = "<h3>Collection I18N names cache</h3>"
    out += "- collectionname table last updated: %s" % get_table_update_time('collectionname')
    out += "<br />- i18nname cache timestamp: %s" % collection_i18nname_cache.timestamp
    out += "<br />- i18nname cache contents:"
    out += "<blockquote>"
    for coll in collection_i18nname_cache.cache.keys():
        for ln in collection_i18nname_cache.cache[coll].keys():
            out += "%s, %s = %s<br />" % (coll, ln, collection_i18nname_cache.cache[coll][ln])
    out += "</blockquote>"
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
                datetime, dummy_aas, p, f, c, nbhits = string.split(line,"#")
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

def get_all_field_values(tag):
    """
    Return all existing values stored for a given tag.
    @param tag: the full tag, e.g. 909C0b
    @type tag: string
    @return: the list of values
    @rtype: list of strings
    """
    table = 'bib%2dx' % int(tag[:2])
    return [row[0] for row in run_sql("SELECT DISTINCT(value) FROM %s WHERE tag=%%s" % table, (tag, ))]

def get_most_popular_field_values(recids, tags, exclude_values=None, count_repetitive_values=True):
    """
    Analyze RECIDS and look for TAGS and return most popular values
    and the frequency with which they occur sorted according to
    descending frequency.

    If a value is found in EXCLUDE_VALUES, then do not count it.

    If COUNT_REPETITIVE_VALUES is True, then we count every occurrence
    of value in the tags.  If False, then we count the value only once
    regardless of the number of times it may appear in a record.
    (But, if the same value occurs in another record, we count it, of
    course.)

    Example:
     >>> get_most_popular_field_values(range(11,20), '980__a')
     (('PREPRINT', 10), ('THESIS', 7), ...)
     >>> get_most_popular_field_values(range(11,20), ('100__a', '700__a'))
     (('Ellis, J', 10), ('Ellis, N', 7), ...)
     >>> get_most_popular_field_values(range(11,20), ('100__a', '700__a'), ('Ellis, J'))
     (('Ellis, N', 7), ...)
    """

    def _get_most_popular_field_values_helper_sorter(val1, val2):
        "Compare VAL1 and VAL2 according to, firstly, frequency, then secondly, alphabetically."
        compared_via_frequencies = cmp(valuefreqdict[val2], valuefreqdict[val1])
        if compared_via_frequencies == 0:
            return cmp(val1.lower(), val2.lower())
        else:
            return compared_via_frequencies

    valuefreqdict = {}
    ## sanity check:
    if not exclude_values:
        exclude_values = []
    if isinstance(tags, str):
        tags = (tags,)
    ## find values to count:
    vals_to_count = []
    displaytmp = {}
    if count_repetitive_values:
        # counting technique A: can look up many records at once: (very fast)
        for tag in tags:
            vals_to_count.extend(get_fieldvalues(recids, tag))
    else:
        # counting technique B: must count record-by-record: (slow)
        for recid in recids:
            vals_in_rec = []
            for tag in tags:
                for val in get_fieldvalues(recid, tag, False):
                    vals_in_rec.append(val)
            # do not count repetitive values within this record
            # (even across various tags, so need to unify again):
            dtmp = {}
            for val in vals_in_rec:
                dtmp[val.lower()] = 1
                displaytmp[val.lower()] = val
            vals_in_rec = dtmp.keys()
            vals_to_count.extend(vals_in_rec)
    ## are we to exclude some of found values?
    for val in vals_to_count:
        if val not in exclude_values:
            if valuefreqdict.has_key(val):
                valuefreqdict[val] += 1
            else:
                valuefreqdict[val] = 1
    ## sort by descending frequency of values:
    out = ()
    vals = valuefreqdict.keys()
    vals.sort(_get_most_popular_field_values_helper_sorter)
    for val in vals:
        tmpdisplv = ''
        if displaytmp.has_key(val):
            tmpdisplv = displaytmp[val]
        else:
            tmpdisplv = val
        out += (tmpdisplv, valuefreqdict[val]),
    return out

def profile(p="", f="", c=CFG_SITE_NAME):
    """Profile search time."""
    import profile
    import pstats
    profile.run("perform_request_search(p='%s',f='%s', c='%s')" % (p, f, c), "perform_request_search_profile")
    p = pstats.Stats("perform_request_search_profile")
    p.strip_dirs().sort_stats("cumulative").print_stats()
    return 0
