# -*- coding: utf-8 -*-
## $Id$
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

"""WebJournal Web Interface."""

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

import urllib
from invenio.webinterface_handler import wash_urlargd, WebInterfaceDirectory
from invenio.access_control_engine import acc_authorize_action
from invenio.config import CFG_SITE_URL, CFG_SITE_LANG
from invenio.webuser import getUid
from invenio.urlutils import redirect_to_url
from invenio.errorlib import register_exception
from invenio.webjournal_config import \
     InvenioWebJournalNoJournalOnServerError, \
     InvenioWebJournalNoNameError, \
     InvenioWebJournalNoCurrentIssueError, \
     InvenioWebJournalIssueNumberBadlyFormedError, \
     InvenioWebJournalArchiveDateWronglyFormedError, \
     InvenioWebJournalJournalIdNotFoundDBError, \
     InvenioWebJournalNoArticleNumberError, \
     InvenioWebJournalNoPopupRecordError, \
     InvenioWebJournalNoCategoryError
from invenio.webjournal_utils import \
     get_xml_from_config, \
     get_current_issue, \
     guess_journal_name, \
     get_current_issue, \
     get_journal_id, \
     get_recid_from_legacy_number
from invenio.webjournal_washer import \
     wash_category, \
     wash_issue_number, \
     wash_journal_name, \
     wash_journal_language, \
     wash_article_number, \
     wash_popup_record, \
     wash_archive_date
from invenio.webjournal import \
     perform_request_index, \
     perform_request_article, \
     perform_request_popup, \
     perform_request_search

import invenio.template
webjournal_templates = invenio.template.load('webjournal')

