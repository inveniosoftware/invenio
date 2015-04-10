# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2007, 2008, 2009, 2010, 2011 CERN.
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
WebJournal exceptions classes
"""

from __future__ import unicode_literals

import cgi
from invenio.config import \
     CFG_SITE_URL, \
     CFG_ETCDIR
from invenio.base.i18n import gettext_set_language
from invenio.legacy.webjournal.utils import get_journal_name_intl
import invenio.legacy.template
webjournal_templates = invenio.legacy.template.load('webjournal')

class InvenioWebJournalTemplateNotFoundError(Exception):
    """
    Exception if a journal template is not found in the config.
    """
    def __init__(self, ln, journal_name, template=''):
        """
        Initialisation.
        """
        self.journal_name = journal_name
        self.ln = ln
        self.template = template
        self.journal_name_intl = get_journal_name_intl(self.journal_name,
                                                       self.ln)

    def __str__(self):
        """
        String representation.
        """
        return '''No %(tmpl)s template was provided for journal: %(name)s.
        The path to this file should be defined in %(CFG_ETCDIR)s/webjournal/%(name)s/%(name)s-config.xml
        ''' % {'tmpl': self.template,
               'name': self.journal_name,
               'CFG_ETCDIR': CFG_ETCDIR}

    def user_box(self, req=None):
        """
        user-friendly error message with formatting.
        Just say that page does not exist
        """
        _ = gettext_set_language(self.ln)
        return webjournal_templates.tmpl_webjournal_error_box(req,
            self.ln,
            ' ',
            _('Page not found'),
            _('The requested page does not exist'))

class InvenioWebJournalNoArticleRuleError(Exception):
    """
    Exception if there are no article type rules defined.
    """
    def __init__(self, ln, journal_name):
        """
        Initialisation.
        """
        self.journal_name = journal_name
        self.ln = ln
        self.journal_name_intl = get_journal_name_intl(self.journal_name,
                                                       self.ln)
    def __str__(self):
        """
        String representation.
        """
        return 'The config.xml file for journal: %s does not contain any \
        article rules. These rules are needed to associate collections from \
        your Invenio installation to navigable article types. A rule should \
        have the form of <rule>NameOfArticleType, \
        marc_tag:ExpectedContentOfMarcTag' % self.journal_name

    def user_box(self, req=None):
        """
        user-friendly error message with formatting.
        """
        _ = gettext_set_language(self.ln)
        return webjournal_templates.tmpl_webjournal_error_box(req,
            self.ln,
            _("No journal articles"),
            _("Problem with the configuration of this journal"),
            "The system couldn't find the definitions for different article \
            kinds (e.g. News, Sports, etc). If there is nothing defined, \
            nothing can be shown and it thus indicates that there is either a \
            problem with the setup of this journal or in the Software itself.\
            There is nothing you can do at this moment. If you wish you can \
            send an inquiry to the responsible developers. We apologize \
            for the inconvenience.")


class InvenioWebJournalNoIssueNumberTagError(Exception):
    """
    Exception if there is no marc tag for issue number defined.
    """
    def __init__(self, ln, journal_name):
        """
        Initialisation.
        """
        self.journal_name = journal_name
        self.ln = ln
        self.journal_name_intl = get_journal_name_intl(self.journal_name,
                                                       self.ln)

    def __str__(self):
        """
        String representation.
        """
        return 'The config.xml file for journal: %s does not contain a marc tag\
         to deduce the issue number from. WebJournal is an issue number based \
        system, meaning you have to give some form of numbering system in a \
        dedicated marc tag, so the system can see which is the active journal \
        publication of the date.' % self.journal_name_intl

    def user_box(self, req=None):
        """
        user-friendly error message with formatting.
        """
        _ = gettext_set_language(self.ln)
        return webjournal_templates.tmpl_webjournal_error_box(req,
                self.ln,
                _("No journal issues"),
                _("Problem with the configuration of this journal"),
                "The system couldn't find a definition for an issue \
                    numbering system. Issue numbers conrol the date of the \
                    publication you are seing. This indicates that there is an \
                    error in the setup of this journal or the Software itself. \
                    There is nothing you can do at the moment. If you wish you \
                    can send an inquiry to the responsible developers. We \
                    apologize for the inconvenience.")


class InvenioWebJournalNoArticleNumberError(Exception):
    """
    Exception if an article was called without its order number.
    """
    def __init__(self, ln, journal_name):
        """
        Initialisation.
        """
        self.journal_name = journal_name
        self.ln = ln
        self.journal_name_intl = get_journal_name_intl(self.journal_name,
                                                       self.ln)
    def __str__(self):
        """
        String representation.
        """
        return 'In Journal %s an article was called without specifying the order \
        of this article in the issue. This parameter is mandatory and should be \
        provided by internal links in any case. Maybe this was a bad direct url \
        hack. Check where the request came from.' % self.journal_name

    def user_box(self, req=None):
        """
        user-friendly error message with formatting.
        """
        _ = gettext_set_language(self.ln)
        return webjournal_templates.tmpl_webjournal_error_box(req,
            self.ln,
            _('Journal article error'),
            _('We could not know which article you were looking for'),
            'The url you passed did not provide an article number or the \
              article number was badly formed. If you \
              came to this page through some link on the journal page, please \
              report this to the admin. If you got this link through some \
              external resource, e.g. an email, you can try to put in a number \
              for the article in the url by hand or just visit the front \
              page at %s/journal/%s' % (CFG_SITE_URL, cgi.escape(self.journal_name)))

class InvenioWebJournalNoJournalOnServerError(Exception):
    """
    Exception that is thrown if there are no Journal instances on the server
    """
    def __init__(self, ln):
        """
        Initialisation.
        """
        self.ln = ln

    def __str__(self):
        """
        String representation.
        """
        return 'Apparently there are no journals configured on this \
        installation of Invenio. You can try to use the sample Invenio \
        Atlantis Journal for testing.'

    def user_box(self, req=None):
        """
        user-friendly message with formatting.
        """
        _ = gettext_set_language(self.ln)
        return webjournal_templates.tmpl_webjournal_error_box(req,
                        self.ln,
                        _('No journals available'),
                        _('We could not provide you any journals'),
                        _('It seems that there are no journals defined on this server. '
                          'Please contact support if this is not right.'))

class InvenioWebJournalNoNameError(Exception):
    """
    """
    def __init__(self, ln):
        """
        Initialisation.
        """
        self.ln = ln

    def __str__(self):
        """
        String representation.
        """
        return 'User probably forgot to add the name parameter for the journal\
        Maybe you also want to check if dns mappings are configured correctly.'

    def user_box(self, req=None):
        """
        user-friendly message with formatting.
        """
        _ = gettext_set_language(self.ln)
        return webjournal_templates.tmpl_webjournal_missing_info_box(req,
                        self.ln,
                        _("Select a journal on this server"),
                        _("We couldn't guess which journal you are looking for"),
                        _("You did not provide an argument for a journal name. "
                          "Please select the journal you want to read in the list below."))

class InvenioWebJournalNoCurrentIssueError(Exception):
    """
    """
    def __init__(self, ln):
        """
        Initialisation.
        """
        self.ln = ln

    def __str__(self):
        """
        String representation.
        """
        return 'There seems to be no current issue number stored for this \
        journal. Is this the first time you use the journal? Otherwise, check\
        configuration.'

    def user_box(self, req=None):
        """
        user-friendly message with formatting.
        """
        _ = gettext_set_language(self.ln)
        return webjournal_templates.tmpl_webjournal_error_box(req,
                    self.ln,
                    _('No current issue'),
                    _('We could not find any informtion on the current issue'),
                    _('The configuration for the current issue seems to be empty. '
                      'Try providing an issue number or check with support.'))


class InvenioWebJournalIssueNumberBadlyFormedError(Exception):
    """
    """
    def __init__(self, ln, issue):
        """
        Initialisation.
        """
        self.ln = ln
        self.issue = issue

    def __str__(self):
        """
        String representation.
        """
        return 'The issue number was badly formed. If this comes from the \
        user it is no problem.'

    def user_box(self, req=None):
        """
        user-friendly message with formatting.
        """
        _ = gettext_set_language(self.ln)
        return webjournal_templates.tmpl_webjournal_error_box(req,
                    self.ln,
                    _('Issue number badly formed'),
                    _('We could not read the issue number you provided'),
                    'The issue number you provided in the url seems to be badly\
                    formed. Issue numbers have to be in the form of ww/YYYY, so\
                    e.g. 50/2007. You provided the issue number like so: \
                    %s.' % cgi.escape(self.issue))

class InvenioWebJournalArchiveDateWronglyFormedError (Exception):
    """
    """
    def __init__(self, ln, date):
        """
        Initialisation.
        """
        self.ln = ln
        self.date = date

    def __str__(self):
        """
        String representation.
        """
        return 'The archive date was badly formed. If this comes from the \
        user it is no problem.'

    def user_box(self, req=None):
        """
        user-friendly message with formatting.
        """
        _ = gettext_set_language(self.ln)
        return webjournal_templates.tmpl_webjournal_error_box(req,
                    self.ln,
                    _('Archive date badly formed'),
                    _('We could not read the archive date you provided'),
                    'The archive date you provided in the form seems to be badly\
                    formed. Archive dates have to be in the form of dd/mm/YYYY, so\
                    e.g. 02/12/2007. You provided the archive date like so: \
                    %s.' % cgi.escape(self.date))

class InvenioWebJournalNoPopupRecordError(Exception):
    """
    Exception that is thrown if a popup is requested without specifying the
    type of the popup to call.
    """
    def __init__(self, ln, journal_name, recid):
        """
        Initialisation.
        """
        self.ln = ln
        self.journal_name = journal_name
        self.recid = recid
        self.journal_name_intl = get_journal_name_intl(self.journal_name,
                                                       self.ln)

    def __str__(self):
        """
        String representation.
        """
        return 'There was no recid provided to the popup system of webjournal \
        or the recid was badly formed. The recid was %s' % repr(self.recid)

    def user_box(self, req=None):
        """
        user-friendly message with formatting.
        """
        _ = gettext_set_language(self.ln)
        return webjournal_templates.tmpl_webjournal_error_box(req,
                    self.ln,
                    _('No popup record'),
                    _('We could not deduce the popup article you requested'),
                    'You called a popup window on Invenio without \
                      specifying a record in which you are interested or the \
                      record was badly formed. Does this link come \
                      from a Invenio Journal? If so, please contact \
                      support.')

class InvenioWebJournalReleaseUpdateError(Exception):
    """
    Exception that is thrown if an update release was not successful.
    """
    def __init__(self, ln, journal_name):
        """
        Initialisation.
        """
        self.ln = ln
        self.journal_name = journal_name
        self.journal_name_intl = get_journal_name_intl(self.journal_name,
                                                       self.ln)
    def __str__(self):
        """
        String representation.
        """
        return 'There were no updates submitted on a click on the update button.\
         This should never happen and must be due to an internal error.'

    def user_box(self, req=None):
        """
        user-friendly message with formatting.
        """
        _ = gettext_set_language(self.ln)
        return webjournal_templates.tmpl_webjournal_error_box(req,
                    self.ln,
                    _('Update error'),
                    _('There was an internal error'),
                    'We encountered an internal error trying to update the \
                      journal issue. You can try to launch the update again or \
                      contact the administrator. We apologize for the \
                      inconvenience.')

class InvenioWebJournalReleaseDBError(Exception):
    """
    Exception that is thrown if an update release was not successful.
    """
    def __init__(self, ln):
        """
        Initialisation.
        """
        self.ln = ln

    def __str__(self):
        """
        String representation.
        """
        return 'There was an error in synchronizing DB times with the actual \
        Python time objects.'

    def user_box(self, req=None):
        """
        user-friendly message with formatting.
        """
        _ = gettext_set_language(self.ln)
        return webjournal_templates.tmpl_webjournal_error_box(req,
                    self.ln,
                    _('Journal publishing DB error'),
                    _('There was an internal error'),
                    'We encountered an internal error trying to publish the \
                      journal issue. You can try to launch the publish interface \
                      again or contact the administrator. We apologize for the \
                      inconvenience.')

class InvenioWebJournalIssueNotFoundDBError(Exception):
    """
    Exception that is thrown if there was an issue number not found
    """
    def __init__(self, ln, journal_name, issue_number):
        """
        Initialisation.
        """
        self.ln = ln
        self.journal_name = journal_name
        self.issue_number = issue_number
        self.journal_name_intl = get_journal_name_intl(self.journal_name,
                                                       self.ln)
    def __str__(self):
        """
        String representation.
        """
        return 'The issue %s does not seem to exist for %s.' % (self.issue_number, self.journal_name)

    def user_box(self, req=None):
        """
        user-friendly message with formatting.
        """
        _ = gettext_set_language(self.ln)
        return webjournal_templates.tmpl_webjournal_error_box(req,
                    self.ln,
                    _('Journal issue error'),
                    _('Issue not found'),
                    'The issue you were looking for was not found for %s' % \
                    cgi.escape(self.journal_name_intl))

class InvenioWebJournalJournalIdNotFoundDBError(Exception):
    """
    Exception that is thrown if there was an issue number not found in the
    """
    def __init__(self, ln, journal_name):
        """
        Initialisation.
        """
        self.ln = ln
        self.journal_name = journal_name
        self.journal_name_intl = get_journal_name_intl(self.journal_name,
                                                       self.ln)
    def __str__(self):
        """
        String representation.
        """
        return 'The id for journal %s was not found in the Database. Make \
        sure the entry exists!' % (self.journal_name)

    def user_box(self, req=None):
        """
        user-friendly message with formatting.
        """
        _ = gettext_set_language(self.ln)
        return webjournal_templates.tmpl_webjournal_error_box(req,
                    self.ln,
                    _('Journal ID error'),
                    _('We could not find the id for this journal in the Database'),
                    'We encountered an internal error trying to get the id \
                    for this journal. You can try to refresh the page or \
                    contact the administrator. We apologize for the \
                    inconvenience.')

class InvenioWebJournalNoCategoryError(Exception):
    """
    Raised when trying to access a category that does not exist.
    """
    def __init__(self, ln, category, categories):
        """
        Initialisation.
        """
        self.ln = ln
        self.category = category
        self.categories = categories

    def __str__(self):
        """
        String representation.
        """
        return 'The specified category "%s" does not exist' % \
               self.category

    def user_box(self, req=None):
        """
        user-friendly message with formatting.
        """
        _ = gettext_set_language(self.ln)
        return webjournal_templates.tmpl_webjournal_error_box(req,
                    self.ln,
                    _('Category "%(category_name)s" not found') % \
                       {'category_name': cgi.escape(self.category)},
                    _('Category "%(category_name)s" not found') % \
                       {'category_name': cgi.escape(self.category)},
                    _('Sorry, this category does not exist for this journal and issue.'))
