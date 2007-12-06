# -*- coding: utf-8 -*-
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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

from urllib2 import urlopen
import smtplib
import sets
import time

from invenio.bibformat_engine import BibFormatObject, \
                                    format_with_format_template
from invenio.errorlib import register_exception
from invenio.webpage import page
from invenio.config import weburl, etcdir

from invenio.webjournal_config import InvenioWebJournalNoIndexTemplateError, \
                                      InvenioWebJournalNoIssueNumberTagError, \
                                      InvenioWebJournalNoArticleTemplateError, \
                                      InvenioWebJournalNoArticleRuleError, \
                                      InvenioWebJournalNoPopupTemplateError
from invenio.webjournal_utils import get_xml_from_config
from invenio.webjournal_utils import get_recid_from_order_CERNBulletin, \
                                    get_article_page_from_cache, \
                                    cache_article_page, \
                                    createhtmlmail, \
                                    put_css_in_file, \
                                    get_monday_of_the_week
from invenio.webjournal_templates import tmpl_webjournal_alert_success_msg, \
                                tmpl_webjournal_alert_subject_CERNBulletin, \
                                tmpl_webjournal_alert_plain_text_CERNBulletin, \
                                tmpl_webjournal_alert_interface, \
                                tmpl_webjournal_issue_control_interface, \
                                tmpl_webjournal_issue_control_success_msg

def perform_request_index(req, journal_name, issue_number, language, category):
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
            raise InvenioWebJournalNoIndexTemplateError(language, journal_name)
    except InvenioWebJournalNoIndexTemplateError, e:
        register_exception(req=req)
        return e.user_box()
    index_page_template_path = 'webjournal/%s' % (index_page_template)
    rule_list = config_strings["rule"]
    try:
        if len(rule_list) == 0:
            raise InvenioWebJournalNoArticleRuleError(language, journal_name) 
    except InvenioWebJournalNoArticleRuleError, e:     
        register_exception(req=req)
        return e.user_box()
    try:
        try:
            issue_number_tag = config_strings["issue_number"][0]
        except:
            raise InvenioWebJournalNoIssueNumberTagError(language, journal_name)
    except InvenioWebJournalNoIssueNumberTagError, e:
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
            i+=1
    else:
        # add the first category to the url string as a default
        req.journal_defaults["category"] = rule_list[0].split(",")[0]
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
    bfo = BibFormatObject(0, ln=language, xml_record=temp_marc, req=req)
    html = format_with_format_template(index_page_template_path, bfo)[0]
    return html

def perform_request_article(req, journal_name, issue_number, language,
                              category, number, editor):
    """
    Central logic function for article pages.
    Loads the format template for article display and displays the requested
    article using BibFormat.
    'Editor' Mode genereates edit links on the article view page and disables
    caching.
    """
    # init all the values we need from config.xml
    config_strings = get_xml_from_config(["detailed", "rule"], journal_name)
    try:
        try:    
            index_page_template = config_strings["detailed"][0]
        except:
            raise InvenioWebJournalNoArticleTemplateError(language,
                                                          journal_name)
    except InvenioWebJournalNoArticleTemplateError, e:
        register_exception(req=req)
        return e.user_box()
    index_page_template_path = 'webjournal/%s' % (index_page_template)
    rule_list = config_strings["rule"]
    try:
        if len(rule_list) == 0:
            raise InvenioWebJournalNoArticleRuleError(language, journal_name) 
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
            i+=1     
    rule_string = rule_list[current_category_in_list].replace(" ", "")
    rule = rule_string.split(",")[1]
    # try to get the page from the cache
    recid = get_recid_from_order_CERNBulletin(number, rule, issue_number)
    cached_html = get_article_page_from_cache(journal_name, category, recid,
                                              issue_number, language)
    if cached_html and editor == "False":
        return cached_html
    # create a record and get HTML back from bibformat
    bfo = BibFormatObject(recid, ln=language, req=req)
    html_out = format_with_format_template(index_page_template_path,
                                           bfo)[0]
    # cache if not in editor mode
    if editor == "False":
        cache_article_page(html_out, journal_name, category,
                           recid, issue_number, language)
    
    return html_out

