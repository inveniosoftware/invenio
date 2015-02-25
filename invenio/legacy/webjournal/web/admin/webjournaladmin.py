# This file is part of Invenio.
# Copyright (C) 2008, 2009, 2010, 2011, 2012 CERN.
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

"""Invenio WebJournal Administrator Interface."""

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

import invenio.legacy.webjournal.adminlib as wjn
from invenio.modules.access.engine import acc_authorize_action
from invenio.legacy.webpage import page, error_page
from invenio.config import CFG_SITE_URL, CFG_SITE_LANG, CFG_SITE_NAME
from invenio.legacy.webuser import getUid, page_not_authorized
from invenio.base.i18n import wash_language, gettext_set_language
from invenio.utils.url import wash_url_argument
from invenio.ext.logging import register_exception
from invenio.legacy.webjournal.config import \
     InvenioWebJournalNoJournalOnServerError, \
     InvenioWebJournalNoNameError, \
     InvenioWebJournalNoCurrentIssueError, \
     InvenioWebJournalIssueNumberBadlyFormedError, \
     InvenioWebJournalJournalIdNotFoundDBError

from invenio.legacy.webjournal.washer import \
     wash_journal_name, \
     wash_issue_number

def index(req, ln=CFG_SITE_LANG, journal_name=None, action=""):
    """
    Main administration page.

    Lists the journals, and offers options to edit them, delete them
    or add new journals
    """
    navtrail_previous_links = wjn.getnavtrail()

    ln = wash_language(ln)
    _ = gettext_set_language(ln)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    try:
        journal_name = wash_journal_name(ln, journal_name)
        action = wash_url_argument(action, 'str')
    except InvenioWebJournalNoJournalOnServerError as e:
        # Ok, no journal. Let the admin add one...
        pass
    except InvenioWebJournalNoNameError as e:
        register_exception(req=req)
        return e.user_box()
    if action in ['delete', 'askDelete']:
        # To perform these, one must be authorized
        auth = acc_authorize_action(getUid(req), 'cfgwebjournal',
                                    name=journal_name, with_editor_rights='yes')
    else:
        auth = acc_authorize_action(getUid(req), 'cfgwebjournal')
    if auth[0] == 0:
        return page(title=_('WebJournal Admin'),
                    body=wjn.perform_index(ln=ln,
                                           journal_name=journal_name,
                                           action=action,
                                           uid=getUid(req)),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def administrate(req, journal_name, ln=CFG_SITE_LANG):
    """
    Shows the settings of a journal
    """
    navtrail_previous_links = wjn.getnavtrail(' &gt; <a class="navtrail" href="%s/admin/webjournal/webjournaladmin.py">WebJournal Admin</a>' % CFG_SITE_URL)

    ln = wash_language(ln)
    _ = gettext_set_language(ln)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    try:
        journal_name = wash_journal_name(ln, journal_name)
    except InvenioWebJournalNoJournalOnServerError as e:
        register_exception(req=req)
        return e.user_box()
    except InvenioWebJournalNoNameError as e:
        register_exception(req=req)
        return e.user_box()
    auth = acc_authorize_action(getUid(req), 'cfgwebjournal',
                                name="%s" % journal_name)
    if auth[0] == 0:
        as_editor = acc_authorize_action(getUid(req), 'cfgwebjournal',
                                         name="%s" % journal_name,
                                         with_editor_rights='yes')[0] == 0

        return page(title=_('Administrate %(journal_name)s' % {'journal_name':journal_name}),
                    body=wjn.perform_administrate(ln=ln, journal_name=journal_name,
                                                  as_editor=as_editor),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def feature_record(req, journal_name="", recid="", img_url="", ln=CFG_SITE_LANG, action=""):
    """
    Interface to feature a record. Will be saved in a flat file.
    """

    navtrail_previous_links = wjn.getnavtrail(' &gt; <a class="navtrail" href="%s/admin/webjournal/webjournaladmin.py">WebJournal Admin</a> &gt; <a class="navtrail" href="%s/admin/webjournal/webjournaladmin.py/administrate?journal_name=%s">%s</a>' % (CFG_SITE_URL, CFG_SITE_URL, journal_name, journal_name))

    ln = wash_language(ln)
    _ = gettext_set_language(ln)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    try:
        journal_name = wash_journal_name(ln, journal_name)
    except InvenioWebJournalNoJournalOnServerError as e:
        register_exception(req=req)
        return e.user_box()
    except InvenioWebJournalNoNameError as e:
        register_exception(req=req)
        return e.user_box()

    auth = acc_authorize_action(getUid(req), 'cfgwebjournal',
                                name="%s" % journal_name,
                                with_editor_rights='yes')
    if auth[0] == 0:
        return page(title=_("Feature a record"),
                    body=wjn.perform_feature_record(ln=ln,
                                                    journal_name=journal_name,
                                                    recid=recid,
                                                    img_url=img_url,
                                                    action=action),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


def alert(req, journal_name="", ln=CFG_SITE_LANG, sent="False", plainText=u"",
          htmlMail="", recipients="", subject="", issue="", force="False"):
    """
    Sends an email alert, in HTML/PlainText or only PlainText to a mailing
    list to alert for new journal releases.
    """
    navtrail_previous_links = wjn.getnavtrail(' &gt; <a class="navtrail" href="%s/admin/webjournal/webjournaladmin.py">WebJournal Admin</a> &gt; <a class="navtrail" href="%s/admin/webjournal/webjournaladmin.py/administrate?journal_name=%s">%s</a>' % (CFG_SITE_URL, CFG_SITE_URL, journal_name, journal_name))

    ln = wash_language(ln)
    _ = gettext_set_language(ln)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    try:
        journal_name = wash_journal_name(ln, journal_name)
        issue = wash_issue_number(ln,
                                         journal_name,
                                         issue)
        plain_text = wash_url_argument(plainText, 'str')
        html_mail = wash_url_argument(htmlMail, 'str')
        recipients = wash_url_argument(recipients, 'str')
        subject = wash_url_argument(subject, 'str')
        sent = wash_url_argument(sent, 'str')
        force = wash_url_argument(force, 'str')
    except InvenioWebJournalNoJournalOnServerError as e:
        register_exception(req=req)
        return e.user_box()
    except InvenioWebJournalNoNameError as e:
        register_exception(req=req)
        return e.user_box()
    except InvenioWebJournalNoCurrentIssueError as e:
        register_exception(req=req)
        return e.user_box()
    except InvenioWebJournalIssueNumberBadlyFormedError as e:
        register_exception(req=req)
        return e.user_box()
    except InvenioWebJournalJournalIdNotFoundDBError as e:
        register_exception(req=req)
        return e.user_box()

    auth = acc_authorize_action(getUid(req), 'cfgwebjournal',
                                name="%s" % journal_name,
                                with_editor_rights='yes')
    if auth[0] == 0:
        return page(title=_("Email Alert System"),
                    body=wjn.perform_request_alert(journal_name=journal_name,
                                                   issue=issue,
                                                   ln=ln,
                                                   sent=sent,
                                                   plain_text=plain_text,
                                                   subject=subject,
                                                   recipients=recipients,
                                                   html_mail=html_mail,
                                                   force=force),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def regenerate(req, journal_name="", issue="", ln=CFG_SITE_LANG,
               confirmed_p="", publish_draft_articles_p=""):
    """
    Clears the cache for the given issue.
    """
    navtrail_previous_links = wjn.getnavtrail(' &gt; <a class="navtrail" href="%s/admin/webjournal/webjournaladmin.py">WebJournal Admin</a> &gt; <a class="navtrail" href="%s/admin/webjournal/webjournaladmin.py/administrate?journal_name=%s">%s</a>' % (CFG_SITE_URL, CFG_SITE_URL, journal_name, journal_name))

    ln = wash_language(ln)
    _ = gettext_set_language(ln)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    try:
        journal_name = wash_journal_name(ln, journal_name)
        issue_number = wash_issue_number(ln, journal_name,
                                         issue)
        confirmed_p = wash_url_argument(confirmed_p, 'str') == "confirmed"
        publish_draft_articles_p = wash_url_argument(publish_draft_articles_p, 'str') == "move"

    except InvenioWebJournalNoJournalOnServerError as e:
        register_exception(req=req)
        return e.user_box()
    except InvenioWebJournalNoNameError as e:
        register_exception(req=req)
        return e.user_box()
    except InvenioWebJournalNoCurrentIssueError as e:
        register_exception(req=req)
        return e.user_box()
    except InvenioWebJournalIssueNumberBadlyFormedError as e:
        register_exception(req=req)
        return e.user_box()

    auth = acc_authorize_action(getUid(req), 'cfgwebjournal',
                                name="%s" % journal_name)
    if auth[0] == 0:
        return page(title=confirmed_p and _("Issue regenerated") or _("Regenerate Issue"),
                    body=wjn.perform_regenerate_issue(ln=ln,
                                                      journal_name=journal_name,
                                                      issue=issue,
                                                      confirmed_p=confirmed_p,
                                                      publish_draft_articles_p=publish_draft_articles_p),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def issue_control(req, journal_name="", issue=[],
                  ln=CFG_SITE_LANG, action="cfg"):
    """
    Page that allows full control over creating, backtracing, adding to,
    removing from issues.
    """
    navtrail_previous_links = wjn.getnavtrail(' &gt; <a class="navtrail" href="%s/admin/webjournal/webjournaladmin.py">WebJournal Admin</a> &gt; <a class="navtrail" href="%s/admin/webjournal/webjournaladmin.py/administrate?journal_name=%s">%s</a>' % (CFG_SITE_URL, CFG_SITE_URL, journal_name, journal_name))

    ln = wash_language(ln)
    _ = gettext_set_language(ln)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)
    try:
        journal_name = wash_journal_name(ln, journal_name)
        action = wash_url_argument(action, 'str')
        issue = wash_url_argument(issue, 'list')
        issues = [wash_issue_number(ln,journal_name, _issue) \
                  for _issue in issue \
                  if _issue != "ww/YYYY"]
    except InvenioWebJournalNoJournalOnServerError as e:
        register_exception(req=req)
        return e.user_box()
    except InvenioWebJournalNoNameError as e:
        register_exception(req=req)
        return e.user_box()
    except InvenioWebJournalNoCurrentIssueError as e:
        register_exception(req=req)
        return e.user_box()
    except InvenioWebJournalIssueNumberBadlyFormedError as e:
        register_exception(req=req)
        return e.user_box()

    auth = acc_authorize_action(getUid(req), 'cfgwebjournal',
                                name="%s" % journal_name,
                                with_editor_rights='yes')
    if auth[0] == 0:
        return page(title=_("Publishing Interface"),
                    body=wjn.perform_request_issue_control(journal_name=journal_name,
                                                           issues=issues,
                                                           ln=ln,
                                                           action=action),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def configure(req, journal_name=None, ln=CFG_SITE_LANG, xml_config=u'', action='edit'):
    """
    Let admins configure the journal settings
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)

    if journal_name is None:
        navtrail_previous_links = wjn.getnavtrail(' &gt; <a class="navtrail" href="%s/admin/webjournal/webjournaladmin.py">WebJournal Admin</a>' % CFG_SITE_URL)
    else:
        navtrail_previous_links = wjn.getnavtrail(' &gt; <a class="navtrail" href="%s/admin/webjournal/webjournaladmin.py">WebJournal Admin</a> &gt; <a class="navtrail" href="%s/admin/webjournal/webjournaladmin.py/administrate?journal_name=%s">%s</a>' % (CFG_SITE_URL, CFG_SITE_URL, journal_name, journal_name))

    if action in ['add', 'addDone']:
        page_title = _('Add Journal')
    else:
        page_title = _("Edit Settings")

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    try:
        journal_name = wash_journal_name(ln, journal_name, guess=False)
        xml_config = wash_url_argument(xml_config, 'str')
        action = wash_url_argument(action, 'str')
    except InvenioWebJournalNoJournalOnServerError as e:
        # Ok, no journal. Let the admin add one...
        pass
    except InvenioWebJournalNoNameError as e:
        register_exception(req=req)
        return e.user_box()

    auth = acc_authorize_action(getUid(req), 'cfgwebjournal',
                                name="%s" % journal_name,
                                with_editor_rights='yes')
    if auth[0] == 0:
        return page(title=page_title,
                    body=wjn.perform_request_configure(journal_name=journal_name,
                                                       ln=ln,
                                                       xml_config=xml_config,
                                                       action=action),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)
