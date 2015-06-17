# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012,
#               2013, 2014, 2015 CERN.
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

# pylint: disable=C0301,W0703

"""Invenio Search Engine in mod_python."""

import warnings

from invenio.utils.deprecation import RemovedInInvenio23Warning

warnings.warn("Legacy search_engine will be removed in 2.3. Please check "
              "'invenio.modules.search' module.",
              RemovedInInvenio23Warning)

__lastupdated__ = """$Date$"""

__revision__ = "$Id$"

# import general modules:
import cgi
import re
import urllib
import urlparse
import zlib

# import Invenio stuff:
from invenio.config import \
     CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS, \
     CFG_BASE_URL, \
     CFG_BIBFORMAT_HIDDEN_TAGS, \
     CFG_BIBINDEX_CHARS_PUNCTUATION, \
     CFG_BIBRANK_SHOW_DOWNLOAD_GRAPHS, \
     CFG_BIBSORT_BUCKETS, \
     CFG_BIBSORT_ENABLED, \
     CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG, \
     CFG_BIBUPLOAD_SERIALIZE_RECORD_STRUCTURE, \
     CFG_CERN_SITE, \
     CFG_INSPIRE_SITE, \
     CFG_LOGDIR, \
     CFG_OAI_ID_FIELD, \
     CFG_WEBSEARCH_FIELDS_CONVERT, \
     CFG_WEBSEARCH_DEF_RECORDS_IN_GROUPS, \
     CFG_WEBSEARCH_FULLTEXT_SNIPPETS, \
     CFG_WEBSEARCH_DISPLAY_NEAREST_TERMS, \
     CFG_WEBSEARCH_WILDCARD_LIMIT, \
     CFG_WEBSEARCH_IDXPAIRS_FIELDS,\
     CFG_WEBSEARCH_IDXPAIRS_EXACT_SEARCH, \
     CFG_BIBUPLOAD_SERIALIZE_RECORD_STRUCTURE, \
     CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG, \
     CFG_BIBRANK_SHOW_DOWNLOAD_GRAPHS, \
     CFG_WEBSEARCH_SYNONYM_KBRS, \
     CFG_SITE_LANG, \
     CFG_SITE_NAME, \
     CFG_LOGDIR, \
     CFG_SITE_URL, \
     CFG_SOLR_URL, \
     CFG_WEBSEARCH_DETAILED_META_FORMAT, \
     CFG_SITE_RECORD, \
     CFG_WEBSEARCH_PREV_NEXT_HIT_LIMIT, \
     CFG_WEBSEARCH_VIEWRESTRCOLL_POLICY, \
     CFG_WEBSEARCH_WILDCARD_LIMIT, \
     CFG_XAPIAN_ENABLED

try:
    from invenio.config import CFG_BIBSORT_DEFAULT_FIELD, \
        CFG_BIBSORT_DEFAULT_FIELD_ORDER
except ImportError:
    CFG_BIBSORT_DEFAULT_FIELD = 'latest first'
    CFG_BIBSORT_DEFAULT_FIELD_ORDER = 'd'

from invenio.modules.search.searchext.engines.native import search_unit
from invenio.modules.search.utils import get_most_popular_field_values
from invenio.modules.search.errors import \
     InvenioWebSearchUnknownCollectionError, \
     InvenioWebSearchWildcardLimitError, \
     InvenioWebSearchReferstoLimitError, \
     InvenioWebSearchCitedbyLimitError
from invenio.legacy.bibrecord import (get_fieldvalues,
                                      get_fieldvalues_alephseq_like)
from .utils import record_exists
from invenio.legacy.bibrecord import create_record, record_xml_output
from invenio.legacy.bibrank.record_sorter import (
    get_bibrank_methods,
    is_method_valid,
    rank_records as rank_records_bibrank,
    rank_by_citations)
from invenio.legacy.bibrank.downloads_similarity import register_page_view_event, calculate_reading_similarity_list
from invenio.legacy.bibindex.engine_stemmer import stem
from invenio.modules.indexer.tokenizers.BibIndexDefaultTokenizer import BibIndexDefaultTokenizer
from invenio.legacy.bibindex.engine_utils import author_name_requires_phrase_search, \
    get_field_tags
