#
# This file is part of Invenio.
# Copyright (C) 2013, 2014 CERN.
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

""" Elasticsearch extension for Invenio.

invenio.ext.elasticsearch
-------------------------
Elasticsearch a search engine for Invenio.

It should be able to perform:
    - metadata and fulltext search almost without DB
    - metadata facets such as authors, Invenio collection facets both with the
      corresponding filters
    - fulltext and metadata fields highlightings
    - fast collection indexing, mid-fast metadata indexing, almost fast fulltext
      indexing


Requirements
^^^^^^^^^^^^

Elasticsearch >= 1.0, pyelasticsearch.


Installation (for developpement)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Download the tarball form http://elasticsearch.org, uncompress it and add the
bin/ directory in your path.
Go to the invenio src directory and run ``honcho start`` or equivalent.


Deployment
^^^^^^^^^^^

...

Testing
^^^^^^^

This extension is working with the demosite. Indexing is done automagicaly
using webcoll/bibupload signals. Note: bibindex is not required.

Usage
^^^^^
    >>> es = current_app.extensions.get("elasticsearch")
    >>> res = es.search(query="title:Sneutrinos",
                    facet_filters=[("facet_authors", "Schael, S"),
                    ("facet_authors", "Bruneliere, R")])

see: `a simple of search interface <http://github.com/jma/elasticsearch_view>`_
or invenio/ext/elasticsearch/scripts/test_es.py for a complete manual
indexing and searching example.

TODO:
    - adding exceptions
    - decide if we create one ES document type for each JsonAlchemy document type
    - convert an Invenio query into a ES query
    - add sort options in JsonAchemy
    - check collection access restriction with collection filters
        - probably needs a collection exclusion list as search params
        - Note: file access restriction is not managed by the indexer
    - multi-lingual support (combo plugin, in config files)
    - term boosting configuration (in JsonAlchemy?)
    - search by marc field support?
    - test hierachical collections
    - test similar documents
    - and many more...
"""
from werkzeug.utils import cached_property
from pyelasticsearch import ElasticSearch as PyElasticSearch


