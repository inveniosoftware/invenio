# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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

"""A warpper between Invenio and elasticsearch.

invenio.ext.elasticsearch.es_query
----------------------------------

A warpper between Invenio and elasticsearch.

usage:
    >>> from es_query import process_es_query, process_es_results
    >>> es = ElasticSearch(app)
    >>> es.query_handler(process_es_query)
    >>> es.results_handler(process_es_results)

"""
from UserDict import UserDict


def process_es_query(query):
    """Convert an Invenio query into an ES query.

    :param query: [string] Invenio query

    :return: [dict] ES query
    """
    es_query = {
        "query": {
            "bool": {
                "should": [{
                    "query_string": {
                        "query": query
                        }
                    },
                    {
                        "has_child": {
                            "type": "documents",
                            "query": {
                                "query_string": {
                                    "default_field": "fulltext",
                                    "query": query
                                    }
                                }
                            }
                        }],
                "minimum_should_match": 1
                }
            }
        }
    return es_query


def process_es_results(results):
    """Convert a ES results into a Invenio search engine result.

    :param results: [object] elasticsearch results

    :return: [object] standard Invenio search engine results
    """
    return Response(results)


class Response(object):

    """An Invenio response object.

    Contains, Hits, Facet results and Higlights.
    """

    def __init__(self, data):
        """New Response instance."""
        self.data = data
        self.hits = Hits(data)
        self.facets = Facets(data)
        self.highlights = Highlights(data)


class Hits(object):

    """Iterator over all recids that matched the query."""

    def __init__(self, data):
        """New Hits instance."""
        self.data = data.get("hits")

    def __iter__(self):
        """Iteration over values.

        TODO: query with token if you ask for more then len(self)
        """
        for hit in self.data['hits']:
            yield int(hit['_id'])

    def __len__(self):
        """Number of elements."""
        return self.data['total']


class Facets(UserDict):

    """Facet response objects."""

    def __init__(self, data):
        """New Facets instance."""
        UserDict.__init__(self, data.get("aggregations"))


class Highlights(UserDict):

    """Hightlights response objects."""

    def __init__(self, data):
        """New Hightlights instance.

        TODO: add fulltext highlights.
        """
        new_data = {}
        for hit in data.get('hits', {}).get('hits', []):
            if hit.get("highlight"):
                new_data[int(hit.get('_id'))] = hit.get("highlight")
            else:
                new_data[int(hit.get('_id'))] = {}
        UserDict.__init__(self, new_data)