from invenio.legacy.bibindex.engine_washer import wash_index_term, lower_index_term, wash_author_name
from invenio.legacy.bibindex.engine_config import CFG_BIBINDEX_SYNONYM_MATCH_TYPE
from invenio.legacy.bibrank.downloads_grapher import create_download_history_graph_and_box
from invenio.legacy.miscutil.data_cacher import DataCacher
from invenio.legacy.websearch_external_collections import print_external_results_overview, perform_external_collection_search
from invenio.modules.access.control import acc_get_action_id
from invenio.modules.access.local_config import VIEWRESTRCOLL, \
    CFG_ACC_GRANT_AUTHOR_RIGHTS_TO_EMAILS_IN_TAGS, \
    CFG_ACC_GRANT_AUTHOR_RIGHTS_TO_USERIDS_IN_TAGS, \
    CFG_ACC_GRANT_VIEWER_RIGHTS_TO_EMAILS_IN_TAGS, \
    CFG_ACC_GRANT_VIEWER_RIGHTS_TO_USERIDS_IN_TAGS

from invenio.legacy.websearch.adminlib import get_detailed_page_tabs, get_detailed_page_tabs_counts
from intbitset import intbitset
from invenio.legacy.dbquery import InvenioDbQueryWildcardLimitError
from invenio.utils.serializers import deserialize_via_marshal
from invenio.modules.access.engine import acc_authorize_action
from invenio.ext.logging import register_exception
from invenio.utils.text import encode_for_xml, wash_for_utf8, strip_accents
from invenio.legacy import bibrecord

import invenio.legacy.template
websearch_templates = invenio.legacy.template.load('websearch')

from invenio.legacy.bibrank.citation_searcher import calculate_cited_by_list, \
    calculate_co_cited_with_list, get_records_with_num_cites, \
    get_refersto_hitset, get_citedby_hitset, get_cited_by_list, \
    get_refers_to_list, get_citers_log

from invenio.legacy.bibrank.citation_grapher import create_citation_history_graph_and_box
from invenio.legacy.bibrank.selfcites_searcher import get_self_cited_by_list, \
                                                      get_self_cited_by, \
                                                      get_self_refers_to_list

from invenio.legacy.dbquery import run_sql, run_sql_with_limit, \
    wash_table_column_name, get_table_update_time
from invenio.legacy.webuser import getUid, collect_user_info
from invenio.legacy.webpage import pageheaderonly, pagefooteronly, create_error_box, write_warning
from invenio.base.i18n import gettext_set_language

from invenio.utils import apache

from invenio.legacy.websearch_external_collections import calculate_hosted_collections_results, do_calculate_hosted_collections_results
from invenio.legacy.websearch_external_collections.config import CFG_EXTERNAL_COLLECTION_MAXRESULTS

from sqlalchemy.exc import DatabaseError

VIEWRESTRCOLL_ID = acc_get_action_id(VIEWRESTRCOLL)

# em possible values
EM_REPOSITORY={"body" : "B",
               "header" : "H",
               "footer" : "F",
               "search_box" : "S",
               "see_also_box" : "L",
               "basket" : "K",
               "alert" : "A",
               "search_info" : "I",
               "overview" : "O",
               "all_portalboxes" : "P",
               "te_portalbox" : "Pte",
               "tp_portalbox" : "Ptp",
               "np_portalbox" : "Pnp",
               "ne_portalbox" : "Pne",
               "lt_portalbox" : "Plt",
               "rt_portalbox" : "Prt",
               "search_services": "SER"};

from invenio.modules.collections.cache import collection_reclist_cache
from invenio.modules.collections.cache import collection_restricted_p
from invenio.modules.collections.cache import restricted_collection_cache
from invenio.modules.search.utils import get_permitted_restricted_collections
from invenio.modules.collections.cache import get_all_restricted_recids


from invenio.modules.records.access import check_user_can_view_record

from invenio.modules.collections.cache import get_collection_reclist
from invenio.modules.collections.cache import get_coll_i18nname
from invenio.modules.search.cache import get_field_i18nname

from invenio.modules.indexer.models import IdxINDEX


get_index_id_from_field = IdxINDEX.get_index_id_from_field


def create_navtrail_links(cc=CFG_SITE_NAME, aas=0, ln=CFG_SITE_LANG, self_p=1, tab=''):
    """Creates navigation trail links, i.e. links to collection
    ancestors (except Home collection).  If aas==1, then links to
    Advanced Search interfaces; otherwise Simple Search.
    """

    dads = []
    for dad in get_coll_ancestors(cc):
        if dad != CFG_SITE_NAME: # exclude Home collection
            dads.append((dad, get_coll_i18nname(dad, ln, False)))

    if self_p and cc != CFG_SITE_NAME:
        dads.append((cc, get_coll_i18nname(cc, ln, False)))

    return websearch_templates.tmpl_navtrail_links(
        aas=aas, ln=ln, dads=dads)

