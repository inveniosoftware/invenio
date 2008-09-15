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
# pylint: disable-msg=C0301
"""CDS Invenio WebJournal Administration Interface."""

__revision__ = "$Id$"

import sets
import smtplib
import cPickle
import re
import os
import MimeWriter
import mimetools
import cStringIO
from urllib2 import urlopen
from invenio.errorlib import register_exception
from invenio.config import \
     CFG_SITE_URL, \
     CFG_SITE_LANG, \
     CFG_SITE_NAME, \
     CFG_ETCDIR
from invenio.messages import gettext_set_language
from invenio.webjournal_config import \
     InvenioWebJournalJournalIdNotFoundDBError, \
     InvenioWebJournalReleaseUpdateError, \
     InvenioWebJournalIssueNotFoundDBError
from invenio.webjournal_utils import \
     get_journals_ids_and_names, \
     guess_journal_name, \
     get_current_issue, \
     get_current_publication, \
     get_list_of_issues_for_publication, \
     count_week_string_up, \
     get_featured_records, \
     add_featured_record, \
     remove_featured_record, \
     clear_cache_for_issue, \
     get_current_issue_time, \
     get_all_issue_weeks, \
     get_next_journal_issues, \
     issue_times_to_week_strings, \
     issue_week_strings_to_times, \
     get_release_time, \
     get_journal_id, \
     sort_by_week_number, \
     get_xml_from_config, \
     get_journal_info_path

from invenio.dbquery import run_sql

import invenio.template
wjt = invenio.template.load('webjournal')

def getnavtrail(previous = ''):
    """Get the navtrail"""

    navtrail = """<a class="navtrail" href="%s/help/admin">Admin Area</a> """ % (CFG_SITE_URL,)
    navtrail = navtrail + previous
    return navtrail

def perform_index(ln=CFG_SITE_LANG, journal_name=None, action=None):
    """
    Index page

    Lists the journals, and offers options to edit them, delete them
    or add new journal.

    Parameters:
        journal_name  -  the journal affected by action, if any
              action  -  one of ['', 'askDelete', _('Delete'), _('Cancel')]
                  ln  -  language
    """
    _ = gettext_set_language(ln)

    msg = None
    if action == 'askDelete' and journal_name is not None:
        msg = '''<fieldset style="display:inline;margin-left:auto;margin-right:auto;">
        <legend>Delete Journal Configuration</legend><span style="color:#f00">Are you sure you want to delete the configuration of %(journal_name)s?
        <form action="%(CFG_SITE_URL)s/admin/webjournal/webjournaladmin.py">
        <input type="hidden" name="journal_name" value="%(journal_name)s" />
        <input class="formbutton" type="submit" name="action" value="%(delete)s" />
        <input class="formbutton" type="submit" name="action" value="%(cancel)s" />
        </form></span></fieldset>''' % {'CFG_SITE_URL': CFG_SITE_URL,
                                        'journal_name': journal_name,
                                        'delete': _("Delete"),
                                        'cancel': _("Cancel")}

    if action == _("Delete") and journal_name is not None:
        # User confirmed and clicked on "Delete" button
        remove_journal(journal_name)

    journals = get_journals_ids_and_names()
    return wjt.tmpl_admin_index(ln=ln,
                                journals=journals,
                                msg=msg)

def perform_administrate(ln=CFG_SITE_LANG, journal_name=None):
    """
    Administration of a journal

    Show the current and next issues/publications, and display links
    to more specific administrative pages.

    Parameters:
        journal_name  -  the journal to be administrated
                  ln  -  language
    """
    if journal_name is None:
        try:
            journal_name = guess_journal_name(ln)
        except InvenioWebJournalNoJournalOnServerError, e:
            return e.user_box()

    if not can_read_xml_config(journal_name):
        return '<span style="color:#f00">Configuration could not be read. Please check that %s/webjournal/%s/config.xml exists and can be read by the server.</span><br/>' % (CFG_ETCDIR, journal_name)

    current_issue = get_current_issue(ln, journal_name)
    current_publication = get_current_publication(journal_name,
                                                  current_issue,
                                                  ln)
    issue_list = get_list_of_issues_for_publication(current_publication)
    next_issue_number = count_week_string_up(issue_list[-1])
    return wjt.tmpl_admin_administrate(journal_name,
                                       current_issue,
                                       current_publication,
                                       issue_list,
                                       next_issue_number,
                                       ln)

