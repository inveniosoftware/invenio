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

from mod_python import apache
from invenio.access_control_engine import acc_authorize_action
from invenio.config import weburl, webdir, cdslang, etcdir, \
                           CFG_ACCESS_CONTROL_LEVEL_SITE
from invenio.messages import gettext_set_language
from invenio.webpage import page
from invenio.webuser import getUid, page_not_authorized, isGuestUser
from invenio.webbasket import *
from invenio.webbasket_config import CFG_WEBBASKET_CATEGORIES, \
                                     CFG_WEBBASKET_ACTIONS
from invenio.urlutils import get_referer, redirect_to_url
from invenio.webinterface_handler import wash_urlargd, WebInterfaceDirectory

from invenio.errorlib import register_exception
from webjournal_config import InvenioWebJournalNoArticleNumberError, \
                                InvenioWebJournalNoArticleRuleError, \
                                InvenioWebJournalNoIndexTemplateError, \
                                InvenioWebJournalNoIssueNumberTagError, \
                                InvenioWebJournalNoArticleNumberError, \
                                InvenioWebJournalNoArticleTemplateError, \
                                webjournal_missing_info_box, \
                                webjournal_error_box

import time
import os
import smtplib
from urllib2 import urlopen
from email import message_from_string
from xml.dom import minidom
from invenio.bibformat_engine import format_with_format_template, BibFormatObject
from invenio.search_engine import search_pattern

from invenio.webjournal_utils import get_recid_from_order, \
                                        get_recid_from_order_CERNBulletin, \
                                        parse_url_string, \
                                        get_xml_from_config, \
                                        please_login, \
                                        get_current_issue, \
                                        get_rule_string_from_rule_list, \
                                        get_monday_of_the_week, \
                                        createhtmlmail, \
                                        put_css_in_file

