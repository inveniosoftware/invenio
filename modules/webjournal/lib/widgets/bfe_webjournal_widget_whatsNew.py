# -*- coding: utf-8 -*-
## $Id: bfe_webjournal_widget_whatsNew.py,v 1.24 2009/01/27 07:25:12 jerome Exp $
##
## This file is part of Invenio.
## Copyright (C) 2009, 2010, 2011 CERN.
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
"""
WebJournal widget - Display the index of the lastest articles,
including 'breaking news'.
"""
import time
import os

from invenio.search_engine import search_pattern, record_exists
from invenio.bibformat_engine import BibFormatObject
from invenio.config import \
     CFG_SITE_URL, \
     CFG_CACHEDIR, \
     CFG_ACCESS_CONTROL_LEVEL_SITE
from invenio.webjournal_utils import \
     parse_url_string, \
     make_journal_url, \
     get_journal_info_path, \
     get_journal_categories, \
     get_journal_articles, \
     get_current_issue
from invenio.messages import gettext_set_language

def format_element(bfo, latest_issue_only='yes', newest_articles_only='yes',
           link_category_headers='yes', display_categories='', hide_when_only_new_records="no"):
    """
    Display the index to the newest articles (of the latest issue, or of the displayed issue)

    @param latest_issue_only: if 'yes', always display articles of the latest issue, even if viewing a past issue
    @param newest_articles_only: only display new articles, not those that also appeared in previous issues
    @param link_category_headers: if yes, category headers link to index page of that category
    @param display_categories: comma-separated list of categories to display. If none, display all
    @param hide_when_only_new_records: if 'yes' display new articles only if old articles exist in this issue
    """
    args = parse_url_string(bfo.user_info['uri'])
    journal_name = args["journal_name"]
    ln = args["ln"]
    _ = gettext_set_language(ln)

    if latest_issue_only.lower() == 'yes':
        issue_number = get_current_issue(bfo.lang, journal_name)
    else:
        issue_number = args["issue"]

    # Try to get HTML from cache
    if args['verbose'] == 0:
        cached_html = _get_whatsNew_from_cache(journal_name, issue_number, ln)
        if cached_html:
            return cached_html

    # No cache? Build from scratch
    # 1. Get the articles
    journal_categories = get_journal_categories(journal_name,
                                                issue_number)
    if display_categories:
        display_categories = display_categories.lower().split(',')
        journal_categories = [category for category in journal_categories \
                              if category.lower() in display_categories]
    whats_new_articles = {}
    for category in journal_categories:
        whats_new_articles[category] = get_journal_articles(journal_name,
                                                            issue_number,
                                                            category,
                                                            newest_only=newest_articles_only.lower() == 'yes')

    # Do we want to display new articles only if they have been added
    # to an issue that contains non-new records?
    if hide_when_only_new_records.lower() == "yes":
        # First gather all articles in this issue
        all_whats_new_articles = {}
        for category in journal_categories:
            all_whats_new_articles[category] = get_journal_articles(journal_name,
                                                                    issue_number,
                                                                    category,
                                                                    newest_first=True,
                                                                    newest_only=False)
        # Then check if we have some articles at position > -1
        has_old_articles = False
        for articles in all_whats_new_articles.values():
            if len([order for order in articles.keys() if order > -1]) > 0:
                has_old_articles = True
                break
        if not has_old_articles:
            # We don't have old articles? Thend don't consider any
            for category in journal_categories:
                whats_new_articles[category] = {}

    # 2. Build the HTML
    html_out = _get_breaking_news(ln, journal_name)
    for category in journal_categories:
        articles_in_category = whats_new_articles[category]
        html_articles_in_category = ""
        # Generate the list of articles in this category
        order_numbers = articles_in_category.keys()
        order_numbers.sort()
        for order in order_numbers:
            articles = articles_in_category[order]
            for recid in articles:
                link = make_journal_url(bfo.user_info['uri'], {'journal_name': journal_name,
                                                               'issue_number': issue_number.split('/')[0],
                                                               'issue_year': issue_number.split('/')[1],
                                                               'category': category,
                                                               'recid': recid,
                                                               'ln': bfo.lang})
                temp_rec = BibFormatObject(recid)
                if ln == 'fr':
                    try:
                        title = temp_rec.fields('246_1a')[0]
                    except:
                        continue
                else:
                    try:
                        title = temp_rec.field('245__a')
                    except:
                        continue
                try:
                    html_articles_in_category += '<li><a href="%s">%s</a></li>' % \
                                                 (link, title)
                except:
                    pass

        if html_articles_in_category:
            # Good, we found some new articles for this category.
            # Then insert the genereated results into a larger list
            # with category as "parent".
            html_out += '<li>'
            if link_category_headers.lower() == 'yes':
                html_out += '<a href="'
                html_out += make_journal_url(bfo.user_info['uri'],
                                             {'journal_name': journal_name,
                                              'issue_number': issue_number.split('/')[0],
                                              'issue_year': issue_number.split('/')[1],
                                              'category': category,
                                              'recid': '',
                                              'ln': bfo.lang})
                html_out += '" class="whatsNewCategory">%s</a>' % _(category)
            else:
                html_out += '<span class="whatsNewCategory">%s</span>' % _(category)

            html_out += '<ul class="whatsNewItem">'
            html_out += html_articles_in_category
            html_out += '</ul></li>'

    if not html_out:
        html_out = '<i>' + _('There are no new articles for the moment') + '</i>'
    else:
        html_out = '<ul class="whatsNew">' + html_out + '</ul>'

    if args['verbose'] == 0:
        cache_whatsNew(html_out, journal_name, issue_number, ln)

    return html_out