def perform_feature_record(journal_name,
                           recid,
                           img_url='',
                           action='',
                           ln=CFG_SITE_LANG):
    """
    Interface to feature a record

    Used to list, add and remove featured records of the journal.

    Parameters:
        journal_name  -  the journal for which the article is featured
               recid  -  the record affected by 'action'
             img_url  -  the URL to image displayed with given record
                         (only when action == 'add')
              action  -  One of ['', 'add', 'askremove', _('Remove'), _('Cancel')]
                  ln  -  language
    """
    _ = gettext_set_language(ln)

    if action == 'add':
        result = add_featured_record(journal_name, recid, img_url)
        if result == 0:
            msg ='''<span style="color:#0f0">Successfully featured
            <a href="%(CFG_SITE_URL)s/record/%(recid)s">record %(recid)s</a>.
        Go to the <a href="%(CFG_SITE_URL)s/journal/%(name)s">%(name)s journal</a> to
        see the result.</span>''' % {'CFG_SITE_URL': CFG_SITE_URL,
                                  'name': journal_name,
                                  'recid': recid}
        elif result == 1:
            msg = '''<span style="color:#f00"><a href="%(CFG_SITE_URL)s/record/%(recid)s">record %(recid)s</a> is already featured. Choose another one or remove it first.</span>''' % \
                  {'CFG_SITE_URL': CFG_SITE_URL,
                   'recid': recid}
        else:
            msg = '''<span style="color:#f00">Record could not be featured. Check file permission.</span>'''

        featured_records = get_featured_records(journal_name)
        return wjt.tmpl_admin_feature_record(ln=ln,
                                             journal_name=journal_name,
                                             featured_records=featured_records,
                                             msg=msg)
    elif action == 'askremove':
        msg = '''<fieldset style="display:inline;margin-left:auto;margin-right:auto;">
        <legend>Remove featured record</legend><span style="color:#f00">Are you sure you want to remove <a href="%(CFG_SITE_URL)s/record/%(recid)s">record %(recid)s</a> from the list of featured record?
        <form action="%(CFG_SITE_URL)s/admin/webjournal/webjournaladmin.py/feature_record">
        <input type="hidden" name="journal_name" value="%(name)s" />
        <input type="hidden" name="recid" value="%(recid)s" />
        <input class="formbutton" type="submit" name="action" value="%(remove)s" />
        <input class="formbutton" type="submit" name="action" value="%(cancel)s" />
        </form></span></fieldset>''' % \
            {'CFG_SITE_URL': CFG_SITE_URL,
             'name': journal_name,
             'recid': recid,
             'cancel': _("Cancel"),
             'remove': _("Remove")}
        featured_records = get_featured_records(journal_name)
        return wjt.tmpl_admin_feature_record(ln=ln,
                                             journal_name=journal_name,
                                             featured_records=featured_records,
                                             msg=msg)
    elif action == _("Remove"):
        result = remove_featured_record(journal_name, recid)
        msg = '''<span style="color:#f00"><a href="%(CFG_SITE_URL)s/record/%(recid)s">Record %(recid)s</a>
        has been removed.</span>''' % \
            {'CFG_SITE_URL': CFG_SITE_URL,
             'recid': recid}
        featured_records = get_featured_records(journal_name)
        return wjt.tmpl_admin_feature_record(ln=ln,
                                             journal_name=journal_name,
                                             featured_records=featured_records,
                                             msg=msg)
    else:
        msg = '''Here you can choose which records from the %s should
        be featured on the journal webpage.''' % CFG_SITE_NAME
        featured_records = get_featured_records(journal_name)
        return wjt.tmpl_admin_feature_record(ln=ln,
                                             journal_name=journal_name,
                                             featured_records=featured_records,
                                             msg=msg)
def perform_regenerate_issue(issue,
                             journal_name,
                             ln=CFG_SITE_LANG):
    """
    Clears the cache for the given issue.

    Parameters:
        journal_name  -  the journal for which the cache should be
                         deleted
               issue  -  the issue for which the cache should be deleted
                  ln  -  language
    """
    success = clear_cache_for_issue(journal_name,
                                    issue)
    if success:
        return wjt.tmpl_admin_regenerate_success(ln,
                                                 journal_name,
                                                 issue)
    else:
        return wjt.tmpl_admin_regenerate_error(ln,
                                               journal_name,
                                               issue)