class ElasticSearch(object):

    """
    Flask extension.

    Initialization of the extension:

    >>> from flask import Flask
    >>> from flask_elasticsearch import ElasticSearch
    >>> app = Flask('myapp')
    >>> s = ElasticSearch(app=app)

    or alternatively using the factory pattern:

    >>> app = Flask('myapp')
    >>> s = ElasticSearch()
    >>> s.init_app(app)
    """

    def __init__(self, app=None):
        """Build the extension object."""
        self.app = app

        #default process functions
        self.process_query = lambda x: x
        self.process_results = lambda x: x

        # TODO: to put in config?
        self.records_doc_type = "records"
        self.documents_doc_type = "documents"
        self.collections_doc_type = "collections"

        # to cache recids collections
        self._recids_collections = {}

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """
        Initialize a Flask application.

        Only one Registry per application is allowed.
        """
        app.config.setdefault('ELASTICSEARCH_URL', 'http://localhost:9200/')
        app.config.setdefault('ELASTICSEARCH_INDEX', "invenio")
        app.config.setdefault('ELASTICSEARCH_NUMBER_OF_SHARDS', 1)
        app.config.setdefault('ELASTICSEARCH_NUMBER_OF_REPLICAS', 0)
        app.config.setdefault('ELASTICSEARCH_DATE_DETECTION', False)
        app.config.setdefault('ELASTICSEARCH_NUMERIC_DETECTION', False)
        app.config.setdefault('ELASTICSEARCH_ANALYSIS', {
            "default": {"type": "simple"}})

        # Follow the Flask guidelines on usage of app.extensions
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        if 'elasticsearch' in app.extensions:
            raise Exception("Flask application already initialized")

        app.extensions['elasticsearch'] = self
        self.app = app

    @cached_property
    def connection(self):
        """Return a pyelasticsearch connection object."""
        return PyElasticSearch(self.app.config['ELASTICSEARCH_URL'])

    def set_query_handler(self, handler):
        """
        Specify a function to convert the invenio query into a ES query.

        :param handler: [function] take a query[string] parameter
        """
        self.process_query = handler

    def set_results_handler(self, handler):
        """
        Set a function to process the search results.

        To convert ES search results into an object understandable by Invenio.

        :param handler: [function] take a query[string] parameter
        """
        self.process_results = handler

    @property
    def status(self):
        """The status of the ES cluster.

        See: http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/cluster-health.html
        for more.

        TODO: is it useful?

        :return: [string] possible values: green, yellow, red. green means all
          ok including replication, yellow means replication not active, red
          means partial results.
        """
        return self.connection.health().get("status")

    def index_exists(self, index=None):
        """Check if the index exists in the cluster.

        :param index: [string] index name

        :return: [bool] True if exists
        """
        if index is None:
            index = self.app.config['ELASTICSEARCH_INDEX']
        if self.connection.status().get("indices").get(index):
            return True
        return False

    def delete_index(self, index=None):
        """Delete the given index.

        :param index: [string] index name

        :return: [bool] True if success
        """
        if index is None:
            index = self.app.config['ELASTICSEARCH_INDEX']
        try:
            self.connection.delete_index(index=index)
            return True
        except:
            return False

    def create_index(self, index=None):
        """Create the given index.

        Also set basic configuration and doc type mappings.

        :param index: [string] index name

        :return: [bool] True if success
        """
        if index is None:
            index = self.app.config['ELASTICSEARCH_INDEX']
        if self.index_exists(index=index):
            return True
        try:
            #create index
            index_settings = {
                #should be set to 1 for exact facet count
                "number_of_shards":
                self.app.config['ELASTICSEARCH_NUMBER_OF_SHARDS'],

                #in case of primary shard failed
                "number_of_replicas":
                self.app.config['ELASTICSEARCH_NUMBER_OF_REPLICAS'],

                #disable automatic type detection
                #that can cause errors depending of the indexing order
                "date_detection":
                self.app.config['ELASTICSEARCH_DATE_DETECTION'],
                "numeric_detection":
                self.app.config['ELASTICSEARCH_NUMERIC_DETECTION']
            }
            if self.app.config['ELASTICSEARCH_ANALYSIS']:
                index_settings["analysis"] = \
                    self.app.config['ELASTICSEARCH_ANALYSIS']

            self.connection.create_index(index=index, settings=index_settings)

            from es_config import get_records_fields_config, \
                get_documents_fields_config, \
                get_collections_fields_config
            #mappings
            self._mapping(index=index, doc_type=self.records_doc_type,
                          fields_mapping=get_records_fields_config())

            self._mapping(index=index, doc_type=self.documents_doc_type,
                          fields_mapping=get_documents_fields_config(),
                          parent_type=self.records_doc_type)

            self._mapping(index=index, doc_type=self.collections_doc_type,
                          fields_mapping=get_collections_fields_config(),
                          parent_type=self.records_doc_type)

            return True
        except:
            return False

    def _mapping(self, index, doc_type, fields_mapping, parent_type=None):
        mapping = {
            doc_type: {
                "properties": fields_mapping
            }
        }

        # specific conf for join like query
        if parent_type:
            mapping[doc_type]["_parent"] = {"type": parent_type}
        try:
            self.connection.put_mapping(index=index, doc_type=doc_type,
                                        mapping=mapping)
            return True
        except:
            return False

    def _bulk_index_docs(self, docs, doc_type, index):
        if not docs:
            return []
        self.app.logger.info("Indexing: %d records for %s" % (len(docs),
                             doc_type))
        results = self.connection.bulk_index(index=index,
                                             doc_type=doc_type, docs=docs,
                                             id_field='_id',
                                             refresh=self.app.config.get("DEBUG"))
        errors = []
        for it in results.get("items"):
            if it.get("index").get("error"):
                errors.append((it.get("index").get("_id"), it.get("index").get("error")))
        return errors

    def _documents_has_been_updated(self, recid):
        from invenio.legacy.bibdocfile.api import BibRecDocs
        import datetime

        bibdocs = BibRecDocs(recid)
        #TODO: replace legacy code
        from invenio.legacy.dbquery import run_sql
        (record_creation_date, record_modification_date) = \
            run_sql("SELECT creation_date, modification_date from bibrec where id=%s"
                    % (recid))[0]

        #wait for a JsonAlchemy bug resolution
        #record = self._get_record(recid)

        #record_modification_date = \
        #    datetime.datetime.strptime(record.get("modification_date"),
        #        "%Y-%m-%dT%H:%M:%S")
        #record_creation_date = \
        #    datetime.datetime.strptime(record.get("creation_date"),
        #        "%Y-%m-%dT%H:%M:%S.%f")
        if not bibdocs.list_bibdocs():
            self.app.logger.debug("No docs for: %s" % recid)
        for b in bibdocs.list_bibdocs():
            #should add fews seconds for rounding problem
            if b.md + datetime.timedelta(seconds=2) >= record_modification_date:
                return True
        return False

    def _get_record(self, recid):
        from invenio.modules.records.api import get_record
        record_as_dict = get_record(recid, reset_cache=True).dumps()
        del record_as_dict["__meta_metadata__"]
        return record_as_dict

    def _get_text(self, recid):
        from invenio.legacy.bibdocfile.api import BibRecDocs
        text = BibRecDocs(recid).get_text(True)
        if not text:
            self.app.logger.debug("No text for:%s" % recid)
            return None
        return {
            "fulltext": text,
            "recid": recid,
            "_id": recid,
            "_parent": recid}

    def _get_collections(self, recid):
        return {
            "recid": recid,
            "_id": recid,
            "_parent": recid,
            "name": self._recids_collections.get(recid, "")}

    def get_all_collections_for_records(self, recreate_cache_if_needed=True):
        """Return a dict with recid as key and collection list as value.

        This replace existing Invenio function for performance reason.

        :param recreate_cache_if_needed: [bool] True if regenerate the cache
        """
        from invenio.legacy.search_engine import collection_reclist_cache, get_collection_reclist
        from invenio.legacy.websearch.webcoll import Collection
        ret = {}

        #update the cache?
        if recreate_cache_if_needed:
            collection_reclist_cache.recreate_cache_if_needed()

        for name in collection_reclist_cache.cache.keys():
            recids = get_collection_reclist(name, recreate_cache_if_needed=False)
            full_path_name = "/".join([v.name for v in
                                       Collection(name).get_ancestors()] +
                                      [name])
            for recid in recids:
                ret.setdefault(recid, []).append(full_path_name)
        self._recids_collections = ret

    def index_collections(self, recids=None, index=None, bulk_size=100000, **kwargs):
        """Index collections.

        Collections maps computed by webcoll is indexed into the given index in
        order to allow filtering by collection.

        :param recids: [list of int] recids to index
        :param index: [string] index name
        :param bulk_size: [int] batch size to index

        :return: [list of int] list of recids not indexed due to errors
        """
        self.get_all_collections_for_records()
        if not recids:
            recids = self._recids_collections.keys()
        if index is None:
            index = self.app.config['ELASTICSEARCH_INDEX']
        return self._index_docs(recids, self.collections_doc_type, index,
                                bulk_size, self._get_collections)

    def index_documents(self, recids, index=None, bulk_size=100000, **kwargs):
        """Index fulltext files.

        Put the fullext extracted by Invenio into the given index.

        :param recids: [list of int] recids to index
        :param index: [string] index name
        :param bulk_size: [int] batch size to index

        :return: [list of int] list of recids not indexed due to errors
        """
        if index is None:
            index = self.app.config['ELASTICSEARCH_INDEX']
        recids_to_index = filter(self._documents_has_been_updated, recids)
        if recids_to_index:
            self.app.logger.debug("Indexing document for %s" % recids)
        return self._index_docs(recids_to_index, self.documents_doc_type, index,
                                bulk_size, self._get_text)

    def index_records(self, recids, index=None, bulk_size=100000, **kwargs):
        """Index bibliographic records.

        The document structure is provided by JsonAlchemy.

        Note: the __metadata__ is removed for the moment.

        TODO: is should be renamed as index?

        :param recids: [list of int] recids to index
        :param index: [string] index name
        :param bulk_size: [int] batch size to index

        :return: [list] list of recids not indexed due to errors
        """
        if index is None:
            index = self.app.config['ELASTICSEARCH_INDEX']
        return self._index_docs(recids, self.records_doc_type, index,
                                bulk_size, self._get_record)

    def _index_docs(self, recids, doc_type, index, bulk_size, get_docs):
        docs = []
        errors = []
        for recid in recids:
            doc = get_docs(recid)
            if doc:
                docs.append(doc)
            if len(docs) >= bulk_size:
                errors += self._bulk_index_docs(docs, doc_type=doc_type,
                                                index=index)
                docs = []
        errors += self._bulk_index_docs(docs, doc_type=doc_type, index=index)
        return errors

    def find_similar(self, recid, index=None, **kwargs):
        """Find simlar documents to the given recid.

        TODO: tests

        :param recid: [int] document id to find similar
        :param index: [string] index name

        :return: [list] list of recids
        """
        if index is None:
            index = self.app.config['ELASTICSEARCH_INDEX']
        fields_to_compute_similarity = ["_all"]
        return self.connection.more_like_this(index=index,
                                              doc_type=self.records_doc_type,
                                              id=recid,
                                              mlt_fields=fields_to_compute_similarity)

    def _search_records(self, query=None, index=None, main_options={}, sort_options={},
                        facets={}, highlights={}, facet_filters=[]):
        """Perform search on records.

        It compute:
          - hits
          - metadata facets
          - metadata highlights

        :param query: [nested dict] ES query derived from Invenio query
        :param index: [string] index name
        :param main_options: [nested dict] ES main options such as paging
        :param sort_options: [nested dict] ES sort options
        :param facets: [nested dict] ES facets configuration
        :param highlights: [nested dict] ES highlight configuration
        :param facet_filters: [nested dict] ES facet filters, i.e. when the
            user click on the facet term

        Here is the basic form of the query:
        {
            #here search options such as paging
            "query": {
                "filtered" : {
                    "query": {
                        "bool": {
                            #this is valid for a pure textual query, will
                            #becomes a more complexe query with a Invenio to ES
                            #converter see:
                            #http://pythonhosted.org/Whoosh/parsing.html for
                            #create_create_basic_search_unit
                            #inspiration
                            "should": [{
                                #records query
                            },
                            {
                                #fulltext is on query part as is a part of ranking
                                "has_child": {
                                    "type": "documents",
                                    "query": {#children query}
                                }
                            }],
                            # or condition
                            "minimum_should_match" : 1
                        }
                    }
                },
                "filter": {
                    "bool": {
                        "must": [
                            #facet filters including collection filters using has_child
                        ]
                    }
                }
            },
            "sort": {#sort options},
            "highlights": {#hightlight options},
            "facets": {#facets options without facet_filter as it is done on the query part}

        }
        """
        if not query:
            query = {
                "query": {
                    "match_all": {}
                }
            }
        es_query = {}
        es_query.update(main_options)
        if facet_filters:
            es_query.update({
                "query": {
                    "filtered": {
                        "query": query.get("query"),
                        "filter": {
                            "bool": {
                                "must": facet_filters
                            }
                        }
                    }
                }
            })
        else:
            es_query.update(query)
        es_query.update(sort_options)
        es_query.update(facets)
        es_query.update(highlights)
        results = self.process_results(self.connection.search(es_query,
                                       index=index,
                                       doc_type=self.records_doc_type))
        return (results, es_query)

    def _search_documents(self, query, index, filtered_ids):
        """Preform a search query to extract hilights from documents.

        :param query: [nested dict] ES query derived from Invenio query
        :param index: [string] index name
        :param filtered_ids: [list of int] list of record ids return by the
            records search query

        :return: [object] response

        Here is the basic form of the query:
        {
            "size": 10,
            "fields": [],
            "query": {
                "filtered": {
                    "query": {#fulltext query similar than records query with has_child -> has_parent},
                    "filter": {
                        "ids": {
                            "values": #ids returned by records search
                        }
                    }
                }
            },
            "highlight": {#fulltext highlights config}
        }
        """
        from es_config import get_documents_highlights_config
        documents_query = {
            "size": 10,
            "fields": [],
            "query": {
                "filtered": {
                    "query": {
                        "query_string": {
                            "default_field": "fulltext",
                            "query": query}},
                    "filter": {
                        "ids": {
                            "values": filtered_ids
                        }
                    }
                }
            },
            "highlight": get_documents_highlights_config()
        }

        #submit query for fulltext highlighting
        return self.process_results(self.connection.search(documents_query,
                                    index=index,
                                    doc_type=self.documents_doc_type))

    def _search_collections(self, records_query, index, include_collections):
        """Perform a search query to extract hilights from documents.

        :param records_query: [nested dict] query used to search into records
        :param index: [string] index name
        :param exclude_collections: [list of strings] collection name to exclude to facets

        :return: [object] response

        Here is the basic form of the query:
        {
            #no results only facets/aggregators computation
            "size": 0,
            "query": {
                "has_parent": {
                    "parent_type" : "records",
                    "query": #same as records query
                    },
                },
            "aggs": {
                "collections": {
                    "terms" : {
                        "field" : "name",
                        #options
                        "min_doc_count": 1,
                        "order" : { "_term" : "asc" },
                        }
                    }
                }
        }
        """
        collections_query = {
            "size": 0,
            "query": {
                "has_parent": {
                    "parent_type": "records",
                    "query": records_query.get("query")
                }
            },
            "aggs": {
                "collections": {
                    "terms": {
                        "field": "name",
                        "min_doc_count": 1,
                        "order": {"_term": "asc"}
                    }
                }
            }
        }

        return self.process_results(self.connection.search(collections_query,
                                    index=index,
                                    doc_type=self.collections_doc_type))

    def search(self, query, index=None, cc=None, f="", rg=None,
               sf=None, so="d", jrec=0, facet_filters=[], **kwargs):
        """Perform a search query.

        Note: a lot of work to do.

        :param query: [string] search query
        :param recids: [list of int] recids to index
        :param index: [string] index name
        :param cc: [string] main collection name
        :param f: [string] field to search (not yet used)
        :param rg: [int] number of results to return
        :param sf: [string] sort field
        :param so: [string] sort order in [d,a]
        :param jrec: [int] result offset for paging
        :param facet_filters: [list of tupple of strings] filters to prune the
          results. Each filter is defined as a tupple of term, value: (i.e.
          [("facet_authors", "Ellis, J.")])

        :return: [object] response
        """
        if index is None:
            index = self.app.config['ELASTICSEARCH_INDEX']

        if cc is None:
            cc = self.app.config['CFG_SITE_NAME']

        if rg is None:
            rg = int(self.app.config['CFG_WEBSEARCH_DEF_RECORDS_IN_GROUPS'])
        #converted Invenio query
        es_query = self.process_query(query)

        #search main options
        main_options = {
            "size": rg,
            "from": jrec,
            "fields": []
        }

        # sorting
        sort_options = {}
        if sf:
            sort_options = {
                "sort": [{
                    "sort_%s" % sf: {
                        "order": "desc" if so == "d" else "asc"
                        }
                }]
            }

        # facet_filters
        include_collection = []
        #es_filters = []
        es_filters = [{
            "has_child": {
                "type": self.collections_doc_type,
                "filter": {
                    "term": {
                        "name": {
                            "value": cc
                        }
                    }
                }
            }
        }]
        for ft in facet_filters:
            (term, value) = ft
            if term == "facet_collections":
                include_collection.append(value)
                es_filters.append({
                    "has_child": {
                        "type": self.collections_doc_type,
                        "filter": {
                            "term": {
                                "name": {
                                    "value": value
                                }
                            }
                        }
                    }
                })
            else:
                es_filters.append({
                    "term": {
                        term: value
                    }
                })
        if not include_collection:
            include_collection = [cc]

        # facet configuration
        from es_config import get_records_facets_config
        facets = {
            "aggs": get_records_facets_config()
        }

        # hightlight configuration
        from es_config import get_records_highlights_config
        highlights = {
            "highlight": get_records_highlights_config()
        }

        (results, records_query) = self._search_records(query=es_query, index=index,
                                                        main_options=main_options,
                                                        sort_options=sort_options,
                                                        facets=facets,
                                                        highlights=highlights,
                                                        facet_filters=es_filters)

        #build query for fulltext highlighting
        matched_ids = [recid for recid in results.hits]
        hi_results = self._search_documents(query=query, index=index, filtered_ids=matched_ids)

        #merge with existing metadata highlights
        for recid, hi in hi_results.highlights.iteritems():
            results.highlights.data[int(recid)].update(hi)

        #compute facets for collections
        cols_results = self._search_collections(records_query=records_query,
                                                index=index,
                                                include_collections=include_collection)
        results.facets.update(cols_results.facets)

        return results


