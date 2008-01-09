# -*- coding: utf-8 -*-
## $Id$
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

"""WebJournal Web Interface."""

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

import time
import os
import urllib
from urllib2 import urlopen
from email import message_from_string
from xml.dom import minidom

from mod_python import apache
from invenio.webinterface_handler import wash_urlargd, WebInterfaceDirectory

from invenio.access_control_engine import acc_authorize_action
from invenio.config import weburl, webdir, cdslang, etcdir
from invenio.webpage import page
from invenio.webuser import getUid
from invenio.urlutils import redirect_to_url
from invenio.errorlib import register_exception
from invenio.bibformat_engine import format_with_format_template, BibFormatObject
from invenio.search_engine import search_pattern

from webjournal_config import *
from invenio.webjournal_utils import get_recid_from_order, \
                                        get_recid_from_order_CERNBulletin, \
                                        parse_url_string, \
                                        get_xml_from_config, \
                                        please_login, \
                                        get_current_issue, \
                                        get_rule_string_from_rule_list, \
                                        get_monday_of_the_week, \
                                        cache_index_page, \
                                        get_index_page_from_cache, \
                                        get_article_page_from_cache, \
                                        cache_article_page, \
                                        clear_cache_for_issue

from invenio.webjournal_washer import wash_category, \
                                        wash_issue_number, \
                                        wash_journal_name, \
                                        wash_journal_language, \
                                        wash_article_number, \
                                        wash_popup_type, \
                                        wash_popup_record
from invenio.webjournal import perform_request_index, \
                                perform_request_article, \
                                perform_request_alert, \
                                perform_request_issue_control, \
                                perform_request_popup, \
                                perform_request_administrate
from invenio.webjournal_templates import tmpl_webjournal_regenerate_success, \
                                tmpl_webjournal_regenerate_error, \
                                tmpl_webjournal_feature_record_interface, \
                                tmpl_webjournal_feature_record_success, \
                                tmpl_webjournal_alert_plain_text_CERNBulletin, \
                                tmpl_webjournal_alert_subject_CERNBulletin, \
                                tmpl_webjournal_alert_success_msg, \
                                tmpl_webjournal_alert_interface

