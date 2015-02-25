# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2014 CERN.
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
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.import re

"""Provide the infrastructure to load/query search services."""

import re
from invenio.config import CFG_SITE_LANG
from invenio.modules.knowledge.api import get_kb_mappings
from invenio.legacy.miscutil.data_cacher import DataCacher
from invenio.legacy.bibindex.engine_stemmer import stem
from invenio.legacy.dbquery import get_table_update_time
from invenio.base.i18n import gettext_set_language
from invenio.legacy import template

from . import registry

CFG_WEBSEARCH_SERVICE_MAX_SERVICE_ANSWER_RELEVANCE = 100  # from 0 to 100
"""
The following scale is should be considered by services:

- 100: the service thinks it has found the only answer to the question.
  No other service can find an answer, and no other service will be displayed.

- 90: The service thinks it has found the good answer, probably the one
  expected by the user. However some other services with really good relevance
  might still run.

- 80: The service thinks it has found a good answer

- 50: The service thinks the answer might be useful to the user in some cases

- 30: The service found some answer, which might help the user in some cases

- 20: The service found some answer, but it is unlikely that it will help the
  user.

- 10: The service could not give an answer to the question

- 0: The service could not understand the question
"""

CFG_WEBSEARCH_SERVICE_MAX_RELEVANCE_DIFFERENCE = 30
"""
What is the max distance from the most relevant answer do we still display the
answer from a service? For eg, with
CFG_WEBSEARCH_SERVICE_MAX_RELEVANCE_DIFFERENCE==30 and the most relevant
service returning a relevance of 80, we would still display a service relevant
at 50 or above, but not a service with a relevance below 50
"""

CFG_WEBSEARCH_SERVICE_MIN_RELEVANCE_TO_DISPLAY = 21
"""Consider that a service is not relevant enough to be displayed."""

CFG_WEBSEARCH_SERVICE_MAX_NB_SERVICE_DISPLAY = 2
"""Max number of answers/services to display to the user."""

CFG_WEBSEARCH_MAX_SEARCH_COLL_RESULTS_TO_PRINT = 4
"""
Maximum number of matching collections names to be displayed on the
search results page. All the rest of the collections will be hidden
by a "See more collections" link.
"""


# Base class
class SearchService:

    """Abstract base class for search services.

    New services should subclass this class, and:
      - Override L{get_decription} to specify service description
      - Override L{prepare_data_cache} to prepare some cache needed for answers
      - Override L{timestamp_verifier} to indicate if cache must be refreshed
      - Override L{answer} to return answer (score, html_string)

    Services that inherits directly from this class are fully
    responsible for displaying the output. See also
    L{ListLinksService} and L{KnowledgeBaseService}
    """

    cache = None

    def get_description(self, ln=CFG_SITE_LANG):
        """Return service description.

        :rtype: string
        """
        return ""

    def prepare_data_cache(self):
        """Helper function to cache some data.

        If you need to pre-process some data and fill a cache,
        overrides this method and return the data to be cached. You
        can invalidate this data by overridding method
        L{timestamp_verifier} and retrieve the data from
        L{get_data_cache}.
        """
        return None

    def timestamp_verifier(self):
        """Return the time at which your data was last updated.

        If the value returned by the function is newer than the cache, the
        cache will be invalidated.

        :return: string-formatted time '%Y-%m-%d %H:%M:%S'
        """
        return lambda x: 0

    def answer(self, req, user_info, of, cc, colls_to_search, p, f,
               search_units, ln):
        """Answer question given by context.

        Returns (relevance, html_string) where relevance is integer
        from 0 to 100 indicating how relevant to the question the
        answer is (see L{CFG_WEBSEARCH_SERVICE_MAX_SERVICE_ANSWER_RELEVANCE}
        for details), and html_string being an HTML-formatted answer.

        @rtype: tuple(int, string)
        """
        return (0, "")

    def get_data_cache(self, recreate_cache_if_needed=True):
        """Return always up-to-date data from cache.

        The returned value depends on the what has been stored with
        :meth:`~SearchService.prepare_data_cache`.

        :param recreate_cache_if_needed: if True, force refreshing data cache.
        """
        try:
            self.__class__.cache.is_ok_p
        except Exception:
            self.__class__.cache = DataCacher(self.prepare_data_cache,
                                              self.timestamp_verifier)
        if recreate_cache_if_needed:
            self.__class__.cache.recreate_cache_if_needed()

        return self.__class__.cache.cache


# List display service
class ListLinksService(SearchService):
    """
    Abstract class for services that displays an inline list of links
    as answers.

    In order to provide a service that returns a list of answers in a
    standardized way, subclass this class and:
      - Override L{get_decription} to specify service description
      - Override L{prepare_data_cache} to prepare some cache needed for answers
      - Override L{timestamp_verifier} to indicate if cache must be refreshed
      - Override L{answer} to return answer (score, html_string)
      - Override L{get_label} to specify service output label

    Services that inherits this class can make use of
    L{self.display_answer_helper} function to format the response in
    L{answer} function.

    See also L{KnowledgeBaseService}.
    """
    def get_label(self, ln=CFG_SITE_LANG):
        """
        Return label displayed next to the service responses.

        @rtype: string
        """
        return ""

    def display_answer_helper(self, labels_and_urls, ln=CFG_SITE_LANG):
        """Display HTML to return an answer as HTML.

        Use this function to process your list of response and return
        an HTML-formatted string in your L{answer} function.

        :param labels_and_urls: list of answers in the form (label, URL)
        :param ln: the language in which is used to answer
        :return: HTML-formatted string
        """
        websearch_templates = template.load('websearch')
        label = self.get_label(ln=ln)
        return websearch_templates.tmpl_print_service_list_links(
            label, labels_and_urls, ln=ln)