def perform_request_issue_control(journal_name, issues,
                                  action, ln=CFG_SITE_LANG):
    """
    Central logic for issue control.

    Regenerates the flat files 'current_issue' and 'issue_group' of
    the journal that control which issue is currently active for the
    journal.

    Parameters:
        journal_name  -  the journal affected by 'action'
              issues  -  list of issues affected by 'action' TODO: check
              action  -  One of ['cfg', _('Add'), _('Refresh'),
                         _('Publish'), _('Update')]
                  ln  -  language
    """
    _ = gettext_set_language(ln)

    out = ''
    if action == "cfg" or action == _("Refresh") or action == _("Add"):
        # find out if we are in update or release
        try:
            current_issue_time = get_current_issue_time(journal_name)
            all_issue_weeks = get_all_issue_weeks(current_issue_time,
                                                  journal_name,
                                                  ln)
        except InvenioWebJournalIssueNotFoundDBError, e:
            register_exception(req=None)
            return e.user_box()
        except InvenioWebJournalJournalIdNotFoundDBError, e:
            register_exception(req=None)
            return e.user_box()
        if max(all_issue_weeks) > current_issue_time:
            # propose an update
            next_issue_week = None
            all_issue_weeks.sort()
            for issue_week in all_issue_weeks:
                if issue_week > current_issue_time:
                    next_issue_week = issue_week
                    break
            out = wjt.tmpl_admin_update_issue(ln,
                                              journal_name,
                                              issue_times_to_week_strings([next_issue_week,])[0],
                                              issue_times_to_week_strings([current_issue_time,])[0])
        else:
            # propose a release
            next_issues = get_next_journal_issues(current_issue_time,
                                                  journal_name)
            next_issues = issue_times_to_week_strings(next_issues,
                                                      ln)
            if action == _("Refresh"):
                next_issues += issues
                next_issues = list(sets.Set(next_issues))# avoid double entries
            elif action == _("Add"):
                next_issues += issues
                next_issues = list(sets.Set(next_issues))# avoid double entries
                next_issues_times = issue_week_strings_to_times(next_issues,
                                                                ln)
                highest_issue_so_far = max(next_issues_times)
                one_more_issue = get_next_journal_issues(highest_issue_so_far,
                                                         journal_name,
                                                         ln,
                                                         1)
                one_more_issue = issue_times_to_week_strings(one_more_issue,
                                                            ln)
                next_issues += one_more_issue
                next_issues = list(sets.Set(next_issues)) # avoid double entries
                next_issues.sort()
            else:
                # get the next (default 2) issue numbers to publish
                next_issues = get_next_journal_issues(current_issue_time,
                                                      journal_name,
                                                      ln)
                next_issues = issue_times_to_week_strings(next_issues,
                                                          ln)
            out = wjt.tmpl_admin_control_issue(ln,
                                               journal_name,
                                               next_issues)
    elif action == _("Publish"):
        # Publish the given issues (mark them as current issues)
        publish_issues = issues
        publish_issues = list(sets.Set(publish_issues)) # avoid double entries
        publish_issues.sort()
        try:
            release_journal_issue(publish_issues, journal_name, ln)
        except InvenioWebJournalJournalIdNotFoundDBError, e:
            register_exception(req=None)
            return e.user_box()
        out = wjt.tmpl_admin_control_issue_success_msg(ln,
                                                       publish_issues,
                                                       journal_name)

    elif action == _("Update"):
        try:
            try:
                update_issue = issues[0]
            except:
                raise InvenioWebJournalReleaseUpdateError(ln, journal_name)
        except InvenioWebJournalReleaseUpdateError, e:
            register_exception(req=None)
            return e.user_box()
        try:
            release_journal_update(update_issue, journal_name, ln)
        except InvenioWebJournalJournalIdNotFoundDBError, e:
            register_exception(req=None)
            return e.user_box()
        out = wjt.tmpl_admin_updated_issue_msg(ln,
                                               update_issue,
                                               journal_name)

    return out

