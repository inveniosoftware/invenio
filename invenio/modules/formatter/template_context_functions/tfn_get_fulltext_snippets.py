# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014, 2015 CERN.
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

"""Template context function to get fulltext snippets via Solr."""

from invenio.config import CFG_WEBSEARCH_FULLTEXT_SNIPPETS
from invenio.ext.cache import cache
from invenio.ext.logging import register_exception
from invenio.modules.formatter.utils import get_pdf_snippets
from invenio.modules.search.cache import get_pattern_from_cache


@cache.memoize(timeout=5)
def get_fulltext_terms_from_search_pattern(search_pattern):
    """Return fulltext terms from search pattern."""
    from invenio.modules.search.api import Query
    return Query(search_pattern).terms(keywords=['fulltext'])


def template_context_function(id_bibrec, pattern, qid, current_user):
    """Return fulltext snippets.

    :param id_bibrec: ID of record
    :param pattern: search pattern
    :param current_user: user object
    :param qid: query id
    :return: HTML containing snippet
    """

    if not pattern:
        pattern = get_pattern_from_cache(qid)

    if id_bibrec and pattern and current_user:
        # Requires search in fulltext field
        if CFG_WEBSEARCH_FULLTEXT_SNIPPETS and 'fulltext:' in pattern:
            terms = get_fulltext_terms_from_search_pattern(pattern)
            if terms:
                snippets = ''
                try:
                    snippets = get_pdf_snippets(
                        id_bibrec, terms, current_user).decode('utf8')
                    if snippets:
                        return ' ... ' + snippets + ' ... '
                except:
                    register_exception()
                return ''
        else:
            return ''
    else:
        return None