from invenio.modules.indexer.utils import get_synonym_terms

from invenio.modules.search.washers import *


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


from invenio.modules.collections.cache import get_collection_allchildren


def browse_pattern_phrases(req, colls, p, f, rg, ln=CFG_SITE_LANG):
    """Returns either biliographic phrases or words indexes."""

    ## is p enclosed in quotes? (coming from exact search)
    if p.startswith('"') and p.endswith('"'):
        p = p[1:-1]

    ## okay, "real browse" follows:
    ## FIXME: the maths in the get_nearest_terms_in_bibxxx is just a test

    if not f and p.find(":") > 0: # does 'p' contain ':'?
        f, p = p.split(":", 1)

    coll_hitset = intbitset()
    for coll_name in colls:
        coll_hitset |= get_collection_reclist(coll_name)

    index_id = get_index_id_from_field(f)
    if index_id != 0:
        browsed_phrases_in_colls = get_nearest_terms_in_idxphrase_with_collection(p, index_id, rg/2, rg/2, coll_hitset)
    else:
        browsed_phrases = get_nearest_terms_in_bibxxx(p, f, (rg+1)/2+1, (rg-1)/2+1)
        while not browsed_phrases:
            # try again and again with shorter and shorter pattern:
            try:
                p = p[:-1]
                browsed_phrases = get_nearest_terms_in_bibxxx(p, f, (rg+1)/2+1, (rg-1)/2+1)
            except:
                register_exception(req=req, alert_admin=True)
                # probably there are no hits at all:
                return []

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
                #write_warning(req, """<p>No match close to <em>%s</em> found in given collections.
                #Please try different term.<p>Displaying matches in any collection...""" % p_orig)
                ## try to get nbhits for these phrases in any collection:
                for phrase in browsed_phrases:
                    nbhits = get_nbhits_in_bibxxx(phrase, f, coll_hitset)
                    if nbhits > 0:
                        browsed_phrases_in_colls.append([phrase, nbhits])

    return browsed_phrases_in_colls


