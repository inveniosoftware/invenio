# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011 CERN.
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
"""WebAuthorProfile Web Interface Logic and URL handler."""
# pylint: disable=W0105
# pylint: disable=C0301
# pylint: disable=W0613

import os

def handleSIGCHLD():
    os.waitpid(-1, os.WNOHANG)

from invenio.bibauthorid_webauthorprofileinterface import get_papers_by_person_id, \
    get_person_db_names_count, create_normalized_name, \
    get_person_redirect_link, is_valid_canonical_id, split_name_parts, \
    gathered_names_by_personid, get_canonical_id_from_personid, get_coauthor_pids, \
    get_person_names_count, get_existing_personids
from invenio.webauthorprofile_dbapi import get_cached_element, precache_element, cache_element, \
    expire_all_cache_for_person, get_expired_person_ids
from invenio.search_engine_summarizer import summarize_records
from invenio.bibrank_citation_searcher import get_cited_by_list as real_get_cited_by_list
from invenio.search_engine import get_most_popular_field_values
from invenio.search_engine import perform_request_search
from invenio.bibrank_downloads_indexer import get_download_weight_total
from invenio.intbitset import intbitset
from invenio.bibformat import format_record, format_records


try:
    import cPickle as pickle
except ImportError:
    import pickle

import time
import datetime

from invenio.config import CFG_BIBRANK_SHOW_DOWNLOAD_STATS
from invenio.config import CFG_WEBAUTHORPROFILE_CACHE_EXPIRED_DELAY_LIVE
from invenio.config import CFG_WEBAUTHORPROFILE_MAX_HEP_CHOICES
from invenio.config import CFG_WEBAUTHORPROFILE_USE_BIBAUTHORID

#After this delay, we assume that a process computing a empty claimed cache is dead and we
#spawn a new one to finish the job
RECOMPUTE_PRECACHED_ELEMENT_DELAY = datetime.timedelta(minutes=30)

#After this timeout we silently recompute the cache in the background, so that next refresh will be
#up-to-date
CACHE_IS_OUTDATED_DELAY = datetime.timedelta(days=CFG_WEBAUTHORPROFILE_CACHE_EXPIRED_DELAY_LIVE)

#tag constants
AUTHOR_TAG = "100__a"
AUTHOR_INST_TAG = "100__u"
COAUTHOR_TAG = "700__a"
COAUTHOR_INST_TAG = "700__u"
VENUE_TAG = "909C4p"
KEYWORD_TAG = "695__a"
FKEYWORD_TAG = "6531_a"
COLLABORATION_TAG = "710__g"



def update_cache(cached, name, key, target, *args):
    '''
    Actual update of cached valeus in name,key, updates to the result of target(args).
    If value already cached and up to date this does nothing, otherwise if present, not up to date
    but last_updated less then four minutes ago does nothing as well, as someone surely precached it
    and is computing the results, already.
    '''
    if cached['present']:
        delay = datetime.datetime.now() - cached['last_updated']
        if delay < RECOMPUTE_PRECACHED_ELEMENT_DELAY and cached['precached']:
            return
        if cached['upToDate'] and delay < CACHE_IS_OUTDATED_DELAY:
            return
    precache_element(name, key)
    el = target(*args)
    cache_element(name, key, pickle.dumps(el))
    return el

def retrieve_update_cache(name, key, target, *args):
    '''
    Retrieves the result of target(args) from name,key cache element.
    If element not present, returns [None, False] while spawning a process which will compute the
    result and cache it. If value Present but expired returs [value, False], and [value, True]
    otherwise
    '''
#    if not name and not key and not target:
#        #magic key to fake a false result
#        return [None, False]

    cached = get_cached_element(name, str(key))
    if cached['present']:
        if cached['upToDate']:
            delay = datetime.datetime.now() - cached['last_updated']
            if delay < CACHE_IS_OUTDATED_DELAY:
                return [pickle.loads(cached['value']), True]
    val = update_cache(cached, name, str(key), target, *args)
    if val:
        return [val, True]
    else:
        return [None, False]

def foo(x, y, z):
    '''
    foo to test the caching mechanism
    '''
    return retrieve_update_cache('foo', x, _foo, x, y, z)

def _foo(x, y, z):
    '''
    foo function to test the caching mechanism
    '''
    return [x, y, z]