class WebInterfaceJournalPages(WebInterfaceDirectory):
    """Defines the set of /journal pages."""

    journal_name = None
    journal_issue_year = None
    journal_issue_number = None
    category = None
    article_id = None

    _exports = ['popup', 'search']

    def _lookup(self, component, path):
        """ This handler is invoked for the dynamic URLs """
        if component in ['article', 'issue_control', 'edit_article', 'alert',
                         'feature_record', 'regenerate', 'administrate']:
            return WebInterfaceJournalPagesLegacy(), [component]

        return self, []

    def __call__(self, req, form):
        """ Maybe resolve the final / of a directory """
        path = req.uri[1:].split('/')
        journal_name = None
        journal_issue_year = None
        journal_issue_number = None
        category = None
        article_id = None
        if len(path) > 1:
            journal_name = path[1]
        if len(path) > 2:
            journal_issue_year = path[2]
        if len(path) > 3:
            journal_issue_number = path[3]
        if len(path) > 4:
            category = urllib.unquote(path[4])
        if len(path) > 5 and path[5].isdigit():
            article_id = path[5]

        ## Support for legacy journal/[empty]?(args*) urls. There are
        ## these parameters only in that case
        argd = wash_urlargd(form, {'name': (str, ""),
                                   'issue': (str, ""),
                                   'category': (str, ""),
                                   'ln': (str, CFG_SITE_LANG),
                                   'number': (int, None),
                                   'verbose': (int, 0)}
                            )

        if 'name' in form.keys() or \
            'issue' in form.keys() or \
            'category' in form.keys():
            ln = wash_journal_language(argd['ln'])
            journal_name = wash_journal_name(ln, argd['name'])
            issue = wash_issue_number(ln, journal_name,
                                             argd['issue'])
            issue_year = issue.split('/')[1]
            issue_number = issue.split('/')[0]
            category = wash_category(ln, argd['category'], journal_name)
            redirect_to_url(req, CFG_SITE_URL + '/journal/%(name)s/%(issue_year)s/%(issue_number)s/%(category)s/?ln=%(ln)s' % \
                            {'name': journal_name,
                             'issue_year': issue_year,
                             'issue_number': issue_number,
                             'category': category,
                             'ln': ln})
        ## End support for legacy urls

        # Check that given journal name exists.
        if journal_name:
            try:
                get_journal_id(journal_name)
            except InvenioWebJournalJournalIdNotFoundDBError, e:
                register_exception(req=req)
                return e.user_box()

        # If some parameters are missing, deduce them and
        # redirect
        if not journal_name or \
           not journal_issue_year or \
           not journal_issue_number or \
           not category:
            if not journal_name:
                try:
                    journal_name = guess_journal_name(argd['ln'])
                except InvenioWebJournalNoJournalOnServerError, e:
                    register_exception(req=req)
                    return e.user_box()
                except InvenioWebJournalNoNameError, e:
                    register_exception(req=req)
                    return e.user_box()
            if not journal_issue_year or not journal_issue_number:
                journal_issue = get_current_issue(argd['ln'], journal_name)
                journal_issue_year = journal_issue.split('/')[1]
                journal_issue_number = journal_issue.split('/')[0]

            if not category:
                config_strings = get_xml_from_config(["index", "rule", "issue_number"],
                                                     journal_name)
                rule_list = config_strings["rule"]
                category = rule_list[0].split(",")[0]
            redirect_to_url(req, CFG_SITE_URL + '/journal/%(name)s/%(issue_year)s/%(issue_number)s/%(category)s/?ln=%(ln)s' % \
                            {'name': journal_name,
                             'issue_year': journal_issue_year,
                             'issue_number': journal_issue_number,
                             'category': category,
                             'ln': argd['ln']})

        journal_issue = ""
        if journal_issue_year is not None and \
           journal_issue_number is not None:
            journal_issue = journal_issue_number + '/' + \
                            journal_issue_year

        try:
            journal_name = wash_journal_name(argd['ln'], journal_name)
            issue = wash_issue_number(argd['ln'], journal_name, journal_issue)
            category = wash_category(argd['ln'], category, journal_name)
        except InvenioWebJournalNoJournalOnServerError, e:
            register_exception(req=req)
            return e.user_box()
        except InvenioWebJournalNoNameError, e:
            register_exception(req=req)
            return e.user_box()
        except InvenioWebJournalIssueNumberBadlyFormedError, e:
            register_exception(req=req)
            return e.user_box()
        except InvenioWebJournalNoCategoryError, e:
            register_exception(req=req)
            return e.user_box()

        editor = False
        if acc_authorize_action(getUid(req), 'cfgwebjournal',
                                name="%s" % journal_name)[0] == 0:
            editor = True

        if article_id is None:
            html = perform_request_index(req,
                                         journal_name,
                                         journal_issue,
                                         argd['ln'],
                                         category,
                                         editor,
                                         verbose=argd['verbose'])
        else:
            #req.journal_defaults["editor"] = editor
            html = perform_request_article(req,
                                           journal_name,
                                           journal_issue,
                                           argd['ln'],
                                           category,
                                           article_id,
                                           editor,
                                           verbose=argd['verbose'])
        return html

    def popup(self, req, form):
        """
        simple pass-through function that serves as a checker for popups.
        """
        argd = wash_urlargd(form, {'name': (str, ""),
                                   'record': (str, ""),
                                   'ln': (str, "")
                                   })
        try:
            ln = wash_journal_language(argd['ln'])
            journal_name = wash_journal_name(ln, argd['name'])
            record = wash_popup_record(ln, argd['record'], journal_name)
        except InvenioWebJournalNoJournalOnServerError, e:
            register_exception(req=req)
            return e.user_box()
        except InvenioWebJournalNoNameError, e:
            register_exception(req=req)
            return e.user_box()
        except InvenioWebJournalNoPopupRecordError, e:
            register_exception(req=req)
            return e.user_box()

        html = perform_request_popup(req, ln, journal_name, record)

        return html

    def search(self, req, form):
        """
        Display search interface
        """
        argd = wash_urlargd(form, {'name': (str, ""),
                                   'issue': (str, ""),
                                   'archive_year': (str, ""),
                                   'archive_issue': (str, ""),
                                   'archive_select': (str, "False"),
                                   'archive_date': (str, ""),
                                   'archive_search': (str, "False"),
                                   'ln': (str, CFG_SITE_LANG),
                                   'verbose': (int, 0)})
        try:
            ln = wash_journal_language(argd['ln'])
            journal_name = wash_journal_name(ln, argd['name'])
            archive_issue = wash_issue_number(ln, journal_name,
                                              argd['archive_issue'])
            archive_date = wash_archive_date(ln, journal_name,
                                             argd['archive_date'])
            archive_select = argd['archive_select']
            archive_search = argd['archive_search']
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
        except InvenioWebJournalArchiveDateWronglyFormedError, e:
            register_exception(req=req)
            return e.user_box()

        html = perform_request_search(req=req,
                                      journal_name=journal_name,
                                      ln=ln,
                                      archive_issue=archive_issue,
                                      archive_select=archive_select,
                                      archive_date=archive_date,
                                      archive_search=archive_search,
                                      verbose=argd['verbose'])
        return html


    index = __call__


