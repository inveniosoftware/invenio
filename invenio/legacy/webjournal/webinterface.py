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

"""WebJournal Web Interface."""

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

import urllib
from invenio.ext.legacy.handler import wash_urlargd, WebInterfaceDirectory
from invenio.modules.access.engine import acc_authorize_action
from invenio.config import \
     CFG_SITE_URL, \
     CFG_SITE_SECURE_URL, \
     CFG_SITE_LANG, \
     CFG_CERN_SITE
from invenio.legacy.webuser import getUid
from invenio.utils.url import redirect_to_url
from invenio.ext.logging import register_exception
from invenio.legacy.webjournal.config import \
     InvenioWebJournalNoJournalOnServerError, \
     InvenioWebJournalNoNameError, \
     InvenioWebJournalNoCurrentIssueError, \
     InvenioWebJournalIssueNumberBadlyFormedError, \
     InvenioWebJournalArchiveDateWronglyFormedError, \
     InvenioWebJournalJournalIdNotFoundDBError, \
     InvenioWebJournalNoArticleNumberError, \
     InvenioWebJournalNoPopupRecordError, \
     InvenioWebJournalIssueNotFoundDBError, \
     InvenioWebJournalNoCategoryError
from invenio.legacy.webjournal.utils import \
     get_current_issue, \
     get_recid_from_legacy_number, \
     get_journal_categories
from invenio.legacy.webjournal.washer import \
     wash_category, \
     wash_issue_number, \
     wash_journal_name, \
     wash_journal_language, \
     wash_article_number, \
     wash_popup_record, \
     wash_archive_date
from invenio.legacy.webjournal.api import \
     perform_request_index, \
     perform_request_article, \
     perform_request_contact, \
     perform_request_popup, \
     perform_request_search
from invenio.legacy.webstat.api import register_customevent

import invenio.legacy.template
webjournal_templates = invenio.legacy.template.load('webjournal')

