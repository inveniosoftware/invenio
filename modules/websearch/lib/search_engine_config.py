## This file is part of Invenio.
## Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2010, 2011, 2012 CERN.
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

"""Invenio Search Engine config parameters."""

__revision__ = \
    "$Id$"

## Note: many interesting search engine config variables are defined
## in the global config.py.  This file should define locally
## interesting variables only.

## do we want experimental features? (0=no, 1=yes)
CFG_EXPERIMENTAL_FEATURES = 0

## CFG_WEBSEARCH_IDXPAIRS_FIELDS -- a comma separated list of index
## fields. This list contains all the index fields on which exact
## phrase search should use idxPairs tables.
CFG_WEBSEARCH_IDXPAIRS_FIELDS = ['global','abstract','title','caption']

## CFG_WEBSEARCH_IDXPAIRS_EXACT_SEARCH -- if true, it will eliminate
## all the false positives when using the word pairs for search.
## (Example: `foo bar baz' being search as `foo bar' and `bar baz' may
## lead to false positives if there is no second-pass.)  FIXME: we
## need this to be defined per index if we want to eliminate
## single-quoted vs double-quoted search difference, e.g. False for
## title search, but True for report number search.
CFG_WEBSEARCH_IDXPAIRS_EXACT_SEARCH = False

## Maximum number of collections to be displayed on the search results
## page. All the rest of the collections will be hidden by a
## "See more collections" link.
CFG_WEBSEARCH_RESULTS_OVERVIEW_MAX_COLLS_TO_PRINT = 10

class InvenioWebSearchUnknownCollectionError(Exception):
    """Exception for bad collection."""
    def __init__(self, colname):
        """Initialisation."""
        self.colname = colname
    def __str__(self):
        """String representation."""
        return repr(self.colname)

class InvenioWebSearchWildcardLimitError(Exception):
    """Exception raised when query limit reached."""
    def __init__(self, res):
        """Initialization."""
        self.res = res

class InvenioWebSearchReferstoLimitError(Exception):
    """
    Exception raised when CFG_WEBSEARCH_MAX_RECORDS_REFERSTO limit is reached.
    """
    def __init__(self, res):
        """Initialization."""
        self.res = res

class InvenioWebSearchCitedbyLimitError(Exception):
    """
    Exception raised when CFG_WEBSEARCH_MAX_RECORDS_CITEDBY limit is reached.
    """
    def __init__(self, res):
        """Initialization."""
        self.res = res
