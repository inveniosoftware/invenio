# -*- coding: utf-8 -*-
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

from invenio.config import adminemail, supportemail, etcdir, weburl, cdslang
from invenio.messages import gettext_set_language
from invenio.webpage import page

def tmpl_webjournal_missing_info_box(language, title, msg_title, msg):
    """
    returns a box indicating that the given journal was not found on the
    server, leaving the opportunity to select an existing journal from a list.
    """
    _ = gettext_set_language(language)
    #title = _(title)
    #box_title = _(msg_title)
    #box_text = _(msg)
    box_list_title = _("Available Journals")
    # todo: move to DB call
    find_journals = lambda path: [entry for entry in os.listdir(str(path)) if os.path.isdir(str(path)+str(entry))]
    try:
        all_journals = find_journals('%s/webjournal/' % etcdir)
    except:
        all_journals = []
    box = '''
    <div style="text-align: center;">
        <fieldset style="width:400px; margin-left: auto; margin-right:
        auto;background: url('%s/img/blue_gradient.gif') top left repeat-x;">
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
                Mail
                <a href="mailto:%s"> the Administrator.</a>
            </div>
        </fieldset>
    </div>
            ''' % (weburl,
                   box_title,
                   box_text,
                   box_list_title,
                   "".join(['<li><a href="%s/journal/?name=%s">%s</a></li>'
                            % (weburl,
                               journal,
                               journal) for journal in all_journals]),
                   adminemail)
    return page(title=title, body=box)

def tmpl_webjournal_error_box(language, title, title_msg, msg):
    """
    returns an error box for webjournal errors.
    """
    _ = gettext_set_language(language)
    title = _(title)
    title_msg = _(title_msg)
    msg = _(msg)
    mail_msg = _("Mail %(x_url_open)s the developers%(x_url_close)s") % {'x_url_open' :
        '<a href="mailto:%s">' % supportemail,
        'x_url_close' : '</a>'}
    box = '''
    <div style="text-align: center;">
        <fieldset style="width:400px; margin-left: auto; margin-right: auto;
        background: url('%s/img/red_gradient.gif') top left repeat-x;">
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
            ''' % (weburl, title_msg, msg, mail_msg)
    return page(title=title, body=box)

def tmpl_webjournal_regenerate_success(language, journal_name, issue_number):
    """
    Success message if a user applied the "regenerate" link. Links back to
    the regenerated journal.
    """
    _ = gettext_set_language(language)
    return page(
        title=_("Issue regenerated"),
        body = _('''
    The issue number %s for the journal %s has been successfully
    regenerated.
    Look at your changes: >> <a href="%s/journal/?name=%s"> %s </a>
    ''') % (issue_number, journal_name, weburl, journal_name, journal_name))

def tmpl_webjournal_regenerate_error(language, journal_name, issue_number):
    """
    Failure message for a regeneration try.
    """
    _ = gettext_set_language(language)
    return page(
        title=_("Regeneration Error"),
        body = _('''
        The issue could not be correctly regenerated. Please contact
        your administrator.
        '''))

def tmpl_webjournal_feature_record_interface(language, journal_name):
    """
    Draws an interface form to feature a specific record from CDS Invenio.
    """
    _ = gettext_set_language(language)
    interface = _('''
    <form action="%s/journal/feature_record" name="alert">
        <input type="hidden" name="name" value="%s"/>
        <p>Featured Record's ID:</p>
        <input type="text" name="recid" value="" />
        <p>Link to the picture that should be displayed</p>
        <input type="text" name="url" value="" />
        <br/>
        <input class="formbutton" type="submit" value="feature" name="featured"/>
    </form>
    ''') % (weburl, journal_name)
    return page(title=_("Feature a record"), body=interface)

def tmpl_webjournal_feature_record_success(language, journal_name, recid):
    """
    Draw a success message for featuring a record and a backlink to the journal
    """
    _ = gettext_set_language(language)
    title = _("Successfully featured record: %s") % recid
    msg = _('''Return to your Journal here >>
            <a href="%s/journal/?name=%s">%s</a>''') % (weburl,
                                                         journal_name,
                                                        journal_name)
    return page(title = title, body = msg)

def tmpl_webjournal_alert_plain_text_CERNBulletin(language, issue):
    """
    Plain Text message for alert of CERN Bulletin. No multilanguage since the
    message should always be in two languages.
    """
    plain_text = u'''Dear Subscriber,
                    
The latest issue of the CERN Bulletin, no. %s, has been released.
You can access it at the following URL:
http://www.bulletin.cern.ch/

Best Wishes,
CERN Bulletin team

----
Cher Abonné,

Le nouveau numéro du CERN Bulletin, no. %s, vient de paraître.
Vous pouvez y accéder à cette adresse :
http://www.bulletin.cern.ch/fre

Bonne lecture,
L'équipe du Bulletin du CERN
''' % (issue, issue)
    return plain_text 