class WebInterfaceJournalPages(WebInterfaceDirectory):
    """Defines the set of /journal pages."""

    _exports = ['', 'article', 'issue_control', 'edit_article', 'alert',
                'feature_record', 'popup', 'regenerate', 'administrate']
    # profiler
    #def index(self, req, form):
    #    import hotshot
    #    pr = hotshot.Profile('/tmp/journal_profile')
    #    return pr.runcall(self.index_bla, req=req, form=form)

    def index(self, req, form):
        """
        Index page.
        Washes all the parameters and stores them in journal_defaults dict
        for subsequent format_elements.
        Passes on to logic function and eventually returns HTML.
        """
        argd = wash_urlargd(form, {'name': (str, ""),
                                    'issue': (str, ""),
                                    'category': (str, ""),
                                    'ln': (str, "")}
                            )
        try:
            language = wash_journal_language(argd['ln'])
            journal_name = wash_journal_name(language, argd['name'])
            issue_number = wash_issue_number(language, journal_name,
                                             argd['issue'])
            category = wash_category(language, argd['category'])
        except InvenioWebJournalNoJournalOnServerError, e:
            register_exception(req=req)
            return e.user_box()
        except InvenioWebJournalNoNameError, e:
            register_exception(req=req)
            return e.user_box()
        except InvenioWebJournalNoCurrentIssueError, e:
            register_exception(req=req)
            return e.user_box()
        except InvenioWebJournalIssueNumberBadlyFormedError, e:
            register_exception(req=req)
            return e.user_box()
        # the journal_defaults will be used by format elements that have no
        # direct access to the params here, no more checking needed
        req.journal_defaults = {"name": journal_name,
                                "issue": issue_number,
                                "ln": language,
                                "category": category}
        
        html = perform_request_index(req, journal_name, issue_number, language,
                              category)
        return html
    
    def article(self, req, form):
        """
        Article page.
        Washes all the parameters and stores them in journal_defaults dict
        for subsequent format_elements.
        Passes on to logic function and eventually returns HTML.
        """
        argd = wash_urlargd(form, {'name': (str, ""),
                                    'issue': (str, ""),
                                    'category': (str, ""),
                                    'number': (str, ""),
                                    'ln': (str, ""),
                                    'editor': (str, "False")}
                            )
        try:
            language = wash_journal_language(argd['ln'])
            journal_name = wash_journal_name(language, argd['name'])
            issue_number = wash_issue_number(language, journal_name,
                                             argd['issue'])
            category = wash_category(language, argd['category'])
            number = wash_article_number(language, argd['number'], journal_name)
            editor = argd['editor']
        except InvenioWebJournalNoJournalOnServerError, e:
            register_exception(req=req)
            return e.user_box()
        except InvenioWebJournalNoNameError, e:
            register_exception(req=req)
            return e.user_box()
        except InvenioWebJournalNoCurrentIssueError, e:
            register_exception(req=req)
            return e.user_box()
        except InvenioWebJournalIssueNumberBadlyFormedError, e:
            register_exception(req=req)
            return e.user_box()
        except InvenioWebJournalNoArticleNumberError, e:
            register_exception(req=req)
            return e.user_box()
        # automatically make all logged in users of cfgwebjournal editors
        if acc_authorize_action(getUid(req), 'cfgwebjournal',
                                name="%s" % journal_name)[0] == 0:
            editor = "True"
        # the journal_defaults will be used by format elements that have no
        # direct access to the params here, no more checking needed
        req.journal_defaults = {"name" : journal_name,
                                "issue" : issue_number,
                                "ln" : language,
                                "category" : category,
                                "editor" : editor,
                                "number" : number}
            
        html = perform_request_article(req, journal_name, issue_number,
                                       language, category, number, editor)
        return html
    
    def edit_article(self, req, form):
        """
        Simple url redirecter to toggle the edit mode on for article pages.
        Checks if user is logged in.
        """
        argd = wash_urlargd(form, {'name': (str, ""),
                                    'ln': (str, "")})
        try:
            language = wash_journal_language(argd['ln'])
            journal_name = wash_journal_name(language, argd['name'])
        except InvenioWebJournalNoJournalOnServerError, e:
            register_exception(req=req)
            return e.user_box()
        except InvenioWebJournalNoNameError, e:
            register_exception(req=req)
            return e.user_box()
        
        if acc_authorize_action(getUid(req), 'cfgwebjournal',
                                name="%s" % journal_name)[0] != 0:
            return please_login(req, journal_name,
                                backlink='%s/journal/edit_article?%s'
                                % (weburl, urllib.quote(req.args)))
                                # todo: use make_canonical_url from urlutils
        redirect_to_url(req,
                        "%s/journal/article?%s&editor=True"
                        % (weburl, req.args))

    def administrate(self, req, form):
        """Index page."""
        argd = wash_urlargd(form, {'name': (str, ""),
                                    'ln': (str, "")
                                    })
        try:
            language = wash_journal_language(argd['ln'])
            journal_name = wash_journal_name(language, argd['name'])
        except InvenioWebJournalNoJournalOnServerError, e:
            register_exception(req=req)
            return e.user_box()
        except InvenioWebJournalNoNameError, e:
            register_exception(req=req)
            return e.user_box()
        # check for user rights
        if acc_authorize_action(getUid(req), 'cfgwebjournal',
                                name="%s" % journal_name)[0] != 0:
            return please_login(req, journal_name,
                                backlink='%s/journal/administrate?name=%s'
                                % (weburl, journal_name))
        
        return perform_request_administrate(journal_name, language)
    
    def feature_record(self, req, form):
        """
        Interface to feature a record. Will be saved in a flat file.
        """
        argd = wash_urlargd(form, {'name': (str, ""),
                                    'recid': (str, "init"),
                                    'featured': (str, "false"),
                                    'url': (str, "init"),
                                    'ln': (str, "")
                                    })
        try:
            language = wash_journal_language(argd['ln'])
            journal_name = wash_journal_name(language, argd['name'])
            recid = argd['recid']
            url = argd['url']
            featured = argd['featured']
        except InvenioWebJournalNoJournalOnServerError, e:
            register_exception(req=req)
            return e.user_box()
        except InvenioWebJournalNoNameError, e:
            register_exception(req=req)
            return e.user_box()
        # check for user rights
        if acc_authorize_action(getUid(req), 'cfgwebjournal',
                                name="%s" % journal_name)[0] != 0:
            return please_login(req, journal_name,
                                backlink='%s/journal/feature_record?name=%s'
                                % (weburl, journal_name))
       
        if recid == "init":
            return tmpl_webjournal_feature_record_interface(language,
                                                            journal_name)   
        else:
            # todo: move to DB, maybe?
            fptr = open('%s/webjournal/%s/featured_record'
                        % (etcdir, journal_name), "w")
            fptr.write(recid)
            fptr.write('\n')
            fptr.write(argd['url'])
            fptr.close()
            return tmpl_webjournal_feature_record_success(language,
                                                          journal_name, recid)    
    
    def regenerate(self, req, form):
        """
        Clears the cache for the issue given.
        """
        argd = wash_urlargd(form, {'name': (str, ""),
                                    'issue': (str, ""),
                                    'ln': (str, "")})
        try:
            language = wash_journal_language(argd['ln'])
            journal_name = wash_journal_name(language, argd['name'])
            issue_number = wash_issue_number(language, journal_name,
                                             argd['issue'])
        except InvenioWebJournalNoJournalOnServerError, e:
            register_exception(req=req)
            return e.user_box()
        except InvenioWebJournalNoNameError, e:
            register_exception(req=req)
            return e.user_box()
        except InvenioWebJournalNoCurrentIssueError, e:
            register_exception(req=req)
            return e.user_box()
        except InvenioWebJournalIssueNumberBadlyFormedError, e:
            register_exception(req=req)
            return e.user_box()
        # check for user rights
        if acc_authorize_action(getUid(req), 'cfgwebjournal',
                                name="%s" % journal_name)[0] != 0:
            return please_login(req, journal_name,
                                backlink='%s/journal/regenerate?name=%s'
                                % (weburl, journal_name))
        # clear cache
        success = clear_cache_for_issue(journal_name, issue_number)
        if success:
            return tmpl_webjournal_regenerate_success(language, journal_name,
                                                      issue_number)
        else:
            return tmpl_webjournal_regenerate_error(language, journal_name,
                                                    issue_number)
        
    def alert(self, req, form):
        """
        Alert system.
        Sends an email alert, in HTML/PlainText or only PlainText to a mailing
        list to alert for new journal releases.
        """
        argd = wash_urlargd(form, {'name': (str, ""),
                                    'sent': (str, "False"),
                                    'plainText': (str, u''),
                                    'htmlMail': (str, ""),
                                    'recipients': (str, ""),
                                    'subject': (str, ""),
                                    'ln': (str, ""),
                                    'issue': (str, ""),
                                    'force': (str, "False")})
        try:
            language = wash_journal_language(argd['ln'])
            journal_name = wash_journal_name(language, argd['name'])
            issue_number = wash_issue_number(language, journal_name,
                                             argd['issue'])
            plain_text = argd['plainText']
            html_mail = argd['htmlMail']
            recipients = argd['recipients']
            subject = argd['subject']
            sent = argd['sent']
            force = argd['force']
        except InvenioWebJournalNoJournalOnServerError, e:
            register_exception(req=req)
            return e.user_box()
        except InvenioWebJournalNoNameError, e:
            register_exception(req=req)
            return e.user_box()
        except InvenioWebJournalNoCurrentIssueError, e:
            register_exception(req=req)
            return e.user_box()
        except InvenioWebJournalIssueNumberBadlyFormedError, e:
            register_exception(req=req)
            return e.user_box()
        # login
        if acc_authorize_action(getUid(req), 'cfgwebjournal',
                                name="%s" % journal_name)[0] != 0:
            return please_login(req, journal_name,
                                backlink='%s/journal/alert?name=%s'
                                % (weburl, journal_name))
        
        html = perform_request_alert(req, journal_name, issue_number, language,
                              sent, plain_text, subject, recipients,
                              html_mail, force)
        return html
    
    def issue_control(self, req, form):
        """
        page that allows full control over creating, backtracing, adding to,
        removing from issues.
        """
        argd = wash_urlargd(form, {'name': (str, ""),
                                    'add': (str, ""),
                                    'action_publish': (str, "cfg"),
                                    'issue_number': (list, []),
                                    'ln': (str, "")}
                            )
        try:
            language = wash_journal_language(argd['ln'])
            journal_name = wash_journal_name(language, argd['name'])
            issue_numbers = []
            for number in argd['issue_number']:
                if number != "ww/YYYY":
                    issue_numbers.append(wash_issue_number(language,
                                                           journal_name,
                                                            number))
            add = argd['add']
            action = argd['action_publish']
        except InvenioWebJournalNoJournalOnServerError, e:
            register_exception(req=req)
            return e.user_box()
        except InvenioWebJournalNoNameError, e:
            register_exception(req=req)
            return e.user_box()
        except InvenioWebJournalNoCurrentIssueError, e:
            register_exception(req=req)
            return e.user_box()
        except InvenioWebJournalIssueNumberBadlyFormedError, e:
            register_exception(req=req)
            return e.user_box()
        # check user rights
        if acc_authorize_action(getUid(req), 'cfgwebjournal',
                                name="%s" % journal_name)[0] != 0:
            return please_login(req, journal_name)
        
        html = perform_request_issue_control(req, journal_name, issue_numbers,
                                      language, add, action)
        
        return html
    
    def popup(self, req, form):
        """
        simple pass-through function that serves as a checker for popups.
        """
        argd = wash_urlargd(form, {'name': (str, ""),
                                    'record': (str, ""),
                                    'type': (str, ""),
                                    'ln': (str, "")
                                    })
        try:
            language = wash_journal_language(argd['ln'])
            journal_name = wash_journal_name(language, argd['name'])
            type = wash_popup_type(language, argd['type'], journal_name)
            record = wash_popup_record(language, argd['record'], journal_name)
        except InvenioWebJournalNoJournalOnServerError, e:
            register_exception(req=req)
            return e.user_box()
        except InvenioWebJournalNoNameError, e:
            register_exception(req=req)
            return e.user_box()
        except IvenioWebJournalNoPopupTypeError, e:
            register_exception(req=req)
            return e.user_box()
        except InvenioWebJournalNoPopupRecordError, e:
            register_exception(req=req)
            return e.user_box()
        
        html = perform_request_popup(req, language, journal_name, type, record)
        
        return html
        
        
        
