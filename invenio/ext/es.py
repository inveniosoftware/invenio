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

from elasticsearch import Elasticsearch

from invenio.celery import celery

es = Elasticsearch()


@celery.task
def index_record(recid):
    from invenio_records.models import RecordMetadata
    record = RecordMetadata.query.get(recid)
    es.index(
        index='records',
        doc_type='record',
        body=record.json,
        id=record.id
    )


def create_index(sender, **kwargs):
    es.indices.create(index='records', ignore=400)


def delete_index(sender, **kwargs):
    es.indices.delete(index='records', ignore=404)


def setup_app(app):
    """Set up the extension for the given app."""
    from invenio.base import signals
    from invenio.base.scripts.database import recreate, drop, create

    from invenio_records.models import RecordMetadata

    from sqlalchemy.event import listens_for

    signals.pre_command.connect(delete_index, sender=drop)
    signals.post_command.connect(create_index, sender=create)
    signals.pre_command.connect(delete_index, sender=recreate)
    signals.post_command.connect(create_index, sender=recreate)

    @listens_for(RecordMetadata, 'after_insert')
    @listens_for(RecordMetadata, 'after_update')
    def new_record(mapper, connection, target):
        index_record.delay(target.id)