def index_record(sender, recid):
    """
    Index a given record.

    Used to connect to signal.

    :param recid: [int] recid to index
    """
    from .tasks import index_records
    return index_records.delay(sender, recid)


def index_collections(sender, collections):
    """
    Index a given ghe collection.

    Used to connect to signal.

    Note: all collections are indexed as it is fast.
    :param collections: [list of string] collection names
    """
    from .tasks import index_collections
    return index_collections.delay(sender, [])


def drop_index(sender, *args, **kwargs):
    """
    Remove the elasticsearch index.

    Used to connect to signal.
    """
    from flask import current_app
    es = current_app.extensions.get("elasticsearch")
    es.delete_index()


def create_index(sender, *args, **kwargs):
    """
    Create the elasticsearch index.

    Index creation, settings and mapping.

    Used to connect to signal.
    """
    from flask import current_app
    es = current_app.extensions.get("elasticsearch")
    es.delete_index()
    es.create_index()


def setup_app(app):
    """Set up the extension for the given app."""
    from es_query import process_es_query, process_es_results
    es = ElasticSearch(app)
    es.set_query_handler(process_es_query)
    es.set_results_handler(process_es_results)

    app.extensions["registry"]["packages"].register("invenio.ext.elasticsearch")
    from invenio.base import signals
    signals.record_after_update.connect(index_record)
    signals.record_after_create.connect(index_record)
    signals.webcoll_after_reclist_cache_update.connect(index_collections)
    from invenio.base.scripts.database import recreate, drop, create
    signals.pre_command.connect(drop_index, sender=drop)
    signals.post_command.connect(create_index, sender=create)
    signals.pre_command.connect(drop_index, sender=recreate)
    signals.post_command.connect(create_index, sender=recreate)