def get_pubs(person_id):
    '''
    person's publication list.
    @param person_id: int person id
    @return [[rec1,rec2,...],bool]
    '''
    return retrieve_update_cache('pubs_list', 'pid:' + str(person_id), _get_pubs, person_id)

def get_self_pubs(person_id):
    '''
    person's publication list.
    @param person_id: int person id
    @return [[rec1,rec2,...],bool]
    '''
    return retrieve_update_cache('self_pubs_list', 'pid:' + str(person_id), _get_self_pubs, person_id)

def get_institute_pub_dict(person_id):
    """
    Return a dictionary consisting of institute -> list of publications given a personID.
    @param person_id: int person id
    @return [{'intitute':[pubs,...]},bool]
    """
    pubs = get_pubs(person_id)[0]
    namesdict = get_person_names_dicts(person_id)[0]
    db_names_dict = namesdict['db_names_dict']
    names_list = db_names_dict.keys()
    return retrieve_update_cache('institute_pub_dict', 'pid:' + str(person_id), _get_institute_pub_dict,
                    pubs, names_list, person_id)

def get_person_names_dicts(person_id):
    '''
    returns a dict with longest name, normalized names variations and db names variations.
    @param person_id: int personid
    @return [{'db_names_dict': {'name1':count,...}
              'longest':'longest name'}
              'names_dict': {'name1':count,...},
              bool]
    '''
    return retrieve_update_cache('person_names_dicts', 'pid:' + str(person_id), _get_person_names_dicts, person_id)

