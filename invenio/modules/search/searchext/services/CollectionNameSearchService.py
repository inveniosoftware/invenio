# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012 CERN.
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
WebSearch service to search in collection names
"""
import re
import urllib
from invenio.modules.search.services import ListLinksService
from invenio.base.i18n import gettext_set_language
from invenio.legacy.bibindex.engine_stemmer import stem
from invenio.legacy.dbquery import get_table_update_time
from invenio.config import \
     CFG_WEBSEARCH_COLLECTION_NAMES_SEARCH, \
     CFG_SITE_URL, \
     CFG_SITE_NAME, \
     CFG_SITE_LANG, \
     CFG_CERN_SITE

__plugin_version__ = "Search Service Plugin API 1.0"

whitespace_re = re.compile('\s*')
non_alphanum_chars_only_re = re.compile('\W')

class CollectionNameSearchService(ListLinksService):
    """
    Search collection names
    """
    def get_description(self, ln=CFG_SITE_LANG):
        "Return service description"
        return "Return collections of interest based on query"

    def get_label(self, ln=CFG_SITE_LANG):
        "Return label for the list of answers"
        _ = gettext_set_language(ln)
        return _("Looking for a particular collection? Try:")

    def answer(self, req, user_info, of, cc, colls_to_search, p, f, search_units, ln):
        """
        Answer question given by context.

        Return (relevance, html_string) where relevance is integer
        from 0 to 100 indicating how relevant to the question the
        answer is (see C{CFG_WEBSEARCH_SERVICE_MAX_SERVICE_ANSWER_RELEVANCE} for details) ,
        and html_string being a formatted answer.
        """
        from invenio.legacy.search_engine import \
             get_permitted_restricted_collections, \
             get_coll_i18nname, \
             collection_i18nname_cache, \
             collection_restricted_p
        _ = gettext_set_language(ln)
        # stem search units. remove those with field
        # TODO: search in hosted collection names too
        # TODO: ignore unattached trees
        # TODO: use synonyms
        if f or (CFG_WEBSEARCH_COLLECTION_NAMES_SEARCH < 0) or \
               (CFG_WEBSEARCH_COLLECTION_NAMES_SEARCH == 0 and cc != CFG_SITE_NAME):
            return (0, '')

        words = [stem(unit[1], ln) for unit in search_units if unit[2] in ('', 'collection')] # Stemming

        if not words:
            return (0, '')

        permitted_restricted_collections = get_permitted_restricted_collections(user_info)
        cache = self.get_data_cache()

        matching_collections = {}
        for word in words:
            if CFG_CERN_SITE and word == 'cern':
                # This keyword is useless here...
                continue

            colls = cache.get(word.lower(), [])
            for coll in colls:
                if collection_restricted_p(coll) and \
                       not coll in permitted_restricted_collections:
                    # Skip restricted collection user do not have access
                    continue
                if not matching_collections.has_key(coll):
                    matching_collections[coll] = 0
                matching_collections[coll] += 1


        matching_collections_sorted = sorted(matching_collections.iteritems(), key=lambda (k, v): (v, k), reverse=True)
        if not matching_collections_sorted:
            return (0, '')

        matching_collections_names = [(get_coll_i18nname(coll, ln, False), CFG_SITE_URL + '/collection/' + urllib.quote(coll, safe='') + '?ln=en') \
                                      for coll, score in matching_collections_sorted]

        best_score = matching_collections_sorted[0][1]
        best_coll_words = whitespace_re.split(matching_collections_sorted[0][0])

        relevance = min(100, max(0, (100 * float(2 * best_score) /  float(len(best_coll_words) + len(words)) - 10)))

        if (('submit' in p.lower()) or (_('submit') in p.lower())) and \
               not (('submit' in best_coll_words) or (_('submit') in best_coll_words)):
            # User is probably looking for a submission. Decrease relevance
            relevance = max(0, relevance - 30)

        return (relevance, self.display_answer_helper(matching_collections_names, ln))

    def prepare_data_cache(self):
        """
        "Index" collection names
        """
        from invenio.legacy.search_engine import collection_i18nname_cache
        cache = {}
        words_and_coll = [(' '.join([' '.join([stem(word.lower(), ln) for word in \
                                               whitespace_re.split(non_alphanum_chars_only_re.sub(' ', translation))]) for ln, translation in \
                                     translations.iteritems()]), coll_name) for coll_name, translations in \
                          collection_i18nname_cache.cache.iteritems()]
        for words, coll in words_and_coll:
            for word in whitespace_re.split(words):
                if not word.strip():
                    continue
                if not cache.has_key(word):
                    cache[word] = []
                if not coll in cache[word]:
                    cache[word].append(coll)
        return cache

    def timestamp_verifier(self):
        """
        Return the time at which the data was last updated.  If the
        value returned by the function is newer than the cache, the
        cache will be invalidated.

        @return: string-formatted time '%Y-%m-%d %H:%M:%S'
        """
        return max(get_table_update_time('collectionname'),
                   get_table_update_time('collection_collection'))
