# -*- coding: utf-8 -*-
## $Id$
## Messaging system (internal)


## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002, 2003, 2004, 2005 CERN.
##
## The CDSware is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## The CDSware is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDSware; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
"""webmessage module, messaging system"""

__lastupdated__ = """$Date$"""

# CDSWare imports
from cdsware.webmessage_dblayer import *
from cdsware.webmessage_config import *
from cdsware.config import cdslang
from cdsware.messages import gettext_set_language
from cdsware.dateutils import date_convert_to_MySQL

import cdsware.template

webmessage_templates = cdsware.template.load('webmessage')

def perform_request_display_msg(uid, msgid, ln = cdslang):
    """
    Displays a specific message
    @param uid:   user id
    @param msgid: message id
    
    @return a (body, errors[], warnings[]) formed tuple
    """
    # Wash the arguments...
    uid   = wash_url_argument(uid, 'int')
    msgid = wash_url_argument(msgid, 'int')
    
    errors = []
    warnings = []
    body = ""

    if (check_user_owns_message(uid, msgid) == 0):
        # The user doesn't own this message
        errors.append(('ERR_WEBMESSAGE_NOTOWNER',))
    else:
        (msg_id,
         msg_from_id,
         msg_from_nickname,
         msg_sent_to,
         msg_sent_to_group,
         msg_subject,
         msg_body,
         msg_sent_date,
         msg_received_date,
         msg_status) = get_message(uid, msgid)

        if (msg_id == ""):
	    # The message exists in table user_msgMESSAGE
	    # but not in table msgMESSAGE => table inconsistency
            errors.append(('ERR_WEBMESSAGE_NOMESSAGE',))
        else:
            if (msg_status == 'N'):
                set_message_status(uid, msgid, 'R')
            body = webmessage_templates.tmpl_display_msg(msg_id, 
                                                         msg_from_id,
                                                         msg_from_nickname,
							 msg_sent_to,
							 msg_sent_to_group,
							 msg_subject, 
							 msg_body,
							 msg_sent_date,
                                                         msg_received_date,
                                                         ln)
          
    return (body, errors, warnings)
													  

def perform_request_display(uid, errors=[], warnings=[], infos=[], ln=cdslang):
    """
    Displays the user's Inbox
    @param uid:   user id

    @return a (body, [errors], [warnings]) formed tuple
    """
    # Wash the arguments...
    uid = wash_url_argument(uid, 'int')

    body = ""    
    rows = []
    rows = get_all_messages_for_user(uid)
    nb_messages = 0
    
    if (uid != 1):
        nb_messages = count_nb_messages(uid)
        
    body = webmessage_templates.tmpl_display_inbox(messages=rows,
                                                   infos=infos,
                                                   warnings=warnings,
                                                   nb_messages=nb_messages,
                                                   ln=ln)
    return (body, errors, warnings)


def perform_request_delete_msg(uid, msgid, ln=cdslang):
    """
    Delete a given message from user inbox
    @param uid: user id (int)
    @param msgid: message id (int)
    @param ln: language
    @return a (body, errors, warning tuple)
    """
     # Wash the arguments...
    uid   = wash_url_argument(uid, 'int')
    msgid = wash_url_argument(msgid, 'int')

    _ = gettext_set_language(ln)
    
    errors = []
    warnings = []
    infos = []

    if (check_user_owns_message(uid, msgid) == 0):
        # The user doesn't own this message
        errors.append(('ERR_WEBMESSAGE_NOTOWNER',))
    else:
        if (delete_message_from_user_inbox(uid, msgid)==0):
            warnings.append(_("The message could not be deleted"))
        else:
            infos.append(_("Delete successful"))

    return perform_request_display(uid, errors, warnings, infos, ln) 


def perform_request_delete_all(uid, confirmed=0, ln=cdslang):
    """
    Delete every message for a given user
    @param uid: user id (int)
    @param confirmed: 0 will produce a confirmation message
    @param ln: language
    @return a (body, errors, warnings) tuple
    """
    
    infos = []
    warnings = []
    errors = []
    confirmed = wash_url_argument(confirmed, 'int')

    _ = gettext_set_language(ln)
    if (confirmed == 1):
        delete_all_messages(uid)
        infos = [_("Your mailbox has been emptied")]
        return perform_request_display(uid, warnings, errors, infos, ln)
    else:
        body = webmessage_templates.tmpl_confirm_delete(ln)
        return (body, errors, warnings)