def _get_breaking_news(lang, journal_name):
    """
    Gets the 'Breaking News' articles that are currently active according to
    start and end dates.
    """
    # CERN Bulletin only
    if not journal_name.lower() == 'cernbulletin':
        return ''
    # Look for active breaking news
    breaking_news_recids = [recid for recid in search_pattern(p='980__a:BULLETINBREAKING') \
                            if record_exists(recid) == 1]
    today = time.mktime(time.localtime())
    breaking_news = ""
    for recid in breaking_news_recids:
        temp_rec = BibFormatObject(recid)
        try:
            end_date = time.mktime(time.strptime(temp_rec.field("925__b"),
                                                 "%m/%d/%Y"))
        except:
            end_date = time.mktime(time.strptime("01/01/1970", "%m/%d/%Y"))
        if end_date < today:
            continue
        try:
            start_date = time.mktime(time.strptime(temp_rec.field("925__a"),
                                                   "%m/%d/%Y"))
        except:
            start_date = time.mktime(time.strptime("01/01/2050", "%m/%d/%Y"))
        if start_date > today:
            continue
        publish_date = temp_rec.field("269__c")
        if lang == 'fr':
            title = temp_rec.field("246_1a")
        else:
            title = temp_rec.field("245__a")
        breaking_news += '''
<h2 class="%s">%s<br/>
    <strong>
        <a href="%s/journal/popup?name=%s&amp;type=breaking_news&amp;record=%s&amp;ln=%s" target="_blank">%s</a>
    </strong>
</h2>
''' % ("", publish_date, CFG_SITE_URL, journal_name, recid, lang, title)
    if breaking_news:
        breaking_news = '<li>%s</li>' % breaking_news

    return breaking_news

def _get_whatsNew_from_cache(journal_name, issue, ln):
    """
    Try to get the "whats new" box from cache.
    """
    cache_path = os.path.abspath('%s/webjournal/%s/%s_whatsNew_%s.html' % \
                                  (CFG_CACHEDIR,
                                   journal_name,
                                   issue.replace('/','_'),
                                   ln))
    if not cache_path.startswith(CFG_CACHEDIR + '/webjournal'):
        # Make sure we are reading from correct directory (you
        # know, in case there are '../../' inside journal name..)
        return False
    try:
        last_update = os.path.getctime(cache_path)
    except:
        return False

    try:
        # Get last journal update, based on journal info file last
        # modification time
        journal_info_path = get_journal_info_path(journal_name)
        last_journal_update = os.path.getctime(journal_info_path)
    except:
        return False

    now = time.time()
    if ((last_update + 30*60) < now) or \
           (last_journal_update > last_update):
        # invalidate after 30 minutes or if last journal release is
        # newer than cache
        return False
    try:
        cached_file = open(cache_path).read()
    except:
        return False

    return cached_file

def cache_whatsNew(html, journal_name, issue, ln):
    """
    caches the whats new box for 30 minutes.
    """
    if not CFG_ACCESS_CONTROL_LEVEL_SITE == 2:
        cache_path = os.path.abspath('%s/webjournal/%s/%s_whatsNew_%s.html' % \
                                      (CFG_CACHEDIR,
                                       journal_name,
                                       issue.replace('/','_'),
                                       ln))
        if cache_path.startswith(CFG_CACHEDIR + '/webjournal'):
            # Do not try to cache if the journal name led us to some
            # other directory ('../../' inside journal name for
            # example)
            cache_dir = CFG_CACHEDIR + '/webjournal/' + journal_name
            if not os.path.isdir(cache_dir):
                os.makedirs(cache_dir)
            cache_file = file(cache_path, "w")
            cache_file.write(html)
            cache_file.close()

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0

_ = gettext_set_language('en')
dummy = _("What's new")