def perform_request_alert(journal_name, issue,
                          sent, plain_text, subject, recipients,
                          html_mail, force, ln=CFG_SITE_LANG):
    """
    All the logic for alert emails.

    Display a form to edit email/recipients and options to send the
    email.  Sent in HTML/PlainText or only PlainText if wished so.
    Also prevent mistake of sending the alert more than one for a
    particular issue.

    Parameters:
        journal_name  -  the journal for which the alert is sent
               issue  -  the issue for which the alert is sent
                sent  -  Display interface to edit email if "False"
                         (string). Else send the email.
          plain_text  -  the text of the mail
             subject  -  the subject of the mail
          recipients  -  the recipients of the mail (string with
                         comma-separated emails)
           html_mail  -  if 'html', also send email as HTML (copying
                         from the current issue on the web)
               force  -  if different than "False", the email is sent
                         even if it has already been sent.
                  ln  -  language
    """

    if not get_release_time(issue, journal_name, ln):
        # Trying to send an alert for an unreleased issue
        return wjt.tmpl_admin_alert_unreleased_issue(ln,
                                                     journal_name)
    if sent == "False":
        # Retrieve default message, subject and recipients, and
        # display email editor
        subject = wjt.tmpl_admin_alert_subject(journal_name,
                                               ln,
                                               issue)
        plain_text = wjt.tmpl_admin_alert_plain_text(journal_name,
                                                     ln,
                                                     issue)
        plain_text = plain_text.encode('utf-8')
        recipients = wjt.tmpl_admin_alert_recipients(journal_name,
                                                     ln,
                                                     issue)
        return wjt.tmpl_admin_alert_interface(ln,
                                              journal_name,
                                              subject,
                                              plain_text,
                                              recipients)
    else:
        # User asked to send the mail
        if was_alert_sent_for_issue(issue,
                                    journal_name,
                                    ln) != False and force == "False":
            # Mmh, email already sent before for this issue. Ask
            # confirmation
            return wjt.tmpl_admin_alert_was_already_sent(ln,
                                                         journal_name,
                                                         subject,
                                                         plain_text,
                                                         recipients,
                                                         html_mail,
                                                         issue)
        if html_mail == "html":
            # Also send as HTML: retrieve from current issue
            html_file = urlopen('%s/journal/%s?ln=en'
                                % (CFG_SITE_URL, journal_name))
            html_string = html_file.read()
            html_file.close()
            html_string = put_css_in_file(html_string, journal_name)
        else:
            # Send just as plain text
            html_string = plain_text.replace("<br/>", '\n')

        message = createhtmlmail(html_string, plain_text,
                                 subject, recipients)

        ## Transform the recipients string into a list for the mail server:
        to_addresses = [raw_address.strip() for raw_address in \
                        recipients.split(",")]
        recipients = to_addresses

        ## Send the mail:
        server = smtplib.SMTP("localhost", 25)
        server.sendmail('Bulletin-Support@cern.ch', recipients, message)
        # todo: has to go to some messages config
        update_DB_for_alert(issue, journal_name, ln)
        return wjt.tmpl_admin_alert_success_msg(ln,
                                                journal_name)