def search_pattern(req=None, p=None, f=None, m=None, ap=0, of="id", verbose=0,
                   ln=CFG_SITE_LANG, display_nearest_terms_box=True, wl=0):
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
       'ap' is also internally used for allowing hidden tag search
       (for requests coming from webcoll, for example). In this
       case ap=-9

       The 'of' argument governs whether to print or not some
       information to the user in case of no match found.  (Usually it
       prints the information in case of HTML formats, otherwise it's
       silent).

       The 'verbose' argument controls the level of debugging information
       to be printed (0=least, 9=most).

       All the parameters are assumed to have been previously washed.

       This function is suitable as a mid-level API.
    """
    if f is None:
        from invenio.modules.search.api import Query
        results = Query(p).search()
    else:
        results = search_unit(p, f, m, wl=wl)
    import warnings
    warnings.warn(
        'Deprecated search_pattern(p={0}, f={1}, m={2}) = {3}.'.format(
            p, f, m, results),
        stacklevel=2
    )
    return results


from invenio.modules.search.searchext.engines.native import *


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
        recID = int(recID)
        # dirty hack for ATLAS collections at CERN:
        if out in ('ATLAS Communications', 'ATLAS Internal Notes'):
            for alternative_collection in ('ATLAS Communications Physics',
                                           'ATLAS Communications General',
                                           'ATLAS Internal Notes Physics',
                                           'ATLAS Internal Notes General',):
                if recID in get_collection_reclist(alternative_collection):
                    return alternative_collection

        # dirty hack for FP
        FP_collections = {'DO': ['Current Price Enquiries', 'Archived Price Enquiries'],
                          'IT': ['Current Invitation for Tenders', 'Archived Invitation for Tenders'],
                          'MS': ['Current Market Surveys', 'Archived Market Surveys']}
        fp_coll_ids = [coll for coll in dbcollids if coll in FP_collections]
        for coll in fp_coll_ids:
            for coll_name in FP_collections[coll]:
                if recID in get_collection_reclist(coll_name):
                    return coll_name

    return out


_re_collection_url = re.compile('/collection/(.+)')
def guess_collection_of_a_record(recID, referer=None, recreate_cache_if_needed=True):
    """Return collection name a record recid belongs to, by first testing
       the referer URL if provided and otherwise returning the
       primary collection."""
    if referer:
        dummy, hostname, path, dummy, query, dummy = urlparse.urlparse(referer)
        # requests can come from different invenio installations, with
        # different collections
        if CFG_SITE_URL.find(hostname) < 0:
            return guess_primary_collection_of_a_record(recID)
        g = _re_collection_url.match(path)
        if g:
            name = urllib.unquote_plus(g.group(1))
            # check if this collection actually exist (also normalize the name
            # if case-insensitive)
            name = Collection.query.filter_by(name=name).value('name')
            if name and recID in get_collection_reclist(name):
                return name
        elif path.startswith('/search'):
            if recreate_cache_if_needed:
                collection_reclist_cache.recreate_cache_if_needed()
            query = cgi.parse_qs(query)
            for name in query.get('cc', []) + query.get('c', []):
                name = Collection.query.filter_by(name=name).value('name')
                if name and recID in get_collection_reclist(name, recreate_cache_if_needed=False):
                    return name
    return guess_primary_collection_of_a_record(recID)


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


from invenio.modules.search.models import Field

get_field_name = Field.get_field_name


def get_merged_recid(recID):
    """ Return the record ID of the record with
    which the given record has been merged.
    @param recID: deleted record recID
    @type recID: int
    @return: merged record recID
    @rtype: int or None
    """
    merged_recid = None
    for val in get_fieldvalues(recID, "970__d"):
        try:
            merged_recid = int(val)
            break
        except ValueError:
            pass
    return merged_recid


def record_empty(recID):
    """
    Is this record empty, e.g. has only 001, waiting for integration?

    @param recID: the record identifier.
    @type recID: int
    @return: 1 if the record is empty, 0 otherwise.
    @rtype: int
    """
    return bibrecord.record_empty(get_record(recID))

def record_public_p(recID, recreate_cache_if_needed=True):
    """Return 1 if the record is public, i.e. if it can be found in the Home collection.
       Return 0 otherwise.
    """
    return recID in get_collection_reclist(CFG_SITE_NAME, recreate_cache_if_needed=recreate_cache_if_needed)


from invenio.modules.sorter.cache import SORTING_METHODS, CACHE_SORTED_DATA


def rank_records(rank_method_code, rank_limit_relevance, hitset_global,
                 pattern=None, verbose=0, sort_order='d', of='hb',
                 ln=CFG_SITE_LANG, rg=None, jrec=None, field='',
                 sorting_methods=SORTING_METHODS):
    """Initial entry point for ranking records, acts like a dispatcher.
       (i) rank_method_code is in bsrMETHOD, bibsort buckets can be used;
       (ii)rank_method_code is not in bsrMETHOD, use bibrank;
    """
    # Special case: sorting by citations is fast because we store the
    # ranking dictionary in memory, so we do not use bibsort buckets.
    if CFG_BIBSORT_ENABLED and sorting_methods and rank_method_code != 'citation':
        for sort_method in sorting_methods:
            definition = sorting_methods[sort_method]
            if definition.startswith('RNK') and \
                   definition.replace('RNK:', '').strip().lower() == rank_method_code.lower():
                solution_recs, solution_scores = \
                        sort_records_bibsort(req, hitset_global, sort_method,
                                             '', sort_order, verbose, of, ln,
                                             rg, jrec, 'r')
                comment = ''
                if verbose > 0:
                    comment = 'find_citations retlist %s' % [[solution_recs[i], solution_scores[i]] for i in range(len(solution_recs))]
                return solution_recs, solution_scores, '(', ')', comment

    if rank_method_code.lower() == 'citation':
        related_to = []
    else:
        related_to = pattern

    solution_recs, solution_scores, prefix, suffix, comment = \
        rank_records_bibrank(rank_method_code=rank_method_code,
                             rank_limit_relevance=rank_limit_relevance,
                             hitset=hitset_global,
                             verbose=verbose,
                             field=field,
                             related_to=related_to,
                             rg=rg,
                             jrec=jrec)

    # Solution recs can be None, in case of error or other cases
    # which should be all be changed to return an empty list.
    if solution_recs and sort_order == 'd':
        solution_recs.reverse()
        solution_scores.reverse()

    return solution_recs, solution_scores, prefix, suffix, comment


def sort_or_rank_records(req, recIDs, rm, sf, so, sp, p, verbose=0, of='hb',
                         ln=CFG_SITE_LANG, rg=None, jrec=None, field='',
                         sorting_methods=SORTING_METHODS):
    """Sort or rank records.

    Entry point for deciding to either sort or rank records.
    """
    if rm:
        ranking_result = rank_records(rm, 0, recIDs, p, verbose, so,
                                      of, ln, rg, jrec, field,
                                      sorting_methods)
        if ranking_result[0]:
            return ranking_result[0]  # ranked recids
    elif sf or (CFG_BIBSORT_ENABLED and SORTING_METHODS):
        from invenio.modules.sorter.engine import sort_records
        return sort_records(recIDs, sf, so, sp, rg, jrec)
    return recIDs.tolist()


def slice_records(recIDs, jrec, rg):
    if not jrec:
        jrec = 1
    if rg:
        recIDs = recIDs[jrec-1:jrec-1+rg]
    else:
        recIDs = recIDs[jrec-1:]
    return recIDs


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


def get_record(recid):
    """Directly the record object corresponding to the recid."""
    import warnings
    warnings.warn('Deprecated get_record({}).'.format(str(recid)),
                  stacklevel=2)
    from invenio.modules.records import api
    try:
        return api.get_record(recid).legacy_create_recstruct()
    except AttributeError:
        return api.Record.create({'recid': recid}, 'json').legacy_create_recstruct()

def print_record(recID, format='hb', ot='', ln=CFG_SITE_LANG, decompress=zlib.decompress,
                 search_pattern=None, user_info=None, verbose=0, sf='', so='d',
                 sp='', rm='', brief_links=True):
    """
    Print record 'recID' formatted according to 'format'.

    'sf' is sort field and 'rm' is ranking method that are passed here
    only for proper linking purposes: e.g. when a certain ranking
    method or a certain sort field was selected, keep it selected in
    any dynamic search links that may be printed.
    """
    from invenio.modules.formatter import format_record
    return format_record(
        recID, of=format, ln=ln, verbose=verbose,
        search_pattern=search_pattern
    ) if record_exists(recID) != 0 else ""


def create_add_to_search_pattern(p, p1, f1, m1, op1):
    """Create the search pattern """
    if not p1:
        return p
    init_search_pattern = p
    # operation: AND, OR, AND NOT
    if op1 == 'a' and p: # we don't want '+' at the begining of the query
        op =  ' +'
    elif op1 == 'o':
        op = ' |'
    elif op1 == 'n':
        op = ' -'
    else:
        op = ' ' if p else ''

    # field
    field = ''
    if f1:
        field = f1 + ':'

    # type of search
    pattern = p1
    start = '('
    end = ')'
    if m1 == 'e':
        start = end = '"'
    elif m1 == 'p':
        start = end = "'"
    elif m1 == 'r':
        start = end = '/'
    else: # m1 == 'o' or m1 =='a'
        words = p1.strip().split(' ')
        if len(words) == 1:
            start = end = ''
            pattern = field + words[0]
        elif m1 == 'o':
            pattern = ' |'.join([field + word for word in words])
        else:
            pattern = ' '.join([field + word for word in words])
        #avoid having field:(word1 word2) since this is not currently correctly working
        return init_search_pattern + op + start + pattern + end
    if not pattern:
        return ''
    #avoid having field:(word1 word2) since this is not currently correctly working
    return init_search_pattern + op + field + start + pattern + end


### CALLABLES

def perform_request_search(req=None, cc=CFG_SITE_NAME, c=None, p="", f="", rg=None, sf="", so="a", sp="", rm="", of="id", ot="", aas=0,
                        p1="", f1="", m1="", op1="", p2="", f2="", m2="", op2="", p3="", f3="", m3="", sc=0, jrec=0,
                        recid=-1, recidb=-1, sysno="", id=-1, idb=-1, sysnb="", action="", d1="",
                        d1y=0, d1m=0, d1d=0, d2="", d2y=0, d2m=0, d2d=0, dt="", verbose=0, ap=0, ln=CFG_SITE_LANG, ec=None, tab="",
                        wl=0, em=""):
    kwargs = prs_wash_arguments(req=req, cc=cc, c=c, p=p, f=f, rg=rg, sf=sf, so=so, sp=sp, rm=rm, of=of, ot=ot, aas=aas,
                                p1=p1, f1=f1, m1=m1, op1=op1, p2=p2, f2=f2, m2=m2, op2=op2, p3=p3, f3=f3, m3=m3, sc=sc, jrec=jrec,
                                recid=recid, recidb=recidb, sysno=sysno, id=id, idb=idb, sysnb=sysnb, action=action, d1=d1,
                                d1y=d1y, d1m=d1m, d1d=d1d, d2=d2, d2y=d2y, d2m=d2m, d2d=d2d, dt=dt, verbose=verbose, ap=ap, ln=ln, ec=ec,
                                tab=tab, wl=wl, em=em)

    import warnings
    warnings.warn('Deprecated perform_request_search({}).'.format(str(kwargs)),
                  stacklevel=2)
    from invenio.modules.search.api import Query
    p = create_add_to_search_pattern(p, p1, f1, m1, "")
    p = create_add_to_search_pattern(p, p2, f2, m2, op1)
    p = create_add_to_search_pattern(p, p3, f3, m3, op2)
    return Query(p).search(collection=cc)


def prs_wash_arguments(req=None, cc=CFG_SITE_NAME, c=None, p="", f="", rg=CFG_WEBSEARCH_DEF_RECORDS_IN_GROUPS,
                      sf="", so="d", sp="", rm="", of="id", ot="", aas=0,
                      p1="", f1="", m1="", op1="", p2="", f2="", m2="", op2="", p3="", f3="", m3="",
                      sc=0, jrec=0, recid=-1, recidb=-1, sysno="", id=-1, idb=-1, sysnb="", action="", d1="",
                      d1y=0, d1m=0, d1d=0, d2="", d2y=0, d2m=0, d2d=0, dt="", verbose=0, ap=0, ln=CFG_SITE_LANG,
                      ec=None, tab="", uid=None, wl=0, em="", **dummy):
    """
    Sets the (default) values and checks others for the PRS call
    """

    # wash output format:
    of = wash_output_format(of)

    # wash all arguments requiring special care
    p = wash_pattern(p)
    f = wash_field(f)
    p1 = wash_pattern(p1)
    f1 = wash_field(f1)
    p2 = wash_pattern(p2)
    f2 = wash_field(f2)
    p3 = wash_pattern(p3)
    f3 = wash_field(f3)
    (d1y, d1m, d1d, d2y, d2m, d2d) = map(int, (d1y, d1m, d1d, d2y, d2m, d2d))
    datetext1, datetext2 = wash_dates(d1, d1y, d1m, d1d, d2, d2y, d2m, d2d)

    # wash ranking method:
    if not is_method_valid(None, rm):
        rm = ""

    if id > 0 and recid == -1:
        recid = id
    if idb > 0 and recidb == -1:
        recidb = idb
    # deduce collection we are in (if applicable):
    if recid > 0:
        referer = None
        if req:
            referer = req.headers_in.get('Referer')
        cc = guess_collection_of_a_record(recid, referer)
    # deduce user id (if applicable):
    if uid is None:
        try:
            uid = getUid(req)
        except:
            uid = 0

    _ = gettext_set_language(ln)

    kwargs = {'req': req, 'cc': cc, 'c': c, 'p': p, 'f': f, 'rg': rg, 'sf': sf,
              'so': so, 'sp': sp, 'rm': rm, 'of': of, 'ot': ot, 'aas': aas,
              'p1': p1, 'f1': f1, 'm1': m1, 'op1': op1, 'p2': p2, 'f2': f2,
              'm2': m2, 'op2': op2, 'p3': p3, 'f3': f3, 'm3': m3, 'sc': sc,
              'jrec': jrec, 'recid': recid, 'recidb': recidb, 'sysno': sysno,
              'id': id, 'idb': idb, 'sysnb': sysnb, 'action': action, 'd1': d1,
              'd1y': d1y, 'd1m': d1m, 'd1d': d1d, 'd2': d2, 'd2y': d2y,
              'd2m': d2m, 'd2d': d2d, 'dt': dt, 'verbose': verbose, 'ap': ap,
              'ln': ln, 'ec': ec, 'tab': tab, 'wl': wl, 'em': em,
              'datetext1': datetext1, 'datetext2': datetext2, 'uid': uid,
              '_': _,
              'selected_external_collections_infos': None,
              }

    kwargs.update(**dummy)
    return kwargs