#def search(self, req, form):
    #    """
    #    Creates a temporary record containing all the information needed for
    #    the search, meaning list of issue_numbers (timeframe), list of keywords,
    #    list of categories to search in. In this way everything can be configured
    #    globally in the config for the given webjournal and we can reuse the bibformat
    #    for whatever search we want.
    #    """
    #    argd = wash_urlargd(form, {'name': (str, ""),
    #                                'category': (list, []),
    #                                'issue': (list, []),
    #                                'keyword': (str, ""),
    #                                'ln': (str, cdslang)})
    #    if argd['name'] == "":
    #        register_exception(stream='warning',
    #                           suffix="User tried to search without providing a journal name.")
    #        return webjournal_missing_info_box(req, title="Journal not found",
    #                                      msg_title="We don't know which journal you are looking for",
    #                                      msg='''You were looking for a journal without providing a name.
    #                Unfortunately we cannot know which journal you are looking for.
    #                Below you have a selection of journals that are available on this server.
    #                If you should find your journal there, just click the link,
    #                otherwise please contact the server admin and ask for existence
    #                of the journal you are looking for.''')
    #    else:
    #        journal_name = argd['name']
    #        
    #    config_strings = get_xml_from_config(["search", "issue_number", "rule"], journal_name)
    #    try:
    #        try:    
    #            search_page_template = config_strings["search"][0]
    #        except:
    #            raise InvenioWebJournalNoArticleTemplateError(journal_name) # todo: new exception
    #    except InvenioWebJournalNoArticleTemplateError:
    #        register_exception(req=req)
    #        return webjournal_error_box(req,
    #                                    "Search Page Template not found",
    #                                    "Problem with the configuration for this journal.",
    #                                    "The system couldn't find the template for the search result page of this journal. This is a mandatory file and thus indicates that the journal was setup wrong or produced an internal error. If you are neither admin nor developer there is nothing you can do at this point, but send an email request. We apologize for the inconvenience.")
    #    search_page_template_path = 'webjournal/%s' % (search_page_template)
    #    try:
    #        try:
    #            issue_number_tag = config_strings["issue_number"][0]
    #        except KeyError:
    #            raise InvenioWebJournalNoIssueNumberTagError(journal_name)
    #    except InvenioWebJournalNoIssueNumberTagError:
    #        register_exception(req=req)
    #        return webjournal_error_box(req,
    #                                    title="No Issues",
    #                                    title_msg="Problem with the configuration of this journal",
    #                                    msg="The system couldn't find a definition for an issue numbering system. Issue numbers conrol the date of the publication you are seing. This indicates that there is an error in the setup of this journal or the Software itself. There is nothing you can do at the moment. If you wish you can send an inquiry to the responsible developers. We apologize for the inconvenience.")
    #    rule_list = config_strings["rule"]
    #    try:
    #        if len(rule_list) == 0:
    #            raise InvenioWebJournalNoArticleRuleError() 
    #    except InvenioWebJournalNoArticleRuleError, e:     
    #        register_exception(req=req)
    #        return webjournal_error_box(req,
    #                                    "No searchable Articles",
    #                                    "Problem with the configuration of this journal",
    #                                    "The system couldn't find the definitions for different article kinds (e.g. News, Sports, etc.). If there is nothing defined, nothing can be shown and it thus indicates that there is either a problem with the setup of this journal or in the Software itself. There is nothing you can do at this moment. If you wish you can send an inquiry to the responsible developers. We apologize for the inconvenience.")
    #    category_rules = []
    #    if argd['category'] == []:
    #        # append all categories
    #        for rule_string in rule_list:
    #            marc = {}
    #            marc["category"] = rule_string.split(",")[0]
    #            rule = rule_string.split(",")[1]
    #            marc_datafield = rule.split(":")[0]
    #            marc["rule_match"] = rule.split(":")[1]
    #            marc["marc_tag"] = marc_datafield[1:4]
    #            marc["marc_ind1"] = (marc_datafield[4] == "_") and " " or marc_datafield[4]
    #            marc["marc_ind2"] = (marc_datafield[5] == "_") and " " or marc_datafield[5]
    #            marc["marc_subfield"] = marc_datafield[6]
    #            category_rules.append(marc)
    #    else:
    #        # append only categories from the url param
    #        for single_category in argd['category']:
    #            rule_string = get_rule_string_from_rule_list(rule_list, single_category)
    #            marc = {}
    #            marc["category"] = rule_string.split(",")[0]
    #            rule = rule_string.split(",")[1]
    #            marc_datafield = rule.split(":")[0]
    #            marc["rule_match"] = rule.split(":")[1]
    #            marc["marc_tag"] = marc_datafield[1:4]
    #            marc["marc_ind1"] = (marc_datafield[4] == "_") and " " or marc_datafield[4]
    #            marc["marc_ind2"] = (marc_datafield[5] == "_") and " " or marc_datafield[5]
    #            marc["marc_subfield"] = marc_datafield[6]
    #            category_rules.append(marc)
    #            
    #    category_fields = "\n".join(['''
    #                                <datafield tag="%s" ind1="%s" ind2="%s">
    #                                    <subfield code="%s">%s</subfield>
    #                                </datafield> 
    #                                 ''' % (marc["marc_tag"],
    #                                         marc["marc_ind1"],
    #                                         marc["marc_ind2"],
    #                                         marc["marc_subfield"],
    #                                         marc["rule_match"]) for marc in category_rules])
    #    
    #    issue_number_fields = "\n".join(['''
    #                        <datafield tag="%s" ind1="%s" ind2="%s">
    #                            <subfield code="%s">%s</subfield>
    #                        </datafield>
    #    ''' % (issue_number_tag[:3],
    #           (issue_number_tag[3] == "_") and " " or issue_number_tag[3],
    #           (issue_number_tag[4] == "_") and " " or issue_number_tag[4],
    #           issue_number_tag[5],
    #           issue_number) for issue_number in argd['issue']])
    #    
    #    temp_marc = '''<record>
    #                        <controlfield tag="001">0</controlfield>
    #                        %s
    #                        %s
    #                    </record>''' % (issue_number_fields, category_fields)
    #
    #
    #    # create a record and get HTML back from bibformat
    #    bfo = BibFormatObject(0, ln=argd['ln'], xml_record=temp_marc, req=req) # pass 0 for rn, we don't need it
    #    html_out = format_with_format_template(search_page_template_path, bfo)[0]
    #       
    #    #perform_request_search(cc="News Articles", p="families and 773__n:23/2007")
    #    #cc = argd['category']
    #    #p = keyword
    #    #for issue_number in argd['issue_number']:
    #    #    p += " and 773__n:%s" % issue_number
    #    ## todo: issue number tag generic from config
    #    #results = perform_request_search(cc=cc, p=p)
    #    
    #    return html_out

if __name__ == "__main__":
    index()