class WebInterfaceJournalPages(WebInterfaceDirectory):
    """Defines the set of /journal pages."""

    _exports = ['', 'administrate', 'article', 'issue_control', 'search', 'alert',
                'feature_record', 'popup']

    def index(self, req, form):
        """Index page."""
        argd = wash_urlargd(form, {'name': (str, ""),
                                    'issue': (str, ""),
                                    'category': (str, ""),
                                    'ln': (str, "")}
                            )
        # get / set url parameter
        journal_name = ""
        issue_number = ""
        category = ""
        req.journal_defaults = {}
        try:
            journal_name = argd['name']
            if journal_name == "":
                raise KeyError
        except KeyError:
            register_exception(stream='warning', req=req, suffix="No Journal Name was provided.")
            return webjournal_missing_info_box(req, title="Template not found",
                                          msg_title="We don't know which journal you are looking for",
                                          msg='''You were looking for a journal without providing a name.
                    Unfortunately we cannot know which journal you are looking for.
                    Below you have a selection of journals that are available on this server.
                    If you should find your journal there, just click the link,
                    otherwise please contact the server admin and ask for existence
                    of the journal you are looking for.''')
        try:
            issue_number = argd['issue']
            if issue_number == "":
                raise KeyError
        except KeyError:
            issue_number = get_current_issue(journal_name)
            req.journal_defaults["issue"] = issue_number
        try :
            category = argd['category']
        except KeyError:
            pass # optional parameter
        try:
            language = argd['ln']
        except KeyError:
            language = "en"
            req.journal_defaults["ln"] = "en"
            # english is default
        # get all strings you want from the config files
        config_strings = get_xml_from_config(["index", "rule", "issue_number"], journal_name)        
        try:
            try:
                index_page_template = config_strings["index"][0]
            except:
                raise InvenioWebJournalNoIndexTemplateError(journal_name)
        except InvenioWebJournalNoIndexTemplateError, e:
            register_exception(req=req)
            return webjournal_error_box(req,
                                        "Main Page Template not found",
                                        "Problem with the configuration for this journal",
                                        "The system couldn't find the template for the main page of this journal. This is a mandatory file and thus indicates that the journal was setup wrong or produced an internal error. If you are neither admin nor developer there is nothing you can do at this point, but send an email request. We apologize for the inconvenience.")
        index_page_template_path = 'webjournal/%s' % (index_page_template)
        
        # find current selected category from the list of rules in the config
        rule_list = config_strings["rule"]
        try:
            if len(rule_list) == 0:
                raise InvenioWebJournalNoArticleRuleError() 
        except InvenioWebJournalNoArticleRuleError, e:     
            register_exception(req=req)
            return webjournal_error_box(req,
                                        "No Articles",
                                        "Problem with the configuration of this journal",
                                        "The system couldn't find the definitions for different article kinds (e.g. News, Sports, etc.). If there is nothing defined, nothing can be shown and it thus indicates that there is either a problem with the setup of this journal or in the Software itself. There is nothing you can do at this moment. If you wish you can send an inquiry to the responsible developers. We apologize for the inconvenience.")
        try:
            try:
                issue_number_tag = config_strings["issue_number"][0]
            except KeyError:
                raise InvenioWebJournalNoIssueNumberTagError(journal_name)
        except InvenioWebJournalNoIssueNumberTagError:
            register_exception(req=req)
            return webjournal_error_box(req,
                                        title="No Issues",
                                        title_msg="Problem with the configuration of this journal",
                                        msg="The system couldn't find a definition for an issue numbering system. Issue numbers conrol the date of the publication you are seing. This indicates that there is an error in the setup of this journal or the Software itself. There is nothing you can do at the moment. If you wish you can send an inquiry to the responsible developers. We apologize for the inconvenience.")
        
        current_category_in_list = 0
        i = 0
        if category != "":
            for rule_string in rule_list:
                category_from_config = rule_string.split(",")[0]
                if category_from_config.lower() == category.lower():
                    current_category_in_list = i
                i+=1
        else:
            # add the first category to the url string
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
        bfo = BibFormatObject(0, ln=language, xml_record=temp_marc, req=req) # pass 0 for rn, we don't need it
        html_out = format_with_format_template(index_page_template_path, bfo)[0]
        # done ;)
        return html_out
    
    def article(self, req, form):
        """
        """
        argd = wash_urlargd(form, {'name': (str, ""),
                                    'issue': (str, ""),
                                    'category': (str, ""),
                                    'number': (str, ""),
                                    'ln': (str, "")}
                            )
        
         # get / set url parameter
        journal_name = ""
        issue_number = ""
        category = ""
        number = ""
        req.journal_defaults = {}
        try:
            journal_name = argd['name']
            if journal_name == "":
                raise KeyError
        except KeyError:
            register_exception(stream='warning', req=req, suffix="No Journal Name was provided.")
            return webjournal_missing_info_box(req, title="Template not found",
                                          msg_title="We don't know which journal you are looking for",
                                          msg='''You were looking for a journal without providing a name.
                    Unfortunately we cannot know which journal you are looking for.
                    Below you have a selection of journals that are available on this server.
                    If you should find your journal there, just click the link,
                    otherwise please contact the server admin and ask for existence
                    of the journal you are looking for.''')
        try:
            issue_number = argd['issue']
            if issue_number == "":
                raise KeyError
        except KeyError:
            issue_number = get_current_issue(journal_name)
            req.journal_defaults["issue"] = issue_number
        try:
            try:
                number = argd['number']
                if number == "":
                    raise KeyError
            except KeyError:
                raise InvenioWebJournalNoArticleNumberError(journal_name)
        except InvenioWebJournalNoArticleNumberError, e: 
            register_exception(req=req)
            return webjournal_error_box(req,
                                        title="No Article Number",
                                        title_msg="We couldn't find the article you're looking for",
                                        msg='''The system could not deduce the
                article number you were looking for. This could have several
                reasons. If you typed the adress directly to the browser, try
                looking at the list of available journals <a href="%s/journal">
                here</a>. If you came to this page from a regular journal, then
                this is most probably an error in the Software or the Archive
                and there is nothing you can do at this point. If you wish you
                can send an inquiry to the responsible developers. We apologize
                for the inconvenience.''' % weburl)
        try:
            category = argd['category']
        except KeyError:
            pass # optional parameter
        try:
            language = argd['ln']
        except KeyError:
            language = "en"
            req.journal_defaults["ln"] = "en"
        config_strings = get_xml_from_config(["detailed", "rule"], journal_name)
        # get the path to the format_template of this page    
        try:
            try:    
                index_page_template = config_strings["detailed"][0]
            except:
                raise InvenioWebJournalNoArticleTemplateError(journal_name)
        except InvenioWebJournalNoArticleTemplateError:
            register_exception(req=req)
            return webjournal_error_box(req,
                                        "Article view Template not found",
                                        "Problem with the configuration for this journal.",
                                        "The system couldn't find the template for the article pages of this journal. This is a mandatory file and thus indicates that the journal was setup wrong or produced an internal error. If you are neither admin nor developer there is nothing you can do at this point, but send an email request. We apologize for the inconvenience.")
            
        index_page_template_path = 'webjournal/%s' % (index_page_template)
        
        # find current selected category from the list of rules in the config
        rule_list = config_strings["rule"]
        current_category_in_list = 0
        i = 0
        if category != "":
            for rule_string in rule_list:
                category_from_config = rule_string.split(",")[0]
                if category_from_config.lower() == category.lower():
                    current_category_in_list = i
                i+=1
        # get the important values for the category from the config file        
        rule_string = rule_list[current_category_in_list].replace(" ", "")
        rule = rule_string.split(",")[1]
        
       # recid = get_recid_from_order(number, rule, issue_number)
        recid = get_recid_from_order_CERNBulletin(number, rule, issue_number)
        # create a record and get HTML back from bibformat
        bfo = BibFormatObject(recid, ln=language, req=req)
        
        html_out = format_with_format_template(index_page_template_path,
                                               bfo)[0]
        return html_out
        
    def administrate(self, req, form):
        """Index page."""
        return "Not implemented yet."
    
    def feature_record(self, req, form):
        """
        in the CERNBulletin used for "For the Eyes" section
        """
        argd = wash_urlargd(form, {'name': (str, ""),
                                    'recid': (str, ""),
                                    'featured': (str, "false"),
                                    'url': (str, "")
                                    })
        if argd['name'] == "":
            return webjournal_missing_info_box(req, title="Journal not found",
                                          msg_title="We don't know which journal you are looking for",
                                          msg='''You were looking for a journal without providing a name.
                    Unfortunately we cannot know which journal you are looking for.
                    Below you have a selection of journals that are available on this server.
                    If you should find your journal there, just click the link,
                    otherwise please contact the server admin and ask for existence
                    of the journal you are looking for.''')
        else:
            journal_name = argd['name']
            
        # login
        if acc_authorize_action(getUid(req), 'cfgwebjournal', name="%s" % journal_name)[0] != 0:
            # todo: pass correct language
            return please_login(req, journal_name, backlink='%s/journal/feature_record?name=%s' % (weburl, journal_name))
       
        if argd['recid'] == "":
            interface = '''
            <form action="%s/journal/feature_record" name="alert">
                <input type="hidden" name="name" value="%s"/>
                <p>Featured Record's ID:</p>
                <input type="text" name="recid" value="" />
                <p>Link to the picture that should be displayed</p>
                <input type="text" name="url" value="" />
                <br/>
                <input class="formbutton" type="submit" value="feature" name="featured"/>
            </form>
            ''' % (weburl, journal_name)
            return page(title="Feature a record", body=interface)
        else:
            fptr = open('%s/webjournal/%s/featured_record' % (etcdir, journal_name), "w")
            fptr.write(argd['recid'])
            fptr.write('\n')
            fptr.write(argd['url'])
            fptr.close()
            return page(title="Successfully featured record: %s" % argd['recid'], body="")
    
    def alert(self, req, form):
        """Alert system."""
        argd = wash_urlargd(form, {'name': (str, ""),
                                    'sent': (str, "false"),
                                    'plainText': (str, u''),
                                    'htmlMail': (str, ""),
                                    'recipients': (str, ""),
                                    'subject': (str, "")})
        if argd['name'] == "":
            return webjournal_missing_info_box(req, title="Journal not found",
                                          msg_title="We don't know which journal you are looking for",
                                          msg='''You were looking for a journal without providing a name.
                    Unfortunately we cannot know which journal you are looking for.
                    Below you have a selection of journals that are available on this server.
                    If you should find your journal there, just click the link,
                    otherwise please contact the server admin and ask for existence
                    of the journal you are looking for.''')
        else:
            journal_name = argd['name']
        config_strings = get_xml_from_config(["niceName", "niceURL"], journal_name)
        try:
            display_name = config_strings["niceName"][0]
        except:
            display_name = journal_name
        try:
            url = config_string["niceURL"][0]
        except:
            url = '%s/journal/%s' % (weburl, journal_name)
        issue = get_current_issue(journal_name)
        # login
        if acc_authorize_action(getUid(req), 'cfgwebjournal', name="%s" % journal_name)[0] != 0:
            # todo: pass correct language
            return please_login(req, journal_name, backlink='%s/journal/alert?name=%s' % (weburl, journal_name))
        subject = "%s %s released!" % (display_name, issue)
        plain_text = u'''Dear Subscriber,
                    
The latest issue of the %s, no. %s, has been released.
You can access it at the following URL:
%s

Best Wishes,
The %s team

----
Cher Abonné,

Le nouveau numéro du %s, no. %s, vient de paraître.
Vous pouvez y accéder à cette adresse :
%s

Bonne lecture,
L'équipe du %s
''' % (display_name, issue, url, display_name,
        display_name, issue, url, display_name)

        plain_text = plain_text.encode('utf-8')
        
        if argd['sent'] == "false":
            interface = '''
            <form action="%s/journal/alert" name="alert" method="POST">
                <input type="hidden" name="name" value="%s"/>
                <p>Recipients:</p>
                <input type="text" name="recipients" value="gabriel.hase@cern.ch" />
                <p>Subject:</p>
                <input type="text" name="subject" value="%s" />
                <p>Plain Text Message:</p>
                <textarea name="plainText" wrap="soft" rows="25" cols="50">%s</textarea>
                <p> Send Homepage as html:
                    <input type="checkbox" name="htmlMail" value="html" checked="checked" />
                </p>
                <br/>
                <input class="formbutton" type="submit" value="alert" name="sent"/>
            </form>
            ''' % (weburl, journal_name, subject, plain_text)
            return page(title="alert system", body=interface)
        else:
            plain_text = argd['plainText']
            subject = argd['subject']
            
            if argd['htmlMail'] == "html": 
                html_file = urlopen('%s/journal/?name=%s&ln=en' % (weburl, journal_name))    
                html_string = html_file.read()
                html_file.close()
                html_string = put_css_in_file(html_string, journal_name)
            else:
                html_string = plain_text.replace("\n", "<br/>")
            #html_message = message_from_string(html_string)
            
            #subject = "%s %s released!" % (display_name, issue)
            message = createhtmlmail(html_string, plain_text, subject, argd['recipients'])
            server = smtplib.SMTP("localhost", 25)
            server.sendmail('Bulletin-Support@cern.ch', argd['recipients'], message)

            return page(title="Alert sent successfully!", body="")
    
    def search(self, req, form):
        """
        Creates a temporary record containing all the information needed for
        the search, meaning list of issue_numbers (timeframe), list of keywords,
        list of categories to search in. In this way everything can be configured
        globally in the config for the given webjournal and we can reuse the bibformat
        for whatever search we want.
        """
        argd = wash_urlargd(form, {'name': (str, ""),
                                    'category': (list, []),
                                    'issue': (list, []),
                                    'keyword': (str, ""),
                                    'ln': (str, cdslang)})
        if argd['name'] == "":
            register_exception(stream='warning',
                               suffix="User tried to search without providing a journal name.")
            return webjournal_missing_info_box(req, title="Journal not found",
                                          msg_title="We don't know which journal you are looking for",
                                          msg='''You were looking for a journal without providing a name.
                    Unfortunately we cannot know which journal you are looking for.
                    Below you have a selection of journals that are available on this server.
                    If you should find your journal there, just click the link,
                    otherwise please contact the server admin and ask for existence
                    of the journal you are looking for.''')
        else:
            journal_name = argd['name']
            
        config_strings = get_xml_from_config(["search", "issue_number", "rule"], journal_name)
        try:
            try:    
                search_page_template = config_strings["search"][0]
            except:
                raise InvenioWebJournalNoArticleTemplateError(journal_name) # todo: new exception
        except InvenioWebJournalNoArticleTemplateError:
            register_exception(req=req)
            return webjournal_error_box(req,
                                        "Search Page Template not found",
                                        "Problem with the configuration for this journal.",
                                        "The system couldn't find the template for the search result page of this journal. This is a mandatory file and thus indicates that the journal was setup wrong or produced an internal error. If you are neither admin nor developer there is nothing you can do at this point, but send an email request. We apologize for the inconvenience.")
        search_page_template_path = 'webjournal/%s' % (search_page_template)
        try:
            try:
                issue_number_tag = config_strings["issue_number"][0]
            except KeyError:
                raise InvenioWebJournalNoIssueNumberTagError(journal_name)
        except InvenioWebJournalNoIssueNumberTagError:
            register_exception(req=req)
            return webjournal_error_box(req,
                                        title="No Issues",
                                        title_msg="Problem with the configuration of this journal",
                                        msg="The system couldn't find a definition for an issue numbering system. Issue numbers conrol the date of the publication you are seing. This indicates that there is an error in the setup of this journal or the Software itself. There is nothing you can do at the moment. If you wish you can send an inquiry to the responsible developers. We apologize for the inconvenience.")
        rule_list = config_strings["rule"]
        try:
            if len(rule_list) == 0:
                raise InvenioWebJournalNoArticleRuleError() 
        except InvenioWebJournalNoArticleRuleError, e:     
            register_exception(req=req)
            return webjournal_error_box(req,
                                        "No searchable Articles",
                                        "Problem with the configuration of this journal",
                                        "The system couldn't find the definitions for different article kinds (e.g. News, Sports, etc.). If there is nothing defined, nothing can be shown and it thus indicates that there is either a problem with the setup of this journal or in the Software itself. There is nothing you can do at this moment. If you wish you can send an inquiry to the responsible developers. We apologize for the inconvenience.")
        category_rules = []
        if argd['category'] == []:
            # append all categories
            for rule_string in rule_list:
                marc = {}
                marc["category"] = rule_string.split(",")[0]
                rule = rule_string.split(",")[1]
                marc_datafield = rule.split(":")[0]
                marc["rule_match"] = rule.split(":")[1]
                marc["marc_tag"] = marc_datafield[1:4]
                marc["marc_ind1"] = (marc_datafield[4] == "_") and " " or marc_datafield[4]
                marc["marc_ind2"] = (marc_datafield[5] == "_") and " " or marc_datafield[5]
                marc["marc_subfield"] = marc_datafield[6]
                category_rules.append(marc)
        else:
            # append only categories from the url param
            for single_category in argd['category']:
                rule_string = get_rule_string_from_rule_list(rule_list, single_category)
                marc = {}
                marc["category"] = rule_string.split(",")[0]
                rule = rule_string.split(",")[1]
                marc_datafield = rule.split(":")[0]
                marc["rule_match"] = rule.split(":")[1]
                marc["marc_tag"] = marc_datafield[1:4]
                marc["marc_ind1"] = (marc_datafield[4] == "_") and " " or marc_datafield[4]
                marc["marc_ind2"] = (marc_datafield[5] == "_") and " " or marc_datafield[5]
                marc["marc_subfield"] = marc_datafield[6]
                category_rules.append(marc)
                
        category_fields = "\n".join(['''
                                    <datafield tag="%s" ind1="%s" ind2="%s">
                                        <subfield code="%s">%s</subfield>
                                    </datafield> 
                                     ''' % (marc["marc_tag"],
                                             marc["marc_ind1"],
                                             marc["marc_ind2"],
                                             marc["marc_subfield"],
                                             marc["rule_match"]) for marc in category_rules])
        
        issue_number_fields = "\n".join(['''
                            <datafield tag="%s" ind1="%s" ind2="%s">
                                <subfield code="%s">%s</subfield>
                            </datafield>
        ''' % (issue_number_tag[:3],
               (issue_number_tag[3] == "_") and " " or issue_number_tag[3],
               (issue_number_tag[4] == "_") and " " or issue_number_tag[4],
               issue_number_tag[5],
               issue_number) for issue_number in argd['issue']])
        
        temp_marc = '''<record>
                            <controlfield tag="001">0</controlfield>
                            %s
                            %s
                        </record>''' % (issue_number_fields, category_fields)


        # create a record and get HTML back from bibformat
        bfo = BibFormatObject(0, ln=argd['ln'], xml_record=temp_marc, req=req) # pass 0 for rn, we don't need it
        html_out = format_with_format_template(search_page_template_path, bfo)[0]
           
        #perform_request_search(cc="News Articles", p="families and 773__n:23/2007")
        #cc = argd['category']
        #p = keyword
        #for issue_number in argd['issue_number']:
        #    p += " and 773__n:%s" % issue_number
        ## todo: issue number tag generic from config
        #results = perform_request_search(cc=cc, p=p)
        
        return html_out
    
    def issue_control(self, req, form):
        """
        page that allows full control over creating, backtracing, adding to,
        removing from issues.
        """
        argd = wash_urlargd(form, {'name': (str, ""),
                                    'add': (str, ""),
                                    'action_publish': (str, "cfg"),
                                    'issue_number': (list, [])}
                            )
        if argd['name'] == "":
            return webjournal_missing_info_box(req, title="Journal not found",
                                          msg_title="We don't know which journal you are looking for",
                                          msg='''You were looking for a journal without providing a name.
                    Unfortunately we cannot know which journal you are looking for.
                    Below you have a selection of journals that are available on this server.
                    If you should find your journal there, just click the link,
                    otherwise please contact the server admin and ask for existence
                    of the journal you are looking for.''')
        else:
            journal_name = argd['name']
            
        action = argd['action_publish']
        issue_numbers = argd['issue_number']
        
        if acc_authorize_action(getUid(req), 'cfgwebjournal', name="%s" % journal_name)[0] != 0:
            # todo: pass correct language
            return please_login(req, journal_name)
        
        if action == "cfg" or action == "Refresh":
            active_issues = []
            if action == "Refresh":
                active_issues = issue_numbers
                try:
                    active_issues.remove("mm/yyyy")
                except:
                    pass
                from sets import Set
                active_issues = list(Set(active_issues)) # avoid double entries
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
                                       suffix="Couldn't find any current issue, if this is the first time for this journal this is fine.")
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
            
            output = '''
                        <div align="center">
                            <h2>CERN eBulletin Publishing Interface</h2>
                            <p>This interface gives you the possibilite to create
                            your current webjournal publication. Every checked
                            issue number will be in the current publication. Once
                            you've made your selection you can publish the new
                            issue by clicking the Publish button at the end.</p>
                            <form action="%s/journal/issue_control" name="publish">
                                <input type="hidden" name="name" value="%s"/>
                                <ul>
                                <p>Active issues::..</p>
                                %s
                                <br/>
                                <p>This weeks issue::..</p>
                                <li>%s</li>
                                <p>Add custom issue</p>
                                <input type="text" value="mm/yyyy" name="issue_number"/>
                                <input class="formbutton" type="submit" value="Refresh" name="action_publish"/>
                                <br/>
                                <br/>
                                <input class="formbutton" type="submit" value="Publish" name="action_publish"/>
                            </form>
                        </div>
            ''' % (weburl,
                   journal_name,
                   "".join(['<li><input type="checkbox" name="issue_number" value="%s" CHECKED>&nbsp;%s</input></li>' % (issue, issue) for issue in active_issues]),
                   '<input type="checkbox" name="issue_number" value="%s">&nbsp;%s</input>' % (this_weeks_issue, this_weeks_issue))
            
        elif action == "Publish":
            active_issues = issue_numbers
            try:
                active_issues.remove("mm/yyyy")
            except:
                pass
            from sets import Set
            active_issues = list(Set(active_issues)) # avoid double entries
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
                                                     get_monday_of_the_week(high_bound, year)))
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
            
            output = '''
                        <h2>Congrats! You are a true publisher.</h2>
                        <p>Your current journal has been published with the
                        following issue numbers: </p>
                        <ul>
                            %s
                        </ul>
                        <br/>
                        <p>If you need to make changes just go back <a href="%s">here</a></p>
                        <p>To look at your newly creted bulletin, go <a href="%s">here</a></p>
            ''' % ("".join(["<li>%s</li>" % issue for issue in active_issues]),
                    weburl + "/journal/issue_control?name=" + journal_name,
                    weburl + "/journal/?name=" + journal_name)
            
        return page(title="Publish System", body=output)
    
    def popup(self, req, form):
        """
        checks if the required popup page is in the cache and serves it if so
        """
        argd = wash_urlargd(form, {'name': (str, ""),
                                    'record': (str, ""),
                                    'type': (str, ""),
                                    'ln': (str, "")
                                    })
        if argd['name'] == "":
            return webjournal_missing_info_box(req, title="Journal not found",
                                          msg_title="We don't know which journal you are looking for",
                                          msg='''You were looking for a journal without providing a name.
                    Unfortunately we cannot know which journal you are looking for.
                    Below you have a selection of journals that are available on this server.
                    If you should find your journal there, just click the link,
                    otherwise please contact the server admin and ask for existence
                    of the journal you are looking for.''')
        else:
            journal_name = argd['name']
            
        if argd['record'] == "":
            return "no recid" # todo: make exception
        else:
            record = argd['record']
            
        if argd['type'] == "":
            return "no popup type" # todo: make exception
        else:
            type = argd['type']
            
        if argd['ln'] == "":
            ln = "en"
        else:
            ln = argd['ln']
            
        config_strings = get_xml_from_config(["popup"], journal_name)        
        try:
            popup_page_template = config_strings["popup"][0]
        except:
            return "no popup template" # todo: make exception
        
        popup_page_template_path = 'webjournal/%s' % popup_page_template
        
#        temp_marc = '''<record>
#                            <controlfield tag="001">%s</controlfield>
#                        </record>''' % (record)
        #temp_marc = temp_marc.decode('utf-8').encode('utf-8')
        
        #xml_record = record_get_xml(recid)
        #if xml_record == "":
        #    return
        #record = bibrecord.create_record(xml_answer)
        # create a record and get HTML back from bibformat
        #bfo = BibFormatObject(0, ln=ln, xml_record=temp_marc, req=req) # pass 0 for rn, we don't need it
        bfo = BibFormatObject(record, ln=ln, req=req)

        html_out = format_with_format_template(popup_page_template_path, bfo)[0]
        # done ;)
        return html_out
        
        #    
        #try:
        #    open('%s/%s_%s_%s_%s.html' % (cachedir,
        #                                  journal_name,
        #                                  type,
        #                                  record,
        #                                  ln), "r")
        #except:
        #    return "popup does not exist" # todo: make exception, and make it in the popup!!
        #
        #index()

if __name__ == "__main__":
    index()
