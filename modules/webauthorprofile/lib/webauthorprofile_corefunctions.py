# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011, 2012 CERN.
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
WebAuthorProfile web interface logic and URL handler
"""

# pylint: disable=W0105
# pylint: disable=C0301
# pylint: disable=W0613

from time import time, sleep
from datetime import timedelta, datetime
from re import split as re_split
from re import compile as re_compile
from urllib import urlopen
from collections import deque
# NB: For future reference, elementtree.ElementTree is depreciated after
# Python 2.4, Inspire instances on higher Python versions should use xml.etree
# instead. The root.getiterator() function should also be updated.
try:
    import elementtree.ElementTree as ET
except ImportError:
    from xml.etree import ElementTree as ET

from invenio.webauthorprofile_config import serialize, deserialize
from invenio.webauthorprofile_config import CFG_BIBRANK_SHOW_DOWNLOAD_STATS, \
    CFG_WEBAUTHORPROFILE_CACHE_EXPIRED_DELAY_LIVE, \
    CFG_WEBAUTHORPROFILE_USE_BIBAUTHORID, CFG_WEBAUTHORPROFILE_USE_ALLOWED_FIELDCODES, \
    CFG_WEBAUTHORPROFILE_ALLOWED_FIELDCODES, CFG_WEBAUTHORPROFILE_KEYWORD_TAG, \
    CFG_WEBAUTHORPROFILE_FKEYWORD_TAG, CFG_WEBAUTHORPROFILE_COLLABORATION_TAG, \
    CFG_WEBAUTHORPROFILE_FIELDCODE_TAG
from invenio.bibauthorid_webauthorprofileinterface import get_papers_by_person_id, \
    get_names_of_author, create_normalized_name, \
    get_person_redirect_link, is_valid_canonical_id, split_name_parts, \
    gathered_names_by_personid, get_canonical_name_of_author, get_coauthors_of_author, \
    get_names_count_of_author, get_existing_authors, get_confirmed_papers_of_author, \
    get_title_of_paper, get_orcid_id_of_author, get_arxiv_papers_of_author, \
    get_hepnames, remove_empty_authors
from invenio.bibauthorid_general_utils import get_title_of_doi, get_title_of_arxiv_pubid
from invenio.webauthorprofile_dbapi import get_cached_element, precache_element, cache_element, \
    expire_all_cache_for_person, get_expired_person_ids, get_cache_oldest_date
from invenio.search_engine_summarizer import summarize_records
from invenio.search_engine import get_most_popular_field_values
from invenio.search_engine import perform_request_search
from invenio.search_engine_summarizer import generate_citation_summary
from invenio.bibrank_downloads_indexer import get_download_weight_total
from invenio.intbitset import intbitset
from invenio.bibformat import format_record, format_records
from invenio.crossrefutils import get_marcxml_for_doi, CrossrefError
from invenio.webauthorprofile_orcidutils import get_dois_from_orcid


# After this delay, we assume that a process computing an empty claimed cache is dead
# and we spawn a new one to finish the job
RECOMPUTE_PRECACHED_ELEMENT_DELAY = timedelta(minutes=30)

# After this timeout we silently recompute the cache in the background,
# so that next refresh will be up-to-date
CACHE_IS_OUTDATED_DELAY = timedelta(days=CFG_WEBAUTHORPROFILE_CACHE_EXPIRED_DELAY_LIVE)
FORCE_CACHE_IS_EXPIRED = False


IS_BATCH_PROCESS = False
CONNECTION_WAITTIME = 2

def set_force_expired_cache(val=True):
    global FORCE_CACHE_IS_EXPIRED
    FORCE_CACHE_IS_EXPIRED = val


year_pattern = re_compile(r'(\d{4})')


def update_cache(cached, name, key, target, *args):
    '''
    Actual update of cached value of (name, key). Updates to the result of target(args).
    If value present in cache, not up to date but last_updated less than a threshold it does nothing,
    as someone surely precached it and is computing the results already. If not present in cache it
    precaches it, computes its value and stores it in cache returning its value.
    '''
    #print '--Updating cache: ', name,' ',key
    if cached['present']:
        delay = datetime.now() - cached['last_updated']
        if delay < RECOMPUTE_PRECACHED_ELEMENT_DELAY and cached['precached']:
            #print '--!!!Udating cache skip precached!'
            return [False, None]
    precache_element(name, key)
    el = target(*args)
    cache_element(name, key, serialize(el))
    #print '--Updating cache: ', name,' ',key, ' returning! ', str(el)[0:10]
    return [True, el]

def retrieve_update_cache(name, key, target, *args):
    '''
    Retrieves the result of target(args)(= value) from (name, key) cached element.
    If element present and UpToDate it returns [value, True]. If element present and Precached it returns [None, False]
    because it is currently computed. If element is not present it computes its value, updates the cache and returns [value, True].
    '''
    #print '--Getting ', name, ' ', key
    cached = get_cached_element(name, str(key))
    if cached['present']:
        if cached['upToDate'] and not FORCE_CACHE_IS_EXPIRED:
            delay = datetime.now() - cached['last_updated']
            if delay < CACHE_IS_OUTDATED_DELAY:
                return [deserialize(cached['value']), True]
    val = update_cache(cached, name, str(key), target, *args)
    if val[0]:
        return [val[1], True]
    else:
        return [None, False]

def foo(x, y, z, t):
    ''' foo to test the caching mechanism. '''
    return retrieve_update_cache('foo', x, _foo, x, y, z, t)

def _foo(x, y, z, t):
    ''' foo function to test the caching mechanism. '''
    sleep(t)
    return [x, y, z]

def get_person_oldest_date(person_id):
    ''' Returns oldest date of cached data for person ID, None if not available. '''
    cache_oldest_date = get_cache_oldest_date('pid:' + str(person_id))

    if cache_oldest_date:
        return cache_oldest_date
    return datetime.now().replace(microsecond=0)

def expire_caches_for_person(person_id):
    ''' Expires all caches for personid. '''
    expire_all_cache_for_person(person_id)

def get_pubs(person_id):
    '''
    Returns a list of person's publications.
    @param person_id: int person id
    @return [[rec1,rec2,...], bool]
    '''
    return retrieve_update_cache('pubs_list', 'pid:' + str(person_id), _get_pubs, person_id)

def get_self_pubs(person_id):
    '''
    Returns a list of person's publications.
    @param person_id: int person id
    @return [[rec1,rec2,...], bool]
    '''
    return retrieve_update_cache('self_pubs_list', 'pid:' + str(person_id), _get_self_pubs, person_id)

def get_institute_pubs(person_id):
    '''
    Returns a dict consisting of: institute -> list of publications (given a personID).
    @param person_id: int person id
    @return [{'intitute':[pubs,...]}, bool]
    '''
    namesdict, status = get_person_names_dicts(person_id)
    if not status:
        return [None, False]
    names_list = namesdict['db_names_dict'].keys()
    return retrieve_update_cache('institute_pub_dict', 'pid:' + str(person_id), _get_institute_pubs,
                                 names_list, person_id)

def get_pubs_per_year(person_id):
    '''
    Returns a dict consisting of: year -> number of publications in that year (given a personID).
    @param person_id: int person id
    @return [{'year':no_of_publications}, bool]
    '''
    return retrieve_update_cache('pubs_per_year', 'pid:' + str(person_id), _get_pubs_per_year, person_id)

def get_person_names_dicts(person_id):
    '''
    Returns a dict with longest name, normalized names variations and db names variations.
    @param person_id: int personid
    @return [{'db_names_dict': {'name1':count,...}
              'longest':'longest name'}
              'names_dict': {'name1':count,...},
              bool]
    '''
    return retrieve_update_cache('person_names_dicts', 'pid:' + str(person_id), _get_person_names_dicts, person_id)

def get_total_downloads(person_id):
    '''
    Returns the total downloads of the set of given papers.
    @param person_id: int person id
    @return: [int total downloads, bool up_to_date]
    '''
    pubs = get_pubs(person_id)[0]
    return retrieve_update_cache('total_downloads', 'pid:' + str(person_id),
                          _get_total_downloads, pubs)

def get_veryfy_my_pubs_list_link(person_id):
    '''
    Returns a link for the authorpage of this person_id; if there is a canonical name it will be
    that, otherwise just the presonid.
    @param personid: int person id
    '''
    return retrieve_update_cache('verify_my_pu_list_link', 'pid:' + str(person_id),
                          _get_veryfy_my_pubs_list_link, person_id)

def get_kwtuples(person_id):
    '''
    Returns the keyword tuples for given personid.
    @param person_id: int person id
    @return [ (('kword',count),),
            bool]
    '''
    pubs, pubstatus = get_pubs(person_id)
    if not pubstatus:
        return [None, False]
    return retrieve_update_cache('kwtuples', 'pid:' + str(person_id),
                           _get_kwtuples, pubs, person_id)

def get_fieldtuples(person_id):
    '''
    Returns the fieldcode tuples for given personid.
    @param person_id: int person id
    @return [ (('fieldcode',count),),
            bool]
    '''
    pubs, pubstatus = get_pubs(person_id)
    if not pubstatus:
        return [None, False]
    return retrieve_update_cache('fieldtuples', 'pid:' + str(person_id),
                           _get_fieldtuples, pubs, person_id)

def get_collabtuples(person_id):
    '''
    Returns the keyword tuples for given personid.
    @param person_id: int person id
    @return [ (('kword',count),),
            bool]
    '''
    pubs, pubstatus = get_pubs(person_id)
    if not pubstatus:
        return [None, False]
    return retrieve_update_cache('collabtuples', 'pid:' + str(person_id),
                           _get_collabtuples, pubs, person_id)

def get_coauthors(person_id):
    '''
    Returns a list of coauthors.
    @param person_id: int person id
    @returns: [{'author name': coauthored}, bool]
    '''
    collabs = get_collabtuples(person_id)[0]
    return retrieve_update_cache('coauthors', 'pid:' + str(person_id), _get_coauthors, collabs, person_id)

def get_rec_query(person_id):
    '''
    Returns query to find author's papers in search engine.
    @param: person_id: int person id
    @return: ['author:"canonical name or pid"', bool]
    '''
    namesdict, ndstatus = get_person_names_dicts(person_id)
    if not ndstatus:
        return [None, False]
    authorname = namesdict['longest']
    db_names_dict = namesdict['db_names_dict']
    person_link, plstatus = get_veryfy_my_pubs_list_link(person_id)
    if not plstatus:
        return [None, False]
    bibauthorid_data = {"is_baid": True, "pid":person_id, "cid":person_link}
    return retrieve_update_cache('rec_query', 'pid:' + str(person_id),
                          _get_rec_query, bibauthorid_data, authorname, db_names_dict, person_id)

def get_hepnames_data(person_id):
    '''
    Returns hepnames data.
    @param bibauthorid_data: dict with 'is_baid':bool, 'cid':canonicalID, 'pid':personid
    @return: [data, bool]
    '''
    person_link, plstatus = get_veryfy_my_pubs_list_link(person_id)
    if not plstatus:
        return [None, False]
    bibauthorid_data = {"is_baid": True, "pid":person_id, "cid":person_link}
    return retrieve_update_cache('hepnames_data', 'pid:' + str(bibauthorid_data['pid']),
                          _get_hepnames_data, bibauthorid_data, person_id)

def _get_hepnames_data(bibauthorid_data, person_id):
    return get_hepnames(person_id, bibauthorid_data)

def get_summarize_records(person_id):
    '''
    Returns html for records summary given personid, tag and ln.
    @param person_id: int person id
    @param tag: str kind of output
    @param ln: str language
    @return: [htmlsnippet, bool]
    '''
    pubs, pubstatus = get_pubs(person_id)
    if not pubstatus:
        return [None, False]
    rec_query, rcstatus = get_rec_query(person_id)
    if not rcstatus:
        return [None, False]
    return retrieve_update_cache('summarize_records', 'pid:' + str(person_id),
                          _get_summarize_records, pubs, rec_query)

def _get_summarize_records(pubs, rec_query):
    '''
    Returns  html for records summary given personid, tag and ln.
    @param person_id: int person id
    @param tag: str kind of output
    @param ln: str language
    '''
    citation_summary = generate_citation_summary(intbitset(pubs))

    # the serialization function (msgpack.packb) cannot serialize an intbitset
    for i in citation_summary[0].keys():
        citation_summary[0][i] = list(citation_summary[0][i])

    return (citation_summary, rec_query)

def get_internal_publications(person_id):
    '''
    Returns internal pubs for given personid.
    @param person_id: int, person id
    @return
    '''
    return retrieve_update_cache('internal_pubs', 'pid:' + str(person_id), _get_internal_publications, person_id)

def _get_internal_publications(person_id):
    '''
    Returns internal pubs for given personid.
    @param person_id: int, person id
    @return
    '''
    internal_pubs = dict()

    recs = get_confirmed_papers_of_author(person_id)
    for rec in recs:
        internal_pubs[rec] = get_title_of_paper(rec)

    return internal_pubs

def get_datasets(person_id):
    '''
    Returns a list of hepdata recordids given a personid.
    @param person_id: int, person id
    @return
    '''
    return retrieve_update_cache('datasets_pubs', 'pid:' + str(person_id), _get_datasets, person_id)

def _get_datasets(person_id):
    recs =  get_confirmed_papers_of_author(person_id)
    data_recs = set()

    for rec in recs:
        data_recs_tmp = perform_request_search(p="%s" % str(rec), f='786', m1='w', cc='Data', rg=0)
        data_recs.update(set(data_recs_tmp))

    datasets_pubs = dict()
    for rec in data_recs:
        datasets_pubs[rec] = get_title_of_paper(rec)

    return datasets_pubs

def get_external_publications(person_id):
    '''
    Returns external pubs for given personid.
    @param person_id: int, person id
    @return
    '''
    return retrieve_update_cache('external_pubs', 'pid:' + str(person_id), _get_external_publications, person_id)

def _get_external_publications(person_id):
    '''
    Returns external pubs for given personid.
    @param person_id: int, person id
    @return
    '''
    def get_arxiv_pubs(person_id):
        arxiv_pub_ids = get_arxiv_papers_of_author(person_id)

        if arxiv_pub_ids is None:
            return dict()

        arxiv_pubs = dict()
        for arxiv_pubid in arxiv_pub_ids:
            recids = perform_request_search(p=arxiv_pubid, f='037', m1='e', cc='HEP', rg=0)
            if not recids:
                arxiv_pubs[arxiv_pubid] = get_title_of_arxiv_pubid(arxiv_pubid)

            if IS_BATCH_PROCESS:
                time.sleep(CONNECTION_WAITTIME)

        return arxiv_pubs

    def get_orcid_pubs(person_id):
        try:
            orcid_id = get_orcid_id_of_author(person_id)[0][0]
        except IndexError:
            # TODO: what should I return in this case
            return dict()

        orcid_dois = get_dois_from_orcid(orcid_id)
        # TODO: what to do in case some ORCID server error occurs?
        if orcid_dois is None:
            return dict()

        orcid_pubs = dict()
        for doi in orcid_dois:
            recids = perform_request_search(p=doi, f='doi', m1='e', cc='HEP', rg=0)
            if not recids:
                orcid_pubs[doi] = get_title_of_doi(doi)

            if IS_BATCH_PROCESS:
                time.sleep(CONNECTION_WAITTIME)

        return orcid_pubs

    external_pubs = dict()
    external_pubs['arxiv'] = get_arxiv_pubs(person_id)
    external_pubs['doi'] = get_orcid_pubs(person_id)

    # TODO: (ORCID pubs | ARXIV pubs) - (ORCID pubs & ARXIV pubs)

    return external_pubs

def _compute_cache_for_person(person_id):
    start = time()
    if not FORCE_CACHE_IS_EXPIRED:
        expire_all_cache_for_person(person_id)
    f_to_call = [
               (get_pubs,),
               (get_person_names_dicts,),
               (get_veryfy_my_pubs_list_link,),
               (get_rec_query,),
               (get_collabtuples,),
               (get_coauthors,),
               (get_institute_pubs,),
               (get_pubs_per_year,),
               (get_total_downloads,),
               (get_kwtuples,),
               (get_fieldtuples,),
               (get_hepnames_data,),
               (get_summarize_records,),
               (get_self_pubs,),
               (get_internal_publications,),
               (get_external_publications,),
               (get_datasets,)
                ]

    waited = 0
    for f in f_to_call:
        r = [None, False]
        failures_delay = 0.01
        while not r[1]:
            if len(f) < 2:
                r = f[0](person_id)
            else:
                r = f[0](person_id, *f[1])
            #print str(f), r[1]
            if not r[1]:
                sleep(failures_delay)
                failures_delay *= 1.05
                waited += 1
                #print 'Waiting for ', str(f)
    #print 'Waited ', waited, ' ', failures_delay

    print person_id, ',' , str(time() - start)

def precompute_cache_for_person(person_ids=None, all_persons=False, only_expired=False):
    pids = set()
    if all_persons:
        pids = get_existing_authors(with_papers_only=True)
    elif only_expired:
        pids = set(get_expired_person_ids())
    if person_ids:
        pids |= person_ids

    empty_pids = remove_empty_authors(remove=False)
    pids = pids - empty_pids

    last = len(pids)

    global IS_BATCH_PROCESS
    IS_BATCH_PROCESS = True
    for i, p in enumerate(pids):
#        start = time()
        print 'Doing ', i,' of ', last
        #print 'STARTED: ', p, ' ', i
        _compute_cache_for_person(p)
        #print 'DONE: ', p , ',' , str(time() - start)
    IS_BATCH_PROCESS = False

def multiprocessing_precompute_cache_for_person(person_ids=None, all_persons=False, only_expired=False):
    pids = set()
    if all_persons:
        pids = get_existing_authors(with_papers_only=True)
    elif only_expired:
        pids = set(get_expired_person_ids())
    if person_ids:
        pids |= person_ids

    from multiprocessing import Pool
    p = Pool()
    p.map(_compute_cache_for_person, pids)


def _get_pubs_bai(person_id):
    '''
    Person's publication list.
    @param person_id: int person id
    '''
    full_pubs = get_papers_by_person_id(person_id, -1)
    pubs = [int(row[0]) for row in full_pubs]
    return pubs

def _get_self_pubs_bai(person_id):
    '''
    Person's publication list.
    @param person_id: int person id
    '''
    cid = canonical_name(person_id)
    return perform_request_search(rg=0, p='author:%s and authorcount:1' % cid)

def canonical_name(pid):
    try:
        return get_canonical_name_of_author(pid)[0][0]
    except IndexError:
        return str(pid)

def _get_institute_pubs_bai(names_list, person_id):
    ''' Returns a dict consisting of: institute -> list of publications. '''
    cid = canonical_name(person_id)
    recids = perform_request_search(rg=0, p='author:%s' % str(cid))
    return _get_institute_pubs_dict(recids, names_list)

def _get_institute_pubs_dict(recids, names_list):
    a = format_records(recids, 'WAPAFF')
    a = [deserialize(p) for p in a.strip().split('!---THEDELIMITER---!') if p]
    affdict = {}
    for rec, affs in a:
        keys = affs.keys()
        for name in names_list:
            if name in keys and affs[name]:
                for aff in affs[name]:
                    try:
                        affdict[aff].add(rec)
                    except KeyError:
                        affdict[aff] = set([rec])
    # the serialization function (msgpack.packb) cannot serialize a python set
    for key in affdict.keys():
        affdict[key] = list(affdict[key])
    return affdict

def _get_pubs_per_year_bai(person_id):
    '''
    Returns a dict consisting of: year -> number of publications in that year (given a personID).
    @param person_id: int personid
    @return [{'year':no_of_publications}, bool]
    '''
    cid = canonical_name(person_id)
    recids = perform_request_search(rg=0, p='author:%s' % str(cid))
    a = format_records(recids, 'WAPDAT')
    a = [deserialize(p) for p in a.strip().split('!---THEDELIMITER---!') if p]
    return _get_pubs_per_year_dictionary(a)

def _get_pubs_per_year_dictionary(pubyearslist):
    '''
    Returns a dict consisting of: year -> number of publications in that year (given a personID).
    @param person_id: int personid
    @return [{'year':no_of_publications}, bool]
    '''
    yearsdict = {}
    for _, years in pubyearslist:
        year_list = []
        for date in years['year_fields']:
            try:
                year_list.append(int(re_split(year_pattern, date[0])[1]))
            except IndexError:
                continue

        if year_list:
            min_year = min(year_list)
            try:
                yearsdict[min_year] += 1
            except KeyError:
                yearsdict[min_year] = 1

    return yearsdict

def _get_person_names_dicts_bai(person_id):
    '''
    Returns a dict with longest name, normalized names variations and db names variations.
    @param person_id: int personid
    @return [dict{},bool up_to_date]
    '''
    longest_name = ""
    names_dict = {}
    db_names_dict = {}

    for aname, acount in get_names_count_of_author(person_id):
        names_dict[aname] = acount
        norm_name = create_normalized_name(split_name_parts(aname))

        if len(norm_name) > len(longest_name):
            longest_name = norm_name

    for aname, acount in get_names_of_author(person_id):
        try:
            db_names_dict[aname] += acount
        except KeyError:
            db_names_dict[aname] = acount

    return {'longest': longest_name, 'names_dict': names_dict,
            'db_names_dict': db_names_dict}


def _get_total_downloads_bai(pubs):
    '''
    Returns the total downloads of the set of given papers
    @param pubs: list of recids
    @return: [int total downloads, bool up_to_date]
    '''
    return _get_total_downloads_num(pubs)

def _get_total_downloads_num(pubs):
    totaldownloads = 0
    if CFG_BIBRANK_SHOW_DOWNLOAD_STATS:
        recsloads = {}
        recsloads = get_download_weight_total(recsloads, pubs)
        for k in recsloads.keys():
            totaldownloads = totaldownloads + recsloads[k]
    return totaldownloads


def _get_veryfy_my_pubs_list_link_bai(person_id):
    ''' Returns canonical name links. '''
    person_link = person_id
    cid = get_person_redirect_link(person_id)

    if is_valid_canonical_id(cid):
        person_link = cid
    return person_link


def _get_kwtuples_bai(pubs, person_id):
    '''
    Returns the list of keyword tuples for given personid.
    @param person_id: int person id
    '''
    tup = get_most_popular_field_values(pubs,
                            (CFG_WEBAUTHORPROFILE_KEYWORD_TAG), count_repetitive_values=True)
    return tup

def _get_fieldtuples_bai(pubs, person_id):
    return _get_fieldtuples_bai_tup(pubs, person_id)

def _get_fieldtuples_bai_tup(pubs, person_id):
    '''
    Returns the fieldcode tuples for given personid.
    @param person_id: int person id
    '''
    tup = get_most_popular_field_values(pubs,
                            CFG_WEBAUTHORPROFILE_FIELDCODE_TAG, count_repetitive_values=True)
    if CFG_WEBAUTHORPROFILE_USE_ALLOWED_FIELDCODES and CFG_WEBAUTHORPROFILE_ALLOWED_FIELDCODES:
        return tuple([x for x in tup if x[0] in CFG_WEBAUTHORPROFILE_ALLOWED_FIELDCODES])
    return tup


def _get_collabtuples_bai(pubs, person_id):
    '''
    Returns the list keyword tuples for given personid.
    @param person_id: int person id
    '''
    tup = get_most_popular_field_values(pubs,
                            CFG_WEBAUTHORPROFILE_COLLABORATION_TAG, count_repetitive_values=True)
    return tup

# python 2.4 does not supprt max() with key argument.
# Please remove this function when python 2.6 is supported.
def max_key(iterable, key):
    try:
        ret = iterable[0]
    except IndexError:
        return None
    for i in iterable[1:]:
        if key(i) > key(ret):
            ret = i
    return ret

def _get_coauthors_bai(collabs, person_id):
    cid = canonical_name(person_id)

    exclude_recs = None
    if collabs:
        query = 'author:%s and (%s)' % (cid, ' or '.join([('collaboration:"%s"' % x) for x in zip(*collabs)[0]]))
        exclude_recs = perform_request_search(rg=0, p=query)

    personids = get_coauthors_of_author(person_id, exclude_recs)

    coauthors = []
    for p in personids:
        cn = canonical_name(p[0])
        #ln is used only for exact search in case canonical name is not available. Never happens
        # with bibauthorid, let's print there the canonical name.
        #ln = max_key(gathered_names_by_personid(p[0]), key=len)
        ln = str(cn)
        # exact number of papers based on query. Not activated for performance reasons.
        # paps = len(perform_request_search(rg=0, p="author:%s author:%s" % (cid, cn)))
        paps = p[1]
        if paps:
            coauthors.append((cn, ln, paps))
    return coauthors

def  _get_rec_query_bai(bibauthorid_data, authorname, db_names_dict, person_id):
    ''' Returns query to find author's papers in search engine. '''
    rec_query = ""
    extended_author_search_str = ""

    is_bibauthorid = True

    if bibauthorid_data['is_baid']:
        if bibauthorid_data["cid"]:
            rec_query = 'author:"%s"' % bibauthorid_data["cid"]
        elif bibauthorid_data["pid"] > -1:
            rec_query = 'author:"%s"' % bibauthorid_data["pid"]

    if not rec_query:
        rec_query = 'exactauthor:"' + authorname + '"'

        if is_bibauthorid:
            if len(db_names_dict.keys()) > 1:
                extended_author_search_str = '('

            for name_index, name_query in enumerate(db_names_dict.keys()):
                if name_index > 0:
                    extended_author_search_str += " OR "

                extended_author_search_str += 'exactauthor:"' + name_query + '"'

            if len(db_names_dict.keys()) > 1:
                extended_author_search_str += ')'

        if is_bibauthorid and extended_author_search_str:
            rec_query = extended_author_search_str
    return rec_query

def _get_pubs_fallback(person_id):
    '''
    Returns person's publication list.
    @param person_id: int person id
    '''
    pubs = perform_request_search(rg=0, p='exactauthor:"%s"' % str(person_id))
    return pubs

def _get_self_pubs_fallback(person_id):
    '''
    Returns person's publication list.
    @param person_id: int person id
    '''
    return perform_request_search(rg=0, p='exactauthor:"%s" and authorcount:1' % str(person_id))

def _get_institute_pubs_fallback(names_list, person_id):
    ''' Returns a dict consisting of: institute -> list of publications. '''
    recids = perform_request_search(rg=0, p='exactauthor:"%s"' % str(person_id))
    return _get_institute_pubs_dict(recids, names_list)

def _get_pubs_per_year_fallback(person_id):
    '''
    Returns a dict consisting of: year -> number of publications in that year (given a personID).
    @param person_id: int personid
    @return [{'year':no_of_publications}, bool]
    '''
    recids = perform_request_search(rg=0, p='exactauthor:"%s"' % str(person_id))
    a = format_records(recids, 'WAPDAT')
    a = [deserialize(p) for p in a.strip().split('!---THEDELIMITER---!') if p]
    return _get_pubs_per_year_dictionary(a)

def _get_person_names_dicts_fallback(person_id):
    '''
    Returns a dict with longest name, normalized names variations and db names variations.
    @param person_id: int personid
    @return [dict{},bool up_to_date]
    '''
    p = perform_request_search(rg=0, p='exactauthor:"%s"' % person_id)
    pcount = len(p)
    if p:
        formatted = format_record(p[0], 'XM')
        try:
            s = formatted.lower().index(person_id.lower())
            person_id = formatted[s:s + len(person_id)]
        except (IndexError, ValueError):
            pass
    return {'longest':person_id, 'names_dict':{person_id:pcount}, 'db_names_dict':{person_id:pcount}}

def _get_total_downloads_fallback(pubs):
    '''
    Returns the total downloads of the set of given papers.
    @param pubs: list of recids
    @return: [int total downloads, bool up_to_date]
    '''
    return _get_total_downloads_num(pubs)

def _get_veryfy_my_pubs_list_link_fallback(person_id):
    ''' Returns canonical name links. '''
    return ''


def _get_kwtuples_fallback(pubs, person_id):
    '''
    Returns the list of keyword tuples for given personid.
    @param person_id: int person id
    '''

    tup = get_most_popular_field_values(pubs,
                            (CFG_WEBAUTHORPROFILE_KEYWORD_TAG, CFG_WEBAUTHORPROFILE_FKEYWORD_TAG), count_repetitive_values=True)
    return tup

def _get_fieldtuples_fallback(pubs, person_id):
    return _get_fieldtuples_bai_tup(pubs, person_id)

def _get_collabtuples_fallback(pubs, person_id):
    '''
    Returns the list of keyword tuples for given personid.
    @param person_id: int person id
    '''
    tup = get_most_popular_field_values(pubs,
                            CFG_WEBAUTHORPROFILE_COLLABORATION_TAG, count_repetitive_values=True)
    return tup

def _get_coauthors_fallback(collabs, person_id):
    exclude_recs = []
    if collabs:
        query = 'exactauthor:"%s" and (%s)' % (person_id, ' or '.join([('collaboration:"%s"' % x) for x in zip(*collabs)[0]]))
        exclude_recs = perform_request_search(rg=0, p=query)
    recids = perform_request_search(rg=0, p='exactauthor:"%s"' % str(person_id))
    recids = list(set(recids) - set(exclude_recs))
    a = format_records(recids, 'WAPAFF')
    a = [deserialize(p) for p in a.strip().split('!---THEDELIMITER---!') if p]
    coauthors = {}
    for rec, affs in a:
        keys = affs.keys()
        for n in keys:
            try:
                coauthors[n].add(rec)
            except KeyError:
                coauthors[n] = set([rec])

    coauthors = [(x, x, len(coauthors[x])) for x in coauthors if x.lower() != person_id.lower()]
    return coauthors

def  _get_rec_query_fallback(bibauthorid_data, authorname, db_names_dict, person_id):
    ''' Returns query to find author's papers in search engine. '''
    if authorname == None:
        authorname = ''
    rec_query = ""
    extended_author_search_str = ""

    is_bibauthorid = True

    if bibauthorid_data['is_baid']:
        if bibauthorid_data["cid"]:
            rec_query = 'exactauthor:"%s"' % bibauthorid_data["cid"]
        elif bibauthorid_data["pid"] > -1:
            rec_query = 'exactauthor:"%s"' % bibauthorid_data["pid"]

    if not rec_query:
        rec_query = 'exactauthor:"' + authorname + '"'

        if is_bibauthorid:
            if len(db_names_dict.keys()) > 1:
                extended_author_search_str = '('

            for name_index, name_query in enumerate(db_names_dict.keys()):
                if name_index > 0:
                    extended_author_search_str += " OR "
                if not name_query:
                    name_query = ''

                extended_author_search_str += 'exactauthor:"' + name_query + '"'

            if len(db_names_dict.keys()) > 1:
                extended_author_search_str += ')'

        if is_bibauthorid and extended_author_search_str:
            rec_query = extended_author_search_str
    return rec_query


if CFG_WEBAUTHORPROFILE_USE_BIBAUTHORID:
    _get_pubs = _get_pubs_bai
    _get_self_pubs = _get_self_pubs_bai
    _get_institute_pubs = _get_institute_pubs_bai
    _get_pubs_per_year = _get_pubs_per_year_bai
    _get_person_names_dicts = _get_person_names_dicts_bai
    _get_total_downloads = _get_total_downloads_bai
    _get_veryfy_my_pubs_list_link = _get_veryfy_my_pubs_list_link_bai
    _get_kwtuples = _get_kwtuples_bai
    _get_fieldtuples = _get_fieldtuples_bai
    _get_collabtuples = _get_collabtuples_bai
    _get_coauthors = _get_coauthors_bai
    _get_rec_query = _get_rec_query_bai
else:
    _get_pubs = _get_pubs_fallback
    _get_self_pubs = _get_self_pubs_fallback
    _get_institute_pubs = _get_institute_pubs_fallback
    _get_pubs_per_year = _get_pubs_per_year_fallback
    _get_person_names_dicts = _get_person_names_dicts_fallback
    _get_total_downloads = _get_total_downloads_fallback
    _get_veryfy_my_pubs_list_link = _get_veryfy_my_pubs_list_link_fallback
    _get_kwtuples = _get_kwtuples_fallback
    _get_fieldtuples = _get_fieldtuples_fallback
    _get_collabtuples = _get_collabtuples_fallback
    _get_coauthors = _get_coauthors_fallback
    _get_rec_query = _get_rec_query_fallback