# KnowledgeBase type service
class KnowledgeBaseService(ListLinksService):

    """Abstract class for Knowledge Base based services.

    In order to provide a service that returns a list of answers in a
    standardized way using a Knowledge Basee, subclass this class and:
      - Override L{get_decription} to specify service description
      - Override L{get_label} to specify service output label
      - Override L{get_kbname} to specify knowledge base to consider

    The answer is retrieved from the knowledge base defined by
    L{get_kbname}, and must map a list of whitespace-separated
    words to an answer in the form "label|url". See for eg. KB 'FAQ'.
    """

    def get_kbname(self):
        """Return name of the knowledge base to use for answering.

        The knowedge base should be defined in BibKnowledge, and must
        map a list of whitespace-separated words to an answer in the
        form C{label|url}.

        @rtype: string
        """
        return ""

    def answer(self, req, user_info, of, cc, colls_to_search, p, f,
               search_units, ln):
        """Answer question given by context, using knowledge base.

        Return (relevance, html_string) where relevance is integer
        from 0 to 100 indicating how relevant to the question the
        answer is (see L{CFG_WEBSEARCH_SERVICE_MAX_SERVICE_ANSWER_RELEVANCE}
        for details), and html_string being a formatted answer.
        """
        _ = gettext_set_language(ln)
        # words = [stem(unit[1], ln) for unit in search_units if unit[2] == '']
        words = [stem(unit[1].lower(), CFG_SITE_LANG) for unit in search_units
                 if unit[2] == '']
        cache = self.get_data_cache()

        matching_values = {}
        for word in words:
            res = cache.get(word, [])
            for keyword in res:
                if keyword not in matching_values:
                    matching_values[keyword] = 1
                else:
                    matching_values[keyword] += 1

        # order matching values per score
        matching_values_sorted = sorted(matching_values.iteritems(),
                                        key=lambda (k, v): (v, k),
                                        reverse=True)

        if not matching_values_sorted:
            return (0, '')

        best_score = matching_values_sorted[0][1]

        # Compute relevance. How many words from query did match
        relevance = min(100, max(
            0, (100 * float(best_score) / len(
                [word for word in words if len(word) > 3]
            )) - 10))
        labels_and_links = [m.split("|", 1) for m in matching_values.keys()]
        translated_labels_and_links = [(_(label), url)
                                       for label, url in labels_and_links]

        return (relevance, self.display_answer_helper(
            translated_labels_and_links, ln))

    def prepare_data_cache(self):
        """*Index* knowledge base and cache it."""
        cache = {}
        for mapping in get_kb_mappings(self.get_kbname()):
            key = mapping['key']
            value = mapping['value']
            words = clean_and_split_words_and_stem(key, CFG_SITE_LANG,
                                                   stem_p=True)
            for word in words:
                if word not in cache:
                    cache[word] = []
                if value not in cache[word]:
                    cache[word].append(value)
        return cache

    def timestamp_verifier(self):
        """Return the time at which the data was last updated.

        If the value returned by the function is newer than the cache, the
        cache will be invalidated.

        :return: string-formatted time ``'%Y-%m-%d %H:%M:%S'``
        """
        # This is an approximation...
        return get_table_update_time('knwKBRVAL')

re_split_words_pattern = re.compile('\s*')
re_non_alphanum_only = re.compile('\W')


def clean_and_split_words_and_stem(string, ln=CFG_SITE_LANG, stem_p=True):
    """Split and stemp words in a string.

    :param ln: language to consider for stemming
    :param stem_p: if True, also stem the word according to ``ln``
    :return: list of (stemmed) word.
    """
    alphanum_string = re_non_alphanum_only.sub(" ", string).lower()
    words = re_split_words_pattern.split(alphanum_string)
    if stem_p:
        # lowering must be done after stemming
        words = [stem(word, ln) for word in words]

    return words


def get_answers(req, user_info, of, cc, colls_to_search, p, f, ln):
    """Return answers from all registered search services."""
    if p:
        from invenio.legacy.search_engine import create_basic_search_units
        search_units = create_basic_search_units(req, p, f)
    else:
        search_units = []

    def search_service_answers():
        for search_service in registry.services:
            yield search_service.answer(req, user_info, of, cc,
                                        colls_to_search, p, f,
                                        search_units, ln)

    nb_answers = 0
    best_relevance = None

    for answer_relevance, answer_html in sorted(
            search_service_answers(), reverse=True):
        nb_answers += 1
        if best_relevance is None:
            best_relevance = answer_relevance
        if best_relevance <= CFG_WEBSEARCH_SERVICE_MIN_RELEVANCE_TO_DISPLAY:
            # The answer is not relevant enough
            break
        if nb_answers > CFG_WEBSEARCH_SERVICE_MAX_NB_SERVICE_DISPLAY:
            # We have reached the max number of service to display
            break
        if best_relevance - answer_relevance > \
                CFG_WEBSEARCH_SERVICE_MAX_RELEVANCE_DIFFERENCE:
            # The service gave an answer that is way less good than previous
            # ones.
            break
        yield answer_relevance, answer_html

        if answer_relevance == \
                CFG_WEBSEARCH_SERVICE_MAX_SERVICE_ANSWER_RELEVANCE:
            # The service assumes it has given the definitive answer
            break
