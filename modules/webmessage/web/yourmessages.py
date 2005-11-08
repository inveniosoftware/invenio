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


__lastupdated__ = """$Date$"""

# external imports
from mod_python import apache

# CDSWare imports
from cdsware.access_control_config import CFG_ACCESS_CONTROL_LEVEL_SITE
from cdsware.config                import weburl, cdslang
from cdsware.webuser               import getUid, isGuestUser, page_not_authorized
from cdsware.webmessage            import *
from cdsware.webpage               import page
from cdsware.messages              import wash_language, gettext_set_language



from cdsware.webmessage_scalability_tests import my_tester


### CALLABLE INTERFACE
def index(req):
    """ The function called by default
    """
    req.err_headers_out.add("Location", "%s/yourmessages.py/display?%s" % (weburl, req.args))
    raise apache.SERVER_RETURN, apache.HTTP_MOVED_PERMANENTLY
	

def display(req, ln = cdslang):
    """
    Displays the Inbox of a given user
    @param ln:  language
    @return the page for inbox
    """
    # Check if user is logged
    uid = getUid(req)
    if uid == -1 or isGuestUser(uid) or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1: 
        return page_not_authorized(req, "%s/yourmessages.py/display" % (weburl,))    
    # wash language argument
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    
    (body, errors, warnings) = perform_request_display(uid=uid,
                                                       ln=ln)
       
    return page(title       = _("Your Messages"),
                body        = body,
                navtrail    = get_navtrail(ln),
                description = "",
                keywords    = "",
                uid         = uid,
                lastupdated = __lastupdated__,
                language    = ln,
                errors      = errors,
                warnings    = warnings)


    
def write(req, msg_reply_id="", msg_to="", msg_to_group="", mode_user=1, ln=cdslang):
    """ write(): interface for message composing
    @param msg_reply_id: if this message is a reply to another, id of the other
    @param msg_to: if this message is not a reply, nickname of the user it must be
                   delivered to.
    @param msg_to_group: name of group to send message to
    @param ln: language
    @return the compose page
    """

    # Check if user is logged
    uid = getUid(req)

    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1 or isGuestUser(uid): 
        return page_not_authorized(req, "%s/yourmessages.py/write" % (weburl,))
    
    # wash language argument
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    
    # Request the composing page
    (body, errors, warnings) = perform_request_write(uid=uid,
                                                     msg_reply_id=msg_reply_id,
                                                     msg_to=msg_to,
                                                     msg_to_group=msg_to_group,
                                                     ln=ln)
    title = _("Write a message")
   
    return page(title       = title,
                body        = body,
                navtrail    = get_navtrail(ln, title),
                description = "",
                keywords    = "",
                uid         = uid,
                lastupdated = __lastupdated__,
                language    = ln,
                errors      = errors,
                warnings    = warnings)


def send(req,
         msg_to_user="",
         msg_to_group="",
         msg_subject="",
         msg_body="",
         msg_send_year="0000",
         msg_send_month="00",
         msg_send_day="00",
         users_to_add=[],
         groups_to_add=[], 
         user_search_pattern="",
         group_search_pattern="",
         send_button="",
         switch_to_group_button="",
         switch_to_user_button="",
         search_user_button="",
         search_group_button="",
         add_to_group_button="",
         add_to_user_button="",
         ln=cdslang):
    """
    Sends the message
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
    @param *button: which button was pressed
    @param ln: language
    @return a (body, errors, warnings) formed tuple.
    """
    # Check if user is logged
    uid = getUid(req)
    if uid == -1 or isGuestUser(uid) or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1: 
        return page_not_authorized(req, "%s/yourmessages.py/send" % (weburl,))
    
    # wash language argument
    ln = wash_language(ln)
    _ = gettext_set_language(ln)

    if send_button:
       (body, errors, warnings) = perform_request_send(uid,
                                                       msg_to_user,
                                                       msg_to_group,
                                                       msg_subject,
                                                       msg_body,
                                                       msg_send_year,
                                                       msg_send_month,
                                                       msg_send_day,
                                                       ln)
    else:       
        mode_user = 1
        add_values = 0
        if switch_to_group_button or search_group_button or add_to_group_button:
            mode_user = 0
        if add_to_group_button or add_to_user_button:
            add_values = 1
        (body, errors, warnings) = perform_request_write_with_search(msg_to_user,
                                                                     msg_to_group,
                                                                     msg_subject,
                                                                     msg_body,
                                                                     msg_send_year,
                                                                     msg_send_month,
                                                                     msg_send_day,
                                                                     users_to_add,
                                                                     groups_to_add, 
                                                                     user_search_pattern,
                                                                     group_search_pattern,
                                                                     mode_user,
                                                                     add_values,
                                                                     ln=cdslang)
    return page(title       = _("Your Messages"),
                body        = body,
                navtrail    = get_navtrail(ln),
                description = "",
                keywords    = "",
                uid         = uid,
                lastupdated = __lastupdated__,
                language    = ln,
                errors      = errors,
                warnings    = warnings)


def delete(req, msgid=-1, ln = cdslang):
    """
    Suppress a message
    @param msgid: id of message
    @param ln: language
    @return page
    """
    # Check if user is logged
    uid = getUid(req)
    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1 or isGuestUser(uid): 
        return page_not_authorized(req, "%s/yourmessages.py/delete_msg" % (weburl,))

    # wash language argument
    ln = wash_language(ln)
    _ = gettext_set_language(ln)

    # Generate content
    (body, errors, warnings) = perform_request_delete_msg(uid, msgid, ln)
    return page(title       = _("Your Messages"),
                body        = body,
                navtrail    = get_navtrail(ln),
                description = "",
                keywords    = "",
                uid         = uid,
                lastupdated = __lastupdated__,
                language    = ln,
                errors      = errors,
                warnings    = warnings)


def delete_all(req, confirmed=0, ln=cdslang):
    """
    Empty user's inbox
    @param confimed: 1 if message is confirmed
    @param ln: language
    \return page
    """
    # Check if user is logged
    uid = getUid(req)
    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1 or isGuestUser(uid): 
        return page_not_authorized(req, "%s/yourmessages.py/delete_all" % (weburl,))

    # wash language argument
    ln = wash_language(ln)
    _ = gettext_set_language(ln)

    # Generate content
    (body, errors, warnings) = perform_request_delete_all(uid, confirmed, ln)
    return page(title       = _("Your Messages"),
                body        = body,
                navtrail    = get_navtrail(ln),
                description = "",
                keywords    = "",
                uid         = uid,
                lastupdated = __lastupdated__,
                language    = ln,
                errors      = errors,
                warnings    = warnings)


def display_msg(req, msgid=-1, ln=cdslang):
    """
    Display a message
    @param msgid: id of message
    @param ln: languae
    @return page
    """
    # Check if user is logged
    uid = getUid(req)
    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1 or isGuestUser(uid): 
        return page_not_authorized(req, "%s/yourmessages.py/display_msg" % (weburl,))

    
    # wash language argument
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    # Generate content
    (body, errors, warnings) = perform_request_display_msg(uid, msgid, ln)
    title = _("Read a message")
    return page(title       = title,
                body        = body,
                navtrail    = get_navtrail(ln, title),
                description = "",
                keywords    = "",
                uid         = uid,
                lastupdated = __lastupdated__,
                language    = ln,
                errors      = errors,
                warnings    = warnings)

