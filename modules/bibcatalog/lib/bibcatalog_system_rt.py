# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2009, 2010, 2011, 2012, 2013, 2014, 2015 CERN.
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
Provide a "ticket" interface with a request tracker.
This is a subclass of BibCatalogSystem
"""

import os
import re
import rt
from rt import AuthorizationError, UnexpectedResponse, requests, \
    ConnectionError, NotAllowed, APISyntaxError, BadRequest
import invenio.webuser
from invenio.shellutils import run_shell_command, escape_shell_arg
from invenio.bibcatalog_system import BibCatalogSystem, get_bibcat_from_prefs

from invenio.config import CFG_BIBCATALOG_SYSTEM, \
    CFG_BIBCATALOG_SYSTEM_RT_URL, \
    CFG_BIBCATALOG_SYSTEM_RT_DEFAULT_USER, \
    CFG_BIBCATALOG_SYSTEM_RT_DEFAULT_PWD, \
    CFG_BIBEDIT_ADD_TICKET_RT_QUEUES

class PatchedRt(rt.Rt):
    """
    This differ in the get_attachments method which allows for spotting
    attachement after the third line.
    """

    def get_attachments(self, ticket_id):
        """ Get attachment list for a given ticket

        :param ticket_id: ID of ticket
        :returns: List of tuples for attachments belonging to given ticket.
                  Tuple format: (id, name, content_type, size)
                  Returns None if ticket does not exist.
        """
        msg = self.__request('ticket/%s/attachments' % (str(ticket_id),))
        lines = msg.split('\n')
        if (len(lines) > 2) and self.RE_PATTERNS['does_not_exist_pattern'].match(lines[2]):
            return None
        attachment_infos = []
        if (self.__get_status_code(lines[0]) == 200) and (len(lines) >= 3):
            for line in lines[3:]:
                info = self.RE_PATTERNS['attachments_list_pattern'].match(line)
                if info:
                    attachment_infos.append(info.groups())
        return attachment_infos

    def __get_status_code(self, msg):
        """ Select status code given message.

        :keyword msg: Result message
        :returns: Status code
        :rtype: int
        """
        try:
            return int(msg.split('\n')[0].split(' ')[1])
        except:
            return None

    def __request(self, selector, get_params={}, post_data={}, files=[], without_login=False,
                  text_response=True):
        """ General request for :term:`API`.

        :keyword selector: End part of URL which completes self.url parameter
                           set during class inicialization.
                           E.g.: ``ticket/123456/show``
        :keyword post_data: Dictionary with POST method fields
        :keyword files: List of pairs (filename, file-like object) describing
                        files to attach as multipart/form-data
                        (list is necessary to keep files ordered)
        :keyword without_login: Turns off checking last login result
                                (usually needed just for login itself)
        :keyword text_response: If set to false the received message will be
                                returned without decoding (useful for attachments)
        :returns: Requested messsage including state line in form
                  ``RT/3.8.7 200 Ok\\n``
        :rtype: string or bytes if text_response is False
        :raises AuthorizationError: In case that request is called without previous
                                    login or login attempt failed.
        :raises ConnectionError: In case of connection error.
        """
        try:
            if (not self.login_result) and (not without_login):
                raise AuthorizationError('First login by calling method `login`.')
            url = str(os.path.join(self.url, selector))
            if not files:
                if post_data:
                    response = self.session.post(url, data=post_data)
                else:
                    response = self.session.get(url, params=get_params)
            else:
                files_data = {}
                for i, file_pair in enumerate(files):
                    files_data['attachment_%d' % (i+1)] = file_pair
                response = self.session.post(url, data=post_data, files=files_data)
            if response.status_code == 401:
                raise AuthorizationError('Server could not verify that you are authorized to access the requested document.')
            if response.status_code != 200:
                raise UnexpectedResponse('Received status code %d instead of 200.' % response.status_code)
            try:
                if response.encoding:
                    result = response.content.decode(response.encoding.lower())
                else:
                    # try utf-8 if encoding is not filled
                    result = response.content.decode('utf-8')
            except LookupError:
                raise UnexpectedResponse('Unknown response encoding: %s.' % response.encoding)
            except UnicodeError:
                if text_response:
                    raise UnexpectedResponse('Unknown response encoding (UTF-8 does not work).')
                else:
                    # replace errors - we need decoded content just to check for error codes in __check_response
                    result = response.content.decode('utf-8', 'replace')
            self.__check_response(result)
            if not text_response:
                return response.content
            return result
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError("Connection error", e)

    def steal_ticket(self, ticket_id, Owner):
        """ Edit ticket values.

        :param ticket_id: ID of ticket to edit
        :param Owner: the new owner
        :returns: ``True``
                      Operation was successful
                  ``False``
                      Ticket with given ID does not exist or unknown parameter
                      was set (in this case all other valid fields are changed)
        """
        post_data = 'Owner: %s\n' % Owner
        msg = self.__request('ticket/%s/steal' % (str(ticket_id)), post_data={'content':post_data})
        state = msg.split('\n')
        return len(state) <= 2 or self.RE_PATTERNS['update_pattern'].match(state[2]) is not None

    def edit_ticket(self, ticket_id, **kwargs):
        """ Edit ticket values.

        :param ticket_id: ID of ticket to edit
        :keyword kwargs: Other arguments possible to set:

                         Requestors, Subject, Cc, AdminCc, Owner, Status,
                         Priority, InitialPriority, FinalPriority,
                         TimeEstimated, Starts, Due, Text,... (according to RT
                         fields)

                         Custom fields CF.{<CustomFieldName>} could be set
                         with keywords CF_CustomFieldName.
        :returns: ``True``
                      Operation was successful
                  ``False``
                      Ticket with given ID does not exist or unknown parameter
                      was set (in this case all other valid fields are changed)
        """
        post_data = ''
        for key, value in kwargs.iteritems():
            if isinstance(value, (list, tuple)):
                value = ", ".join(value)
            if key[:3] != 'CF_':
                post_data += "%s: %s\n"%(key, value)
            else:
                post_data += "CF.{%s}: %s\n" % (key[3:], value)
        msg = self.__request('ticket/%s/edit' % (str(ticket_id)), post_data={'content':post_data})
        state = msg.split('\n')
        return len(state) <= 2 or self.RE_PATTERNS['update_pattern'].match(state[2]) is not None

    def __check_response(self, msg):
        """ Search general errors in server response and raise exceptions when found.

        :keyword msg: Result message
        :raises NotAllowed: Exception raised when operation was called with
                            insufficient privileges
        :raises AuthorizationError: Credentials are invalid or missing
        :raises APISyntaxError: Syntax error
        """
        if not isinstance(msg, list):
            msg = msg.split("\n")
        if (len(msg) > 2) and self.RE_PATTERNS['not_allowed_pattern'].match(msg[2]):
            raise NotAllowed(msg[2][2:])
        if self.RE_PATTERNS['credentials_required_pattern'].match(msg[0]):
            raise AuthorizationError('Credentials required.')
        if self.RE_PATTERNS['syntax_error_pattern'].match(msg[0]):
            raise APISyntaxError(msg[2][2:] if len(msg) > 2 else 'Syntax error.')
        if self.RE_PATTERNS['bad_request_pattern'].match(msg[0]):
            raise BadRequest(msg[2][2:] if len(msg) > 2 else 'Bad request.')

class BibCatalogSystemRT(BibCatalogSystem):

    def _get_instance(self, uid=None):
        """
        Return a valid RT instance.
        """
        username, passwd = None, None
        if uid:
            username, passwd = get_bibcat_from_prefs(uid)
        if username is None or not uid:
            username = CFG_BIBCATALOG_SYSTEM_RT_DEFAULT_USER
            passwd = CFG_BIBCATALOG_SYSTEM_RT_DEFAULT_PWD
        if not username or not passwd:
            raise RuntimeError("No valid RT user login specified")
        tracker = PatchedRt(
            url=CFG_BIBCATALOG_SYSTEM_RT_URL + '/REST/1.0/',
            default_login=username,
            default_password=passwd,
        )
        tracker.login()
        return tracker

    def check_system(self, uid=None):
        """return an error string if there are problems"""
        if not CFG_BIBCATALOG_SYSTEM == 'RT':
            return "CFG_BIBCATALOG_SYSTEM is not RT though this is an RT module"

        if not CFG_BIBCATALOG_SYSTEM_RT_URL:
            return "CFG_BIBCATALOG_SYSTEM_RT_URL not defined or empty"
        # Construct URL, split RT_URL at //
        if not CFG_BIBCATALOG_SYSTEM_RT_URL.startswith('http://') and \
           not CFG_BIBCATALOG_SYSTEM_RT_URL.startswith('https://'):
            return "CFG_BIBCATALOG__SYSTEM_RT_URL does not start with 'http://' or 'https://'"

        try:
            self._get_instance(uid)
        except Exception as err:
            return "could not connect to %s: %s" % (CFG_BIBCATALOG_SYSTEM_RT_URL, err)
        return ""

    def ticket_search(self, uid, recordid=-1, subject="", text="", creator="",
                      owner="", date_from="", date_until="", status="",
                      priority="", queue=""):
        """returns a list of ticket ID's related to this record or by
           matching the subject, creator or owner of the ticket."""

        # the search expression will be made by and'ing these
        search_atoms = {}
        if recordid > -1:
            # search by recid
            search_atoms['CF_RecordID'] = str(recordid)
        if subject:
            # search by subject
            search_atoms['Subject__like'] = str(subject)
        if text:
            search_atoms['Content__like'] = str(text)
        if str(creator):
            # search for this person's bibcatalog_username in preferences
            creatorprefs = invenio.webuser.get_user_preferences(creator)
            creator = "Nobody can Have This Kind of Name"
            if "bibcatalog_username" in creatorprefs:
                creator = creatorprefs["bibcatalog_username"]
            search_atoms['Creator'] = str(creator)
        if str(owner):
            ownerprefs = invenio.webuser.get_user_preferences(owner)
            owner = "Nobody can Have This Kind of Name"
            if "bibcatalog_username" in ownerprefs:
                owner = ownerprefs["bibcatalog_username"]
            search_atoms['Owner'] = str(owner)
        if date_from:
            search_atoms['Created__gt'] = str(date_from)
        if date_until:
            search_atoms['Created__lt'] = str(date_until)
        if status:
            search_atoms['Status'] = str(status)
        if str(priority):
            # Try to convert to int
            intpri = -1
            try:
                intpri = int(priority)
            except ValueError:
                pass
            if intpri > -1:
                search_atoms['Priority'] = str(intpri)
        if queue:
            search_atoms['Queue'] = str(queue)
        else:
            search_atoms['Queue'] = rt.ALL_QUEUES
        tickets = []

        if not search_atoms:
            return tickets

        rt_instance = self._get_instance(uid)
        tickets = rt_instance.search(**search_atoms)
        return [int(ticket[u'id'].split('/')[1]) for ticket in tickets]

    def ticket_submit(self, uid=None, subject="", recordid=-1, text="",
                      queue="", priority="", owner="", requestor=""):
        atoms = {}
        if subject:
            atoms['Subject'] = str(subject)
        if recordid:
            atoms['CF_RecordID'] = str(recordid)
        if priority:
            atoms['Priority'] = str(priority)
        if queue:
            atoms['Queue'] = str(queue)
        if requestor:
            atoms['Requestor'] = str(requestor)
        if owner:
            # get the owner name from prefs
            ownerprefs = invenio.webuser.get_user_preferences(owner)
            if "bibcatalog_username" in ownerprefs:
                owner = ownerprefs["bibcatalog_username"]
                atoms['Owner'] = str(owner)
        if text:
            # From: http://requesttracker.wikia.com/wiki/REST
            # If you want to have a multiline Text, prefix every line with a blank.
            text = text.replace("\n", "\n ")

            atoms['Text'] = str(text)

        rt_instance = self._get_instance(uid)
        return rt_instance.create_ticket(**atoms)

    def ticket_comment(self, uid, ticketid, comment):
        """comment on a given ticket. Returns 1 on success, 0 on failure"""

        rt_instance = self._get_instance(uid)
        return rt_instance.comment(ticketid, comment)

    def ticket_assign(self, uid, ticketid, to_user):
        """assign a ticket to an RT user. Returns 1 on success, 0 on failure"""

        return self.ticket_set_attribute(uid, ticketid, "owner", to_user)

    def ticket_steal(self, uid, ticketid):
        """assign a ticket to uid"""
        rt_instance = self._get_instance(uid)
        ownerprefs = invenio.webuser.get_user_preferences(uid)
        if "bibcatalog_username" in ownerprefs:
            owner = ownerprefs["bibcatalog_username"]
            return rt_instance.steal_ticket(ticketid, Owner=owner)
        return False

    def ticket_set_attribute(self, uid, ticketid, attribute, new_value):
        """change the ticket's attribute. Returns 1 on success, 0 on failure"""
        # check that the attribute is accepted..
        if attribute not in BibCatalogSystem.TICKET_ATTRIBUTES:
            return 0
        # we cannot change read-only values.. including text that is an
        # attachment. pity
        if attribute in ['creator', 'date', 'ticketid', 'url_close', 'url_display', 'recordid', 'text']:
            return 0
        # check attribute
        atom = {}
        if attribute == 'priority':
            if not str(new_value).isdigit():
                return 0
            atom['Priority'] = str(new_value)

        if attribute == 'subject':
            atom['Subject'] = str(new_value)

        if attribute == 'owner':
            # convert from invenio to RT
            ownerprefs = invenio.webuser.get_user_preferences(new_value)
            if "bibcatalog_username" not in ownerprefs:
                return 0
            atom['Owner'] = str(ownerprefs['bibcatalog_username'])

        if attribute == 'status':
            atom['Status'] = str(new_value)

        if attribute == 'queue':
            atom['Queue'] = str(new_value)

        # make sure ticketid is numeric
        try:
            dummy = int(ticketid)
        except ValueError:
            return 0

        rt_instance = self._get_instance(uid)
        return rt_instance.edit_ticket(ticketid, **atom)

    def ticket_get_attribute(self, uid, ticketid, attribute):
        """return an attribute of a ticket"""
        ticinfo = self.ticket_get_info(uid, ticketid, [attribute])
        if attribute in ticinfo:
            return ticinfo[attribute]
        return None

    def ticket_get_info(self, uid, ticketid, attributes=None):
        """return ticket info as a dictionary of pre-defined attribute names.
           Or just those listed in attrlist.
           Returns None on failure"""
        # Make sure ticketid is numeric
        try:
            dummy = int(ticketid)
        except ValueError:
            return 0
        if attributes is None:
            attributes = []

        rt_instance = self._get_instance(uid)
        tdict = {}
        for key, value in rt_instance.get_ticket(ticketid).items():
            if isinstance(value, list):
                value = [elem.encode('utf8') for elem in value]
            else:
                value = value.encode('utf8')
            key = key.lower().encode('utf8')
            if key == 'cf.{recordid}':
                key = 'recordid'
            if key == 'id':
                tdict[key] = int(value.split('/')[1])
            tdict[key] = value

        attachments = rt_instance.get_attachments_ids(ticketid)

        text = [rt_instance.get_attachment_content(
            ticketid, attachment) for attachment in attachments]
        tdict['text'] = '\n'.join(text)

        tdict['url_display'] = CFG_BIBCATALOG_SYSTEM_RT_URL + \
            "/Ticket/Display.html?id=" + str(ticketid)
        tdict['url_close'] = CFG_BIBCATALOG_SYSTEM_RT_URL + \
            "/Ticket/Update.html?Action=Comment&DefaultStatus=resolved&id=" + \
            str(ticketid)
        tdict['url_modify'] = CFG_BIBCATALOG_SYSTEM_RT_URL + \
            "/Ticket/ModifyAll.html?id=" + str(ticketid)

        tdict['owner'] = invenio.webuser.get_uid_based_on_pref(
            "bibcatalog_username", tdict['owner'])
        if tdict['owner'] is None:
            tdict['owner'] = 'Nobody'
        return tdict

    def get_queues(self, uid):
        """get all the queues from RT. Returns a list of queues"""
        # get all queues with id from 1-100 in order to get all the available queues.
        # Then filters the queues keeping these selected in the configuration
        # variable
        queues = []

        rt_instance = self._get_instance(uid)
        for i in range(1, 100):
            queue = rt_instance.get_queue(i)
            if queue and queue[u'Disabled'] == u'0':
                # Simulating expected behaviour
                queues.append({'id': str(i), 'name': queue[u'Name'].encode('utf8')})
        return queues
