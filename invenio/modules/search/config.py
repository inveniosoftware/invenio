# -*- coding: utf-8 -*-
#
## This file is part of Invenio.
## Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2010, 2011, 2012, 2013 CERN.
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

## Prefix used for search results cache.
CFG_SEARCH_RESULTS_CACHE_PREFIX = "search_results::"

## CERN Site hack
#CFG_WEBSEARCH_SEARCH_WITHIN = ['title',
#                               'author',
#                               'abstract',
#                               'report number,
#                               'year']

CFG_WEBSEARCH_SEARCH_WITHIN = ['title',
                               'author',
                               'abstract',
                               'keyword',
                               'report number',
                               'journal',
                               'year',
                               'fulltext',
                               'reference']


CFG_WEBSEACH_MATCHING_TYPES = [
        {
        'code': 'a',
        'title': "all of the words",
        'order': 1,
        'tokenize': """
            var vals = val.split(' '),
                result = $.map(vals, function(e) {
              return f+e;
            }).join(' AND ');
            if (vals.length > 1) {
                result = '(' + result +')';
            }
            return result;
        """
        },
        {
        'code': 'o',
        'title': "any of the words",
        'order': 2,
        'tokenize': """
            var vals = val.split(' '),
                result = $.map(vals, function(e) {
              return f+e;
            }).join(' OR ');
            if (vals.length > 1) {
                result = '(' + result +')';
            }
            return result;
        """
        },
        {
        'code': 'e',
        'title': "exact phrase",
        'order': 3,
        'tokenize': """
            return f+'"'+val+'"';
        """
        },
        {
        'code': 'p',
        'title': "partial phrase",
        'order': 4,
        'tokenize': """
            return f+"'"+val+"'";
        """
        },
        {
        'code': 'r',
        'title': "regular expression",
        'order': 5,
        'tokenize': """
            return f+'/'+val+'/';
        """
        }
    ]
