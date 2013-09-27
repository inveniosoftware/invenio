# -*- coding: utf-8 -*-

## This file is part of Invenio.
## Copyright (C) 2012, 2013 CERN.
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

from operator import itemgetter
from itertools import groupby
from werkzeug.utils import cached_property
from flask import g, url_for, request
from flask.ext.login import current_user

from .cache import search_results_cache, \
    get_search_results_cache_key_from_qid
from .models import Collection

from invenio.base.globals import cfg
try:
    from invenio.intbitset import intbitset
except:
    from intbitset import intbitset
from invenio.base.utils import autodiscover_facets


def get_current_user_records_that_can_be_displayed(qid):
    """
    Returns records that current user can display.

    @param qid: query identifier

    @return: records in intbitset
    """
    CFG_WEBSEARCH_SEARCH_CACHE_TIMEOUT = cfg.get(
        'CFG_WEBSEARCH_SEARCH_CACHE_TIMEOUT')
    @search_results_cache.memoize(timeout=CFG_WEBSEARCH_SEARCH_CACHE_TIMEOUT)
    def get_records_for_user(qid, uid):
        from invenio.search_engine import get_records_that_can_be_displayed
        key = get_search_results_cache_key_from_qid(qid)
        data = search_results_cache.get(key)
        if data is None:
            return intbitset([])
        cc = search_results_cache.get(key + '::cc')
        return get_records_that_can_be_displayed(current_user,
                                                 intbitset().fastload(data), cc)
    # Simplifies API
    return get_records_for_user(qid, current_user.get_id())


def faceted_results_filter(recids, filter_data, facets):
    """
    Returns records that match selected filter data.

    @param recids: found records
    @param filter_date: selected facet filters
    @param facet_config: facet configuration

    @return: filtered records
    """

    ## Group filter data by operator and then by facet key.
    sortkeytype = itemgetter(0)
    sortfacet = itemgetter(1)
    data = sorted(filter_data, key=sortkeytype)
    out = {}
    for t, vs in groupby(data, key=sortkeytype):
        out[t] = {}
        for v, k in groupby(sorted(vs, key=sortfacet), key=sortfacet):
            out[t][v] = map(lambda i: i[2], k)

    filter_data = out

    ## Intersect and diff records with selected facets.
    output = recids

    if '+' in filter_data:
        values = filter_data['+']
        for key, facet in facets.iteritems():
            if key in values:
                output.intersection_update(facet.get_facet_recids(values[key]))

    if '-' in filter_data:
        values = filter_data['-']
        for key, facet in facets.iteritems():
            if key in values:
                output.difference_update(facet.get_facet_recids(values[key]))

    return output


def _facet_plugin_checker(plugin_code):
    """
    Handy function to check facet plugin.
    """
    if 'facet' in dir(plugin_code):
        candidate = getattr(plugin_code, 'facet')
        if isinstance(candidate, FacetBuilder):
            return candidate


class FacetLoader(object):

    @cached_property
    def plugins(self):
        """Loaded facet plugins."""
        return filter(None, map(_facet_plugin_checker, autodiscover_facets()))

    @cached_property
    def elements(self):
        """Dict with `FacetBuilder` instances accesible by facet name."""
        return dict((f.name, f) for f in self.plugins)

    def __getitem__(self, key):
        return self.elements[key]

    @cached_property
    def sorted_list(self):
        """List of sorted facets by their order property."""
        return sorted(self.elements.values(), key=lambda x: x.order)

    def config(self, *args, **kwargs):
        """Returns facet config for all loaded plugins."""
        return map(lambda x: x.get_conf(*args, **kwargs), self.sorted_list)


class FacetBuilder(object):
    """Implementation of a general facet builder using function
    `get_most_popular_field_values`."""

    def __init__(self, name, order=0):
        self.name = name
        self.order = order

    def get_title(self, **kwargs):
        return g._('Any ' + self.name.capitalize())

    def get_url(self, qid=None):
        return url_for('.facet', name=self.name, qid=qid)

    def get_conf(self, **kwargs):
        return dict(title=self.get_title(**kwargs),
                    url=self.get_url(kwargs.get('qid')),
                    facet=self.name)

    def get_recids_intbitset(self, qid):
        try:
            return get_current_user_records_that_can_be_displayed(qid)
        except:
            return intbitset([])

    def get_recids(self, qid):
        return self.get_recids_intbitset(qid).tolist()

    def get_facets_for_query(self, qid, limit=20, parent=None):
        from invenio.search_engine import get_most_popular_field_values,\
            get_field_tags
        return get_most_popular_field_values(self.get_recids(qid),
                                             get_field_tags(self.name)
                                             )[0:limit]

    #@blueprint.invenio_memoize(timeout=CFG_WEBSEARCH_SEARCH_CACHE_TIMEOUT / 2)
    def get_value_recids(self, value):
        from invenio.search_engine import search_pattern
        if isinstance(value, unicode):
            value = value.encode('utf8')
        p = '"' + str(value) + '"'
        return search_pattern(p=p, f=self.name)

    #@blueprint.invenio_memoize(timeout=CFG_WEBSEARCH_SEARCH_CACHE_TIMEOUT / 4)
    def get_facet_recids(self, values):
        return reduce(lambda x, y: x.union(y),
                      [self.get_value_recids(v) for v in values],
                      intbitset())


class CollectionFacetBuilder(FacetBuilder):
    """Custom implementation of collection facet builder."""

    def get_title(self, **kwargs):
        """Returns title for collection facet."""
        collection = kwargs.get('collection')
        if collection is not None and collection.id > 1:
            return collection.name_ln
        return super(CollectionFacetBuilder, self).get_title(**kwargs)

    def get_facets_for_query(self, qid, limit=20, parent=None):
        recIDsHitSet = self.get_recids_intbitset(qid)
        parent = request.args.get('parent', None)
        if parent is not None:
            collection = Collection.query.filter(Collection.name == parent).\
                                          first_or_404()
        else:
            cc = search_results_cache.get(
                    get_search_results_cache_key_from_qid(qid) + '::cc')
            if cc is not None:
                collection = Collection.query.filter(Collection.name == cc).\
                                          first_or_404()
            else:
                collection = Collection.query.get(1)
        facet = []
        for c in collection.collection_children_r:
            num_records = len(c.reclist.intersection(recIDsHitSet))
            if num_records:
                facet.append((c.name, num_records, c.name_ln))
        return sorted(facet, key=lambda x: x[1], reverse=True)[0:limit]
