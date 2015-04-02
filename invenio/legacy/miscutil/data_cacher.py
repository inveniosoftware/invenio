# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2007, 2008, 2009, 2010, 2011, 2014, 2015 CERN.
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

"""
Tool for caching important infos, which are slow to rebuild, but that
rarely change.
"""

import time

from werkzeug.utils import cached_property

from invenio.legacy.dbquery import run_sql, get_table_update_time


class InvenioDataCacherError(Exception):

    """Error raised by data cacher."""


class DataCacher(object):
    """
    DataCacher is an abstract cacher system, for caching informations
    that are slow to retrieve but that don't change too much during
    time.

    The .timestamp and .cache objects are exposed to clients.  Most
    use cases use a dict internal structure for .cache, but some use
    lists.
    """
    def __init__(self, cache_filler, timestamp_verifier):
        """ @param cache_filler: a function that fills the cache dictionary.
            @param timestamp_verifier: a function that returns a timestamp for
                   checking if something has changed after cache creation.
        """
        self.timestamp = 0 # WARNING: may be exposed to clients
        self.cache = {} # WARNING: may be exposed to clients; lazy
                        # clients may even alter this object on the fly
        if not callable(cache_filler):
            raise InvenioDataCacherError, "cache_filler is not callable"
        self.cache_filler = cache_filler
        if not callable(timestamp_verifier):
            raise InvenioDataCacherError, "timestamp_verifier is not callable"
        self.timestamp_verifier = timestamp_verifier
        self.is_ok_p = True
        self.create_cache()

    def clear(self):
        """Clear the cache rebuilding it."""
        self.create_cache()

    def create_cache(self):
        """
        Create and populate cache by calling cache filler.  Called on
        startup and used later during runtime as needed by clients.
        """
        self.cache = self.cache_filler()
        self.timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    def recreate_cache_if_needed(self):
        """
        Recreate cache if needed, by verifying the cache timestamp
        against the timestamp verifier function.
        """
        if self.timestamp_verifier() > self.timestamp:
            self.create_cache()

class SQLDataCacher(DataCacher):
    """
    SQLDataCacher is a cacher system, for caching single queries and
    their results.
    """
    def __init__(self, query, param=None, affected_tables=()):
        """ @param query: the query to cache
            @param param: its optional parameters as a tuple
            @param affected_tables: the list of tables queried by the query.
        """
        self.query = query
        self.affected_tables = affected_tables
        assert(affected_tables)

        def cache_filler():
            """Standard SQL filler, with results from sql query."""
            return run_sql(self.query, param)

        def timestamp_verifier():
            """The standard timestamp verifier is looking at affected
            tables time stamp."""
            return max([get_table_update_time(table)
                for table in self.affected_tables])

        DataCacher.__init__(self, cache_filler, timestamp_verifier)


class DataCacherProxy(object):

    """Proxy to data cacher."""

    def __init__(self, data_cacher):
        self.data_cacher = data_cacher

    @cached_property
    def _cache(self):
        return self.data_cacher()

    @property
    def is_ok_p(self):
        return self._cache.is_ok_p

    @property
    def cache(self):
        return self._cache.cache

    def recreate_cache_if_needed(self):
        return self._cache.recreate_cache_if_needed()

