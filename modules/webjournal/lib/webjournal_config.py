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

import os

from invenio.config import adminemail, supportemail, etcdir, weburl, cdslang
from invenio.messages import gettext_set_language
from invenio.webpage import page
from invenio.htmlutils import escape_html
from invenio.messages import gettext_set_language

from invenio.webjournal_utils import parse_url_string
from invenio.webjournal_templates import tmpl_webjournal_error_box,\
                                        tmpl_webjournal_missing_info_box
#from invenio.data_cacher import SQLDataCacher
#
#CFG_JOURNAL_CONFIG_CACHE = {}
#
#def initialize_config_cache():
#    """
#    """
#    journal_id_names = SQLDataCacher("SELECT * FROM jrnJOURNAL", affected_tables=(jrnJOURNAL))

class InvenioWebJournalNoIndexTemplateError(Exception):
    """Exception if no index template is specified in the config."""
    def __init__(self, language, journal_name):
        """Initialisation."""
        self.journal = journal_name
        self.language = language

    def __str__(self):
        """String representation."""
        return 'Admin did not provide a template for the index page of \
        journal: %s. \
        The path to such a file should be given in the config.xml of\
        this journal under the tag <format_template><index>...\
        </index></format_template>' % repr(self.journal)
    
    def user_box(self):
        """
        user-friendly error message with formatting.
        """
        _ = gettext_set_language(self.language)
        return tmpl_webjournal_error_box(self.language,
        _('Internal Configuration Error'),
        _('There is no format configured for this journals index page'),
        _('Admin did not provide a template for the index page of journal: %s. \
        The path to such a file should be given in the config.xml of\
        this journal under the tag <format_template><index>...\
        </index></format_template>') % escape_html(self.journal))

class InvenioWebJournalNoArticleTemplateError(Exception):
    """
    Exception if an article was called without its order number.
    """
    def __init__(self, language, journal_name):
        """
        Initialisation.
        """
        self.journal = journal_name
        self.language = language
        
    def __str__(self):
        """
        String representation.
        """
        return 'Admin did not provide a template for the article view page of journal: %s. \
        The path to such a file should be given in the config.xml of this journal \
        under the tag <format_template><detailed>...</detailed></format_template>' % repr(self.journal)
    
    def user_box(self):
        """
        user-friendly error message with formatting.
        """
        _ = gettext_set_language(self.language)  
        return tmpl_webjournal_error_box(self.language,
            _('Internal Configuration Error'),
            _('There is no format configured for this journals index page'),
            _('Admin did not provide a template for the index page of journal: %s. \
        The path to such a file should be given in the config.xml of\
        this journal under the tag <format_template><index>...\
        </index></format_template>') % escape_html(self.journal))
    
class InvenioWebJournalNoPopupTemplateError(Exception):
    """
    Exception if an article was called without its order number.
    """
    def __init__(self, language, journal_name):
        """
        Initialisation.
        """
        self.journal = journal_name
        self.language = language
        
    def __str__(self):
        """
        String representation.
        """
        return 'Admin did not provide a template for the popup view page \
        of journal: %s. \
        The path to such a file should be given in the config.xml of this \
        journal under the tag \
        <format_template><popup>...</popup></format_template>' % repr(
            self.journal)
    
    def user_box(self):
        """
        user-friendly error message with formatting.
        """
        _ = gettext_set_language(self.language)  
        return tmpl_webjournal_error_box(self.language,
        _('Internal Configuration Error'),
        _('There is no format configured for this journals popup page'),
        _('Admin did not provide a template for the popup page of journal: %s. \
        The path to such a file should be given in the config.xml of\
        this journal under the tag <format_template><popup>...\
        </popup></format_template>') % escape_html(self.journal))
    
class InvenioWebJournalNoArticleRuleError(Exception):
    """
    Exception if there are no article type rules defined.
    """
    def __init__(self, language, journal_name):
        """
        Initialisation.
        """
        self.journal = journal_name
        self.language = language
    def __str__(self):
        """
        String representation.
        """
        return 'The config.xml file for journal: %s does not contain any \
        article rules. These rules are needed to associate collections from \
        your Invenio installation to navigable article types. A rule should \
        have the form of <rule>NameOfArticleType, \
        marc_tag:ExpectedContentOfMarcTag' % escape_html(self.journal)
        
    def user_box(self):
        """
        user-friendly error message with formatting.
        """
        _ = gettext_set_language(self.language)
        return tmpl_webjournal_error_box(self.language,
            _("No Articles"),
            _("Problem with the configuration of this journal"),
            _("The system couldn't find the definitions for different article \
            kinds (e.g. News, Sports, etc.). If there is nothing defined, \
            nothing can be shown and it thus indicates that there is either a \
            problem with the setup of this journal or in the Software itself.\
            There is nothing you can do at this moment. If you wish you can \
            send an inquiry to the responsible developers. We apologize \
            for the inconvenience."))
        
    