class WebInterfaceJournalPagesLegacy(WebInterfaceDirectory):
    """Defines the set of /journal pages."""

    _exports = ['', 'article', 'issue_control', 'edit_article', 'alert',
                'feature_record', 'regenerate', 'administrate']

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
            ln = wash_journal_language(argd['ln'])
            journal_name = wash_journal_name(ln, argd['name'])
            issue_number = wash_issue_number(ln, journal_name,
                                             argd['issue'])
            category = wash_category(ln, argd['category'], journal_name)
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
        except InvenioWebJournalNoCategoryError, e:
            register_exception(req=req)
            return e.user_box()
        # the journal_defaults will be used by format elements that have no
        # direct access to the params here, no more checking needed
        req.journal_defaults = {"name": journal_name,
                                "issue": issue_number,
                                "ln": ln,
                                "category": category}

        html = perform_request_index(req, journal_name, issue_number, ln,
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
                                   }
                            )
        try:
            ln = wash_journal_language(argd['ln'])
            journal_name = wash_journal_name(ln, argd['name'])
            issue = wash_issue_number(ln, journal_name,
                                      argd['issue'])
            issue_year = issue.split('/')[1]
            issue_number = issue.split('/')[0]
            category = wash_category(ln, argd['category'], journal_name)
            number = wash_article_number(ln, argd['number'], journal_name)
            recid = get_recid_from_legacy_number(issue, category, int(number))
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
        except InvenioWebJournalNoCategoryError, e:
            register_exception(req=req)
            return e.user_box()

        if recid != -1:
            # Found a corresponding record
            redirect_to_url(req, CFG_SITE_URL + \
                            '/journal/' + journal_name + '/' + issue_year + \
                            '/' + issue_number + '/' + category + \
                            '/' + str(recid) + '?ln=' + ln)
        else:
            # Corresponding record not found. Display index
            redirect_to_url(req, CFG_SITE_URL + \
                            '/journal/' + journal_name + '/' + issue_year + \
                            '/' + issue_number + '/' + category + \
                            '?ln=' + ln)

    def administrate(self, req, form):
        """Index page."""
        argd = wash_urlargd(form, {'name': (str, ""),
                                    'ln': (str, "")
                                    })
        try:
            ln = wash_journal_language(argd['ln'])
            journal_name = wash_journal_name(ln, argd['name'])
        except InvenioWebJournalNoJournalOnServerError, e:
            register_exception(req=req)
            return e.user_box()
        except InvenioWebJournalNoNameError, e:
            register_exception(req=req)
            return e.user_box()
        redirect_to_url(req, CFG_SITE_URL + \
                        '/admin/webjournal/webjournaladmin.py/administrate?journal_name=' + \
                        journal_name + '&ln=' + ln)

    def feature_record(self, req, form):
        """
        Interface to feature a record. Will be saved in a flat file.
        """
        argd = wash_urlargd(form, {'name': (str, ""),
                                   'recid': (str, "init"),
                                   'url': (str, "init"),
                                   'ln': (str, "")})

        redirect_to_url(req, CFG_SITE_URL + \
                        '/admin/webjournal/webjournaladmin.py/feature_record?journal_name=' + \
                        argd['name'] + '&ln=' + argd['ln'] + '&recid='+ argd['recid'] + '&url='+ argd['url'])

    def regenerate(self, req, form):
        """
        Clears the cache for the issue given.
        """
        argd = wash_urlargd(form, {'name': (str, ""),
                                   'issue': (str, ""),
                                   'ln': (str, "")})

        redirect_to_url(req, CFG_SITE_URL + \
                        '/admin/webjournal/webjournaladmin.py/regenerate?journal_name=' + \
                        argd['name'] + '&ln=' + argd['ln'] + '&issue=' + argd['issue'])

    def alert(self, req, form):
        """
        Alert system.
        Sends an email alert, in HTML/PlainText or only PlainText to a mailing
        list to alert for new journal releases.
        """
        argd = wash_urlargd(form, {'name': (str, ""),
                                   'sent': (str, "False"),
                                   'plainText': (str, ''),
                                   'htmlMail': (str, ""),
                                   'recipients': (str, ""),
                                   'subject': (str, ""),
                                   'ln': (str, ""),
                                   'issue': (str, ""),
                                   'force': (str, "False")})

        redirect_to_url(req, CFG_SITE_URL + \
                        '/admin/webjournal/webjournaladmin.py/alert?journal_name=' + \
                        argd['name'] + '&ln=' + argd['ln'] + '&issue=' + argd['issue'] + \
                        '&sent=' + argd['sent'] + '&plainText=' + argd['plainText'] + \
                        '&htmlMail=' + argd['htmlMail'] + '&recipients=' + argd['recipients'] + \
                        '&force=' + argd['force'] + '&subject=' + argd['subject'])

    def issue_control(self, req, form):
        """
        page that allows full control over creating, backtracing, adding to,
        removing from issues.
        """
        argd = wash_urlargd(form, {'name': (str, ""),
                                   'add': (str, ""),
                                   'action_publish': (str, "cfg"),
                                   'issue_number': (list, []),
                                   'ln': (str, "")})
        redirect_to_url(req, CFG_SITE_URL + \
                        '/admin/webjournal/webjournaladmin.py/issue_control?journal_name=' + \
                        argd['name'] + '&ln=' + argd['ln'] + '&issue=' + argd['issue_number'] + \
                        '&action=' + argd['action_publish'])
