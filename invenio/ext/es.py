# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

"""Simplified Elastic Search integration."""

from __future__ import absolute_import

import json
import six

from elasticsearch import Elasticsearch

from elasticsearch.connection import RequestsHttpConnection

from invenio.base.globals import cfg
from invenio.celery import celery
from invenio.modules.search.api import Query
from invenio.modules.search.registry import mappings

es = None


def get_record_index(record):
    """Decide which index the record should go to."""
    query = 'collection:"{collection}"'
    for collection, index in six.iteritems(
        cfg["SEARCH_ELASTIC_COLLECTION_INDEX_MAPPING"]
    ):
        if Query(query.format(collection=collection)).match(record.json):
            return index


@celery.task
def index_record(recid):
    """Index a record in elasticsearch."""
    from invenio_records.models import RecordMetadata
    record = RecordMetadata.query.get(recid)
    index = get_record_index(record) or cfg['SEARCH_ELASTIC_DEFAULT_INDEX']
    es.index(
        index=index,
        doc_type='record',
        body=record.json,
        id=record.id
    )


@celery.task
def index_collection_percolator(name, dbquery):
    """Create an elasticsearch percolator for a given query."""
    from invenio.modules.search.api import Query
    from invenio.modules.search.walkers.elasticsearch import ElasticSearchDSL
    indices = set(cfg["SEARCH_ELASTIC_COLLECTION_INDEX_MAPPING"].values())
    indices.add(cfg['SEARCH_ELASTIC_DEFAULT_INDEX'])
    for index in indices:
        es.index(
            index=index,
            doc_type='.percolator',
            body={'query': Query(dbquery).query.accept(ElasticSearchDSL())},
            id=name
        )


def create_index(sender, **kwargs):
    """Create or recreate the elasticsearch index for records."""
    indices = set(cfg["SEARCH_ELASTIC_COLLECTION_INDEX_MAPPING"].values())
    indices.add(cfg['SEARCH_ELASTIC_DEFAULT_INDEX'])
    for index in indices:
        mapping = {}
        mapping_filename = index + ".json"
        if mapping_filename in mappings:
            mapping = json.load(open(mappings[mapping_filename], "r"))
        es.indices.delete(index=index, ignore=404)
        es.indices.create(index=index, body=mapping)


def delete_index(sender, **kwargs):
    """Delete the elasticsearch indices for records."""
    indices = set(cfg["SEARCH_ELASTIC_COLLECTION_INDEX_MAPPING"].values())
    indices.add(cfg['SEARCH_ELASTIC_DEFAULT_INDEX'])
    for index in indices:
        es.indices.delete(index=index, ignore=404)


def setup_app(app):
    """Set up the extension for the given app."""
    from invenio.base import signals
    from invenio.base.scripts.database import recreate, drop, create

    from invenio_records.models import RecordMetadata

    from sqlalchemy.event import listens_for

    global es

    es = Elasticsearch(
        app.config.get('ES_HOSTS', None),
        connection_class=RequestsHttpConnection
    )

    signals.pre_command.connect(delete_index, sender=drop)
    signals.pre_command.connect(create_index, sender=create)
    signals.pre_command.connect(delete_index, sender=recreate)
    signals.pre_command.connect(create_index, sender=recreate)

    @listens_for(RecordMetadata, 'after_insert')
    @listens_for(RecordMetadata, 'after_update')
    def new_record(mapper, connection, target):
        index_record.delay(target.id)

    # FIXME add after_delete

    from invenio.modules.collections.models import Collection

    @listens_for(Collection, 'after_insert')
    @listens_for(Collection, 'after_update')
    def new_collection(mapper, connection, target):
        if target.dbquery is not None:
            index_collection_percolator.delay(target.name, target.dbquery)

    # FIXME add after_delete
