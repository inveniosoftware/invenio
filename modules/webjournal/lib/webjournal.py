# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2007, 2008, 2009, 2010, 2011 CERN.
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
WebJournal - Main Public interface of the WebJournals
"""

import datetime
import time
from invenio.bibformat_engine import \
     BibFormatObject, \
     format_with_format_template
from invenio.errorlib import register_exception
from invenio.config import \
     CFG_SITE_URL, \
     CFG_ACCESS_CONTROL_LEVEL_SITE
from invenio.urlutils import redirect_to_url
from invenio.webuser import collect_user_info
from invenio.webjournal_config import \
     InvenioWebJournalTemplateNotFoundError
from invenio.webjournal_utils import \
     get_article_page_from_cache, \
     cache_article_page, \
     get_current_issue, \
     get_journal_template, \
     get_release_datetime, \
     get_journal_articles, \
     get_unreleased_issue_hiding_mode, \
     issue_is_later_than, \
     datetime_to_issue

def perform_request_index(req, journal_name, issue_number, ln,
                          category, editor=False, verbose=0):
    """
    Central logic function for index pages.
    Brings together format templates and MARC rules from the config, with
    the requested index page, given by the url parameters.
    From config:
        - page template for index pages -> formatting
        - MARC rule list -> Category Navigation
        - MARC tag used for issue numbers -> search (later in the format
          elements)
    Uses BibFormatObject and format_with_format_template to produce the
    required HTML.
    """
    current_issue = get_current_issue(ln, journal_name)
    if not get_release_datetime(issue_number, journal_name):
        # Unreleased issue. Display latest released issue?
        unreleased_issues_mode = get_unreleased_issue_hiding_mode(journal_name)
        if not editor and \
               (unreleased_issues_mode == 'all' or \
                (unreleased_issues_mode == 'future' and \
                 issue_is_later_than(issue_number, current_issue))):
            redirect_to_url(req, "%s/journal/%s/%s/%s?ln=%s" % \
                            (CFG_SITE_URL,
                             journal_name,
                             current_issue.split('/')[1],
                             current_issue.split('/')[0],
                             ln))
    try:
        index_page_template = get_journal_template('index',
                                                   journal_name,
                                                   ln)
    except InvenioWebJournalTemplateNotFoundError, e:
        register_exception(req=req)
        return e.user_box(req)

    temp_marc = '''<record>
                        <controlfield tag="001">0</controlfield>
                    </record>'''
    # create a record and get HTML back from bibformat
    user_info = collect_user_info(req)
    bfo = BibFormatObject(0, ln=ln, xml_record=temp_marc,
                          user_info=user_info)
    bfo.req = req
    verbosity = 0
    if editor:
        # Increase verbosity only for editors/admins
        verbosity = verbose

    html = format_with_format_template(index_page_template,
                                       bfo,
                                       verbose=verbosity)
    return html

def perform_request_article(req, journal_name, issue_number, ln,
                            category, recid, editor=False, verbose=0):
    """
    Central logic function for article pages.
    Loads the format template for article display and displays the requested
    article using BibFormat.
    'Editor' mode generates edit links on the article view page and disables
    caching.
    """
    current_issue = get_current_issue(ln, journal_name)
    if not get_release_datetime(issue_number, journal_name):
        # Unreleased issue. Display latest released issue?
        unreleased_issues_mode = get_unreleased_issue_hiding_mode(journal_name)
        if not editor and \
               (unreleased_issues_mode == 'all' or \
                (unreleased_issues_mode == 'future' and \
                 issue_is_later_than(issue_number, current_issue))):
            redirect_to_url(req, "%s/journal/%s/%s/%s?ln=%s" % \
                            (CFG_SITE_URL,
                             journal_name,
                             current_issue.split('/')[1],
                             current_issue.split('/')[0],
                             ln))

    try:
        index_page_template = get_journal_template('detailed',
                                                   journal_name,
                                                   ln)
    except InvenioWebJournalTemplateNotFoundError, e:
        register_exception(req=req)
        return e.user_box(req)

    # if it is cached, return it
    cached_html = get_article_page_from_cache(journal_name, category,
                                              recid, issue_number, ln)

    if cached_html and not editor:
        return cached_html

    # Check that this recid is indeed an article
    is_article = False
    articles = get_journal_articles(journal_name, issue_number, category)
    for order, recids in articles.iteritems():
        if recid in recids:
            is_article = True
            break

    if not is_article:
        redirect_to_url(req, "%s/journal/%s/%s/%s?ln=%s" % \
                        (CFG_SITE_URL,
                         journal_name,
                         issue_number.split('/')[1],
                         issue_number.split('/')[0],
                         ln))


    # create a record and get HTML back from bibformat
    user_info = collect_user_info(req)
    bfo = BibFormatObject(recid, ln=ln, user_info=user_info)
    bfo.req = req
    verbosity = 0
    if editor:
        # Increase verbosity only for editors/admins
        verbosity = verbose
    html_out = format_with_format_template(index_page_template,
                                           bfo,
                                           verbose=verbosity)
    # cache if not in editor mode, and if database is not down
    if not editor and not CFG_ACCESS_CONTROL_LEVEL_SITE == 2:
        cache_article_page(html_out, journal_name, category,
                           recid, issue_number, ln)

    return html_out

def perform_request_contact(req, ln, journal_name, verbose=0):
    """
    Display contact information
    """
    try:
        contact_page_template = get_journal_template('contact',
                                                     journal_name,
                                                     ln)
    except InvenioWebJournalTemplateNotFoundError, e:
        register_exception(req=req)
        return e.user_box(req)

    user_info = collect_user_info(req)
    temp_marc = '''<record>
                       <controlfield tag="001">0</controlfield>
                   </record>'''
    bfo = BibFormatObject(0,
                          ln=ln,
                          xml_record=temp_marc,
                          user_info=user_info)
    bfo.req = req
    html = format_with_format_template(contact_page_template,
                                       bfo)

    return html

def perform_request_popup(req, ln, journal_name, record):
    """
    Display the popup window
    """
    try:
        popup_page_template = get_journal_template('popup',
                                                   journal_name,
                                                   ln)
    except InvenioWebJournalTemplateNotFoundError, e:
        register_exception(req=req)
        return e.user_box(req)

    user_info = collect_user_info(req)
    bfo = BibFormatObject(record, ln=ln, user_info=user_info)
    bfo.req = req
    html = format_with_format_template(popup_page_template,
                                       bfo)

    return html

def perform_request_search(req, journal_name, ln,
                           archive_issue, archive_select,
                           archive_date, archive_search, verbose=0):
    """
    Logic for the search / archive page.
    """
    try:
        search_page_template = get_journal_template('search',
                                                    journal_name,
                                                    ln)
    except InvenioWebJournalTemplateNotFoundError, e:
        register_exception(req=req)
        return e.user_box(req)

    if archive_select == "False" and archive_search == "False":
        temp_marc = '''<record>
                            <controlfield tag="001">0</controlfield>
                        </record>'''

        user_info = collect_user_info(req)
        bfo = BibFormatObject(0,
                              ln=ln,
                              xml_record=temp_marc,
                              user_info=user_info)
        bfo.req = req
        html = format_with_format_template(search_page_template,
                                           bfo,
                                           verbose=verbose)
        return html

    elif archive_select == "Go":
        redirect_to_url(req, "%s/journal/%s/%s/%s?ln=%s" % (CFG_SITE_URL,
                                                            journal_name,
                                                            archive_issue.split('/')[1],
                                                            archive_issue.split('/')[0],
                                                            ln))
    elif archive_search == "Go":
        try:
            archive_issue_time = datetime.datetime(*time.strptime(archive_date, "%d/%m/%Y")[0:5])
            archive_issue = datetime_to_issue(archive_issue_time, journal_name)
            if not archive_issue:
                archive_issue = get_current_issue(ln, journal_name)
        except ValueError:
            archive_issue = get_current_issue(ln, journal_name)
        redirect_to_url(req, "%s/journal/%s/%s/%s?ln=%s" % (CFG_SITE_URL,
                                                            journal_name,
                                                            archive_issue.split('/')[1],
                                                            archive_issue.split('/')[0],
                                                            ln))
