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

from hashlib import md5
from flaskext.cache import Cache
cache = Cache()

# For now we just use the same cache.

CFG_SEARCH_RESULTS_CACHE_PREFIX = "search_results::"

def get_search_query_id(**kwargs):
    p = kwargs.get('p', '')
    f = kwargs.get('f', '')
    cc = kwargs.get('cc', '')
    wl = kwargs.get('wl', '')
    return md5(repr((p, f, cc, wl))).hexdigest()


def get_search_results_cache_key(**kwargs):
    return CFG_SEARCH_RESULTS_CACHE_PREFIX + get_search_query_id(**kwargs)


def get_search_results_cache_key_from_qid(qid):
    return CFG_SEARCH_RESULTS_CACHE_PREFIX + qid

search_results_cache = cache
