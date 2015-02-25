# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2014 CERN.
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

""" WebMessage module, messaging system"""

__revision__ = "$Id$"

import invenio.modules.messages.dblayer as db
from invenio.modules.messages.config import \
    CFG_WEBMESSAGE_STATUS_CODE, \
    CFG_WEBMESSAGE_RESULTS_FIELD, \
    CFG_WEBMESSAGE_SEPARATOR, \
    CFG_WEBMESSAGE_ROLES_WITHOUT_QUOTA, \
    CFG_WEBMESSAGE_MAX_SIZE_OF_MESSAGE
from invenio.modules.messages.errors import InvenioWebMessageError
from invenio.config import CFG_SITE_LANG
from invenio.base.i18n import gettext_set_language
from invenio.utils.date import datetext_default, get_datetext
from invenio.utils.html import escape_html
from invenio.legacy.webuser import collect_user_info, list_users_in_roles
from invenio.modules.access.control import acc_get_role_id, acc_is_user_in_role
try:
    import invenio.legacy.template
    webmessage_templates = invenio.legacy.template.load('webmessage')
except:
    pass
from invenio.ext.logging import register_exception

def perform_request_display_msg(uid, msgid, ln=CFG_SITE_LANG):
    """
    Displays a specific message
    @param uid:   user id
    @param msgid: message id

    @return: body
    """
    _ = gettext_set_language(ln)

    body = ""

    if (db.check_user_owns_message(uid, msgid) == 0):
        # The user doesn't own this message
        try:
            raise InvenioWebMessageError(_('Sorry, this message is not in your mailbox.'))
        except InvenioWebMessageError as exc:
            register_exception()
            body = webmessage_templates.tmpl_error(exc.message, ln)
            return body
    else:
        (msg_id,
         msg_from_id, msg_from_nickname,
         msg_sent_to, msg_sent_to_group,
         msg_subject, msg_body,
         msg_sent_date, msg_received_date,
         msg_status) = db.get_message(uid, msgid)

        if (msg_id == ""):
            # The message exists in table user_msgMESSAGE
            # but not in table msgMESSAGE => table inconsistency
            try:
                raise InvenioWebMessageError(_('This message does not exist.'))
            except InvenioWebMessageError as exc:
                register_exception()
                body = webmessage_templates.tmpl_error(exc.message, ln)
                return body
        else:
            if (msg_status == CFG_WEBMESSAGE_STATUS_CODE['NEW']):
                db.set_message_status(uid, msgid,
                                      CFG_WEBMESSAGE_STATUS_CODE['READ'])
            body = webmessage_templates.tmpl_display_msg(
                                                msg_id,
                                                msg_from_id,
                                                msg_from_nickname,
                                                msg_sent_to,
                                                msg_sent_to_group,
                                                msg_subject,
                                                msg_body,
                                                msg_sent_date,
                                                msg_received_date,
                                                ln)
    return body


def perform_request_display(uid, warnings=[], infos=[], ln=CFG_SITE_LANG):
    """
    Displays the user's Inbox
    @param uid:   user id

    @return: body with warnings
    """
    body = ""
    rows = []
    rows = db.get_all_messages_for_user(uid)
    nb_messages = db.count_nb_messages(uid)
    from invenio.modules.accounts.models import User
    from invenio.modules.access.models import AccROLE
    no_quota = User.query.get(uid).active_roles.join(AccROLE).filter(
        AccROLE.name.in_(CFG_WEBMESSAGE_ROLES_WITHOUT_QUOTA)
    ).first() is not None
    body = webmessage_templates.tmpl_display_inbox(messages=rows,
                                                   infos=infos,
                                                   warnings=warnings,
                                                   nb_messages=nb_messages,
                                                   no_quota=no_quota,
                                                   ln=ln)
    return body


def perform_request_delete_msg(uid, msgid, ln=CFG_SITE_LANG):
    """
    Delete a given message from user inbox
    @param uid: user id (int)
    @param msgid: message id (int)
    @param ln: language
    @return: body with warnings
    """
    _ = gettext_set_language(ln)

    warnings = []
    infos = []
    body = ""

    if (db.check_user_owns_message(uid, msgid) == 0):
        # The user doesn't own this message
        try:
            raise InvenioWebMessageError(_('Sorry, this message is not in your mailbox.'))
        except InvenioWebMessageError as exc:
            register_exception()
            body = webmessage_templates.tmpl_error(exc.message, ln)
            return body
    else:
        if (db.delete_message_from_user_inbox(uid, msgid) == 0):
            warnings.append(_("The message could not be deleted."))
        else:
            infos.append(_("The message was successfully deleted."))
    return perform_request_display(uid, warnings, infos, ln)

