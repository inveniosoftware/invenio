# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012 CERN.
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

from invenio.base.globals import cfg
from invenio.ext.cache import cache
from invenio.utils.hash import md5

search_results_cache = cache


def get_search_query_id(**kwargs):
    """
    Returns unique query indentifier.
    """
    p = kwargs.get('p', '')
    f = kwargs.get('f', '')
    cc = kwargs.get('cc', '')
    wl = kwargs.get('wl', '')
    so = kwargs.get('so', '')
    sf = kwargs.get('sf', '')
    return md5(repr((p, f, cc, wl, sf, so))).hexdigest()


def get_search_results_cache_key(**kwargs):
    """
    Returns key for search results cache.
    """
    return cfg['CFG_SEARCH_RESULTS_CACHE_PREFIX'] + get_search_query_id(**kwargs)


def get_search_results_cache_key_from_qid(qid=None):
    """
    Returns key for search results cache from query identifier.
    """
    if qid is not None:
        return cfg['CFG_SEARCH_RESULTS_CACHE_PREFIX'] + qid


def get_collection_name_from_cache(qid):
    """
    Returns collection name from query identifier.
    """
    return search_results_cache.get(
        get_search_results_cache_key_from_qid(qid) + '::cc')


def get_pattern_from_cache(qid):
    """
    Returns pattern from query identifier.
    """
    return search_results_cache.get(
        get_search_results_cache_key_from_qid(qid) + '::p')
