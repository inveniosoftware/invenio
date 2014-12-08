# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2014, 2015 CERN.
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

"""Implementation of search results caching."""

from intbitset import intbitset

from invenio.base.globals import cfg
from invenio.ext.cache import cache
from invenio.legacy.miscutil.data_cacher import DataCacher, DataCacherProxy
from invenio.utils.hash import md5
from invenio.utils.memoise import memoize

from .models import Collection, Collectionname, Field, Fieldname

search_results_cache = cache


def get_search_query_id(**kwargs):
    """Return unique query indentifier."""
    p = kwargs.get('p', '').strip()
    f = kwargs.get('f', '')
    cc = kwargs.get('cc', '')
    wl = kwargs.get('wl', '')
    so = kwargs.get('so', '')
    sf = kwargs.get('sf', '')
    return md5(repr((p, f, cc, wl, sf, so))).hexdigest()


def get_search_results_cache_key(**kwargs):
    """Return key for search results cache."""
    return cfg['CFG_SEARCH_RESULTS_CACHE_PREFIX'] + \
        get_search_query_id(**kwargs)


def get_search_results_cache_key_from_qid(qid=None):
    """Return key for search results cache from query identifier."""
    if qid is not None:
        return cfg['CFG_SEARCH_RESULTS_CACHE_PREFIX'] + qid


def get_collection_name_from_cache(qid):
    """Return collection name from query identifier."""
    return search_results_cache.get(
        get_search_results_cache_key_from_qid(qid) + '::cc')


def get_pattern_from_cache(qid):
    """Return pattern from query identifier."""
    return search_results_cache.get(
        get_search_results_cache_key_from_qid(qid) + '::p')


def set_results_cache(results, query, collection_name=None, timeout=None):
    """Store search results in cache."""
    if cfg['CFG_WEBSEARCH_SEARCH_CACHE_SIZE'] <= 0:
        return

    timeout = timeout or cfg['CFG_WEBSEARCH_SEARCH_CACHE_TIMEOUT']
    collection_name = collection_name or cfg['CFG_SITE_NAME']
    qid = get_search_results_cache_key(p=query, cc=collection_name)

    search_results_cache.set(qid, results.fastdump(), timeout=timeout)
    search_results_cache.set(qid + '::p', query, timeout=timeout)
    search_results_cache.set(qid + '::cc', collection_name, timeout=timeout)


def get_results_cache(query, collection_name=None):
    """Get results from cache."""
    collection_name = collection_name or cfg['CFG_SITE_NAME']
    qid = get_search_results_cache_key(p=query, cc=collection_name)
    results = search_results_cache.get(qid)
    if results is not None:
        return intbitset().fastload(results)


class CollectionAllChildrenDataCacher(DataCacher):

    """Cache for all children of a collection."""

    def __init__(self):
        """Initilize cache."""
        def cache_filler():
            collections = Collection.query.all()
            collection_index = dict([(c.id, c.name) for c in collections])

            return dict([
                (c.name, map(collection_index.get, c.descendants_ids))
                for c in collections
            ])

        def timestamp_verifier():
            from invenio.legacy.dbquery import get_table_update_time
            return max(get_table_update_time('collection'),
                       get_table_update_time('collection_collection'))

        DataCacher.__init__(self, cache_filler, timestamp_verifier)

collection_allchildren_cache = DataCacherProxy(CollectionAllChildrenDataCacher)


def get_collection_allchildren(coll, recreate_cache_if_needed=True):
    """Return the list of all children of a collection."""
    if recreate_cache_if_needed:
        collection_allchildren_cache.recreate_cache_if_needed()
    if coll not in collection_allchildren_cache.cache:
        return []  # collection does not exist; return empty list
    return collection_allchildren_cache.cache[coll]


class CollectionRecListDataCacher(DataCacher):

    """Implement cache for collection reclist hitsets.

    This class is not to be used directly; use function
    get_collection_reclist() instead.
    """

    def __init__(self):
        def cache_filler():
            collections = Collection.query.all()
            setattr(get_all_recids, 'cache', dict())
            return dict([(c.name, c.reclist) for c in collections])

        def timestamp_verifier():
            from invenio.legacy.dbquery import get_table_update_time
            return get_table_update_time('collection')

        DataCacher.__init__(self, cache_filler, timestamp_verifier)


collection_reclist_cache = DataCacherProxy(CollectionRecListDataCacher)


def get_collection_reclist(coll, recreate_cache_if_needed=True):
    """Return hitset of recIDs that belong to the collection 'coll'."""
    if recreate_cache_if_needed:
        collection_reclist_cache.recreate_cache_if_needed()
    if coll not in collection_reclist_cache.cache:
        return intbitset()
    if not collection_reclist_cache.cache[coll]:
        c_coll = Collection.query.filter_by(name=coll).first()
        if c_coll:
            collection_reclist_cache.cache[coll] = c_coll.reclist
    return collection_reclist_cache.cache[coll] or intbitset()