def perform_request_write(uid,
                          msg_reply_id="",
                          msg_to="",
                          msg_to_group="",
                          ln=cdslang):
    """
    Display a write a message page.
    @param uid: user id (int)
    @param msg_reply_id: if this message is a reply to another, other's ID (int)
    @param msg_to: comma separated usernames (string)
    @param msg_to_group: comma separated groupnames (string)
    @param ln: language
    @return a (body, errors, warnings) tuple
    """
    # wash arguments
    uid = wash_url_argument(uid, 'int')
    msg_reply_id = wash_url_argument(msg_reply_id, 'int')
    msg_to = wash_url_argument(msg_to, 'str')
    msg_to_group = wash_url_argument(msg_to_group, 'str')
    # ln has already been washed in yourmessages.py

    errors = []
    warnings = []
    body = ""

    msg_from_nickname = ""
    msg_subject = ""
    msg_body = ""
    msg_id = 0
    if (msg_reply_id):
        if (check_user_owns_message(uid, msg_reply_id) == 0):
            # The user doesn't own this message
            errors.append(('ERR_WEBMESSAGE_NOTOWNER',))
        else:
            # Junk== make pylint happy!
            junk = 0
            (msg_id,
             junk,
             msg_from_nickname,
             junk,
             junk,
             msg_subject,
             msg_body,
             junk,
             junk,
             junk) = get_message(uid, msg_reply_id)    
            if (msg_id == ""):
                # The message exists in table user_msgMESSAGE
                # but not in table msgMESSAGE => table inconsistency
                errors.append(('ERR_WEBMESSAGE_NOMESSAGE',))
            else:
                msg_to = msg_from_nickname
    
    body = webmessage_templates.tmpl_write(msg_to=msg_to,
                                           msg_to_group=msg_to_group,
                                           msg_id=msg_id,
                                           msg_subject=msg_subject,
                                           msg_body=msg_body,
                                           warnings=[],
                                           ln=ln)
    return (body, errors, warnings)