def get_total_downloads(person_id):
    '''
    returns the total downloads of the set of given papers
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

def get_cited_by_list(person_id):
    '''
    returns the list of citations for the giver person id.
    @param person_id: int person id
    @return [
            [[ [recid, [cits] ],
            bool]
    '''
    pubs = get_pubs(person_id)[0]
    return retrieve_update_cache('cited_by_list', 'pid:' + str(person_id),
                          _get_cited_by_list, pubs, person_id)

def get_kwtuples(person_id):
    '''
    Returns the keyword tuples for given personid.
    @param person_id: int person id
    @return [ (('kword',count),),
            bool]
    '''
    pubs = get_pubs(person_id)[0]
    return retrieve_update_cache('kwtuples', 'pid:' + str(person_id),
                           _get_kwtuples, pubs, person_id)

def get_venuetuples(person_id):
    pubs = get_pubs(person_id)[0]
    return retrieve_update_cache('venuetuples', 'pid:' + str(person_id),
                          _get_venuetuples, pubs, person_id)

def _get_venuetuples(pubs, person_id):
    tup = get_most_popular_field_values(pubs, (VENUE_TAG))
    return tup

def get_collabtuples(person_id):
    '''
    Returns the keyword tuples for given personid.
    @param person_id: int person id
    @return [ (('kword',count),),
            bool]
    '''
    pubs = get_pubs(person_id)[0]
    return retrieve_update_cache('collabtuples', 'pid:' + str(person_id),
                           _get_collabtuples, pubs, person_id)

def get_coauthors(person_id):
    '''
    Returns a list of coauthors.
    @param person_id: int person id
    @returns: [{'author name': coauthored}, bool]
    '''
    collabs = get_collabtuples(person_id)[0]
    return retrieve_update_cache('coauthors', 'pid:' + str(person_id), _get_coauthors, person_id, collabs)

def get_summarize_records(person_id, tag, ln):
    '''
    Returns  html for records summary given personid, tag and ln
    @param person_id: int person id
    @param tag: str kind of output
    @param ln: str language
    @return: [htmlsnippet, bool]
    '''
    pubs = get_pubs(person_id)[0]
    rec_query = get_rec_query(person_id)[0]
    return retrieve_update_cache('summarize_records' + '-' + str(ln), 'pid:' + str(person_id),
                          _get_summarize_records, pubs, tag, ln, rec_query, person_id)

def _get_summarize_records(pubs, tag, ln, rec_query, person_id):
    '''
    Returns  html for records summary given personid, tag and ln
    @param person_id: int person id
    @param tag: str kind of output
    @param ln: str language
    '''
    html = summarize_records(intbitset(pubs), tag, ln, rec_query)
    return html

def get_rec_query(person_id):
    '''
    Returns query to find author's papers in search engine
    @param: person_id: int person id
    @return: ['author:"canonical name or pid"', bool]
    '''
    namesdict = get_person_names_dicts(person_id)[0]
    authorname = namesdict['longest']
    db_names_dict = namesdict['db_names_dict']
    person_link = get_veryfy_my_pubs_list_link(person_id)[0]
    bibauthorid_data = {"is_baid": True, "pid":person_id, "cid":person_link}
    return retrieve_update_cache('rec_query', 'pid:' + str(person_id),
                          _get_rec_query, bibauthorid_data, authorname, db_names_dict, person_id)

def get_hepnames_data(person_id):
    '''
    Returns  hepnames data
    @param bibauthorid_data: dict with 'is_baid':bool, 'cid':canonicalID, 'pid':personid
    @return: [data, bool]
    '''
    person_link = get_veryfy_my_pubs_list_link(person_id)[0]
    bibauthorid_data = {"is_baid": True, "pid":person_id, "cid":person_link}
    return retrieve_update_cache('hepnames_data', 'pid:' + str(bibauthorid_data['pid']),
                          _get_hepnames_data, bibauthorid_data, person_id)

def _compute_cache_for_person(person_id):
    start = time.time()
    expire_all_cache_for_person(person_id)
    _ = get_rec_query(person_id)
    _ = get_pubs(person_id)
    _ = get_self_pubs(person_id)
    _ = get_institute_pub_dict(person_id)
    _ = get_person_names_dicts(person_id)
    _ = get_total_downloads(person_id)
    _ = get_veryfy_my_pubs_list_link(person_id)
    _ = get_cited_by_list(person_id)
    _ = get_kwtuples(person_id)
    _ = get_venuetuples(person_id)
    _ = get_collabtuples(person_id)
    _ = get_coauthors(person_id)
    _ = get_summarize_records(person_id, 'hcs', 'en')
    _ = get_hepnames_data(person_id)
    print person_id, ',' , str(time.time() - start)

def precompute_cache_for_person(person_ids=None, all_persons=False, only_expired=False):
    pids = []
    if all_persons:
        pids = list(get_existing_personids(with_papers_only=True))
    elif only_expired:
        pids = get_expired_person_ids()
    if person_ids:
        pids += person_ids

    for p in pids:
        _compute_cache_for_person(p)

def multiprocessing_precompute_cache_for_person(person_ids=None, all_persons=False, only_expired=False):
    pids = []
    if all_persons:
        pids = list(get_existing_personids(with_papers_only=True))
    elif only_expired:
        pids = get_expired_person_ids()
    if person_ids:
        pids += person_ids

    from multiprocessing import Pool
    p = Pool()
    p.map(_compute_cache_for_person, pids)



def _get_cited_by_list_bai(pubs, person_id):
    '''
    list of citations
    '''
    return real_get_cited_by_list(pubs)

def _get_pubs_bai(person_id):
    '''
    person's publication list.
    @param person_id: int person id
    '''
    full_pubs = get_papers_by_person_id(person_id, -1)
    pubs = [int(row[0]) for row in full_pubs]
    return pubs

def _get_self_pubs_bai(person_id):
    '''
    person's publication list.
    @param person_id: int person id
    '''
    cid = get_canonical_id_from_personid(person_id)
    try:
        cid = cid[0][0]
    except IndexError:
        cid = person_id
    return perform_request_search(rg=0, p='author:%s and authorcount:1' % cid)

def _get_institute_pub_dict_bai(recids, names_list, person_id):
    """return a dictionary consisting of institute -> list of publications"""
    try:
        cid = get_canonical_id_from_personid(person_id)[0][0]
    except IndexError:
        cid = person_id
    recids = perform_request_search(rg=0, p='author:%s' % str(cid))
    a = format_records(recids, 'WAPAFF')
    a = [pickle.loads(p) for p in a.split('!---THEDELIMITER---!') if p]
    affdict = {}
    for rec, affs in a:
        keys = affs.keys()
        for name in names_list:
            if name in keys and affs[name][0]:
                try:
                    affdict[affs[name][0]].add(rec)
                except KeyError:
                    affdict[affs[name][0]] = set([rec])
    return affdict

def _get_person_names_dicts_bai(person_id):
    '''
    returns a dict with longest name, normalized names variations and db names variations.
    @param person_id: int personid
    @return [dict{},bool up_to_date]
    '''
    longest_name = ""
    names_dict = {}
    db_names_dict = {}

    for aname, acount in get_person_names_count(person_id):
        names_dict[aname] = acount
        norm_name = create_normalized_name(split_name_parts(aname))

        if len(norm_name) > len(longest_name):
            longest_name = norm_name

    for aname, acount in get_person_db_names_count(person_id):
        #aname = aname.replace('"', '').strip()
        try:
            db_names_dict[aname] += acount
        except KeyError:
            db_names_dict[aname] = acount

    return {'longest':longest_name, 'names_dict':names_dict, 'db_names_dict':db_names_dict}

def _get_total_downloads_bai(pubs):
    '''
    returns the total downloads of the set of given papers
    @param pubs: list of recids
    @return: [int total downloads, bool up_to_date]
    '''
    totaldownloads = 0
    if CFG_BIBRANK_SHOW_DOWNLOAD_STATS:
        #find out how many times these records have been downloaded
        recsloads = {}
        recsloads = get_download_weight_total(recsloads, pubs)
        #sum up
        for k in recsloads.keys():
            totaldownloads = totaldownloads + recsloads[k]
    return totaldownloads

def _get_veryfy_my_pubs_list_link_bai(person_id):
    '''
    canonical name links
    '''
    person_link = person_id
    cid = get_person_redirect_link(person_id)

    if is_valid_canonical_id(cid):
        person_link = cid
    return person_link

def _get_kwtuples_bai(pubs, person_id):
    '''
    Returns the keyword tuples for given personid.
    @param person_id: int person id
    '''
    tup = get_most_popular_field_values(pubs,
                            (KEYWORD_TAG, FKEYWORD_TAG), count_repetitive_values=False)
    return tup

def _get_collabtuples_bai(pubs, person_id):
    '''
    Returns the keyword tuples for given personid.
    @param person_id: int person id
    '''
    tup = get_most_popular_field_values(pubs,
                            COLLABORATION_TAG, count_repetitive_values=False)
    return tup

def _get_coauthors_bai(personid, collabs):
    def canonical_name(pid):
        ret = get_canonical_id_from_personid(pid)
        if ret:
            return ret[0][0]
        else:
            return ""
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

    cid = canonical_name(personid)
    if not cid:
        cid = str(personid)

    if collabs:
        query = 'author:%s and (%s)' % (cid, ' or '.join([('collaboration:"%s"' % x) for x in zip(*collabs)[0]]))
        exclude_recs = perform_request_search(rg=0, p=query)
    else:
        exclude_recs = None

    personids = get_coauthor_pids(personid, exclude_recs)

    coauthors = []
    for p in personids:
        cn = canonical_name(p[0])
        ln = max_key(gathered_names_by_personid(p[0]), key=len)
        #exact number of papers based on query. Not activated for performance reasons
        #paps = len(perform_request_search(rg=0, p="author:%s author:%s" % (cid, cn)))
        paps = p[1]
        if paps:
            coauthors.append((cn, ln, paps))
    return coauthors

def  _get_rec_query_bai(bibauthorid_data, authorname, db_names_dict, person_id):
    '''
    Returns query to find author's papers in search engine
    '''
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

def _get_hepnames_data_bai(bibauthorid_data, person_id):
    '''
    Returns  hepnames data
    @param bibauthorid_data: dict with 'is_baid':bool, 'cid':canonicalID, 'pid':personid
    '''
    cid = str(person_id)
    hepdict = {}
    if bibauthorid_data['cid']:
        cid = bibauthorid_data['cid']
    hepRecord = perform_request_search(rg=0, cc='HepNames', p='find a "%s"' % cid)[:CFG_WEBAUTHORPROFILE_MAX_HEP_CHOICES]

    hepdict['cid'] = cid
    hepdict['pid'] = person_id

    if not hepRecord or len(hepRecord) > 1:
        #present choice dialog with alternatives?
        names_dict = get_person_names_dicts(person_id)
        dbnames = names_dict[0]['db_names_dict'].keys()
        query = ' or '.join(['"%s"' % str(n) for n in dbnames])
        additional_records = perform_request_search(rg=0, cc='HepNames', p=query)[:CFG_WEBAUTHORPROFILE_MAX_HEP_CHOICES]
        hepRecord += additional_records
        hepdict['HaveHep'] = False
        hepdict['HaveChoices'] = bool(hepRecord)
        #limits possible choiches!
        hepdict['HepChoices'] = [(format_record(x, 'hb'), x) for x in hepRecord ]
        hepdict['heprecord'] = hepRecord
        hepdict['bd'] = bibauthorid_data
    else:
        #show the heprecord we just found.
        hepdict['HaveHep'] = True
        hepdict['HaveChoices'] = False
        hepdict['heprecord'] = format_record(hepRecord[0], 'hd')
        hepdict['bd'] = bibauthorid_data
    return hepdict

def _get_cited_by_list_fallback(pubs, person_id):
    '''
    list of citations
    '''
    return real_get_cited_by_list(pubs)

def _get_pubs_fallback(person_id):
    '''
    person's publication list.
    @param person_id: int person id
    '''
    pubs = perform_request_search(rg=0, p='exactauthor:"%s"' % str(person_id))
    return pubs

def _get_self_pubs_fallback(person_id):
    '''
    person's publication list.
    @param person_id: int person id
    '''
    return perform_request_search(rg=0, p='exactauthor:"%s" and authorcount:1' % str(person_id))

def _get_institute_pub_dict_fallback(recids, names_list, person_id):
    """return a dictionary consisting of institute -> list of publications"""

    recids = perform_request_search(rg=0, p='exactauthor:"%s"' % str(person_id))
    a = format_records(recids, 'WAPAFF')
    a = [pickle.loads(p) for p in a.split('!---THEDELIMITER---!') if p]
    affdict = {}
    for rec, affs in a:
        keys = affs.keys()
        for name in names_list:
            if name in keys and affs[name][0]:
                try:
                    affdict[affs[name][0]].add(rec)
                except KeyError:
                    affdict[affs[name][0]] = set([rec])
    return affdict

def _get_person_names_dicts_fallback(person_id):
    '''
    returns a dict with longest name, normalized names variations and db names variations.
    @param person_id: int personid
    @return [dict{},bool up_to_date]
    '''
    p = perform_request_search(rg=0, p='exactauthor:"%s"' % person_id)
    pcount = len(p)
    if p:
        formatted = format_record(p[0], 'XM')
        s = formatted.lower().index(person_id.lower())
        if s:
            person_id = formatted[s:s + len(person_id)]
    return {'longest':person_id, 'names_dict':{person_id:pcount}, 'db_names_dict':{person_id:pcount}}

def _get_total_downloads_fallback(pubs):
    '''
    returns the total downloads of the set of given papers
    @param pubs: list of recids
    @return: [int total downloads, bool up_to_date]
    '''
    totaldownloads = 0
    if CFG_BIBRANK_SHOW_DOWNLOAD_STATS:
        #find out how many times these records have been downloaded
        recsloads = {}
        recsloads = get_download_weight_total(recsloads, pubs)
        #sum up
        for k in recsloads.keys():
            totaldownloads = totaldownloads + recsloads[k]
    return totaldownloads

def _get_veryfy_my_pubs_list_link_fallback(person_id):
    '''
    canonical name links
    '''
    return ''

def _get_kwtuples_fallback(pubs, person_id):
    '''
    Returns the keyword tuples for given personid.
    @param person_id: int person id
    '''
    tup = get_most_popular_field_values(pubs,
                            (KEYWORD_TAG, FKEYWORD_TAG), count_repetitive_values=False)
    return tup

def _get_collabtuples_fallback(pubs, person_id):
    '''
    Returns the keyword tuples for given personid.
    @param person_id: int person id
    '''
    tup = get_most_popular_field_values(pubs,
                            COLLABORATION_TAG, count_repetitive_values=False)
    return tup

def _get_coauthors_fallback(personid, collabs):
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

    if collabs:
        query = 'exactauthor:"%s" and (%s)' % (personid, ' or '.join([('collaboration:"%s"' % x) for x in zip(*collabs)[0]]))
        exclude_recs = perform_request_search(rg=0, p=query)
    else:
        exclude_recs = []

    recids = perform_request_search(rg=0, p='exactauthor:"%s"' % str(personid))
    recids = list(set(recids) - set(exclude_recs))
    a = format_records(recids, 'WAPAFF')
    a = [pickle.loads(p) for p in a.split('!---THEDELIMITER---!') if p]
    coauthors = {}
    for rec, affs in a:
        keys = affs.keys()
        for n in keys:
            try:
                coauthors[n].add(rec)
            except KeyError:
                coauthors[n] = set([rec])

    coauthors = [(x, x, len(coauthors[x])) for x in coauthors if x.lower() != personid.lower()]
    return coauthors

def  _get_rec_query_fallback(bibauthorid_data, authorname, db_names_dict, person_id):
    '''
    Returns query to find author's papers in search engine
    '''
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

                extended_author_search_str += 'exactauthor:"' + name_query + '"'

            if len(db_names_dict.keys()) > 1:
                extended_author_search_str += ')'

        if is_bibauthorid and extended_author_search_str:
            rec_query = extended_author_search_str
    return rec_query

def _get_hepnames_data_fallback(bibauthorid_data, person_id):
    '''
    Returns  hepnames data
    @param bibauthorid_data: dict with 'is_baid':bool, 'cid':canonicalID, 'pid':personid
    '''
    cid = str(person_id)
    hepdict = {}
    if bibauthorid_data['cid']:
        cid = bibauthorid_data['cid']
    hepRecord = perform_request_search(rg=0, cc='HepNames', p=cid)[:CFG_WEBAUTHORPROFILE_MAX_HEP_CHOICES]

    hepdict['cid'] = cid
    hepdict['pid'] = person_id

    if not hepRecord or len(hepRecord) > 1:
        #present choice dialog with alternatives?
        names_dict = get_person_names_dicts(person_id)
        dbnames = names_dict[0]['db_names_dict'].keys()
        query = ' or '.join(['"%s"' % str(n) for n in dbnames])
        additional_records = perform_request_search(rg=0, cc='HepNames', p=query)[:CFG_WEBAUTHORPROFILE_MAX_HEP_CHOICES]
        hepRecord += additional_records
        hepdict['HaveHep'] = False
        hepdict['HaveChoices'] = bool(hepRecord)
        #limits possible choiches!
        hepdict['HepChoices'] = [(format_record(x, 'hb'), x) for x in hepRecord ]
        hepdict['heprecord'] = hepRecord
        hepdict['bd'] = bibauthorid_data
    else:
        #show the heprecord we just found.
        hepdict['HaveHep'] = True
        hepdict['HaveChoices'] = False
        hepdict['heprecord'] = format_record(hepRecord[0], 'hd')
        hepdict['bd'] = bibauthorid_data
    return hepdict



if CFG_WEBAUTHORPROFILE_USE_BIBAUTHORID:
    _get_pubs = _get_pubs_bai
    _get_self_pubs = _get_self_pubs_bai
    _get_institute_pub_dict = _get_institute_pub_dict_bai
    _get_person_names_dicts = _get_person_names_dicts_bai
    _get_total_downloads = _get_total_downloads_bai
    _get_veryfy_my_pubs_list_link = _get_veryfy_my_pubs_list_link_bai
    _get_kwtuples = _get_kwtuples_bai
    _get_collabtuples = _get_collabtuples_bai
    _get_coauthors = _get_coauthors_bai
    _get_rec_query = _get_rec_query_bai
    _get_hepnames_data = _get_hepnames_data_bai
    _get_cited_by_list = _get_cited_by_list_bai
else:
    _get_pubs = _get_pubs_fallback
    _get_self_pubs = _get_self_pubs_fallback
    _get_institute_pub_dict = _get_institute_pub_dict_fallback
    _get_person_names_dicts = _get_person_names_dicts_fallback
    _get_total_downloads = _get_total_downloads_fallback
    _get_veryfy_my_pubs_list_link = _get_veryfy_my_pubs_list_link_fallback
    _get_kwtuples = _get_kwtuples_fallback
    _get_collabtuples = _get_collabtuples_fallback
    _get_coauthors = _get_coauthors_fallback
    _get_rec_query = _get_rec_query_fallback
    _get_hepnames_data = _get_hepnames_data_fallback
    _get_cited_by_list = _get_cited_by_list_fallback