class RestrictedCollectionDataCacher(DataCacher):
    def __init__(self):
        def cache_filler():
            from invenio.modules.access.control import acc_get_action_id
            from invenio.modules.access.local_config import VIEWRESTRCOLL
            from invenio.modules.access.models import (
                AccAuthorization, AccARGUMENT
            )
            VIEWRESTRCOLL_ID = acc_get_action_id(VIEWRESTRCOLL)

            return [auth[0] for auth in AccAuthorization.query.join(
                AccAuthorization.argument
            ).filter(
                AccARGUMENT.keyword == 'collection',
                AccAuthorization.id_accACTION == VIEWRESTRCOLL_ID
            ).values(AccARGUMENT.value)]

            setattr(get_all_restricted_recids, 'cache', dict())

        def timestamp_verifier():
            from invenio.legacy.dbquery import get_table_update_time
            return max(get_table_update_time('accROLE_accACTION_accARGUMENT'),
                       get_table_update_time('accARGUMENT'))

        DataCacher.__init__(self, cache_filler, timestamp_verifier)


restricted_collection_cache = DataCacherProxy(RestrictedCollectionDataCacher)


def collection_restricted_p(collection, recreate_cache_if_needed=True):
    if recreate_cache_if_needed:
        restricted_collection_cache.recreate_cache_if_needed()
    return collection in restricted_collection_cache.cache


@memoize
def get_all_restricted_recids():
    """Return the set of all the restricted recids.

    I.e. the ids of those records which belong to at least one restricted
    collection.
    """
    ret = intbitset()
    for collection in restricted_collection_cache.cache:
        ret |= get_collection_reclist(collection)
    return ret


@memoize
def get_all_recids():
    """Return the set of all recids."""
    ret = intbitset()
    for collection in collection_reclist_cache.cache:
        ret |= get_collection_reclist(collection)
    return ret


def is_record_in_any_collection(recID, recreate_cache_if_needed=True):
    """Return True if the record belongs to at least one collection.

    This is a good, although not perfect, indicator to guess if webcoll has
    already run after this record has been entered into the system.
    """
    if recreate_cache_if_needed:
        collection_reclist_cache.recreate_cache_if_needed()
    return recID in get_all_recids()


class CollectionI18nNameDataCacher(DataCacher):
    """
    Provides cache for I18N collection names.  This class is not to be
    used directly; use function get_coll_i18nname() instead.
    """
    def __init__(self):
        def cache_filler():
            res = Collection.query.join(
                Collection.collection_names
            ).filter(Collectionname.type == 'ln').values(
                Collection.name, 'ln', 'value'
            )
            ret = {}
            for c, ln, i18nname in res:
                if i18nname:
                    if c not in ret:
                        ret[c] = {}
                    ret[c][ln] = i18nname
            return ret

        def timestamp_verifier():
            from invenio.legacy.dbquery import get_table_update_time
            return get_table_update_time('collectionname')

        DataCacher.__init__(self, cache_filler, timestamp_verifier)

collection_i18nname_cache = DataCacherProxy(CollectionI18nNameDataCacher)


def get_coll_i18nname(c, ln=None, verify_cache_timestamp=True):
    """Return nicely formatted collection name for given language.

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
    ln = ln or cfg['CFG_SITE_LANG']
    if verify_cache_timestamp:
        collection_i18nname_cache.recreate_cache_if_needed()
    out = c
    try:
        out = collection_i18nname_cache.cache[c][ln]
    except KeyError:
        pass  # translation in LN does not exist
    return out


class FieldI18nNameDataCacher(DataCacher):

    """Provide cache for I18N field names.

    This class is not to be used directly; use function get_field_i18nname()
    instead.
    """

    def __init__(self):
        def cache_filler():
            res = Field.query.join(Fieldname).filter(
                Fieldname.type == 'ln'
            ).values(Field.name, 'ln', 'value')
            ret = {}
            for f, ln, i18nname in res:
                if i18nname:
                    if f not in ret:
                        ret[f] = {}
                    ret[f][ln] = i18nname
            return ret

        def timestamp_verifier():
            from invenio.legacy.dbquery import get_table_update_time
            return get_table_update_time('fieldname')

        DataCacher.__init__(self, cache_filler, timestamp_verifier)

field_i18nname_cache = DataCacherProxy(FieldI18nNameDataCacher)


def get_field_i18nname(f, ln=None, verify_cache_timestamp=True):
    """
    Return nicely formatted field name (of type 'ln', 'long name') for
    field F in language LN.

    If VERIFY_CACHE_TIMESTAMP is set to True, then verify DB timestamp
    and field I18N name cache timestamp and refresh cache from the DB
    if needed.  Otherwise don't bother checking DB timestamp and
    return the cached value.  (This is useful when get_field_i18nname
    is called inside a loop.)
    """
    ln = ln or cfg['CFG_SITE_LANG']
    if verify_cache_timestamp:
        field_i18nname_cache.recreate_cache_if_needed()
    out = f
    try:
        out = field_i18nname_cache.cache[f][ln]
    except KeyError:
        pass  # translation in LN does not exist
    return out
