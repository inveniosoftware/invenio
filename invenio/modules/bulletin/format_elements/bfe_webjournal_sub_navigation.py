# -*- coding: utf-8 -*-
# $Id: bfe_webjournal_CERNBulletinSubNavigation.py,v 1.13 2009/02/12 10:00:57 jerome Exp $
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
WebJournal element - Displays vertical subnavigation menu in detailed
article pages.
"""
from invenio.modules.formatter.engine import BibFormatObject
from invenio.base.i18n import gettext_set_language
from invenio.legacy.webjournal.utils import \
     parse_url_string, \
     make_journal_url, \
     get_journal_articles,\
     get_journal_categories

def format_element(bfo, new_articles_first='yes',
           subject_to_css_class_kb="WebJournalSubject2CSSClass",
           display_all_category_articles='no'):
    """
    Creates a navigation for articles in the same issue and category.

    @param new_articles_first: if 'yes', display new articles before other articles
    @param subject_to_css_class_kb: knowledge base that maps 595__a to a CSS class
    @param display_all_category_articles: if yes, display all articles, whatever category is selected
    """
    # get variables
    args = parse_url_string(bfo.user_info['uri'])
    this_recid = bfo.control_field('001')
    this_issue_number = args["issue"]
    category_name = args["category"]
    journal_name = args["journal_name"]
    ln = bfo.lang
    _ = gettext_set_language(ln)

    this_title = ""
    if ln == "fr":
        if bfo.fields('246_1a'):
            this_title = bfo.fields('246_1a')[0]
        elif bfo.fields('245__a'):
            this_title = bfo.fields('245__a')[0]
    else:
        if bfo.fields('245__a'):
            this_title = bfo.fields('245__a')[0]
        elif bfo.fields('246_1a'):
            this_title = bfo.fields('246_1a')[0]

    journal_categories = [category_name]
    if display_all_category_articles.lower() == 'yes':
        # Let's retrieve all categories. Ok, we are not supposed to do
        # that with that element, but if journal editor wants...
        journal_categories = get_journal_categories(journal_name,
                                                    this_issue_number)

    menu_out = ''

    for category in journal_categories:
        ordered_articles = get_journal_articles(journal_name,
                                                this_issue_number,
                                                category,
                                                newest_first=new_articles_first.lower() == 'yes')

        new_articles_only = False
        if ordered_articles.keys() and max(ordered_articles.keys()) < 0:
            # If there are only new articles, don't bother marking them as
            # new
            new_articles_only = True

        menu_out += '<div class="subNavigationMenu">'
        order_numbers = ordered_articles.keys()
        order_numbers.sort()
        for order_number in order_numbers:
            for article_id in ordered_articles[order_number]:
                # A record is considered as new if its position is
                # negative and there are some non-new articles
                article_is_new = (order_number < 0 and not new_articles_only)

                if str(article_id) == this_recid:
                    # Mark as active

                    # Get CSS class (if relevant)
                    notes = bfo.fields('595__a')
                    css_classes = [bfo.kb(subject_to_css_class_kb, note, None) \
                                   for note in notes]
                    css_classes = [css_class for css_class in css_classes \
                                   if css_class is not None]

                    if article_is_new:
                        css_classes.append('new')

                    separator = bfo.field('594__a')
                    if separator == "YES":
                        menu_out += '''<hr/>'''

                    menu_out += '''<div class="active">
            <div class="subNavigationMenuItem %s">%s</div></div>''' % \
                    (' '.join(css_classes),
                     this_title)

                else:
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

                    separator = temp_rec.field('594__a')
                    if separator == "YES":
                        menu_out += '''<hr/>'''

                    menu_out += '''<div class="subNavigationMenuItem %s">
                    <a href="%s">%s</a></div>
                    ''' % (' '.join(css_classes),
                           make_journal_url(bfo.user_info['uri'],
                                            {'recid': article_id,
                                             'ln': bfo.lang,
                                             'category': category}),
                           title)

        menu_out += '</div>'

    return menu_out

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
