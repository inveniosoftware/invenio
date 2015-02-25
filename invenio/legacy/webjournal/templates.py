# -*- coding: utf-8 -*-
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
WebJournal templates - Defines the look of various parts of the
WebJournal modules. Most customizations will however be done through
BibFormat format templates files.
"""

import os

from six import iteritems

from invenio.config import \
     CFG_SITE_SUPPORT_EMAIL, \
     CFG_ETCDIR, \
     CFG_SITE_URL, \
     CFG_SITE_LANG, \
     CFG_SITE_RECORD
from invenio.base.i18n import gettext_set_language
from invenio.legacy.webpage import page
from invenio.legacy.webjournal.utils import \
     get_number_of_articles_for_issue, \
     get_release_datetime, \
     get_announcement_datetime, \
     get_issue_number_display

class Template:
    """Templating class, refer to bibformat.py for examples of call"""

    def tmpl_webjournal_missing_info_box(self, req, ln, title, msg_title, msg):
        """
        returns a box indicating that the given journal was not found on the
        server, leaving the opportunity to select an existing journal from a list.
        """
        _ = gettext_set_language(ln)
        box_title = msg_title
        box_text = msg
        box_list_title = _("Available Journals")
        # todo: move to DB call
        find_journals = lambda path: [entry for entry in os.listdir(str(path)) \
                                      if os.path.isdir(str(path)+str(entry))]
        try:
            all_journals = find_journals('%s/webjournal/' % CFG_ETCDIR)
        except:
            all_journals = []

        mail_msg = _("Contact %(x_url_open)sthe administrator%(x_url_close)s") % \
                   {'x_url_open' :
                    '<a href="mailto:%s">' % CFG_SITE_SUPPORT_EMAIL,
                    'x_url_close' : '</a>'}
        box = '''
        <div style="text-align: center;">
            <fieldset style="width:400px; margin-left: auto; margin-right:auto">
                <legend style="color:#a70509;background-color:#fff;">
                    <i>%s</i>
                </legend>
                <p style="text-align:center;">%s</p>
                <h2 style="color:#0D2B88;">%s</h2>
                <ul class="webjournalBoxList">
                    %s
                </ul>
                <br/>
                <div style="text-align:right;">
                %s
                </div>
            </fieldset>
        </div>
                ''' % (box_title,
                       box_text,
                       box_list_title,
                       "".join(['<li><a href="%s/journal/?name=%s">%s</a></li>'
                                % (CFG_SITE_URL,
                                   journal,
                                   journal) for journal in all_journals]),
                       mail_msg)
        return page(req=req, title=title, body=box)

    def tmpl_webjournal_error_box(self, req, ln, title, title_msg, msg):
        """
        returns an error box for webjournal errors.
        """
        _ = gettext_set_language(ln)
        title = _(title)
        title_msg = _(title_msg)
        msg = _(msg)
        mail_msg = _("Contact %(x_url_open)sthe administrator%(x_url_close)s") % \
                   {'x_url_open' :
                    '<a href="mailto:%s">' % CFG_SITE_SUPPORT_EMAIL,
                    'x_url_close' : '</a>'}
        box = '''
        <div style="text-align: center;">
            <fieldset style="width:400px; margin-left: auto; margin-right: auto;">
                <legend style="color:#a70509;background-color:#fff;">
                    <i>%s</i>
                </legend>
                <p style="text-align:center;">%s</p>
                <br/>
                <div style="text-align:right;">
                    %s
                </div>
            </fieldset>
        </div>
                ''' % (title_msg, msg, mail_msg)
        return page(req=req, title=title, body=box)

    def tmpl_admin_regenerate_confirm(self,
                                      ln,
                                      journal_name,
                                      issue,
                                      issue_released_p):
        """
        Ask user confirmation about regenerating the issue, as well as if
        we should move all the drafts to the public collection.

        Parameters:

             journal_name -  the journal for which the cache should
                             be delete
                    issue -  the issue for which the cache should be
                             deleted
                      ln  -  language
        issue_released_p  -  is issue already released?
        """
        out = '''
    <form action="/admin/webjournal/webjournaladmin.py/regenerate" name="regenerate" method="post">
    You are going to refresh the cache for issue %(issue)s. Do you want to continue? <br/>
    <input type="hidden" name="confirmed_p" value="confirmed"/>
    <input type="hidden" name="journal_name" value="%(journal_name)s">
    <input type="hidden" name="issue" value="%(issue)s">
    <input type="hidden" name="ln" value="%(ln)s">
    <input type="checkbox" name="publish_draft_articles_p" value="move" id="publish_draft_articles_p" %(disabled)s/><label for="publish_draft_articles_p">Also switch all "<em>Offline</em>" articles to "<em>Online</em>"</label>[<a target="_blank" href="/help/admin/webjournal-editor-guide#cache-online">?</a>]<br/></br>
    <input class="adminbutton" type="submit" value="Regenerate"/>
    </form>
    ''' % {'issue': issue,
           'journal_name': journal_name,
           'ln': ln,
           'disabled': not issue_released_p and 'disabled="disabled"' or ""}

        return out

    def tmpl_admin_regenerate_success(self, ln, journal_name, issue):
        """
        Success message if a user applied the "regenerate" link. Links back to
        the regenerated journal.
        """
        _ = gettext_set_language(ln)

        out = '''
        The issue number %(issue)s for the %(journal_name)s journal has been successfully
        regenerated. <br/>
        Look at your changes: &raquo; <a href="%(CFG_SITE_URL)s/journal/%(journal_name)s/%(issue_year)s/%(issue_number)s"> %(journal_name)s </a> <br/> or go back to this journal <a href="%(CFG_SITE_URL)s/admin/webjournal/webjournaladmin.py/administrate?journal_name=%(journal_name)s">administration interface</a>.
        ''' % {'issue': issue,
               'journal_name': journal_name,
               'CFG_SITE_URL': CFG_SITE_URL,
               'issue_year': issue.split('/')[1],
               'issue_number': issue.split('/')[0]}

        return out

    def tmpl_admin_regenerate_error(self, ln, journal_name, issue):
        """
        Failure message for a regeneration try.
        """
        _ = gettext_set_language(ln)
        return page(
            title=_("Regeneration Error"),
            body = _("The issue could not be correctly regenerated. "
                     "Please contact your administrator."))

    def tmpl_admin_feature_record(self, journal_name,
                                  featured_records=[],
                                  ln=CFG_SITE_LANG,
                                  msg=None):
        """
        Display an interface form to feature a specific record from Invenio.
        """
        _ = gettext_set_language(ln)
        out = ''
        out += '''<table class="admin_wvar">
        <tr><th colspan="5" class="adminheaderleft" cellspacing="0">%(menu)s</th></tr>
        <tr>
        <td>0.&nbsp;<small><a href="administrate?journal_name=%(journal_name)s">Administrate</a></small>&nbsp;</td>
        <td>1.&nbsp;<small>Feature a Record</small>&nbsp;</td>
        <td>2.&nbsp;<small><a href="configure?action=edit&amp;journal_name=%(journal_name)s">Edit Configuration</a></small>&nbsp;</td>
        <td>3.&nbsp;<small><a href="%(CFG_SITE_URL)s/journal/%(journal_name)s">Go to the Journal</a></small>&nbsp;</td>
        </tr>
        </table><br/>''' % {'journal_name': journal_name,
                            'menu': _("Menu"),
                            'CFG_SITE_URL': CFG_SITE_URL}
        if msg is not None:
            out += msg
        out += '<br/><br/>'
        out += '''<table class="admin_wvar" cellspacing="0" width="400px">
                      <tr>
                          <th colspan="3" class="adminheader">Featured records</th>
                      </tr>'''
        color = "fff"
        for (recid, img_url) in featured_records:
            out += '''<tr style="background-color:#%(color)s">
               <td class="admintd"><img src="%(img_url)s" alt="" height="40px"/></td>
               <td class="admintdleft"><a href="%(CFG_SITE_URL)s/%(CFG_SITE_RECORD)s/%(recid)s">Record %(recid)s</a></td>
               <td class="admintdright"><a href="%(CFG_SITE_URL)s/admin/webjournal/webjournaladmin.py/feature_record?journal_name=%(journal_name)s&amp;action=askremove&amp;recid=%(recid)s">remove</a></td>
            </tr>''' % {'color': color,
                        'journal_name': journal_name,
                        'recid': recid,
                        'img_url': img_url,
                        'CFG_SITE_URL': CFG_SITE_URL,
                        'CFG_SITE_RECORD': CFG_SITE_RECORD}
            if color == 'fff':
                color = 'EBF7FF'
            else:
                color = 'fff'
        if len(featured_records) == 0:
            out += '<tr><td colspan="3" class="admintd"><em>No record featured for the moment. Add one using the form below.</em></td></tr>'
        out += '</table>'
        out += '''
        <br/><br/><br/>
        <form action="%(CFG_SITE_URL)s/admin/webjournal/webjournaladmin.py/feature_record" method="post">
        <input type="hidden" name="action" value="add" />
        <input type="hidden" name="journal_name" value="%(journal_name)s"/>
        <table class="admin_wvar" cellspacing="0">
            <tr>
                <th colspan="2" class="adminheaderleft">Add a new featured record:</th>
            </tr>
            <tr>
                <td class="admintdright"><label for="recordid"><span style="white-space: nowrap;">Featured Record ID</span></label>:&nbsp;</td>
                <td><input tabindex="1" type="text" name="recid" value="" id="recordid"/></td>
            </tr>
            <tr>
                <td class="admintdright"><label for="image_url"><span style="white-space: nowrap;">Icon URL</span></label>:&nbsp;</td>
                <td><input tabindex="2" type="text" name="img_url" value="" id="image_url" size="60"/><em><br/><small>Image displayed along the featured record</small></em></td>
            </tr>
            <tr>
            <td colspan="2" align="right"><input tabindex="3" class="adminbutton" type="submit" value="Add"/></td>
            </tr>
        </table>
        </form>
        ''' % {'CFG_SITE_URL': CFG_SITE_URL,
               'journal_name': journal_name}
        return out

    def tmpl_admin_alert_plain_text(self, journal_name, ln, issue):
        """
        Default plain text message for email alert of journal updates.
        This will be used to pre-fill the content of the mail alert, that
        can be modified by the admin.

        Customize this function to return different default texts
        based on journal name and language,
        """
        current_publication = get_issue_number_display(issue, journal_name, ln)
        plain_text = u'''Dear Subscriber,

    The latest issue of %(journal_name)s, no. %(current_publication)s, has been released.
    You can access it at the following URL:
    %(CFG_SITE_URL)s/journal/%(journal_name)s/

    Best Wishes,
    %(journal_name)s team

    ----
Cher Abonné,

    Le nouveau numéro de %(journal_name)s, no. %(current_publication)s, vient de paraître.
    Vous pouvez y accéder à cette adresse :
    %(CFG_SITE_URL)s/journal/%(journal_name)s/?ln=fr

    Bonne lecture,
    L'équipe de %(journal_name)s
    ''' % {'journal_name': journal_name,
           'current_publication': current_publication,
           'CFG_SITE_URL': CFG_SITE_URL}
        return plain_text
    # '

    def tmpl_admin_alert_header_html(self, journal_name, ln, issue):
        """
        Returns HTML header to be inserted into the HTML alert

        @param journal_name: the journal name
        @param ln: the current language
        @param issue: the issue for wich the alert is sent
        """
        _ = gettext_set_language(ln)
        journal_url = '%(CFG_SITE_URL)s/journal/%(journal_name)s/%(year)s/%(number)s' % \
                      {'CFG_SITE_URL': CFG_SITE_URL,
                       'journal_name': journal_name,
                       'year': issue.split('/')[1],
                       'number': issue.split('/')[0]}
        journal_link = '<a href="%(journal_url)s">%(journal_url)s</a>' % \
                       {'journal_url': journal_url}
        return '<p class="htmlalertheader">' + \
               _('If you cannot read this email please go to %(x_journal_link)s') % {'x_journal_link': journal_link} + \
               '</p>'

    def tmpl_admin_alert_subject(self, journal_name, ln, issue):
        """
        Default subject for email alert of journal updates.

        Customize this function to return different default texts
        based on journal name and language,
        """
        return "%s %s released" % (journal_name, \
                                   get_issue_number_display(issue,
                                                            journal_name,
                                                            ln))

    def tmpl_admin_alert_interface(self, ln, journal_name, default_subject,
                                   default_msg, default_recipients, alert_ln):
        """
        Alert email interface.
        """
        _ = gettext_set_language(ln)
        interface = '''
        <table>
        <tr>
        <td valign="top">
        <form action="%(CFG_SITE_URL)s/admin/webjournal/webjournaladmin.py/alert" name="alert" method="post">
            <input type="hidden" name="journal_name" value="%(journal_name)s"/>
            <p>Recipients:</p>
            <input type="text" name="recipients" value="%(default_recipients)s" size="60" />
            <p>Subject:</p>
            <input type="text" name="subject" value="%(subject)s" size="60" />
            <p>Plain Text Message:</p>
            <textarea name="plainText" wrap="soft" rows="25" cols="80">%(plain_text)s</textarea>
            <p> <input type="checkbox" name="htmlMail" id="htmlMail" value="html" checked="checked" />
               <label for="htmlMail">Send journal front-page <small>(<em>HTML newsletter</em>)</small></label>
            </p>
            <br/>
            <input class="formbutton" type="submit" value="Send Alert" name="sent"/>
        </form>
        </td><td valign="top">
        <p>HTML newsletter preview:</p>
        <iframe id="htmlMailPreview" src="%(CFG_SITE_URL)s/journal/%(journal_name)s?ln=%(alert_ln)s" height="600" width="600"></iframe>
        </tr>
        </table>
        ''' % {'CFG_SITE_URL': CFG_SITE_URL,
               'journal_name': journal_name,
               'subject': default_subject,
               'plain_text': default_msg,
               'default_recipients': default_recipients,
               'alert_ln': alert_ln}

        return interface

    def tmpl_admin_alert_was_already_sent(self, ln, journal_name,
                                          subject, plain_text, recipients,
                                          html_mail, issue):
        """
        """
        _ = gettext_set_language(ln)
        out = '''
        <form action="%(CFG_SITE_URL)s/admin/webjournal/webjournaladmin.py/alert" name="alert" method="post">
            <input type="hidden" name="journal_name" value="%(journal_name)s"/>
            <input type="hidden" name="recipients" value="%(recipients)s" />
            <input type="hidden" name="subject" value="%(subject)s" />
            <input type="hidden" name="plainText" value="%(plain_text)s" />
            <input type="hidden" name="htmlMail" value="%(html_mail)s" />
            <input type="hidden" name="force" value="True" />
            <p><em>WARNING! </em>The email alert for the issue %(issue)s has already been
            sent. Are you absolutely sure you want to send it again?</p>
            <p>Maybe you forgot to release an update issue? If so, please do this
            first <a href="%(CFG_SITE_URL)s/admin/webjournal/webjournaladmin.py/issue_control?journal_name=%(journal_name)s&amp;issue=%(issue)s">here</a>.</p>
            <p>Proceed with caution, or your subscribers will receive the alert a second time.</p>
            <br/>
            <input class="formbutton" type="submit" value="I really want this!" name="sent"/>
        </form>
                ''' % {'CFG_SITE_URL': CFG_SITE_URL,
                       'journal_name': journal_name,
                       'recipients': recipients,
                       'subject': subject,
                       'plain_text': plain_text,
                       'html_mail': html_mail,
                       'issue': issue}
        return out

    def tmpl_admin_alert_unreleased_issue(self, ln, journal_name):
        """
        Tried to announce an unreleased issue
        """
        _ = gettext_set_language(ln)
        out = '''<p style="color:#f00">An alert cannot be send for this issue!</p>

        You tried to send an alert for an issue that has not yet been released.
        Release it first and retry.<br/>

        Go back to the <a href="%(CFG_SITE_URL)s/admin/webjournal/webjournaladmin.py/administrate?journal_name=%(journal_name)s">administration interface</a>.
        ''' % {'CFG_SITE_URL': CFG_SITE_URL,
               'journal_name': journal_name}
        return out

    def tmpl_admin_alert_success_msg(self, ln, journal_name):
        """
        Success messge for the alert system.
        """
        _ = gettext_set_language(ln)
        out = '''<p style="color:#0f0">Alert sent successfully!</p>
        Return to your journal here: &raquo; \
                 <a href="%(CFG_SITE_URL)s/journal/%(journal_name)s">%(journal_name)s</a> <br/>
                 or go back to the <a href="%(CFG_SITE_URL)s/admin/webjournal/webjournaladmin.py/administrate?journal_name=%(journal_name)s">administration interface</a>''' % {'CFG_SITE_URL': CFG_SITE_URL,
                                      'journal_name': journal_name}
        return out

    def tmpl_admin_control_issue(self, ln, journal_name,
                                 active_issues):
        """
        Display the interface allowing to set the current issue.
        """
        _ = gettext_set_language(ln)
        out = '''
        <p>This interface gives you the possibility to create your
           current webjournal publication. Every checked issue number
           will be in the current publication. Once you have made your
           selection you can publish the new issue by clicking the %(publish)s
           button at the end.
        </p>
            <form action="%(CFG_SITE_URL)s/admin/webjournal/webjournaladmin.py/issue_control" name="publish">
                <input type="hidden" name="journal_name" value="%(journal_name)s"/>
                Issue Numbers to publish:
                <ul>
                %(issues_list)s
                </ul>
                <br/>

                <p>Add a higher issue number by clicking "%(add)s"</p>
                <input class="formbutton" type="submit" value="%(add)s" name="action"/>
                <p>.. or add a custom issue number by typing it here and pressing "%(refresh)s"</p>
                <input type="text" value="ww/YYYY" name="issue"/>
                <input class="formbutton" type="submit" value="%(refresh)s" name="action"/>
                <br/>
                <br/>
                <p>If all issues you want to publish are correctly checked, proceed \
                by clicking "%(publish)s".</p>
                <input class="formbutton" type="submit" value="%(publish)s" name="action"/>
            </form>
            ''' % {'CFG_SITE_URL': CFG_SITE_URL,
                   'journal_name': journal_name,
                   'issues_list': "".join(['<li><input type="checkbox" name="issue" value="%s" CHECKED>&nbsp;%s</input></li>'
                            % (issue, issue) for issue in active_issues]),
                   'add' : _("Add"),
                   'publish' : _("Publish"),
                   'refresh' : _("Refresh")
                   }

        return out

    def tmpl_admin_control_issue_success_msg(self, ln,
                                             active_issues, journal_name):
        """
        An issue was successfully published
        """
        _ = gettext_set_language(ln)
        issue_string = "".join([" - %s" % issue for issue in active_issues])
        title = '<h2>Issue(s) %s created successfully!</h2>' % issue_string
        body = '''<p>Now you can:</p>
                 <p>Return to your journal here: &raquo;
                 <a href="%s/journal/%s"> %s </a>
                 </p>
                 <p>Make additional publications here: &raquo;
                 <a href="%s/admin/webjournal/webjournaladmin.py/administrate?journal_name=%s">Publishing Interface</a>
                </p>
                <p>Send an alert email here: &raquo;
                <a href="%s/admin/webjournal/webjournaladmin.py/alert?journal_name=%s"> Send an alert</a>
                </p>''' % (CFG_SITE_URL, journal_name,
                         journal_name, CFG_SITE_URL,
                         journal_name, CFG_SITE_URL, journal_name)
        return title + body

    def tmpl_admin_update_issue(self, ln, journal_name, next_issue,
                                current_issue):
        """
        A form that lets a user make an update to an issue number.
        """
        _ = gettext_set_language(ln)
        current_articles = get_number_of_articles_for_issue(current_issue,
                                                            journal_name,
                                                            ln)
        next_articles = get_number_of_articles_for_issue(next_issue,
                                                         journal_name,
                                                         ln)

        html = '''
        <p>The Issue that was released on week %(current_issue)s has pending updates scheduled. The
        next update for this issue is %(next_issue)s.</p>
        <p><em>Note: If you want to make a new release, please click through all the
        pending updates first.</em></p>
        <p>Do you want to release the update from issue: <br/>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<em>%(current_issue)s</em> (%(current_articles)s) <br/>
        to issue: <br/>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<em>%(next_issue)s</em> (%(next_articles)s) <br/>
        now?</p>
        <form action="%(CFG_SITE_URL)s/admin/webjournal/webjournaladmin.py/issue_control" name="publish">
            <input type="hidden" name="journal_name" value="%(journal_name)s"/>
            <input type="hidden" name="issue" value="%(next_issue)s"/>
            <input class="formbutton" type="submit" value="%(update)s" name="action"/>
        </form>
        ''' % {'current_issue': current_issue,
               'next_issue' : next_issue,
               'current_articles': ",".join(["%s : %s" % (item[0], item[1]) \
                                             for item in iteritems(current_articles)]),
               'next_articles': ",".join(["%s : %s" % (item[0], item[1]) \
                                          for item in iteritems(next_articles)]),
               'CFG_SITE_URL' : CFG_SITE_URL,
               'journal_name': journal_name,
               'update': _("Update")}
        return html

    def tmpl_admin_updated_issue_msg(self, ln, update_issue, journal_name):
        """
        Prints a success message for the Update release of a journal.
        """
        _ = gettext_set_language(ln)
        title = '<h2>Journal update %s published successfully!</h2>' % update_issue
        body = '''<p>Now you can:</p>
                 <p>Return to your journal here: &raquo;
                 <a href="%s/journal/%s"> %s </a>
                 </p>
                 <p>Go back to the publishing interface: &raquo;
                 <a href="%s/admin/webjournal/webjournaladmin.py/administrate?journal_name=%s">Issue Interface</a>
                 </p>
                 <p>Send an alert email here: &raquo;
                 <a href="%s/journal/alert?name=%s"> Send an alert</a>
                 </p>''' % (CFG_SITE_URL, journal_name, journal_name,
                          CFG_SITE_URL, journal_name, CFG_SITE_URL, journal_name)
        return title + body

    def tmpl_admin_administrate(self, journal_name, current_issue,
                                current_publication, issue_list,
                                next_issue_number, ln=CFG_SITE_LANG,
                                as_editor=True):
        """
        Returns an administration interface that shows the current publication and
        supports links to all important actions.

        @param as_editor: True if can make changes to the configuration. Else read-only mode.
        """
        _ = gettext_set_language(ln)
        out = ''

        if as_editor:
            admin_menu = '''<table class="admin_wvar">
            <tr><th colspan="5" class="adminheaderleft" cellspacing="0">%(menu)s</th></tr>
            <tr>
            <td>0.&nbsp;<small>Administrate</small>&nbsp;</td>
            <td>1.&nbsp;<small><a href="feature_record?journal_name=%(journal_name)s">Feature a Record</a></small>&nbsp;</td>
            <td>2.&nbsp;<small><a href="configure?action=edit&amp;journal_name=%(journal_name)s">Edit Configuration</a></small>&nbsp;</td>
            <td>3.&nbsp;<small><a href="%(CFG_SITE_URL)s/journal/%(journal_name)s">Go to the Journal</a></small>&nbsp;</td>
            </tr>
            </table><br/>'''
        else:
            admin_menu = '''<table class="admin_wvar">
            <tr><th colspan="5" class="adminheaderleft" cellspacing="0">%(menu)s</th></tr>
            <tr>
            <td>0.&nbsp;<small>Administrate</small>&nbsp;</td>
            <td>1.&nbsp;<small><a href="%(CFG_SITE_URL)s/journal/%(journal_name)s">Go to the Journal</a></small>&nbsp;</td>
            </tr>
            </table><br/>'''

        out += admin_menu % {'journal_name': journal_name,
                             'menu': _("Menu"),
                             'CFG_SITE_URL': CFG_SITE_URL}

        # format the issues
        issue_boxes = []
        issue_list.append(next_issue_number)
        for issue in issue_list:
            articles = get_number_of_articles_for_issue(issue,
                                                        journal_name,
                                                        ln)
            released_on = get_release_datetime(issue, journal_name, ln)
            announced_on = get_announcement_datetime(issue, journal_name, ln)
            issue_box = '''
                <tr style="%s">
                    <td class="admintdright" style="vertical-align: middle;"></td>
                    <td class="admintdleft" style="white-space: nowrap; vertical-align: middle;">
                        <p>Issue: %s</p>
                        <p>Publication: %s</p>
                    </td>
                    <td class="admintdright" style="vertical-align: middle;">
                        %s
                    </td>
                    <td class="admintdright" style="vertical-align: middle;">
                        <p>%s</p>
                        <p>%s</p>
                    </td>
                    <td class="admintdright" style="vertical-align: middle;">
                        <p><a href="%s/admin/webjournal/webjournaladmin.py/regenerate?journal_name=%s&amp;issue=%s&amp;ln=%s">&gt;regenerate</a></p>
                    </td>
                <tr>
            ''' % ((issue==current_issue) and "background:#00FF00;" or "background:#F1F1F1;",

                    issue, (issue==next_issue_number) and "?" or current_publication,

                    "\n".join(['<p>%s : %s <a href="%s/journal/%s/%s/%s/%s">&gt;view</a></p>' %
                               (item[0], item[1],
                                CFG_SITE_URL, journal_name,
                                issue.split('/')[1], issue.split('/')[0], item[0]) \
                               for item in iteritems(articles)]),

                    (not released_on) and
                    ('<em>not released</em>' + (as_editor and '<br/><a href="%s/admin/webjournal/webjournaladmin.py/issue_control?journal_name=%s">&gt;release now</a>' % (CFG_SITE_URL, journal_name) or '')) or
                    'released on: %s' % released_on.strftime("%d.%m.%Y"),

                    (not announced_on)
                    and ('<em>not announced</em>' + (as_editor and '<br/><a href="%s/admin/webjournal/webjournaladmin.py/alert?journal_name=%s&issue=%s">&gt;announce now</a>' % (CFG_SITE_URL, journal_name, issue) or '')) or
                    'announced on: %s <br/><a href="%s/admin/webjournal/webjournaladmin.py/alert?journal_name=%s&issue=%s">&gt;re-announce</a>' % (announced_on.strftime("%d.%m.%Y"), CFG_SITE_URL, journal_name, issue),

                    CFG_SITE_URL, journal_name, issue, ln
                )
            issue_boxes.append(issue_box)
        out += '''
                 <table class="admin_wvar" width="80%%" cellspacing="0">
                    <tbody>
                        <tr>
                            <th class="adminheaderleft"></th>
                            <th class="adminheaderleft">Issue / Publication</th>
                            <th class="adminheader">Articles</th>
                            <th class="adminheaderleft">Release / Announcement</th>
                            <th class="adminheaderleft">Cache Status</th>
                        <tr>
                        %s
                    </tbody>
                 </table>
                 ''' % ("\n".join([issue_box for issue_box in issue_boxes]))

        return out

    def tmpl_admin_index(self, ln, journals, msg=None):
        """
        Returns the admin index page content.

        Lists the journals, and offers options to edit them, delete them
        or add new journal

        params:
                 ln  - ln
           journals  - list of tuples (journal_info dict, as_editor)
                msg  - message to be displayed
        """
        out = ""
        if msg is not None:
            out += msg
        out += '''
        <p>Choose the journal you want to administrate.</p>
        <table class="admin_wvar" cellspacing="0">
        <tr>
            <th class="adminheader">Journals</th>
            <th colspan="2" class="adminheader">&nbsp;</th>
        </tr>
        '''
        color = "fff"
        for journal_info, as_editor in journals:
            row = '''<tr style="background-color:#%(color)s">
               <td class="admintdleft"><a href="%(CFG_SITE_URL)s/admin/webjournal/webjournaladmin.py/administrate?journal_name=%(journal_name)s">%(journal_name)s</a></td>
               <td class="admintdright"><a href="%(CFG_SITE_URL)s/admin/webjournal/webjournaladmin.py/administrate?journal_name=%(journal_name)s">edit</a></td>'''
            if as_editor:
                row += '<td class="admintdright"><a href="%(CFG_SITE_URL)s/admin/webjournal/webjournaladmin.py/index?journal_name=%(journal_name)s&action=askDelete">delete</a></td>'
            row += '</tr>'
            out += row % {'color': color,
                          'journal_name': journal_info['journal_name'],
                          'journal_id': journal_info['journal_id'],
                          'CFG_SITE_URL': CFG_SITE_URL}
            if color == 'fff':
                color = 'EBF7FF'
            else:
                color = 'fff'
        out += '''<tr style="background-color:#%(color)s">
            <td class="admintdleft" colspan="3" style="padding: 5px 10px;"><a href="%(CFG_SITE_URL)s/admin/webjournal/webjournaladmin.py/configure?action=add">Add new journal</a></td>
        </tr>''' % {'color': color,
                    'CFG_SITE_URL': CFG_SITE_URL}
        out += '</table>'
        return out

    def tmpl_admin_configure_journal(self, ln, journal_name='', xml_config=None,
                                     action='edit', msg=None):
        """
        Display a page to change the settings of a journal. Also used to
        add a new journal.
        """
        out = ''
        _ = gettext_set_language(ln)
        journal_name_readonly = 'readonly="readonly" disabled="disabled"'
        journal_name_note = ''
        submit_button_label = _('Apply')
        if action == 'add':
            journal_name = ''
            journal_name_readonly = ''
            journal_name_note = 'Used in URLs. Choose it short and meaningful. This cannot be changed later'
            submit_button_label = _('Add')
        elif action in ['edit', 'editDone']:
            # Display navigation menu
            out += '''<table class="admin_wvar">
        <tr><th colspan="5" class="adminheaderleft" cellspacing="0">%(menu)s</th></tr>
        <tr>
        <td>0.&nbsp;<small><a href="administrate?journal_name=%(journal_name)s">Administrate</a></small>&nbsp;</td>
        <td>1.&nbsp;<small><a href="feature_record?journal_name=%(journal_name)s">Feature a Record</a></small>&nbsp;</td>
        <td>2.&nbsp;<small>Edit Configuration</small>&nbsp;</td>
        <td>3.&nbsp;<small><a href="%(CFG_SITE_URL)s/journal/%(journal_name)s">Go to the Journal</a></small>&nbsp;</td>
        </tr>
        </table><br/>''' % {'journal_name': journal_name,
                            'menu': _("Menu"),
                            'CFG_SITE_URL': CFG_SITE_URL}
        if msg is not None:
            out += msg
            out += '<br/><br/>'

        out += '''
          <form action="configure" method="post">
          <input type="hidden" name="ln" value="%(ln)s" />
          <input type="hidden" name="action" value="addDone" />
          <table class="admin_wvar" cellspacing="0" style="width:90%%">
          <tr>
          <th colspan="2" class="adminheaderleft">
          Journal settings</th>
          </tr>
          <tr>
          <td class="admintdright" width="100px"><label for="journal_name">Name</label>:&nbsp;</td>
          <td><input tabindex="0" name="journal_name" type="text" id="journal_name" maxlength="50" size="15" value="%(journal_name)s" %(readonly)s %(journal_name_readonly)s /><small>%(journal_name_note)s</small></td>
          </tr>
          <tr>
          <td class="admintdright"><label for="xml_config">Config</label>:&nbsp;</td>
          <td><textarea wrap="soft" rows="25" style="width:100%%" tabindex="3" name="xml_config" id="xml_config" size="25" %(readonly)s>%(xml_config)s</textarea></td>
          </tr>
          <td colspan="2" align="right"><input type="submit"  class="adminbutton" value="%(submit_button_label)s"></td>
          </tr>
          </table>
          </form>
          ''' % {'journal_name': journal_name,
                 'ln': ln,
                 'readonly': '',
                 'disabled': '',
                 'xml_config': xml_config.encode('utf-8'),
                 'journal_name_note': journal_name_note,
                 'submit_button_label': submit_button_label,
                 'journal_name_readonly': journal_name_readonly}

        return out
