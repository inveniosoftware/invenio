# -*- coding: utf-8 -*-
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
"""
WebJournal - Main Public interface of the WebJournals
"""

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
     InvenioWebJournalNoIndexTemplateError, \
     InvenioWebJournalNoIssueNumberTagError, \
     InvenioWebJournalNoArticleTemplateError, \
     InvenioWebJournalNoArticleRuleError, \
     InvenioWebJournalNoContactTemplateError, \
     InvenioWebJournalNoPopupTemplateError, \
     InvenioWebJournalNoSearchTemplateError
from invenio.webjournal_utils import get_xml_from_config
from invenio.webjournal_utils import \
     get_article_page_from_cache, \
     cache_article_page, \
     issue_times_to_week_strings, \
     count_down_to_monday, \
     get_current_issue

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
    # init all the values we need from config.xml
    config_strings = get_xml_from_config(["index", "rule", "issue_number"],
        journal_name)
    try:
        try:
            index_page_template = config_strings["index"][0]
        except:
            raise InvenioWebJournalNoIndexTemplateError(ln, journal_name)
    except InvenioWebJournalNoIndexTemplateError, e:
        register_exception(req=req)
        return e.user_box()
    index_page_template_path = 'webjournal/%s' % (index_page_template)
    rule_list = config_strings["rule"]
    try:
        if len(rule_list) == 0:
            raise InvenioWebJournalNoArticleRuleError(ln, journal_name)
    except InvenioWebJournalNoArticleRuleError, e:
        register_exception(req=req)
        return e.user_box()
    try:
        try:
            issue_number_tag = config_strings["issue_number"][0]
        except:
            raise InvenioWebJournalNoIssueNumberTagError(ln, journal_name)
    except InvenioWebJournalNoIssueNumberTagError, e:
        register_exception(req=req)
        return e.user_box()
    # get the current category for index display
    current_category_in_list = 0
    i = 0
    if category:
        for rule_string in rule_list:
            category_from_config = rule_string.split(",")[0]
            if category_from_config.lower() == category.lower():
                current_category_in_list = i
            i += 1
##     else:
##         # add the first category to the url string as a default
##         req.journal_defaults["category"] = rule_list[0].split(",")[0]

    # get the important values for the category from the config file
    rule_string = rule_list[current_category_in_list].replace(" ", "")
    category = rule_string.split(",")[0]
    rule = rule_string.split(",")[1]
    marc_datafield = rule.split(":")[0]
    rule_match = rule.split(":")[1]
    marc_tag = marc_datafield[:3]
    marc_ind1 = (str(marc_datafield[3]) == "_") and " " or marc_datafield[3]
    marc_ind2 = (str(marc_datafield[4]) == "_") and " " or marc_datafield[4]
    marc_subfield = marc_datafield[5]
    # create a marc record, containing category and issue number
    temp_marc = '''<record>
                        <controlfield tag="001">0</controlfield>
                        <datafield tag="%s" ind1="%s" ind2="%s">
                            <subfield code="%s">%s</subfield>
                        </datafield>
                        <datafield tag="%s" ind1="%s" ind2="%s">
                            <subfield code="%s">%s</subfield>
                        </datafield>
                    </record>''' % (issue_number_tag[:3],
                    (issue_number_tag[3] == "_") and " " or issue_number_tag[3],
                    (issue_number_tag[4] == "_") and " " or issue_number_tag[4],
                    issue_number_tag[5],
                    issue_number, marc_tag, marc_ind1,
                    marc_ind2, marc_subfield, rule_match)
    #temp_marc = temp_marc.decode('utf-8').encode('utf-8')
    # create a record and get HTML back from bibformat
    user_info = collect_user_info(req)
    bfo = BibFormatObject(0, ln=ln, xml_record=temp_marc,
                          user_info=user_info)
    bfo.req = req
    verbosity = 0
    if editor:
        # Increase verbosity only for editors/admins
        verbosity = verbose

    html = format_with_format_template(index_page_template_path,
                                       bfo,
                                       verbose=verbosity)[0]
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
    # init all the values we need from config.xml
    config_strings = get_xml_from_config(["detailed", "rule"], journal_name)
    try:
        try:
            index_page_template = config_strings["detailed"][0]
        except:
            raise InvenioWebJournalNoArticleTemplateError(ln,
                                                          journal_name)
    except InvenioWebJournalNoArticleTemplateError, e:
        register_exception(req=req)
        return e.user_box()
    index_page_template_path = 'webjournal/%s' % (index_page_template)
    rule_list = config_strings["rule"]
    try:
        if len(rule_list) == 0:
            raise InvenioWebJournalNoArticleRuleError(ln, journal_name)
    except InvenioWebJournalNoArticleRuleError, e:
        register_exception(req=req)
        return e.user_box()
    # get the current category for index display
    current_category_in_list = 0
    i = 0
    if category != "":
        for rule_string in rule_list:
            category_from_config = rule_string.split(",")[0]
            if category_from_config.lower() == category.lower():
                current_category_in_list = i
            i += 1
    rule_string = rule_list[current_category_in_list].replace(" ", "")
    rule = rule_string.split(",")[1]
    # try to get the page from the cache
    cached_html = get_article_page_from_cache(journal_name, category, recid,
                                              issue_number, ln)
    if cached_html and not editor:
        return cached_html
    # create a record and get HTML back from bibformat
    user_info = collect_user_info(req)
    bfo = BibFormatObject(recid, ln=ln, user_info=user_info)
    bfo.req = req
    verbosity = 0
    if editor:
        # Increase verbosity only for editors/admins
        verbosity = verbose
    html_out = format_with_format_template(index_page_template_path,
                                           bfo, verbose=verbosity)[0]
    # cache if not in editor mode, and if database is not down
    if not editor and not CFG_ACCESS_CONTROL_LEVEL_SITE == 2:
        cache_article_page(html_out, journal_name, category,
                           recid, issue_number, ln)

    return html_out