def perform_request_write_with_search(msg_to_user="",
                                      msg_to_group="",
                                      msg_subject="",
                                      msg_body="",
                                      msg_send_year=0,
                                      msg_send_month=0,
                                      msg_send_day=0,
                                      users_to_add=[],
                                      groups_to_add=[], 
                                      user_search_pattern="",
                                      group_search_pattern="",
                                      mode_user=1,
                                      add_values=0,
                                      ln=cdslang):
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
    @return a (body, errors, warnings) formed tuple.
    """
    
    # wash arguments
    users_to_add = wash_url_argument(users_to_add, 'list')
    groups_to_add = wash_url_argument(groups_to_add, 'list')
    msg_send_year = wash_url_argument(msg_send_year, 'int')
    msg_send_month = wash_url_argument(msg_send_month, 'int')
    msg_send_day = wash_url_argument(msg_send_day, 'int')
    
    user_list_output = []
    group_list_output = []
    warnings = []
    errors = []
    
    def separate(name1, name2):
        """
        name1, name2 => "name1, name2"
        """
        return name1 + cfg_webmessage_separator + " " + name2
    
    if mode_user:
        if add_values and users_to_add:
            tmp = users_to_add
            if msg_to_user:
                tmp.insert(0, msg_to_user)
            msg_to_user = reduce(separate, tmp)
        if user_search_pattern:
            users_found = get_nicknames_like(user_search_pattern)
            if users_found:
                for user_name in users_found:
                    user_list_output.append((user_name[0], user_name[0] in users_to_add))
    else: 
        if add_values and groups_to_add:
            tmp = groups_to_add
            if msg_to_group:
                tmp.insert(0, msg_to_group)
            msg_to_group = reduce(separate, tmp)
        if group_search_pattern:
            groups_found = get_groupnames_like(group_search_pattern)
            if groups_found:
                for group_name in groups_found:
                    group_list_output.append((group_name[0], group_name[0] in groups_to_add))        
    body = webmessage_templates.tmpl_write(msg_to=msg_to_user,
                                           msg_to_group=msg_to_group,
                                           msg_subject=msg_subject,
                                           msg_body=msg_body, 
                                           msg_send_year=msg_send_year,
                                           msg_send_month=msg_send_month,
                                           msg_send_day=msg_send_day,
                                           warnings=warnings,
                                           users_to_add=user_list_output,
                                           groups_to_add=group_list_output,
                                           user_search_pattern=user_search_pattern,
                                           group_search_pattern=group_search_pattern,
                                           display_users_to_add=mode_user,
                                           ln=ln)
    return (body, errors, warnings)

    
def perform_request_send(uid,
                         msg_to_user="",
                         msg_to_group="",
                         msg_subject="",
                         msg_body="",
                         msg_send_year=0,
                         msg_send_month=0,
                         msg_send_day=0,
                         ln=cdslang):
    """
    send a message. if unable return warenings to write page
    @param uid: id of user from (int)
    @param msg_to_user: comma separated usernames (recipients) (str)
    @param msg_to_group: comma separated groupnames (recipeints) (str)
    @param msg_subject: subject of message (str)
    @param msg_body: body of message (str)
    @param msg_send_year: send this message on year x (int)
    @param msg_send_month: send this message on month y (int)
    @param msg_send_day: send this message on day z (int)
    @param ln: language
    @return a (body, errors, warnings) tuple
    """
    # wash arguments
    msg_to_user = wash_url_argument(msg_to_user, 'str')
    msg_to_group = wash_url_argument(msg_to_group, 'str')
    msg_subject = wash_url_argument(msg_subject, 'str')
    msg_body = wash_url_argument(msg_body, 'str')
    msg_send_year = wash_url_argument(msg_send_year, 'int')
    msg_send_month = wash_url_argument(msg_send_month, 'int')
    msg_send_day = wash_url_argument(msg_send_day, 'int')

    _ = gettext_set_language(ln)

    def strip_spaces(str):
        """suppress spaces before and after x (str)"""
        return str.strip()
    # wash user input
    users_to = map(strip_spaces, msg_to_user.split(cfg_webmessage_separator))
    groups_to = map(strip_spaces, msg_to_group.split(cfg_webmessage_separator))

    if users_to == [""]:
        users_to = []
    if groups_to == [""]:
        groups_to = []


    warnings = []
    errors = []
    infos = []
    problem = None

    users_to_str = cfg_webmessage_separator.join(users_to)
    groups_to_str = cfg_webmessage_separator.join(groups_to)
    
    if (msg_send_year == msg_send_month == msg_send_day == 0):
        status = cfg_webmessage_status_code['NEW']
    else:
        status = cfg_webmessage_status_code['REMINDER']

    try:
        send_on_date = date_convert_to_MySQL(msg_send_year, msg_send_month, msg_send_day)
    except ValueError:
        warnings.append(_("The chosen date (%i/%i/%i) is invalid")%(msg_send_year, msg_send_month, msg_send_day))
        problem = 1
        
    if not(users_to_str or groups_to_str):
        # <=> not(users_to_str) AND not(groups_to_str)
        warnings.append(_("Please enter a user name or a group name"))
        problem = 1
        
    if len(msg_body) > cfg_webmessage_max_size_of_message:
        warnings.append(_("""Your message is too long, please edit it.
                             Max size allowed is %i characters
                          """)%(cfg_webmessage_max_size_of_message,))
        problem = 1


    users_dict = get_uids_from_nicks(users_to)
    users_to = users_dict.items()
    groups_dict = get_gids_from_groupnames(groups_to)
    groups_to = groups_dict.items()
    gids_to = []
    for (group_name, group_id) in groups_to:
        if not(group_id):
            warnings.append(_("Group '%s' doesn't exist\n")%(group_name))
            problem = 1
        else:
            gids_to.append(group_id)
        
    # Get uids from gids
    uids_from_group = get_uids_members_of_groups(gids_to)
    # Add the original uids, and make sure  there is no double values. 
    tmp_dict = dict.fromkeys(uids_from_group)
    for (user_nick, user_id) in users_to:
        if user_id:
            if user_id not in tmp_dict:
                uids_from_group.append(user_id)
                tmp_dict[user_id] = None
        else:
            warnings.append(_("User '%s' doesn't exist\n")%(user_nick))
            problem = 1
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
        return (body, errors, warnings)
    else:
        msg_id = create_message(uid,
                                users_to_str,
                                groups_to_str,
                                msg_subject,
                                msg_body,
                                send_on_date)
        uid_problem = send_message(uids_from_group, msg_id, status)
        if len(uid_problem) > 0:
            usernames_problem_dict = get_nicks_from_uids(uid_problem)
            usernames_problem = usernames_problem_dict.values()
            def listing(name1, name2):
                """ name1, name2 => 'name1, name2' """
                return str(name1) + ", " + str(name2)
            warning = _("Your message couldn't be sent to the following recipients\n")
            warning += _("These users are overquota: ")
            warnings.append(warning + reduce(listing, usernames_problem)) 
 

        if len(uids_from_group) != len(uid_problem):
            infos.append(_("Your message has been sent."))
        return perform_request_display(uid, errors, warnings, infos, ln)


def account_new_mail(uid, ln=cdslang):
    """
    display new mail info for myaccount.py page.
    @param uid: user id (int)
    @param ln: language
    @return html body
    """
    nb_new_mail = get_nb_new_mail_for_user(uid)
    return webmessage_templates.tmpl_account_new_mail(nb_new_mail, ln)

def get_navtrail(ln=cdslang, title=""):
    """
    gets the navtrail for title...
    @param title: title of the page
    @param ln: language
    @return HTML output
    """
    navtrail = webmessage_templates.tmpl_navtrail(ln, title)
    return navtrail

def wash_url_argument(var, new_type):
    """
    Wash argument into 'new_type', that can be 'list', 'str', or 'int'.
    If var is a list, will change first element into new_type.
    If int check unsuccessful, returns 0
    If needed, the check 'type(var) is not None' should be done before calling this function
    """
    out = []
    if new_type == 'list':  # return lst
        if type(var) is list or type(var) is tuple:
            out = var
        else:
            out = [var]
    elif new_type == 'str':  # return str
        if type(var) is list:
            try:
                out = "%s" % var[0]
            except:
                out = ""
        elif type(var) is str:
            out = var
        else:
            out = "%s" % var
    elif new_type == 'int': # return int
        if type(var) is list:
            try:
                out = int(var[0])
            except:
                out = 0
        elif type(var) is int:
            out = var
        elif type(var) is str:
            try:
                out = int(var)
            except:
                out = 0
        else:
            out = 0
    elif new_type == 'tuple': # return tuple
        if type(var) is tuple:
            out = var
        else:
            out = (var,)
    elif new_type == 'dict': # return dictionary
        if type(var) is dict:
            out = var
        else:
            out = {0:var}
    return out

