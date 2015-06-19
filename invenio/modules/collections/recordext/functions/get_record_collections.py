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

"""Record field function."""

from six import iteritems

from invenio.modules.search.api import Query
from invenio.utils.datastructures import LazyDict

COLLECTIONS_DELETED_RECORDS = '{dbquery} AND NOT collection:"DELETED"'


def _queries():
    """Preprocess collection queries."""
    from invenio.ext.sqlalchemy import db
    from invenio.modules.collections.models import Collection
    return dict(
        (collection.name, dict(
            query=Query(COLLECTIONS_DELETED_RECORDS.format(
                dbquery=collection.dbquery)
            ),
            ancestors=set(c.name for c in collection.ancestors
                          if c.dbquery is None)
        ))
        for collection in Collection.query.filter(
            Collection.dbquery != None,
            db.not_(Collection.dbquery.like('hostedcollection:%'))
        ).all()
    )

queries = LazyDict(_queries)


def get_record_collections(record):
    """Return list of collections to which record belongs to.

    :record: Record instance
    :returns: list of collection names
    """
    output = set()
    for name, data in iteritems(queries):
        if data['query'].match(record):
            output.add(name)
            output |= data['ancestors']
    return list(output)