class InvenioWebJournalNoIssueNumberTagError(Exception):
    """
    Exception if there is no marc tag for issue number defined.
    """
    def __init__(self, language, journal_name):
        """
        Initialisation.
        """
        self.journal = journal_name
        self.language = language
        
    def __str__(self):
        """
        String representation.
        """
        return 'The config.xml file for journal: %s does not contain a marc tag\
         to deduce the issue number from. WebJournal is an issue number based \
        system, meaning you have to give some form of numbering system in a \
        dedicated marc tag, so the system can see which is the active journal \
        publication of the date.' % repr(self.journal)
    
    def user_box(self):
        """
        user-friendly error message with formatting.
        """
        _ = gettext_set_language(self.language)    
        return tmpl_webjournal_error_box(self.language,
                _("No Issues"),
                _("Problem with the configuration of this journal"),
                _("The system couldn't find a definition for an issue \
                    numbering system. Issue numbers conrol the date of the \
                    publication you are seing. This indicates that there is an \
                    error in the setup of this journal or the Software itself. \
                    There is nothing you can do at the moment. If you wish you \
                    can send an inquiry to the responsible developers. We \
                    apologize for the inconvenience."))
        
    
class InvenioWebJournalNoArticleNumberError(Exception):
    """
    Exception if an article was called without its order number.
    """
    def __init__(self, language, journal_name):
        """
        Initialisation.
        """
        self.journal = journal_name
        self.language = language
        
    def __str__(self):
        """
        String representation.
        """
        return 'In Journal %s an article was called without specifying the order \
        of this article in the issue. This parameter is mandatory and should be \
        provided by internal links in any case. Maybe this was a bad direct url \
        hack. Check where the request came from.' % repr(self.journal)
    
    def user_box(self):
        """
        user-friendly error message with formatting.
        """
        _ = gettext_set_language(self.language)  
        return tmpl_webjournal_error_box(self.language,
            _('Article Error'),
            _('We could not know which article you were looking for'),
            _('The url you passed did not provide an article number or the \
              article number was badly formed. If you \
              came to this page through some link on the journal page, please \
              report this to the admin. If you got this link through some \
              external resource, e.g. an email, you can try to put in a number \
              for the article in the url by hand or just visit the front \
              page at %s/journal/?name=%s') % (weburl, self.journal))

class InvenioWebJournalNoJournalOnServerError(Exception):
    """
    Exception that is thrown if there are no Journal instances on the server
    """
    def __init__(self, language):
        """
        Initialisation.
        """
        self.language = language
    
    def __str__(self):
        """
        String representation.
        """
        return 'Apparently there are no journals configured on this \
        installation of CDS Invenio. You can try to use the sample Invenio \
        Atlantis Journal for testing.'
    
    def user_box(self):
        """
        user-friendly message with formatting.
        """
        _ = gettext_set_language(self.language)
        return tmpl_webjournal_error_box(self.language,
                        _('No Journals available'),
                        _('We could not provide you any journals'),
                        _('It seems that there are no journals on this server. \
                        Please contact support if this is not right.'))
    
class InvenioWebJournalNoNameError(Exception):
    """
    """
    def __init__(self, language):
        """
        Initialisation.
        """
        self.language = language
    
    def __str__(self):
        """
        String representation.
        """
        return 'User probably forgot to add the name parameter for the journal\
        Maybe you also want to check if dns mappings are configured correctly.'
    
    def user_box(self):
        """
        user-friendly message with formatting.
        """
        _ = gettext_set_language(self.language)
        return webjournal_missing_info_box(self.language,
                        _("Select a Journal on this server"),
                        _("We couldn't guess which journal you are looking for"),
                        _("You did not provide an argument for a journal name, \
                        please select the journal you want to read in the list \
                        below."))
                                           