def perform_request_delete_all(uid, confirmed=False, ln=CFG_SITE_LANG):
    """
    Delete every message for a given user
    @param uid: user id (int)
    @param confirmed: 0 will produce a confirmation message
    @param ln: language
    @return: body with warnings
    """
    infos = []
    warnings = []
    _ = gettext_set_language(ln)
    if confirmed:
        db.delete_all_messages(uid)
        infos = [_("Your mailbox has been emptied.")]
        return perform_request_display(uid, warnings, infos, ln)
    else:
        body = webmessage_templates.tmpl_confirm_delete(ln)
        return body

def perform_request_write(uid,
                          msg_reply_id="",
                          msg_to="",
                          msg_to_group="",
                          msg_subject="",
                          msg_body="",
                          ln=CFG_SITE_LANG):
    """
    Display a write a message page.

    @param uid: user id.
    @type uid: int
    @param msg_reply_id: if this message is a reply to another, other's ID.
    @type msg_reply_id: int
    @param msg_to: comma separated usernames.
    @type msg_to: string
    @param msg_to_group: comma separated groupnames.
    @type msg_to_group: string
    @param msg_subject: message subject.
    @type msg_subject: string
    @param msg_body: message body.
    @type msg_body: string
    @param ln: language.
    @type ln: string
    @return: body with warnings.
    """
    warnings = []
    body = ""
    _ = gettext_set_language(ln)
    msg_from_nickname = ""
    msg_id = 0
    if (msg_reply_id):
        if (db.check_user_owns_message(uid, msg_reply_id) == 0):
            # The user doesn't own this message
            try:
                raise InvenioWebMessageError(_('Sorry, this message is not in your mailbox.'))
            except InvenioWebMessageError as exc:
                register_exception()
                body = webmessage_templates.tmpl_error(exc.message, ln)
                return body
        else:
            # dummy == variable name to make pylint and pychecker happy!
            (msg_id,
             msg_from_id, msg_from_nickname,
             dummy, dummy,
             msg_subject, msg_body,
             dummy, dummy, dummy) = db.get_message(uid, msg_reply_id)
            if (msg_id == ""):
                # The message exists in table user_msgMESSAGE
                # but not in table msgMESSAGE => table inconsistency
                try:
                    raise InvenioWebMessageError(_('This message does not exist.'))
                except InvenioWebMessageError as exc:
                    register_exception()
                    body = webmessage_templates.tmpl_error(exc.message, ln)
                    return body
            else:
                msg_to = msg_from_nickname or str(msg_from_id)

    body = webmessage_templates.tmpl_write(msg_to=msg_to,
                                           msg_to_group=msg_to_group,
                                           msg_id=msg_id,
                                           msg_subject=msg_subject,
                                           msg_body=msg_body,
                                           warnings=[],
                                           ln=ln)
    return body