class WebInterfaceJournalPages(WebInterfaceDirectory):
    """Defines the set of /journal pages."""

    journal_name = None
    journal_issue_year = None
    journal_issue_number = None
    category = None
    article_id = None

    _exports = ['popup', 'search', 'contact']

    def _lookup(self, component, path):
        """ This handler is invoked for the dynamic URLs """
        if component in ['article', 'issue_control', 'edit_article', 'alert',
                         'feature_record', 'regenerate', 'administrate'] and \
                         CFG_CERN_SITE:
            return WebInterfaceJournalPagesLegacy(), [component]

        return self, []

    def __call__(self, req, form):
        """ Maybe resolve the final / of a directory """
        path = req.uri[1:].split('/')
        journal_name = None
        journal_issue_year = None
        journal_issue_number = None
        specific_category = None
        category = None
        article_id = None
        if len(path) > 1:
            journal_name = path[1]
        if len(path) > 2 and path[2].isdigit():
            journal_issue_year = path[2]
        elif len(path) > 2 and not path[2].isdigit():
            specific_category = urllib.unquote(path[2])
        if len(path) > 3 and path[3].isdigit():
            journal_issue_number = path[3]
        if len(path) > 4:
            category = urllib.unquote(path[4])
        if len(path) > 5 and path[5].isdigit():
            article_id = int(path[5])

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
            try:
                journal_name = wash_journal_name(ln, argd['name'])
            except InvenioWebJournalNoJournalOnServerError as e:
                register_exception(req=req)
                return e.user_box(req)
            except InvenioWebJournalNoNameError as e:
                return e.user_box(req)
            try:
                issue = wash_issue_number(ln, journal_name,
                                          argd['issue'])
                issue_year = issue.split('/')[1]
                issue_number = issue.split('/')[0]
            except InvenioWebJournalIssueNumberBadlyFormedError as e:
                register_exception(req=req)
                return e.user_box(req)
            except InvenioWebJournalJournalIdNotFoundDBError as e:
                register_exception(req=req)
                return e.user_box(req)
            category = wash_category(ln, argd['category'], journal_name, issue).replace(' ', '%20')
            redirect_to_url(req, CFG_SITE_URL + '/journal/%(name)s/%(issue_year)s/%(issue_number)s/%(category)s/?ln=%(ln)s' % \
                            {'name': journal_name,
                             'issue_year': issue_year,
                             'issue_number': issue_number,
                             'category': category,
                             'ln': ln})

        ## End support for legacy urls

        # Check that given journal name exists and that it is written
        # with correct casing.
        redirect_p = False
        try:
            washed_journal_name = wash_journal_name(argd['ln'], journal_name)
            if washed_journal_name != journal_name:
                redirect_p = True
        except InvenioWebJournalNoNameError as e:
            return e.user_box(req)
        except InvenioWebJournalNoJournalOnServerError as e:
            register_exception(req=req)
            return e.user_box(req)

        # If some parameters are missing, deduce them and
        # redirect
        if not journal_issue_year or \
           not journal_issue_number or \
           not category or \
           redirect_p or \
           specific_category:
            if not journal_issue_year or not journal_issue_number:
                journal_issue = get_current_issue(argd['ln'], washed_journal_name)
                journal_issue_year = journal_issue.split('/')[1]
                journal_issue_number = journal_issue.split('/')[0]
            if not category or specific_category:
                categories = get_journal_categories(washed_journal_name,
                                                    journal_issue_number + \
                                                    '/' + journal_issue_year)
                if not categories:
                    # Mmh, it seems that this issue has no
                    # category. Ok get all of them regardless of the
                    # issue
                    categories = get_journal_categories(washed_journal_name)
                    if not categories:
                        # Mmh we really have no category!
                        try:
                            raise InvenioWebJournalIssueNotFoundDBError(argd['ln'],
                                                                        journal_name,
                                                                        '')
                        except InvenioWebJournalIssueNotFoundDBError as e:
                            register_exception(req=req)
                            return e.user_box(req)
                if not category:
                    category = categories[0].replace(' ', '%20')
                if specific_category:
                    category = specific_category.replace(' ', '%20')
            redirect_to_url(req, CFG_SITE_URL + '/journal/%(name)s/%(issue_year)s/%(issue_number)s/%(category)s/?ln=%(ln)s' % \
                            {'name': washed_journal_name,
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
            journal_name = washed_journal_name
            issue = wash_issue_number(argd['ln'], journal_name, journal_issue)
            category = wash_category(argd['ln'], category, journal_name, issue)
        except InvenioWebJournalNoJournalOnServerError as e:
            register_exception(req=req)
            return e.user_box(req)
        except InvenioWebJournalNoNameError as e:
            return e.user_box(req)
        except InvenioWebJournalIssueNumberBadlyFormedError as e:
            register_exception(req=req)
            return e.user_box(req)
        except InvenioWebJournalNoCategoryError as e:
            register_exception(req=req)
            return e.user_box(req)
        except InvenioWebJournalJournalIdNotFoundDBError as e:
            register_exception(req=req)
            return e.user_box(req)

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
            html = perform_request_article(req,
                                           journal_name,
                                           journal_issue,
                                           argd['ln'],
                                           category,
                                           article_id,
                                           editor,
                                           verbose=argd['verbose'])
            # register event in webstat
            try:
                register_customevent("journals", ["display", journal_name, journal_issue, category, argd['ln'], article_id])
            except:
                register_exception(suffix="Do the webstat tables exists? Try with 'webstatadmin --load-config'")
        return html

    def contact(self, req, form):
        """
        Display contact information for the journal.
        """
        argd = wash_urlargd(form, {'name': (str, ""),
                                   'ln': (str, ""),
                                   'verbose': (int, 0)
                                   })
        try:
            ln = wash_journal_language(argd['ln'])
            washed_journal_name = wash_journal_name(ln, argd['name'])
        except InvenioWebJournalNoJournalOnServerError as e:
            register_exception(req=req)
            return e.user_box(req)
        except InvenioWebJournalNoNameError as e:
            return e.user_box(req)

        html = perform_request_contact(req, ln, washed_journal_name,
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
            washed_journal_name = wash_journal_name(ln, argd['name'])
            record = wash_popup_record(ln, argd['record'], washed_journal_name)
        except InvenioWebJournalNoJournalOnServerError as e:
            register_exception(req=req)
            return e.user_box(req)
        except InvenioWebJournalNoNameError as e:
            return e.user_box(req)
        except InvenioWebJournalNoPopupRecordError as e:
            register_exception(req=req)
            return e.user_box(req)

        html = perform_request_popup(req, ln, washed_journal_name, record)

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
            # FIXME: if journal_name is empty, redirect
            ln = wash_journal_language(argd['ln'])
            washed_journal_name = wash_journal_name(ln, argd['name'])
            archive_issue = wash_issue_number(ln, washed_journal_name,
                                              argd['archive_issue'])
            archive_date = wash_archive_date(ln, washed_journal_name,
                                             argd['archive_date'])
            archive_select = argd['archive_select']
            archive_search = argd['archive_search']
        except InvenioWebJournalNoJournalOnServerError as e:
            register_exception(req=req)
            return e.user_box(req)
        except InvenioWebJournalNoNameError as e:
            return e.user_box(req)
        except InvenioWebJournalNoCurrentIssueError as e:
            register_exception(req=req)
            return e.user_box(req)
        except InvenioWebJournalIssueNumberBadlyFormedError as e:
            register_exception(req=req)
            return e.user_box(req)
        except InvenioWebJournalArchiveDateWronglyFormedError as e:
            register_exception(req=req)
            return e.user_box(req)
        except InvenioWebJournalJournalIdNotFoundDBError as e:
            register_exception(req=req)
            return e.user_box(req)

        html = perform_request_search(req=req,
                                      journal_name=washed_journal_name,
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
            category = wash_category(ln, argd['category'], journal_name, issue_number)
        except InvenioWebJournalNoJournalOnServerError as e:
            register_exception(req=req)
            return e.user_box(req)
        except InvenioWebJournalNoNameError as e:
            return e.user_box(req)
        except InvenioWebJournalNoCurrentIssueError as e:
            register_exception(req=req)
            return e.user_box(req)
        except InvenioWebJournalIssueNumberBadlyFormedError as e:
            register_exception(req=req)
            return e.user_box(req)
        except InvenioWebJournalNoCategoryError as e:
            register_exception(req=req)
            return e.user_box(req)
        except InvenioWebJournalJournalIdNotFoundDBError as e:
            register_exception(req=req)
            return e.user_box(req)
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
            category = wash_category(ln, argd['category'], journal_name, issue_number)
            number = wash_article_number(ln, argd['number'], journal_name)
            recid = get_recid_from_legacy_number(issue, category, int(number))
        except InvenioWebJournalNoJournalOnServerError as e:
            register_exception(req=req)
            return e.user_box(req)
        except InvenioWebJournalNoNameError as e:
            return e.user_box(req)
        except InvenioWebJournalNoCurrentIssueError as e:
            register_exception(req=req)
            return e.user_box(req)
        except InvenioWebJournalIssueNumberBadlyFormedError as e:
            register_exception(req=req)
            return e.user_box(req)
        except InvenioWebJournalNoArticleNumberError as e:
            register_exception(req=req)
            return e.user_box(req)
        except InvenioWebJournalNoCategoryError as e:
            register_exception(req=req)
            return e.user_box(req)
        except InvenioWebJournalJournalIdNotFoundDBError as e:
            register_exception(req=req)
            return e.user_box(req)

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
        except InvenioWebJournalNoJournalOnServerError as e:
            register_exception(req=req)
            return e.user_box(req)
        except InvenioWebJournalNoNameError as e:
            return e.user_box(req)
        redirect_to_url(req, CFG_SITE_SECURE_URL + \
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

        redirect_to_url(req, CFG_SITE_SECURE_URL + \
                        '/admin/webjournal/webjournaladmin.py/feature_record?journal_name=' + \
                        argd['name'] + '&ln=' + argd['ln'] + '&recid='+ argd['recid'] + '&url='+ argd['url'])

    def regenerate(self, req, form):
        """
        Clears the cache for the issue given.
        """
        argd = wash_urlargd(form, {'name': (str, ""),
                                   'issue': (str, ""),
                                   'ln': (str, "")})

        redirect_to_url(req, CFG_SITE_SECURE_URL + \
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

        redirect_to_url(req, CFG_SITE_SECURE_URL + \
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
        redirect_to_url(req, CFG_SITE_SECURE_URL + \
                        '/admin/webjournal/webjournaladmin.py/issue_control?journal_name=' + \
                        argd['name'] + '&ln=' + argd['ln'] + '&issue=' + argd['issue_number'] + \
                        '&action=' + argd['action_publish'])