def perform_request_alert(req, journal_name, issue_number, language,
                              sent, plain_text, subject, recipients,
                              html_mail):
    """
    All the logic for alert emails.
    Messages are retrieved from templates. (should be migrated to msg class)
    Mails can be edited by an interface form.
    Sent in HTML/PlainText or only PlainText if wished so.
    """
    subject = tmpl_webjournal_alert_subject_CERNBulletin(issue_number)
    plain_text = tmpl_webjournal_alert_plain_text_CERNBulletin(language,
                                                               issue_number)
    plain_text = plain_text.encode('utf-8')
    
    if sent == "False":
        interface = tmpl_webjournal_alert_interface(language, journal_name,
                                                    subject, plain_text)
        return page(title="alert system", body=interface)
    else:    
        if html_mail == "html": 
            html_file = urlopen('%s/journal/?name=%s&ln=en'
                                % (weburl, journal_name))    
            html_string = html_file.read()
            html_file.close()
            html_string = put_css_in_file(html_string, journal_name)
        else:
            html_string = plain_text.replace("\n", "<br/>")
        
        message = createhtmlmail(html_string, plain_text,
                                 subject, recipients)
        server = smtplib.SMTP("localhost", 25)
        server.sendmail('Bulletin-Support@cern.ch', recipients, message)
        # todo: has to go to some messages config
        return tmpl_webjournal_alert_success_msg(language, journal_name)
    
def perform_request_issue_control(req, journal_name, issue_numbers,
                                      language, add, action):
    """
    Central logic for issue control.
    Regenerates the flat files current_issue and issue_group that control
    the which issue is currently active for the journal.
    Todo: move issue control to DB
    """
    if action == "cfg" or action == "Refresh":
        active_issues = []
        if action == "Refresh":
            active_issues = issue_numbers
            try:
                active_issues.remove("mm/yyyy")
            except:
                pass
            active_issues = list(sets.Set(active_issues)) # avoid double entries
            active_issues.sort()
        else:
            try:
                issue_group = open('%s/webjournal/%s/issue_group' % (etcdir,
                                                        journal_name)).read()
            except:
                issue_group = ""
            try:
                current_issue = open('%s/webjournal/%s/current_issue' % (etcdir,
                                                        journal_name)).read()
            except:
                register_exception(stream='warning', req=req,
                                   suffix="Couldn't find any current issue, if \
                                          this is the first time for this \
                                          journal this is fine.")
                current_issue = ""
            
            if issue_group != "":
                issue_part = issue_group.split(" - ")[0]
                year = issue_part.split("/")[1]
                low_bound = issue_part.split("/")[0].split("-")[0]
                high_bound = issue_part.split("/")[0].split("-")[1]
                for i in range(int(low_bound), int(high_bound)+1):
                    active_issues.append("%s/%s" % (str(i), year))
            elif current_issue != "":
                issue_part = current_issue.split(" - ")[0]
                issue_number = issue_part.replace(" ", "")
                active_issues.append(issue_number)
        this_weeks_issue = time.strftime("%U/%Y", time.localtime())
        
        output = tmpl_webjournal_issue_control_interface(language,
                                                            journal_name,
                                                            active_issues)
    elif action == "Publish":
        active_issues = issue_numbers
        try:
            active_issues.remove("ww/yyyy")
            active_issues.remove("")
        except:
            pass
        active_issues = list(sets.Set(active_issues)) # avoid double entries
        active_issues.sort()
        
        file_issue_group = open('%s/webjournal/%s/issue_group' % (etcdir,
                                                    journal_name), "w")
        file_current_issue = open('%s/webjournal/%s/current_issue' % (etcdir,
                                                    journal_name), "w")
        
        if len(active_issues) > 1:
            low_bound = active_issues[0].split("/")[0]
            high_bound = active_issues[len(active_issues)-1].split("/")[0]
            year = active_issues[len(active_issues)-1].split("/")[1]
            file_issue_group.write('%s-%s/%s - %s' % (low_bound,
                                        high_bound,
                                        year,
                                        get_monday_of_the_week(low_bound, year)))
            file_current_issue.write('%s/%s - %s' % (high_bound,
                                    year,
                                    get_monday_of_the_week(high_bound, year)))
        elif len(active_issues) > 0:
            issue_number = active_issues[0].split("/")[0]
            year = active_issues[0].split("/")[1]
            file_current_issue.write('%s/%s - %s' % (issue_number,
                                    year,
                                    get_monday_of_the_week(issue_number, year)))
        else:
            register_exception(stream='warning', req=req,
                               suffix='empty issue has been published.')
        
        file_current_issue.close()
        file_issue_group.close()
        output = tmpl_webjournal_issue_control_success_msg(language,
                                              active_issues, journal_name)
        
    return page(title="Publish System", body=output)

def perform_request_popup(req, language, journal_name, type, record):
    """
    """
    config_strings = get_xml_from_config(["popup"], journal_name)        
    try:
        try:
            popup_page_template = config_strings["popup"][0]
        except:
            raise InvenioWebJournalNoPopupTemplateError(language)
    except InvenioWebJournalNoPopupTemplateError, e:
        register_exception(req=req)
        return e.user_box()
    
    popup_page_template_path = 'webjournal/%s' % popup_page_template
    bfo = BibFormatObject(record, ln=language, req=req)
    html = format_with_format_template(popup_page_template_path, bfo)[0]

    return html