def tmpl_webjournal_alert_subject_CERNBulletin(issue):
    """
    Subject text for the CERN Bulletin release.
    """
    return "CERN bulletin %s released" % issue

def tmpl_webjournal_alert_interface(language, journal_name, subject,
                                    plain_text):
    """
    Alert eMail interface.
    """
    _ = gettext_set_language(language)
    interface = _('''
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
            ''') % (weburl, journal_name, subject, plain_text)
    return interface
    
def tmpl_webjournal_alert_success_msg(language, journal_name):
    """
    Success messge for the alert system.
    """
    _ = gettext_set_language(language)
    title = _("Alert sent successfully!")
    body = _('Return to your journal here: >> \
             <a href="%s/journal/?name=%s"> %s </a>') % (weburl, journal_name,
                                                         journal_name)
    return page(title=title, body=body)

def tmpl_webjournal_issue_control_interface(language, journal_name,
                                            active_issues):
    """
    """
    _ = gettext_set_language(language)
    interface = _('''
    <div align="center">
        <h2>Publishing Interface</h2>
        <p>This interface gives you the possibilite to create
            your current webjournal publication. Every checked
            issue number will be in the current publication. Once
            you've made your selection you can publish the new
            issue by clicking the Publish button at the end.
        </p>
        <form action="%s/journal/issue_control" name="publish">
            <input type="hidden" name="name" value="%s"/>
            <ul>
            <p>Issue Numbers to publish::..</p>
            %s
            <br/>

            <p>Add a higher issue number by clicking "Refresh"</p>
            <input class="formbutton" type="submit" value="Refresh" name="action_publish"/>
            <br/>
            <br/>
            <p>If all issues you want to publish are correctly checked, proceed \
            by clicking "Publish".</p>
            <input class="formbutton" type="submit" value="Publish" name="action_publish"/>
        </form>
    </div>
        ''') % (weburl,
               journal_name,
               "".join(['<li><input type="checkbox" name="issue_number" value="%s" CHECKED>&nbsp;%s</input></li>'
                        % (issue, issue) for issue in active_issues]),
               )
    
    return interface

def tmpl_webjournal_issue_control_success_msg(language,
                                              active_issues, journal_name):
    """
    """
    _ = gettext_set_language(language)
    issue_string = "".join([" - %s" % issue for issue in active_issues])
    title = _('<h2>Bulletin %s created successfully!</h2>' % issue_string)
    body = _('<p>Return to your journal here: >> \
             <a href="%s/journal/?name=%s"> %s </a>\
             </p>\
             <p>or make additional changes here: >> \
             <a href="%s/journal/issue_control?name=%s">Issue Interface</a> \
            </p>') % (weburl, journal_name, journal_name,
                      weburl, journal_name)
    return title + body

def tmpl_webjournal_update_an_issue(language, journal_name, next_issue,
                                    current_issue):
    """
    A form that lets a user make an update to an issue number.
    """
    _ = gettext_set_language(language)
    html = _('''
    <p>The Issue that was released on week %s has pending updates scheduled. The
    next update for this issue is %s.</p>
    <p><em>Note: If you want to make a new release, please click through all the
    pending updates first.</em></p>
    <br/>
    <p>Do you want to release the update from issue %s to issue %s now?</p>
    <form action="%s/journal/issue_control" name="publish">
        <input type="hidden" name="name" value="%s"/>
        <input type="hidden" name="issue_number" value="%s"/>
        <input class="formbutton" type="submit" value="Update" name="action_publish"/>
    </form>
    ''') % (current_issue, next_issue, current_issue, next_issue,
            weburl, journal_name, next_issue)
    return html

def tmpl_webjournal_updated_issue_msg(language, update_issue, journal_name):
    """
    Prints a success message for the Update release of a journal.
    """
    _ = gettext_set_language(language)
    title = _('<h2>Journal Update %s published successfully!</h2>' %
              update_issue)
    body = _('<p>Return to your journal here: >> \
             <a href="%s/journal/?name=%s"> %s </a>\
             </p>\
             <p>or go back to the publishing interface: >> \
             <a href="%s/journal/issue_control?name=%s">Issue Interface</a> \
            </p>') % (weburl, journal_name, journal_name,
                      weburl, journal_name)
    return title + body