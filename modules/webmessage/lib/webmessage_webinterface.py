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

"""WebMessage web interface"""

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

from invenio.config import CFG_SITE_SECURE_URL, weburl, CFG_ACCESS_CONTROL_LEVEL_SITE
from invenio.webuser import getUid, isGuestUser, page_not_authorized
from invenio.webmessage import perform_request_display, \
                               perform_request_display_msg, \
                               perform_request_write, \
                               perform_request_send, \
                               perform_request_write_with_search, \
                               perform_request_delete_msg, \
                               perform_request_delete_all, \
                               get_navtrail
from invenio.webmessage_config import CFG_WEBMESSAGE_RESULTS_FIELD
from invenio.webmessage_mailutils import escape_email_quoted_text
from invenio.webpage import page
from invenio.messages import gettext_set_language
from invenio.urlutils import redirect_to_url, make_canonical_urlargd
from invenio.htmlutils import escape_html
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
        if CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "%s/yourmessages/display" % \
                                             (weburl,),
                                       navmenuid="yourmessages")
        elif uid == -1 or isGuestUser(uid):
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                CFG_SITE_SECURE_URL,
                make_canonical_urlargd({
                    'referer' : "%s/yourmessages/display%s" % (
                        weburl,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

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
                    warnings    = warnings,
                    navmenuid   = "yourmessages")

    def write(self, req, form):
        """ write(): interface for message composing
        @param msg_reply_id: if this message is a reply to another, id of the
                             other
        @param msg_to: if this message is not a reply, nickname of the user it
                       must be delivered to.
        @param msg_to_group: name of group to send message to
        @param ln: language
        @return the compose page
        """
        argd = wash_urlargd(form, {'msg_reply_id': (int, 0),
                                   'msg_to': (str, ""),
                                   'msg_to_group': (str, "")})

        # Check if user is logged
        uid = getUid(req)

        _ = gettext_set_language(argd['ln'])

        if CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "%s/yourmessages/write" % \
                                             (weburl,),
                                       navmenuid="yourmessages")
        elif uid == -1 or isGuestUser(uid):
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                CFG_SITE_SECURE_URL,
                make_canonical_urlargd({
                    'referer' : "%s/yourmessages/write%s" % (
                        weburl,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))


        # Request the composing page
        (body, errors, warnings) = perform_request_write(
                                        uid=uid,
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
                    warnings    = warnings,
                    navmenuid   = "yourmessages")

    def send(self, req, form):
        """
        Sends the message
        @param msg_to_user: comma separated usernames (str)
        @param msg_to_group: comma separated groupnames (str)
        @param msg_subject: message subject (str)
        @param msg_body: message body (string)
        @param msg_send_year: year to send this message on (int)
        @param_msg_send_month: month to send this message on (int)
        @param_msg_send_day: day to send this message on (int)
        @param results_field: value determining which results field to display.
                              See CFG_WEBMESSAGE_RESULTS_FIELD in
                              webmessage_config.py
        @param names_to_add: list of usernames ['str'] to add to
                             msg_to_user / group
        @param search_pattern: will search for users/groups with this pattern
        @param add_values: if 1 users_to_add will be added to msg_to_user
                           field..
        @param *button: which button was pressed
        @param ln: language
        @return a (body, errors, warnings) formed tuple.
        """
        argd = wash_urlargd(form, {'msg_to_user': (str, ""),
                                   'msg_to_group': (str, ""),
                                   'msg_subject': (str, ""),
                                   'msg_body': (str, ""),
                                   'msg_send_year': (int, 0),
                                   'msg_send_month': (int, 0),
                                   'msg_send_day': (int, 0),
                                   'results_field': (str,
                                        CFG_WEBMESSAGE_RESULTS_FIELD['NONE']),
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
        _ = gettext_set_language(argd['ln'])
        if CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "%s/yourmessages/send" % \
                                             (weburl,),
                                       navmenuid="yourmessages")
        elif uid == -1 or isGuestUser(uid):
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                CFG_SITE_SECURE_URL,
                make_canonical_urlargd({
                    'referer' : "%s/yourmessages/send%s" % (
                        weburl,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        if argd['send_button']:
            (body, errors, warnings, title, navtrail) = perform_request_send(
                            uid=uid,
                            msg_to_user=argd['msg_to_user'],
                            msg_to_group=argd['msg_to_group'],
                            msg_subject=escape_html(argd['msg_subject']),
                            msg_body=escape_email_quoted_text(argd['msg_body']),
                            msg_send_year=argd['msg_send_year'],
                            msg_send_month=argd['msg_send_month'],
                            msg_send_day=argd['msg_send_day'],
                            ln=argd['ln'])
        else:
            title = _('Write a message')
            navtrail = get_navtrail(argd['ln'], title)
            if argd['search_user']:
                argd['results_field'] = CFG_WEBMESSAGE_RESULTS_FIELD['USER']
            elif argd['search_group']:
                argd['results_field'] = CFG_WEBMESSAGE_RESULTS_FIELD['GROUP']
            add_values = 0
            if argd['add_group'] or argd['add_user']:
                add_values = 1
            (body, errors, warnings) = perform_request_write_with_search(
                            uid=uid,
                            msg_to_user=argd['msg_to_user'],
                            msg_to_group=argd['msg_to_group'],
                            msg_subject=escape_html(argd['msg_subject']),
                            msg_body=escape_email_quoted_text(argd['msg_body']),
                            msg_send_year=argd['msg_send_year'],
                            msg_send_month=argd['msg_send_month'],
                            msg_send_day=argd['msg_send_day'],
                            names_selected=argd['names_selected'],
                            search_pattern=argd['search_pattern'],
                            results_field=argd['results_field'],
                            add_values=add_values,
                            ln=argd['ln'])
        return page(title       = title,
                    body        = body,
                    navtrail    = navtrail,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = argd['ln'],
                    errors      = errors,
                    warnings    = warnings,
                    navmenuid   = "yourmessages")

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
        if CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "%s/yourmessages/delete" % \
                                             (weburl,),
                                       navmenuid="yourmessages")
        elif uid == -1 or isGuestUser(uid):
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                CFG_SITE_SECURE_URL,
                make_canonical_urlargd({
                    'referer' : "%s/yourmessages/delete%s" % (
                        weburl,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        _ = gettext_set_language(argd['ln'])

        # Generate content
        (body, errors, warnings) = perform_request_delete_msg(uid,
                                                              argd['msgid'],
                                                              argd['ln'])
        return page(title       = _("Your Messages"),
                    body        = body,
                    navtrail    = get_navtrail(argd['ln']),
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = argd['ln'],
                    errors      = errors,
                    warnings    = warnings,
                    navmenuid   = "yourmessages")

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
        if CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "%s/yourmessages/delete_all" % \
                                             (weburl,),
                                       navmenuid="yourmessages")
        elif uid == -1 or isGuestUser(uid):
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                CFG_SITE_SECURE_URL,
                make_canonical_urlargd({
                    'referer' : "%s/yourmessages/delete_all%s" % (
                        weburl,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        _ = gettext_set_language(argd['ln'])

        # Generate content
        (body, errors, warnings) = perform_request_delete_all(uid,
                                                              argd['confirmed'],
                                                              argd['ln'])
        return page(title       = _("Your Messages"),
                    body        = body,
                    navtrail    = get_navtrail(argd['ln']),
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = argd['ln'],
                    errors      = errors,
                    warnings    = warnings,
                    navmenuid   = "yourmessages")

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
        if CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "%s/yourmessages/display_msg" % \
                                             (weburl,),
                                       navmenuid="yourmessages")
        elif uid == -1 or isGuestUser(uid):
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                CFG_SITE_SECURE_URL,
                make_canonical_urlargd({
                    'referer' : "%s/yourmessages/display_msg%s" % (
                        weburl,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        _ = gettext_set_language(argd['ln'])
        # Generate content
        (body, errors, warnings) = perform_request_display_msg(uid,
                                                               argd['msgid'],
                                                               argd['ln'])
        title = _("Read a message")
        return page(title       = title,
                    body        = body,
                    navtrail    = get_navtrail(argd['ln'], title),
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = argd['ln'],
                    errors      = errors,
                    warnings    = warnings,
                    navmenuid   = "yourmessages")