def perform_request_contact(req, ln, journal_name, verbose=0):
    """
    Display contact information
    """
    config_strings = get_xml_from_config(["contact"], journal_name)
    try:
        try:
            contact_page_template = config_strings["contact"][0]
        except:
            raise InvenioWebJournalNoContactTemplateError(ln, journal_name)
    except InvenioWebJournalNoContactTemplateError, e:
        register_exception(req=req)
        return e.user_box()

    contact_page_template_path = 'webjournal/%s' % contact_page_template
    user_info = collect_user_info(req)
    temp_marc = '''<record>
                       <controlfield tag="001">0</controlfield>
                   </record>'''
    bfo = BibFormatObject(0,
                          ln=ln,
                          xml_record=temp_marc,
                          user_info=user_info)
    bfo.req = req
    html = format_with_format_template(contact_page_template_path,
                                       bfo,
                                       verbose)[0]

    return html

def perform_request_popup(req, ln, journal_name, record):
    """
    Display the popup window
    """
    config_strings = get_xml_from_config(["popup"], journal_name)
    try:
        try:
            popup_page_template = config_strings["popup"][0]
        except:
            raise InvenioWebJournalNoPopupTemplateError(ln, journal_name)
    except InvenioWebJournalNoPopupTemplateError, e:
        register_exception(req=req)
        return e.user_box()

    popup_page_template_path = 'webjournal/%s' % popup_page_template
    user_info = collect_user_info(req)
    bfo = BibFormatObject(record, ln=ln, user_info=user_info)
    bfo.req = req
    html = format_with_format_template(popup_page_template_path, bfo)[0]

    return html

def perform_request_search(req, journal_name, ln,
                           archive_issue, archive_select,
                           archive_date, archive_search, verbose=0):
    """
    Logic for the search / archive page.
    """
    config_strings = get_xml_from_config(["search", "issue_number", "rule"],
        journal_name)
    try:
        try:
            search_page_template = config_strings["search"][0]
        except:
            raise InvenioWebJournalNoSearchTemplateError(journal_name,
                                                         ln)
    except InvenioWebJournalNoSearchTemplateError, e:
        register_exception(req=req)
        return e.user_box()

    search_page_template_path = 'webjournal/%s' % (search_page_template)
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
        html = format_with_format_template(search_page_template_path,
                                           bfo,
                                           verbose=verbose)[0]
        return html
    elif archive_select == "Go":
        redirect_to_url(req, "%s/journal/%s/%s/%s?ln=%s" % (CFG_SITE_URL,
                                                            journal_name,
                                                            archive_issue.split('/')[1],
                                                            archive_issue.split('/')[0],
                                                            ln))
    elif archive_search == "Go":
        try:
            archive_issue_time = time.strptime(archive_date, "%d/%m/%Y")
            archive_issue_time = count_down_to_monday(archive_issue_time)
            archive_issue = issue_times_to_week_strings([archive_issue_time])[0]
        except ValueError:
            archive_issue = get_current_issue(ln, journal_name)
        redirect_to_url(req, "%s/journal/%s/%s/%s?ln=%s" % (CFG_SITE_URL,
                                                            journal_name,
                                                            archive_issue.split('/')[1],
                                                            archive_issue.split('/')[0],
                                                            ln))