def perform_request_write_with_search(
                        uid,
                        msg_to_user="",
                        msg_to_group="",
                        msg_subject="",
                        msg_body="",
                        msg_send_year=0,
                        msg_send_month=0,
                        msg_send_day=0,
                        names_selected=[],
                        search_pattern="",
                        results_field=CFG_WEBMESSAGE_RESULTS_FIELD['NONE'],
                        add_values=0,
                        ln=CFG_SITE_LANG):
    """
    Display a write message page, with prefilled values
    @param msg_to_user: comma separated usernames (str)
    @param msg_to_group: comma separated groupnames (str)
    @param msg_subject: message subject (str)
    @param msg_bidy: message body (string)
    @param msg_send_year: year to send this message on (int)
    @param_msg_send_month: month to send this message on (int)
    @param_msg_send_day: day to send this message on (int)
    @param users_to_add: list of usernames ['str'] to add to msg_to_user
    @param groups_to_add: list of groupnames ['str'] to add to msg_to_group
    @param user_search_pattern: will search users with this pattern (str)
    @param group_search_pattern: will search groups with this pattern (str)
    @param mode_user: if 1 display user search box, else group search box
    @param add_values: if 1 users_to_add will be added to msg_to_user field..
    @param ln: language
    @return: body with warnings
    """
    warnings = []
    search_results_list = []
    def cat_names(name1, name2):
        """ name1, name2 => 'name1, name2' """
        return name1 + CFG_WEBMESSAGE_SEPARATOR + " " + name2

    if results_field == CFG_WEBMESSAGE_RESULTS_FIELD['USER']:
        if add_values and len(names_selected):
            usernames_to_add = reduce(cat_names, names_selected)
            if msg_to_user:
                msg_to_user = cat_names(msg_to_user, usernames_to_add)
            else:
                msg_to_user = usernames_to_add

        users_found = db.get_nicknames_like(search_pattern)
        if users_found:
            for user_name in users_found:
                search_results_list.append((user_name[0],
                                            user_name[0] in names_selected))

    elif results_field == CFG_WEBMESSAGE_RESULTS_FIELD['GROUP']:
        if add_values and len(names_selected):
            groupnames_to_add = reduce(cat_names, names_selected)
            if msg_to_group:
                msg_to_group = cat_names(msg_to_group, groupnames_to_add)
            else:
                msg_to_group = groupnames_to_add
        groups_dict = db.get_groupnames_like(uid, search_pattern)
        groups_found = groups_dict.values()
        if groups_found:
            for group_name in groups_found:
                search_results_list.append((group_name,
                                            group_name in names_selected))

    body = webmessage_templates.tmpl_write(
                            msg_to=msg_to_user,
                            msg_to_group=msg_to_group,
                            msg_subject=msg_subject,
                            msg_body=msg_body,
                            msg_send_year=msg_send_year,
                            msg_send_month=msg_send_month,
                            msg_send_day=msg_send_day,
                            warnings=warnings,
                            search_results_list=search_results_list,
                            search_pattern=search_pattern,
                            results_field=results_field,
                            ln=ln)
    return body

