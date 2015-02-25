# -*- coding: utf-8 -*-
# $Id: bfe_webjournal_MainArticleOverview.py,v 1.28 2009/02/12 10:00:57 jerome Exp $
#
# This file is part of Invenio.
# Copyright (C) 2009, 2010, 2011 CERN.
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
WebJournal Element - Creates an overview of all the articles of a
certain category in one specific issue.
"""
from invenio.modules.formatter.engine import BibFormatObject
from invenio.base.i18n import gettext_set_language
from invenio.config import CFG_ACCESS_CONTROL_LEVEL_SITE
from invenio.legacy.webjournal.utils import \
     parse_url_string, \
     get_journal_articles, \
     cache_index_page, \
     get_index_page_from_cache, \
     get_journal_categories, \
     issue_is_later_than, \
     get_current_issue

def format_element(bfo, new_articles_first='yes',
           subject_to_css_class_kb="WebJournalSubject2CSSClass",
           display_all_category_articles='no', display_category_title='no'):
    """
    List all articles one after the other, on the same page.

    Similar to bfe_webjournal_articles_overview, but displays full articles.

    Note that you cannot use both bfe_webjournal_articles_overview and
    bfe_webjournal_articles: you have to choose one of them, as they
    use the same cache location (It would also not make sense to use
    both...).

    @param new_articles_first: if 'yes', display new articles before other articles
    @param subject_to_css_class_kb: knowledge base that maps 595__a to a CSS class
    @param display_all_category_articles: if yes, display all articles, whatever category is selected
    @param display_category_title: if yes, display category title (useful if display_all_category_articles is enabled)

    @see: bfe_webjournal_articles_overview.py
    """
    args = parse_url_string(bfo.user_info['uri'])
    journal_name = args["journal_name"]
    this_issue_number = args["issue"]
    category_name = args["category"]
    verbose = args["verbose"]
    ln = bfo.lang
    _ = gettext_set_language(ln)

    # Try to get the page from cache. Only if issue is older or equal
    # to latest release.
    latest_released_issue = get_current_issue(ln, journal_name)
    if verbose == 0 and not issue_is_later_than(this_issue_number,
                                                latest_released_issue):
        cached_html = get_index_page_from_cache(journal_name, category_name,
                                                this_issue_number, ln)
        if cached_html:
            return cached_html

    # Shall we display current category, or all?
    categories = [category_name]
    if display_all_category_articles.lower() == 'yes':
        categories = get_journal_categories(journal_name,
                                            this_issue_number)

    out = ''
    for category_name in categories:
        if display_category_title.lower() == 'yes':
            out += '<h2>' + _(category_name) + '</h2>'

        out += '<table border="0" cellpadding="0" cellspacing="0">'
        # Get the id list
        ordered_articles = get_journal_articles(journal_name,
                                                this_issue_number,
                                                category_name,
                                                newest_first=new_articles_first.lower() == 'yes')
        new_articles_only = False
        if ordered_articles.keys() and max(ordered_articles.keys()) < 0:
            # If there are only new articles, don't bother marking them as
            # new
            new_articles_only = True

        order_numbers = ordered_articles.keys()
        order_numbers.sort()

        for order_number in order_numbers:
            for article_id in ordered_articles[order_number]:
                # A record is considered as new if its position is
                # negative and there are some non-new articles
                article_is_new = (order_number < 0 and not new_articles_only)

                temp_rec = BibFormatObject(article_id)
                title = ''
                if ln == "fr":
                    title = temp_rec.field('246_1a')
                    if title == '':
                        title = temp_rec.field('245__a')
                else:
                    title = temp_rec.field('245__a')
                    if title == '':
                        title = temp_rec.field('246_1a')

                # Get CSS class (if relevant)
                notes = temp_rec.fields('595__a')
                css_classes = [temp_rec.kb(subject_to_css_class_kb, note, None) \
                               for note in notes]
                css_classes = [css_class for css_class in css_classes \
                               if css_class is not None]

                if article_is_new:
                    css_classes.append('new')

                # Finally create the output. Two different outputs
                # depending on if we have text to display or not
                text = []
                if ln == "fr":
                    text = temp_rec.fields('590__b')
                    if not text or \
                           (len(text) == 1 and \
                            (text[0].strip() in ['', '<br />', '<!--HTML--><br />'])):
                        text = temp_rec.fields('520__b')
                else:
                    text = temp_rec.fields('520__b')
                    if not text or \
                           (len(text) == 1 and \
                            (text[0].strip() in ['', '<br />', '<!--HTML--><br />'])):
                        text = temp_rec.fields('590__b')
                text = '<br/>'.join(text)


                out += '''
                            <tr><td class="article">
                               <h%(header_tag_size)s class="%(css_classes)s articleTitle" style="clear:both;">
                                   %(title)s
                               </h%(header_tag_size)s>
                               <div class="articleBody">
                                   <div class="articleText">
                                      %(text)s
                                   </div>
                               </div>
                           </td></tr>
                        ''' % {'title': title,
                               'text': text,
                               'header_tag_size': (display_category_title.lower() == 'yes') and '3' or '2',
                               'css_classes': ' '.join(css_classes)}
        out += '</table>'

    if verbose == 0 and not CFG_ACCESS_CONTROL_LEVEL_SITE == 2 :
        cache_index_page(out, journal_name, category_name,
                         this_issue_number, ln)

    return out

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0

