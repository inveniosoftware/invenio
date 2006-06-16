# -*- coding: utf-8 -*-
## $Id$
## Messaging system (internal)

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
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

"""WebMessage web interface"""

__lastupdated__ = """$Date$"""

from invenio.access_control_config import CFG_ACCESS_CONTROL_LEVEL_SITE
from invenio.config import weburl, cdslang
from invenio.webuser import getUid, isGuestUser, page_not_authorized
from invenio.webmessage import *
from invenio.webpage import page
from invenio.messages import wash_language, gettext_set_language
from invenio.urlutils import redirect_to_url
from invenio.webinterface_handler import wash_urlargd, WebInterfaceDirectory

class WebInterfaceYourMessagesPages(WebInterfaceDirectory):
    """Defines the set of /yourmessages pages."""

    _exports = ['', 'display', 'write', 'send', 'delete', 'delete_all',
                'display_msg']

    def index(self, req, form):
        """ The function called by default
        """
        redirect_to_url(req, "%s/yourmessages/display?%s" % (weburl, req.args))

    def display(self, req, form):
        """
        Displays the Inbox of a given user
        @param ln:  language
        @return the page for inbox
        """

        argd = wash_urlargd(form, {})

        # Check if user is logged
        uid = getUid(req)
        if uid == -1 or isGuestUser(uid) or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1: 
            return page_not_authorized(req, "%s/yourmessages/display" % (weburl,))    

        _ = gettext_set_language(argd['ln'])

        (body, errors, warnings) = perform_request_display(uid=uid,
                                                           ln=argd['ln'])

        return page(title       = _("Your Messages"),
                    body        = body,
                    navtrail    = get_navtrail(argd['ln']),
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = argd['ln'],
                    errors      = errors,
                    warnings    = warnings)
    
    def write(self, req, form):
        """ write(): interface for message composing
        @param msg_reply_id: if this message is a reply to another, id of the other
        @param msg_to: if this message is not a reply, nickname of the user it must be
                       delivered to.
        @param msg_to_group: name of group to send message to
        @param ln: language
        @return the compose page
        """

        argd = wash_urlargd(form, {'msg_reply_id': (str, ""),
                                   'msg_to': (str, ""),
                                   'msg_to_group': (str, ""),
                                   'mode_user': (int, 1), # FIXME: unused?
                                   })

        # Check if user is logged
        uid = getUid(req)

        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1 or isGuestUser(uid): 
            return page_not_authorized(req, "%s/yourmessages/write" % (weburl,))

        _ = gettext_set_language(argd['ln'])

        # Request the composing page
        (body, errors, warnings) = perform_request_write(uid=uid,
                                                         msg_reply_id=argd['msg_reply_id'],
                                                         msg_to=argd['msg_to'],
                                                         msg_to_group=argd['msg_to_group'],
                                                         ln=argd['ln'])
        title = _("Write a message")

        return page(title       = title,
                    body        = body,
                    navtrail    = get_navtrail(argd['ln'], title),
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = argd['ln'],
                    errors      = errors,
                    warnings    = warnings)

    def send(self, req, form):
        """
        Sends the message
        @param msg_to_user: comma separated usernames (str)
        @param msg_to_group: comma separated groupnames (str)
        @param msg_subject: message subject (str)
        @param msg_bidy: message body (string)
        @param msg_send_year: year to send this message on (int)
        @param_msg_send_month: month to send this message on (int)
        @param_msg_send_day: day to send this message on (int)
        @param names_to_add: list of usernames ['str'] to add to msg_to_user / group
        @param search_pattern: will search for users/groups with this pattern (str)
        @param add_values: if 1 users_to_add will be added to msg_to_user field..
        @param *button: which button was pressed
        @param ln: language
        @return a (body, errors, warnings) formed tuple.
        """

        argd = wash_urlargd(form, {'msg_to_user': (str, ""),
                                   'msg_to_group': (str, ""),
                                   'msg_subject': (str, ""),
                                   'msg_body': (str, ""),
                                   'msg_send_year': (str, "0000"),
                                   'msg_send_month': (str, "00"),
                                   'msg_send_day': (str, "00"),
                                   'results_field': (str, "none"), # FIXME: docstring? for others too
                                   'names_selected': (list, []), 
                                   'search_pattern': (str, ""), 
                                   'send_button': (str, ""), 
                                   'search_user': (str, ""), 
                                   'search_group': (str, ""), 
                                   'add_user': (str, ""), 
                                   'add_group': (str, ""), 
                                   })

        # Check if user is logged
        uid = getUid(req)
        if uid == -1 or isGuestUser(uid) or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1: 
            return page_not_authorized(req, "%s/yourmessages/send" % (weburl,))

        _ = gettext_set_language(argd['ln'])

        if argd['send_button']:
           (body, errors, warnings, title, navtrail) = perform_request_send(uid,
                                                                            argd['msg_to_user'],
                                                                            argd['msg_to_group'],
                                                                            argd['msg_subject'],
                                                                            argd['msg_body'],
                                                                            argd['msg_send_year'],
                                                                            argd['msg_send_month'],
                                                                            argd['msg_send_day'],
                                                                            argd['ln'])
        else:
            title = _('Write a message')
            navtrail = get_navtrail(argd['ln'], title)
            if argd['search_user']:
                argd['results_field'] = 'user'
            elif argd['search_group']:
                argd['results_field'] = 'group'
            add_values = 0
            if argd['add_group'] or argd['add_user']:
                add_values = 1
            (body, errors, warnings) = perform_request_write_with_search(argd['msg_to_user'],
                                                                         argd['msg_to_group'],
                                                                         argd['msg_subject'],
                                                                         argd['msg_body'],
                                                                         argd['msg_send_year'],
                                                                         argd['msg_send_month'],
                                                                         argd['msg_send_day'],
                                                                         argd['names_selected'],
                                                                         argd['search_pattern'],
                                                                         argd['results_field'],
                                                                         add_values,
                                                                         ln=argd['ln'])
        return page(title       = title,
                    body        = body,
                    navtrail    = navtrail,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = argd['ln'],
                    errors      = errors,
                    warnings    = warnings)

    def delete(self, req, form):
        """
        Suppress a message
        @param msgid: id of message
        @param ln: language
        @return page
        """

        argd = wash_urlargd(form, {'msgid': (int, -1),
                                   })

        # Check if user is logged
        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1 or isGuestUser(uid): 
            return page_not_authorized(req, "%s/yourmessages/delete_msg" % (weburl,))

        _ = gettext_set_language(argd['ln'])

        # Generate content
        (body, errors, warnings) = perform_request_delete_msg(uid, argd['msgid'], argd['ln'])
        return page(title       = _("Your Messages"),
                    body        = body,
                    navtrail    = get_navtrail(argd['ln']),
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = argd['ln'],
                    errors      = errors,
                    warnings    = warnings)

    def delete_all(self, req, form):        
        """
        Empty user's inbox
        @param confimed: 1 if message is confirmed
        @param ln: language
        \return page
        """
        
        argd = wash_urlargd(form, {'confirmed': (int, 0),
                                   })

        # Check if user is logged
        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1 or isGuestUser(uid): 
            return page_not_authorized(req, "%s/yourmessages/delete_all" % (weburl,))

        _ = gettext_set_language(argd['ln'])

        # Generate content
        (body, errors, warnings) = perform_request_delete_all(uid, argd['confirmed'], argd['ln'])
        return page(title       = _("Your Messages"),
                    body        = body,
                    navtrail    = get_navtrail(argd['ln']),
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = argd['ln'],
                    errors      = errors,
                    warnings    = warnings)

    def display_msg(self, req, form):
        """
        Display a message
        @param msgid: id of message
        @param ln: languae
        @return page
        """

        argd = wash_urlargd(form, {'msgid': (int, -1),
                                   })

        # Check if user is logged
        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1 or isGuestUser(uid): 
            return page_not_authorized(req, "%s/yourmessages/display_msg" % (weburl,))

        _ = gettext_set_language(argd['ln'])
        # Generate content
        (body, errors, warnings) = perform_request_display_msg(uid, argd['msgid'], argd['ln'])
        title = _("Read a message")
        return page(title       = title,
                    body        = body,
                    navtrail    = get_navtrail(argd['ln'], title),
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = argd['ln'],
                    errors      = errors,
                    warnings    = warnings)

