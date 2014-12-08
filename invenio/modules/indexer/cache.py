# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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

"""Implementation of indexer caches."""

from invenio.legacy.miscutil.data_cacher import DataCacher, DataCacherProxy

from .models import IdxINDEX


class IndexStemmingDataCacher(DataCacher):

    """Provide cache for stemming information for word/phrase indexes.

    This class is not to be used directly; use function
    get_index_stemming_language() instead.
    """

    def __init__(self):
        def cache_filler():
            return dict(IdxINDEX.query.values(IdxINDEX.id,
                                              IdxINDEX.stemming_language))

        def timestamp_verifier():
            from invenio.legacy.dbquery import get_table_update_time
            return get_table_update_time('idxINDEX')

        DataCacher.__init__(self, cache_filler, timestamp_verifier)

index_stemming_cache = DataCacherProxy(IndexStemmingDataCacher)


def get_index_stemming_language(index_id, recreate_cache_if_needed=True):
    """Return stemming langugage for given index."""
    if recreate_cache_if_needed:
        index_stemming_cache.recreate_cache_if_needed()
    return index_stemming_cache.cache[index_id]