def perform_request_send(uid,
                         msg_to_user="",
                         msg_to_group="",
                         msg_subject="",
                         msg_body="",
                         msg_send_year=0,
                         msg_send_month=0,
                         msg_send_day=0,
                         ln=CFG_SITE_LANG,
                         use_email_address = 0):
    """
    send a message. if unable return warnings to write page
    @param uid: id of user from (int)
    @param msg_to_user: comma separated usernames (recipients) (str)
    @param msg_to_group: comma separated groupnames (recipeints) (str)
    @param msg_subject: subject of message (str)
    @param msg_body: body of message (str)
    @param msg_send_year: send this message on year x (int)
    @param msg_send_month: send this message on month y (int)
    @param msg_send_day: send this message on day z (int)
    @param ln: language
    @return: (body with warnings, title, navtrail)
    """
    _ = gettext_set_language(ln)

    def strip_spaces(text):
        """suppress spaces before and after x (str)"""
        return text.strip()
    # wash user input
    users_to = map(strip_spaces, msg_to_user.split(CFG_WEBMESSAGE_SEPARATOR))
    groups_to = map(strip_spaces, msg_to_group.split(CFG_WEBMESSAGE_SEPARATOR))

    if users_to == ['']:
        users_to = []
    if groups_to == ['']:
        groups_to = []

    warnings = []
    infos = []
    problem = None

    users_to_str = CFG_WEBMESSAGE_SEPARATOR.join(users_to)
    groups_to_str = CFG_WEBMESSAGE_SEPARATOR.join(groups_to)

    send_on_date = get_datetext(msg_send_year, msg_send_month, msg_send_day)
    if (msg_send_year == msg_send_month == msg_send_day == 0):
        status = CFG_WEBMESSAGE_STATUS_CODE['NEW']
    else:
        status = CFG_WEBMESSAGE_STATUS_CODE['REMINDER']
        if send_on_date == datetext_default:
            warning = \
            _("The chosen date (%(x_year)i/%(x_month)i/%(x_day)i) is invalid.")
            warning = warning % {'x_year': msg_send_year,
                                 'x_month': msg_send_month,
                                 'x_day': msg_send_day}
            warnings.append(warning)
            problem = True

    if not(users_to_str or groups_to_str):
        # <=> not(users_to_str) AND not(groups_to_str)
        warnings.append(_("Please enter a user name or a group name."))
        problem = True

    if len(msg_body) > CFG_WEBMESSAGE_MAX_SIZE_OF_MESSAGE:
        warnings.append(_("Your message is too long, please shorten it. "
                          "Maximum size allowed is %(x_size)i characters.",
                          x_size=(CFG_WEBMESSAGE_MAX_SIZE_OF_MESSAGE,)))
        problem = True

    if use_email_address == 0:
        users_dict = db.get_uids_from_nicks(users_to)
        users_to = users_dict.items() # users_to=[(nick, uid),(nick2, uid2)]
    elif use_email_address == 1:
        users_dict = db.get_uids_from_emails(users_to)
        users_to = users_dict.items() # users_to=[(email, uid),(email2, uid2)]
    groups_dict = db.get_gids_from_groupnames(groups_to)
    groups_to = groups_dict.items()
    gids_to = []
    for (group_name, group_id) in groups_to:
        if not(group_id):
            warnings.append(_("Group %(x_name)s does not exist.", x_name=(escape_html(group_name))))
            problem = 1
        else:
            gids_to.append(group_id)

    # Get uids from gids
    uids_from_group = db.get_uids_members_of_groups(gids_to)
    # Add the original uids, and make sure  there is no double values.
    tmp_dict = {}
    for uid_receiver in uids_from_group:
        tmp_dict[uid_receiver] = None
    for (user_nick, user_id) in users_to:
        if user_id:
            if user_id not in tmp_dict:
                uids_from_group.append(user_id)
                tmp_dict[user_id] = None
        else:
            if type(user_nick) == int or \
               type(user_nick) == str and user_nick.isdigit():
                user_nick = int(user_nick)
                if db.user_exists(user_nick) and user_nick not in tmp_dict:
                    uids_from_group.append(user_nick)
                    tmp_dict[user_nick] = None
            else:
                warnings.append(_("User %(x_name)s does not exist.", x_name=(escape_html(user_nick))))
                problem = True
    if problem:
        body = webmessage_templates.tmpl_write(msg_to=users_to_str,
                                               msg_to_group=groups_to_str,
                                               msg_subject=msg_subject,
                                               msg_body=msg_body,
                                               msg_send_year=msg_send_year,
                                               msg_send_month=msg_send_month,
                                               msg_send_day=msg_send_day,
                                               warnings=warnings,
                                               ln=ln)
        title =  _("Write a message")
        navtrail = get_navtrail(ln, title)
        return (body, title, navtrail)
    else:
        msg_id = db.create_message(uid,
                                   users_to_str, groups_to_str,
                                   msg_subject, msg_body,
                                   send_on_date)
        uid_problem = db.send_message(uids_from_group, msg_id, status)
        if len(uid_problem) > 0:
            usernames_problem_dict = db.get_nicks_from_uids(uid_problem)
            usernames_problem = usernames_problem_dict.values()
            def listing(name1, name2):
                """ name1, name2 => 'name1, name2' """
                return str(name1) + ", " + str(name2)
            warning = _("Your message could not be sent to the following recipients as it would exceed their quotas:") + " "
            warnings.append(warning + reduce(listing, usernames_problem))

        if len(uids_from_group) != len(uid_problem):
            infos.append(_("Your message has been sent."))
        else:
            db.check_if_need_to_delete_message_permanently([msg_id])
        body = perform_request_display(uid, warnings,
                                       infos, ln)
        title = _("Your Messages")
        return (body, title, get_navtrail(ln))

def account_new_mail(uid, ln=CFG_SITE_LANG):
    """
    display new mail info for myaccount.py page.
    @param uid: user id (int)
    @param ln: language
    @return: html body
    """
    nb_new_mail = db.get_nb_new_messages_for_user(uid)
    total_mail = db.get_nb_readable_messages_for_user(uid)
    return webmessage_templates.tmpl_account_new_mail(nb_new_mail,
                                                      total_mail, ln)

def get_navtrail(ln=CFG_SITE_LANG, title=""):
    """
    gets the navtrail for title...
    @param title: title of the page
    @param ln: language
    @return: HTML output
    """
    navtrail = webmessage_templates.tmpl_navtrail(ln, title)
    return navtrail

def is_no_quota_user(uid):
    """
    Return True if the user belongs to any of the no_quota roles.
    """
    no_quota_role_ids = [acc_get_role_id(role) for role in CFG_WEBMESSAGE_ROLES_WITHOUT_QUOTA]
    res = {}
    user_info = collect_user_info(uid)
    for role_id in no_quota_role_ids:
        if acc_is_user_in_role(user_info, role_id):
            return True
    return False
