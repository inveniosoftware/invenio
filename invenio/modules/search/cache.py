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
from flask import current_app

from invenio.base.globals import cfg
from invenio.ext.cache import cache
from invenio.legacy.miscutil.data_cacher import DataCacher, DataCacherProxy
from invenio.utils.hash import md5

from .models import Field, Fieldname

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
    try:
        return search_results_cache.get(
            get_search_results_cache_key_from_qid(qid) + '::cc')
    except Exception:
        current_app.logger.exception('Invalid collection name cache.')


def get_pattern_from_cache(qid):
    """Return pattern from query identifier."""
    try:
        return search_results_cache.get(
            get_search_results_cache_key_from_qid(qid) + '::p')
    except Exception:
        current_app.logger.exception('Invalid search pattern cache.')


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
    try:
        results = search_results_cache.get(qid)
        if results is not None:
            return intbitset().fastload(results)
    except Exception:
        current_app.logger.exception('Invalid search results cache.')


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
