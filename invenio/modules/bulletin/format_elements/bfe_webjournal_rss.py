# -*- coding: utf-8 -*-
# $Id: bfe_webjournal_widget_whatsNew.py,v 1.24 2009/01/27 07:25:12 jerome Exp $
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
WebJournal widget - Display the index of the lastest articles,
including 'breaking news'.
"""
from invenio.legacy.webjournal.utils import \
     parse_url_string, \
     get_journal_categories, \
     get_category_query
from invenio.base.i18n import gettext_set_language
from invenio.config import CFG_SITE_URL
from invenio.utils.url import create_html_link
from invenio.legacy.dbquery import run_sql
from urllib import quote

def format_element(bfo, categories, label="Subscribe by RSS",
                   rss_icon_url="/img/rss.png", cc='', css_class="rssLink",
                   rss_icon_width='16px', rss_icon_height='16px'):
    """
    Display RSS links to journal articles, in one or several
    categories, or to the whole journal (if 'cc' parameter is used).

    Note about 'cc': if we want an RSS of *all* articles (whathever
    the category is), either we build an RSS url to each of the
    categories/collections of the journal, or we simply link to the
    main collection ('cc') of the journal (which implies that journal
    categories exist as sub-collections of 'cc'). The second option is
    preferred.

    @param categories: comma-separated list of journal categories that will be linked from this RSS. If 'all', use all. If empty, try to use current category.
    @param label: label of the RSS link
    @param rss_icon_url: if provided, display the RSS icon in front of the label
    @param rss_icon_width: if provided, declared width for the RSS icon
    @param rss_icon_height: if provided, declared height for the RSS icon
    @param cc: if provided, use as root collection for the journal, and ignore 'categories' parameter.
    @param css_class: CSS class of the RSS link.
    """
    args = parse_url_string(bfo.user_info['uri'])
    category_name = args["category"]
    journal_name = args["journal_name"]
    ln = bfo.lang
    _ = gettext_set_language(ln)


    if cc:
        categories = []
    elif categories.lower() == 'all':
        categories = get_journal_categories(journal_name)
    elif not categories and category_name:
        categories = [category_name]
    else:
        categories = categories.split(',')

    # Build the query definition for selected categories. If a
    # category name can a match collection name, we can simply search
    # in this collection. Otherwise we have to search using the query
    # definition of the category.
    # Note that if there is one category that does not match a
    # collection name, we have to use collections queries for all
    # categories (we cannot display all records of a collection +
    # apply search constraint on other collections)
    collections = []
    pattern = []
    must_use_pattern = False
    for category in categories:
        dbquery = get_category_query(journal_name, category)
        if dbquery:
            pattern.append(dbquery)
            res = None
            if not must_use_pattern:
                res = run_sql("SELECT name FROM collection WHERE dbquery=%s",
                              (dbquery,))
            if res:
                collections.append(res[0][0])
            else:
                # Could not find corresponding collection. Maybe
                # replace '980__a' by 'collection'?
                if not must_use_pattern:
                    res = run_sql("SELECT name FROM collection WHERE dbquery=%s",
                                  (dbquery.replace('980__a', 'collection'),))
                if res:
                    collections.append(res[0][0])
                else:
                    # Really no matching collection name
                    # apparently. Use query definition.
                    must_use_pattern = True

    # Build label
    link_label = ''
    if rss_icon_url:
        if rss_icon_url.startswith('/'):
            # Build an absolute URL
            rss_icon_url = CFG_SITE_URL + rss_icon_url
        link_label += '<img src="%s" alt="RSS" border="0"%s%s/> ' % \
                      (rss_icon_url, rss_icon_width and ' width="%s"' % rss_icon_width or '',
                       rss_icon_height and ' height="%s"' % rss_icon_height or '')
    if label:
        link_label += _(label)

    # Build link
    rss_url = CFG_SITE_URL + '/rss'
    if cc:
        rss_url += '?cc=' + quote(cc)
    elif must_use_pattern:
        rss_url += '?p=' + quote(' or '.join(pattern))
    else:
        rss_url += '?c=' + '&amp;c='.join([quote(coll) \
                                               for coll in collections])
    rss_url += '&amp;ln=' + ln

    return create_html_link(rss_url, {},
                            link_label=link_label,
                            linkattrd={'class': css_class})

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0

_ = gettext_set_language('en')
dummy = _("Subscribe by RSS")