class InvenioWebJournalNoCurrentIssueError(Exception):
    """
    """
    def __init__(self, language):
        """
        Initialisation.
        """
        self.language = language
    
    def __str__(self):
        """
        String representation.
        """
        return 'There seems to be no current issue number stored for this \
        journal. Is this the first time you use the journal? Otherwise, check\
        configuration.'
    
    def user_box(self):
        """
        user-friendly message with formatting.
        """
        _ = gettext_set_language(self.language)
        return webjournal_error_box(self.language,
                    _('No current Issue'),
                    _('We could not find any informtion on the current issue'),
                    _('The configuration for the current issue seems to be empty.\
                    Try providing an issue number or check with support.'))
    

class InvenioWebJournalIssueNumberBadlyFormedError(Exception):
    """
    """
    def __init__(self, language, issue):
        """
        Initialisation.
        """
        self.language = language
        self.issue = issue
    
    def __str__(self):
        """
        String representation.
        """
        return 'The issue number was badly formed. If this comes from the \
        user it is no problem.'
    
    def user_box(self):
        """
        user-friendly message with formatting.
        """
        _ = gettext_set_language(self.language)
        return tmpl_webjournal_error_box(self.language,
                    _('Issue Number Badly formed'),
                    _('We could not read the issue number you provided'),
                    _('The issue number you provided in the url seems to be badly\
                    formed. Issue numbers have to be in the form of ww/YYYY, so\
                    e.g. 50/2007. You provided the issue number like so: \
                    %s.') % escape_html(self.issue))
    
class IvenioWebJournalNoPopupTypeError(Exception):
    """
    Exception that is thrown if a popup is requested without specifying the
    type of the popup to call.
    """
    def __init__(self, language, journal_name):
        """
        Initialisation.
        """
        self.language = language
        self.journal_name
    
    def __str__(self):
        """
        String representation.
        """
        return 'There was no popup type provided for a popup window on \
        journal %s.' % repr(self.journal_name)
    
    def user_box(self):
        """
        user-friendly message with formatting.
        """
        _ = gettext_set_language(self.language)
        return tmpl_webjournal_error_box(self.language,
                    _('No Popup Type'),
                    _('We could not know what kind of popup you requested'),
                    _('You called a popup window on CDS Invenio without \
                      specifying the type of the popup. Does this link come \
                      from a CDS Invenio Journal? If so, please contact \
                      support.'))
    
class InvenioWebJournalNoPopupRecordError(Exception):
    """
    Exception that is thrown if a popup is requested without specifying the
    type of the popup to call.
    """
    def __init__(self, language, journal_name, recid):
        """
        Initialisation.
        """
        self.language = language
        self.journal_name
        self.recid = recid
    
    def __str__(self):
        """
        String representation.
        """
        return 'There was no recid provided to the popup system of webjournal \
        or the recid was badly formed. The recid was %s' % repr(self.recid)
    
    def user_box(self):
        """
        user-friendly message with formatting.
        """
        _ = gettext_set_language(self.language)
        return tmpl_webjournal_error_box(self.language,
                    _('No Popup Record'),
                    _('We could not deduce the popup article you requested'),
                    _('You called a popup window on CDS Invenio without \
                      specifying a record in which you are interested or the \
                      record was badly formed. Does this link come \
                      from a CDS Invenio Journal? If so, please contact \
                      support.'))

class InvenioWebJournalReleaseUpdateError(Exception):
    """
    Exception that is thrown if an update release was not successful.
    """
    def __init__(self, language, journal_name):
        """
        Initialisation.
        """
        self.language = language
        self.journal_name = journal_name
    
    def __str__(self):
        """
        String representation.
        """
        return 'There were no updates submitted on a click on the update button.\
         This should never happen and must be due to an internal error.'
    
    def user_box(self):
        """
        user-friendly message with formatting.
        """
        _ = gettext_set_language(self.language)
        return tmpl_webjournal_error_box(self.language,
                    _('Update Error'),
                    _('There was an internal error'),
                    _('We encountered an internal error trying to update the \
                      journal issue. You can try to launch the update again or \
                      contact the Administrator. We apologize for the \
                      inconvenience.'))
    
class InvenioWebJournalReleaseDBError(Exception):
    """
    Exception that is thrown if an update release was not successful.
    """
    def __init__(self, language):
        """
        Initialisation.
        """
        self.language = language
        
    def __str__(self):
        """
        String representation.
        """
        return 'There was an error in synchronizing DB times with the actual \
        python time objects. Debug the code in: \
        webjournal_utils.issue_times_to_week_strings'
    
    def user_box(self):
        """
        user-friendly message with formatting.
        """
        _ = gettext_set_language(self.language)
        return tmpl_webjournal_error_box(self.language,
                    _('Publish DB Error'),
                    _('There was an internal error'),
                    _('We encountered an internal error trying to publish the \
                      journal issue. You can try to launch the publish interface \
                      again or contact the Administrator. We apologize for the \
                      inconvenience.'))
    
