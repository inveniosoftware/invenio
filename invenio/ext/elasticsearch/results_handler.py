"""This file is responsible for treating the elasticsearch results before they
   can be presented by the UI, namely the elasticsearch_view
"""
from UserDict import UserDict


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


class ResultsHandler(object):
    def process_results(self, results):
        """Convert a ES results into a Invenio search engine result.
        :param results: [object] elasticsearch results
        :return: [object] standard Invenio search engine results
        """
        return Response(results)