def perform_request_configure(journal_name, xml_config, action, ln=CFG_SITE_LANG):
    """
    Add a new journal or configure the settings of an existing journal.

    Parameters:
        journal_name  -  the journal to configure, or name of the new journal
          xml_config  -  the xml configuration of the journal (string)
              action  -  One of ['edit', 'editDone', 'add', 'addDone']
                  ln  -  language
    """

    msg = None
    if action == 'edit':
        # Read existing config
        if journal_name is not None:
            if not can_read_xml_config(journal_name):
                return '<span style="color:#f00">Configuration could not be read. Please check that %s/webjournal/%s/config.xml exists and can be read by the server.</span><br/>' % (CFG_ETCDIR, journal_name)
            config_path = '%s/webjournal/%s/config.xml' % (CFG_ETCDIR, journal_name)
            xml_config = file(config_path).read()
        else:
            # cannot edit unknown journal...
            return '<span style="color:#f00">You must specify a journal name</span>'
    if action in ['editDone', 'addDone']:
        # Save config
        if action == 'addDone':
            res = add_journal(journal_name, xml_config)
            if res == -1:
                msg = '<span style="color:#f00">A journal with that name already exists. Please choose another name.</span>'
                action = 'add'
            elif res == -2:
                msg = '<span style="color:#f00">Configuration could not be written (no permission). Please manually copy your config to %s/webjournal/%s/config.xml</span><br/>' % (CFG_ETCDIR, journal_name)
                action = 'edit'
            elif res > 0:
                msg = '<span style="color:#0f0">Journal successfully added.</span>'
                action = 'edit'
            else:
                msg = '<span style="color:#f00">An error occurred. The journal could not be added</span>'
                action = 'edit'
    if action == 'add':
        # Display a sample config. TODO: makes it less CERN-specific
        xml_config = '''<?xml version="1.0" encoding="UTF-8"?>
<webjournal name="CERNBulletin">
    <view>
        <niceName>CERN Bulletin</niceName>
        <niceURL>http://bulletin.cern.ch</niceURL>
        <css>
            <screen>img/webjournal_CERNBulletin/webjournal_CERNBulletin_screen.css</screen>
            <print>img/webjournal_CERNBulletin/webjournal_CERNBulletin_print.css</print>
        </css>
        <images>
            <path>img/Objects/Common</path>
        </images>
        <format_template>
            <index>CERN_Bulletin_Index.bft</index>
            <detailed>CERN_Bulletin_Detailed.bft</detailed>
            <search>CERN_Bulletin_Search.bft</search>
            <popup>CERN_Bulletin_Popup.bft</popup>
            <contact>CERN_Bulletin_Contact.bft</contact>
        </format_template>
    </view>

    <model>
        <record>
            <rule>News Articles, 980__a:BULLETINNEWS</rule>
            <rule>Official News, 980__a:BULLETINOFFICIAL</rule>
            <rule>Training and Development, 980__a:BULLETINTRAINING</rule>
            <rule>General Information, 980__a:BULLETINGENERAL</rule>
        </record>
    </model>

    <controller>
        <widgets>webjournal_weather</widgets>
        <frequency>14</frequency>
        <issue_grouping>True</issue_grouping>
        <marc_tags>
            <rule_tag>980__a</rule_tag>
            <issue_number>773__n</issue_number>
        </marc_tags>
    </controller>
</webjournal>'''

    out = wjt.tmpl_admin_configure_journal(ln=ln,
                                           journal_name=journal_name,
                                           xml_config=xml_config,
                                           action=action,
                                           msg=msg)

    return out

######################## ADDING/REMOVING JOURNALS ###############################

def add_journal(journal_name, xml_config):
    """
    Add a new journal to the DB. Also create the configuration file

    Parameters:
         journal_name  -  the name (used in URLs) of the new journal
           xml_config  -  the xml configuration of the journal (string)
    Returns:
         the id of the journal if successfully added
         -1 if could not be added because journal name already exists
         -2 if config could not be saved
         -3 if could not be added for other reasons
    """
    try:
        get_journal_id(journal_name)
    except InvenioWebJournalJournalIdNotFoundDBError:
        # Perfect, journal does not exist
        res = run_sql("INSERT INTO jrnJOURNAL (name) VALUES(%s)", (journal_name,))
        # Also save xml_config
        config_dir = '%s/webjournal/%s/' % (CFG_ETCDIR, journal_name)
        try:
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
            xml_config_file = file(config_dir + 'config.xml', 'w')
            xml_config_file.write(xml_config)
            xml_config_file.close()
        except Exception:
            res = -2
        # And save some info in file in case database is down
        journal_info_path = get_journal_info_path(journal_name)
        journal_info_file = open(journal_info_path, 'w')
        cPickle.dump({'journal_id': res,
                      'journal_name': journal_name,
                      'current_issue':'01/2000'}, journal_info_file)
        return res
    return -1

def remove_journal(journal_name):
    """
    Remove a journal from the DB. Keep everything else, since the
    journal should still be accessible.
    TODO: Think about removing config.xml file too if needed.

    Parameters:
         journal_name  -  the journal to remove

    Returns:
         the id of the journal if successfully removed or
         -1 if could not be removed because journal name does not exist or
         -2 if could not be removed for other reasons
    """
    run_sql("DELETE FROM jrnJOURNAL WHERE name=%s", (journal_name,))

######################## TIME / ISSUE FUNCTIONS ###############################