class InvenioWebJournalIssueNotFoundDBError(Exception):
    """
    Exception that is thrown if there was an issue number not found in the
    """
    def __init__(self, language, journal_name, issue_number):
        """
        Initialisation.
        """
        self.language = language
        self.journal_name = journal_name
        sefl.issue_number = issue_number
    
    def __str__(self):
        """
        String representation.
        """
        return 'The issue %s could not be found in the DB for journal %s.' % (self.issue_number,
                                                                              self.journal_name)
    
    def user_box(self):
        """
        user-friendly message with formatting.
        """
        _ = gettext_set_language(self.language)
        return tmpl_webjournal_error_box(self.language,
                    _('Publish Interface Error'),
                    _('We could not find a current issue in the Database'),
                    _('We encountered an internal error trying to get an issue \
                      number. You can try to refresh the page or \
                      contact the Administrator. We apologize for the \
                      inconvenience.'))
    
class InvenioWebJournalJournalIdNotFoundDBError(Exception):
    """
    Exception that is thrown if there was an issue number not found in the
    """
    def __init__(self, language, journal_name):
        """
        Initialisation.
        """
        self.language = language
        self.journal_name = journal_name
    
    def __str__(self):
        """
        String representation.
        """
        return 'The id for journal %s was not found in the Database. Make \
        sure the entry exists!' % (self.journal_name)
    
    def user_box(self):
        """
        user-friendly message with formatting.
        """
        _ = gettext_set_language(self.language)
        return tmpl_webjournal_error_box(self.language,
                    _('Journal ID Error'),
                    _('We could not find the id for this journal in the Database'),
                    _('We encountered an internal error trying to get the id \
                      for this journal. You can try to refresh the page or \
                      contact the Administrator. We apologize for the \
                      inconvenience.'))
    
#!!! depreceated !!!#
def webjournal_missing_info_box(language, title, msg_title, msg):
    """
    returns a box indicating that the given journal was not found on the
    server, leaving the opportunity to select an existing journal from a list.
    """
    #params = parse_url_string(req)
    #try:
    #    language = params["ln"]
    #except:
    #    language = cdslang
    _ = gettext_set_language(language)
    title = _(title)
    box_title = _(msg_title)
    box_text = _(msg)
    box_list_title = _("Available Journals")
    find_journals = lambda path: [entry for entry in os.listdir(str(path)) if os.path.isdir(str(path)+str(entry))]
    try:
        all_journals = find_journals('%s/webjournal/' % etcdir)
    except:
        all_journals = []
    box = '''<div style="text-align: center;">
                <fieldset style="width:400px; margin-left: auto; margin-right: auto;background: url('%s/img/blue_gradient.gif') top left repeat-x;">
                    <legend style="color:#a70509;background-color:#fff;"><i>%s</i></legend>
                    <p style="text-align:center;">%s</p>
                    <h2 style="color:#0D2B88;">%s</h2>
                    <ul class="webjournalBoxList">
                        %s
                    </ul>
                    <br/>
                    <div style="text-align:right;">Mail<a href="mailto:%s"> the Administrator.</a></div>
                </fieldset>
            </div>
            ''' % (weburl,
                   box_title,
                   box_text,
                   box_list_title,
                   "".join(['<li><a href="%s/journal/?name=%s">%s</a></li>' % (weburl, journal, journal) for journal in all_journals]),
                   adminemail)
    return page(title=title, body=box)


#!!! depreceated !!!#
def webjournal_error_box(language, title, title_msg, msg):
    """
    """
    #params = parse_url_string(req)
    #try:
    #    language = params["ln"]
    #except:
    #    language = cdslang
    _ = gettext_set_language(language)
    title = _(title)
    title_msg = _(title_msg)
    msg = _(msg)
    box = '''<div style="text-align: center;">
                <fieldset style="width:400px; margin-left: auto; margin-right: auto;background: url('%s/img/red_gradient.gif') top left repeat-x;">
                    <legend style="color:#a70509;background-color:#fff;"><i>%s</i></legend>
                    <p style="text-align:center;">%s</p>
                    <br/>
                    <div style="text-align:right;">Mail<a href="mailto:%s"> the Developers.</a></div>
                </fieldset>
            </div>
            ''' % (weburl, title_msg, msg, supportemail)
    return page(title=title, body=box)
    
