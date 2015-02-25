# -*- coding: utf-8 -*-
# $Id: bfe_webjournal_CERNBulletinMainNavigation.py,v 1.10 2008/06/03 09:52:11 jerome Exp $
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
WebJournal element - Prints main (horizontal) navigation menu
"""
from invenio.legacy.webjournal.utils import \
     parse_url_string, \
     make_journal_url, \
     get_journal_categories
from invenio.utils.url import create_html_link
from invenio.base.i18n import gettext_set_language

def format_element(bfo, category_prefix, category_suffix, separator=" | ",
           display_all_categories='no'):
    """
    Creates the main navigation menu of the journal

    @param category_prefix: value printed before each category
    @param category_suffix: value printed after each category
    @param separator: value printed between each category
    @param display_all_categories: if 'yes', show categories even when there is no corresponding article
    """
    # Retrieve context (journal, issue and category) from URI
    args = parse_url_string(bfo.user_info['uri'])
    journal_name = args["journal_name"]
    selected_category = args["category"]
    this_issue_number = args["issue"]
    ln = bfo.lang
    _ = gettext_set_language(ln)

    # Retrieve categories for this journal and issue
    journal_categories = get_journal_categories(journal_name,
                                                display_all_categories.lower() != 'yes' and \
                                                this_issue_number or None)

    # Build the links to categories
    categories_links = []
    for category in journal_categories:
        # Create URL
        category_url = make_journal_url(bfo.user_info['uri'],
                                        {'category': category,
                                         'recid': '',
                                         'ln': bfo.lang})
        # Create HTML link
        linkattrd = {}
        if category.lower() == selected_category.lower():
            linkattrd = {'class':'selectedNavigationPage'}
        if journal_name == 'CERNBulletin' and \
               category == 'Training and Development':
            category = 'Training'
            if ln == 'fr':
                category = 'Formations'
        category_link = create_html_link(category_url, {},
                                         _(category),
                                         linkattrd=linkattrd)
        # Append to list of links
        categories_links.append(category_link)

    navigation = '<div id="navigationMenu">'
    navigation += separator.join([category_prefix + \
                                  category_link + \
                                  category_suffix for category_link \
                                  in categories_links])
    navigation += '</div>'
    return navigation

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0

_ = gettext_set_language('en')
dummy = _("News Articles")
dummy = _("Official News")
dummy = _("Training and Development")
dummy = _("General Information")
dummy = _("Announcements")
dummy = _("Training")
dummy = _("Events")
dummy = _("Staff Association")