def release_journal_issue(publish_issues, journal_name, ln=CFG_SITE_LANG):
    """
    Releases a new issue.

    This sets the current issue in the database to 'publish_issues' for
    given 'journal_name'

    Parameters:
         journal_name  -  the journal for which we release a new issue
       publish_issues  -  the list of issues that will be considered as
                          current (there can be several)
                   ln  -  language
    """
    journal_id = get_journal_id(journal_name, ln)
    if len(publish_issues) > 1:
        publish_issues.sort(sort_by_week_number)
        low_bound = publish_issues[0]
        high_bound = publish_issues[-1]
        issue_display = '%s-%s/%s' % (low_bound.split("/")[0],
                                      high_bound.split("/")[0],
                                      high_bound.split("/")[1])
        # remember convention: if we are going over a new year, take the higher
    else:
        issue_display = publish_issues[0]
    # produce the DB lines
    for publish_issue in publish_issues:
        run_sql("INSERT INTO jrnISSUE (id_jrnJOURNAL, issue_number, issue_display) \
                VALUES(%s, %s, %s)", (journal_id,
                                      publish_issue,
                                      issue_display))
    # set first issue to published
    release_journal_update(publish_issues[0], journal_name, ln)

    # update information in file (in case DB is down)
    journal_info_path = get_journal_info_path(journal_name)
    journal_info_file = open(journal_info_path, 'w')
    cPickle.dump({'journal_id': journal_id,
                  'journal_name': journal_name,
                  'current_issue': get_current_issue(ln, journal_name)},
                 journal_info_file)

def delete_journal_issue(issue, journal_name, ln=CFG_SITE_LANG):
    """
    Deletes an issue from the DB.
    (Not currently used)
    """
    journal_id = get_journal_id(journal_name, ln)
    run_sql("DELETE FROM jrnISSUE WHERE issue_number=%s \
            AND id_jrnJOURNAL=%s",(issue, journal_id))

    # update information in file (in case DB is down)
    journal_info_path = get_journal_info_path(journal_name)
    journal_info_file = open(journal_info_path, 'w')
    cPickle.dump({'journal_id': journal_id,
                  'journal_name': journal_name,
                  'current_issue': get_current_issue(ln, journal_name)},
                 journal_info_file)

def was_alert_sent_for_issue(issue, journal_name, ln):
    """
    Returns False if alert has not already been sent for given journal and
    issue, else returns time of last alert, as time tuple

    Parameters:
         journal_name  -  the journal for which we want to check last alert
                issue  -  the issue for which we want to check last alert
                   ln  -  language
    Returns:
         time tuple or False. Eg: (2008, 4, 25, 7, 58, 37, 4, 116, -1)
    """
    journal_id = get_journal_id(journal_name, ln)
    date_announced = run_sql("SELECT date_announced FROM jrnISSUE \
                                WHERE issue_number=%s \
                                AND id_jrnJOURNAL=%s", (issue, journal_id))[0][0]
    if date_announced == None:
        return False
    else:
        return date_announced.timetuple()

def update_DB_for_alert(issue, journal_name, ln):
    """
    Update the 'last sent alert' timestamp for the given journal and
    issue.

    Parameters:
         journal_name  -  the journal for which we want to update the time
                          of last alert
                issue  -  the issue for which we want to update the time
                          of last alert
                   ln  -  language
    """
    journal_id = get_journal_id(journal_name, ln)
    run_sql("UPDATE jrnISSUE set date_announced=NOW() \
                WHERE issue_number=%s \
                AND id_jrnJOURNAL=%s", (issue,
                                        journal_id))

def release_journal_update(update_issue, journal_name, ln=CFG_SITE_LANG):
    """
    Releases an update to a journal.
    """
    journal_id = get_journal_id(journal_name, ln)
    run_sql("UPDATE jrnISSUE set date_released=NOW() \
                WHERE issue_number=%s \
                AND id_jrnJOURNAL=%s", (update_issue,
                                        journal_id))

######################## XML CONFIG ###############################

def can_read_xml_config(journal_name):
    """
    Check that configuration xml for given journal name is exists and
    can be read.
    """
    config_path = '%s/webjournal/%s/config.xml' % (CFG_ETCDIR, journal_name)
    try:
        file(config_path).read()
    except IOError:
        return False

    return True

