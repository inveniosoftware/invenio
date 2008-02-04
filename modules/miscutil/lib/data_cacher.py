# -*- coding: utf-8 -*-
## $Id$

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Tool for caching important infos, which are slow to rebuild, but that rarely
   change"""

from invenio.dbquery import run_sql, get_table_update_time
import time

class CacherError(Exception):
    """Error raised by data cacher"""
    pass

class DataCacher:
    """ DataCacher is an abstract cacher system, for caching informations
    that are slow to retrieve but that don't change too much during time."""
    def __init__(self, cache_filler, timestamp_getter):
        """ @param cache_filler a function that receives the cache dictionary.
            @param timestamp_getter a function that returns a timestamp for
            checking if something has changed after cache creation.
        """
        self.timestamp = 0
        self.cache = {}
        if not callable(cache_filler):
            raise CacherError, "cache_filler is not callable"
        self.cache_filler = cache_filler
        if not callable(timestamp_getter):
            raise CacherError, "timestamp_getter is not callable"
        self.timestamp_getter = timestamp_getter
        self.is_ok_p = True
        self.create_cache()

    def clear(self):
        """ Clear the cache rebuilding it"""
        self.create_cache()

    def create_cache(self):
        """Create cache. Called on startup and used later during the search
        time."""
        # populate field I18 name cache:
        self.cache = self.cache_filler()
        self.timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    def get_cache(self):
        """ Obtain an uptodate cache."""
        if self.timestamp_getter() > self.timestamp:
            self.create_cache()
        return self.cache

class SQLDataCacher(DataCacher):
    """ SqlDataCacher is a cacher system, for caching single queries and
    their results."""
    def __init__(self, query, param=None, affected_tables=()):
        """ @param query the query to cache
            @param param its optional parameters as a tuple
            @param affected_tables the list of tables queried by the query.
        """
        self.query = query
        self.affected_tables = affected_tables
        assert(affected_tables)
        def cache_filler():
            """Standard SQL filler, with results from sql query."""
            return run_sql(self.query, param)

        def timestamp_getter():
            """Standard timestamp getter from affected tables by query."""
            return max([get_table_update_time(table)
                for table in self.affected_tables])
        DataCacher.__init__(self, cache_filler, timestamp_getter)



