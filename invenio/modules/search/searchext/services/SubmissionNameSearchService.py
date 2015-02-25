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
WebSearch service to search in submission names
"""
import re
import cgi
from invenio.modules.search.services import ListLinksService, clean_and_split_words_and_stem
from invenio.legacy.dbquery import run_sql
from invenio.base.i18n import gettext_set_language
from invenio.legacy.bibindex.engine_stemmer import stem
from invenio.legacy.dbquery import get_table_update_time
from invenio.config import \
     CFG_WEBSEARCH_COLLECTION_NAMES_SEARCH, \
     CFG_SITE_URL, \
     CFG_SITE_NAME, \
     CFG_SITE_LANG, \
     CFG_CERN_SITE
from invenio.legacy.webuser import isGuestUser
from invenio.modules.access.engine import acc_authorize_action
from invenio.utils.html import nmtoken_from_string

if CFG_CERN_SITE:
    try:
        from invenio.legacy.websubmit.functions.GENSBM_config import SUBMISSIONS_CONFIG as CERN_GENSBM_SUBMISSIONS_CONFIG
    except:
        CERN_GENSBM_SUBMISSIONS_CONFIG = {}
__plugin_version__ = "Search Service Plugin API 1.0"

whitespace_re = re.compile('\s*')
non_alphanum_chars_only_re = re.compile('\W')

class SubmissionNameSearchService(ListLinksService):
    """
    Search submission names
    """

    def get_description(self, ln=CFG_SITE_LANG):
        "Return service description"
        return "Return submissions of interest based on query"

    def get_label(self, ln=CFG_SITE_LANG):
        "Return label for the list of answers"
        _ = gettext_set_language(ln)
        return _("Looking for a particular submission? Try:")

    def answer(self, req, user_info, of, cc, colls_to_search, p, f, search_units, ln):
        """
        Answer question given by context.

        Return (relevance, html_string) where relevance is integer
        from 0 to 100 indicating how relevant to the question the
        answer is (see C{CFG_WEBSEARCH_SERVICE_MAX_SERVICE_ANSWER_RELEVANCE} for details) ,
        and html_string being a formatted answer.
        """
        _ = gettext_set_language(ln)
        if f or (CFG_WEBSEARCH_COLLECTION_NAMES_SEARCH < 0) or \
               (CFG_WEBSEARCH_COLLECTION_NAMES_SEARCH == 0 and cc != CFG_SITE_NAME):
            return (0, '')

        words = [stem(unit[1].lower(), CFG_SITE_LANG) for unit in search_units if unit[2] == '']

        if not words:
            return (0, '')

        cache = self.get_data_cache()

        # TODO: If all categories of a submission match, display only submission (not categories)

        matching_submissions = {}

        for word in words:
            # Look for submission names
            if CFG_CERN_SITE and word == 'cern':
                # This keyword is useless here...
                continue

            submissions = cache.get(word, [])
            for doctype, submission_label, category in submissions:
                if acc_authorize_action(req, 'submit', \
                                        authorized_if_no_roles=not isGuestUser(user_info['uid']), \
                                        doctype=(CFG_CERN_SITE and doctype.startswith('GENSBM#') and 'GENSBM') or doctype,
                                        categ=category)[0] != 0:
                    # Not authorized to submit in this submission
                    continue

                if not matching_submissions.has_key((doctype, submission_label)):
                    matching_submissions[(doctype, submission_label)] = 0
                add_score = 1
                if category != '*':
                    # This is the submission category, consider that
                    # words that are part of the submission name are
                    # less important than others here:
                    if not word.lower() in category.lower():
                        # word is only in submission name
                        add_score = 0.5
                    else:
                        add_score = 1.5

                matching_submissions[(doctype, submission_label)] += add_score

        matching_submissions_sorted = sorted(matching_submissions.iteritems(), key=lambda (k, v): (v, k), reverse=True)
        if not matching_submissions_sorted:
            return (0, '')
        best_score = matching_submissions_sorted[0][1]
        max_score_difference = 1.9

        matching_submissions_names = [(submission_label, \
                                       CFG_SITE_URL + '/submit?doctype=' + doctype.split("#", 1)[0] + '&ln=' + ln + (CFG_CERN_SITE and doctype.startswith('GENSBM#') and '#' + doctype.split("#", 1)[-1] or '') ) \
                                      for (doctype, submission_label), score in matching_submissions_sorted if score > best_score - max_score_difference]

        best_sbm_words = whitespace_re.split(matching_submissions_sorted[0][0][1])

        score_bonus = (((_("Submit").lower() in words) or ("submit" in words)) or \
                       ((_("Revise").lower() in words) or ("revise" in words)) or \
                       ((_("Modify").lower() in words) or ("modify" in words))) and 40 or 0
        relevance = min(100, max(0,  (score_bonus + (100 * float(best_score)  /  float(len(best_sbm_words) + len(words)))) - 10))

        return (relevance, self.display_answer_helper(matching_submissions_names, ln))

    def prepare_data_cache(self):
        """
        "Index" submission names
        """
        from invenio.legacy.websubmit.db_layer import get_categories_of_doctype
        res = run_sql("SELECT sdocname, ldocname FROM sbmDOCTYPE")

        # TODO: only consider submissions that are attached to the tree

        if CFG_CERN_SITE:
            for submission_name, submission_config in CERN_GENSBM_SUBMISSIONS_CONFIG.iteritems():
                if not submission_config.has_key('redirect'):
                    res += (('GENSBM#' + nmtoken_from_string(cgi.escape(submission_name)), submission_name),)

        cache = {}
        for doctype, submission_name in res:
            ## categories_and_submission_name = ' '.join(get_categories_of_doctype(doctype)) + \
            ##                                  ' ' + submission_name


            # Add submission name info
            if CFG_CERN_SITE and doctype in ('ALIPH', 'BULIS', 'CMSREL', 'BULBN', 'BSA'):
                # These submissions are not interesting here
                continue
            for word in clean_and_split_words_and_stem(submission_name):
                if not word.strip():
                    continue
                if not cache.has_key(word):
                    cache[word] = []
                item = (doctype, submission_name, '*')
                if not item in cache[word]:
                    cache[word].append(item)

            # Add submission categories info
            if CFG_CERN_SITE and doctype in ('CMSPUB', 'CMSCOM', 'CMSCMC',
                                             'ATLPUB', 'ATLCOM', 'ATLCMC',
                                             'LHCBPB', 'LHCPCM', 'LHCBCC'):
                # These categories are not interesting here
                continue
            categories = get_categories_of_doctype(doctype)
            for dummy, category, dummy in categories:
                for word in clean_and_split_words_and_stem(submission_name + ' ' + category):
                    if not word.strip():
                        continue
                    if not cache.has_key(word):
                        cache[word] = []
                    item = (doctype, "%s (%s)" % (category, submission_name), category)
                    if not item in cache[word]:
                        cache[word].append(item)

        return cache

    def timestamp_verifier(self):
        """
        Return the time at which the data was last updated.  If the
        value returned by the function is newer than the cache, the
        cache will be invalidated.

        @return: string-formatted time '%Y-%m-%d %H:%M:%S'
        """
        return get_table_update_time('sbmDOCTYPE')