######################## EMAIL HELPER FUNCTIONS ###############################

def createhtmlmail (html, text, subject, toaddr):
    """
    Create a mime-message that will render HTML in popular
    MUAs, text in better ones.
    """
    out = cStringIO.StringIO() # output buffer for our message
    htmlin = cStringIO.StringIO(html)
    txtin = cStringIO.StringIO(text)

    writer = MimeWriter.MimeWriter(out)
    #
    # set up some basic headers... we put subject here
    # because smtplib.sendmail expects it to be in the
    # message body
    #
    writer.addheader("Subject", subject)
    writer.addheader("MIME-Version", "1.0")

    ## Instead of a comma-separated "To" field, add a new "To" header for
    ## each of the addresses:
    to_addresses = [raw_address.strip() for raw_address in toaddr.split(",")]
    for to_address in to_addresses:
        writer.addheader("To", to_address)
    #
    # start the multipart section of the message
    # multipart/alternative seems to work better
    # on some MUAs than multipart/mixed
    #
    writer.startmultipartbody("alternative")
    writer.flushheaders()
    #
    # the plain text section
    #
    subpart = writer.nextpart()
    subpart.addheader("Content-Transfer-Encoding", "quoted-printable")
    #pout = subpart.startbody("text/plain", [("charset", 'us-ascii')])
    pout = subpart.startbody("text/plain", [("charset", 'utf-8')])
    mimetools.encode(txtin, pout, 'quoted-printable')
    txtin.close()
    #
    # start the html subpart of the message
    #
    subpart = writer.nextpart()
    subpart.addheader("Content-Transfer-Encoding", "quoted-printable")
    pout = subpart.startbody("text/html", [("charset", 'utf-8')])
    mimetools.encode(htmlin, pout, 'quoted-printable')
    htmlin.close()
    #
    # Now that we're done, close our writer and
    # return the message body
    #
    writer.lastpart()
    msg = out.getvalue()
    out.close()
    print msg
    return msg

def put_css_in_file(html_message, journal_name):
    """
    Retrieve the CSS of the journal and insert/inline it in the <head>
    section of the given html_message. (Used for HTML alert emails)

    Parameters:
          journal_name  -  the journal name
          html_message  -  the html message (string) in which the CSS
                           should be inserted
    Returns:
          the HTML message with its CSS inlined
    """
    config_strings = get_xml_from_config(["screen"], journal_name)
    try:
        css_path = config_strings["screen"][0]
    except Exception:
        register_exception(req=None,
                           suffix="No css file for journal %s. Is this right?"
                           % journal_name)
        return
    css_file = urlopen('%s/%s' % (CFG_SITE_URL, css_path))
    css = css_file.read()
    css = make_full_paths_in_css(css, journal_name)
    html_parted = html_message.split("</head>")
    if len(html_parted) > 1:
        html = '%s<style type="text/css">%s</style></head>%s' % (html_parted[0],
                                                        css,
                                                        html_parted[1])
    else:
        html_parted = html_message.split("<html>")
        if len(html_parted) > 1:
            html = '%s<html><head><style type="text/css">%s</style></head>%s' % (html_parted[0],
                                                                                 css,
                                                                                 html_parted[1])
        else:
            return
    return html

def make_full_paths_in_css(css, journal_name):
    """
    Update the URLs in a CSS from relative to absolute URLs, so that the
    URLs are accessible from anywhere (Used for HTML alert emails)

    Parameters:
          journal_name  -  the journal name
                   css  -  a cascading stylesheet (string)
    Returns:
          (str) the given css with relative paths converted to absolute paths
    """
    url_pattern = re.compile('''url\(["']?\s*(?P<url>\S*)\s*["']?\)''',
                             re.DOTALL)
    url_iter = url_pattern.finditer(css)
    rel_to_full_path = {}
    for url in url_iter:
        url_string = url.group("url")
        url_string = url_string.replace('"', "")
        url_string = url_string.replace("'", "")
        if url_string[:6] != "http://":
            rel_to_full_path[url_string] = '"%s/img/webjournal_%s/%s"' % \
            (CFG_SITE_URL,
            journal_name,
            url_string)
    for url in rel_to_full_path.keys():
        css = css.replace(url, rel_to_full_path[url])
    return css


