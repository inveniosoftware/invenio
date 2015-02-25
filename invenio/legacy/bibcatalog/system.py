# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2009, 2010, 2011, 2012, 2013, 2014 CERN.
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
Please see the help/hacking/bibcatalog-api page for details.
This is a base class that cannot be instantiated.
"""

from invenio.legacy.webuser import get_user_preferences

class BibCatalogSystem(object):
    """ A template class for ticket support."""

    TICKET_ATTRIBUTES = ['ticketid', 'priority', 'recordid', 'subject', 'text', 'creator', 'owner', 'date', 'status', 'queue', 'url_display', 'url_modify', 'url_close', 'created']

    def check_system(self, uid=None):
        """Check connectivity. Return a string describing the error or an empty str
           @param uid: invenio user id. optional
           @type uid: number
           @return: empty string on success. Otherwise a string describing error.
           @rtype: string
        """
        raise NotImplementedError("This class cannot be instantiated")

    def ticket_search(self, uid, recordid=-1, subject="", text="", creator="", owner="", \
                      date_from="", date_until="", status="", priority="", queue=""):
        """Search for tickets based on various criteria. Return an array of ticket numbers
           @param uid: invenio user id.
           @type uid: number
           @param recordid: search criteria - ticket contains this record id.
           @type recordid: number
           @param subject: search criteria - ticket has this subject (substr).
           @type subject: string
           @param text: search criteria - ticket has this text in body (substr).
           @type text: string
           @param creator: search criteria - ticket creator's id.
           @type creator: number
           @param owner: search criteria - ticket owner's id.
           @type owner: number
           @param date_from: search criteria - ticket created starting from this date. Example: '2009-01-24'
           @type date_until: date in yyyy-mm-dd format
           @param date_until: search criteria - ticket created until from this date. Example: '2009-01-24'
           @type date_from: date in yyyy-mm-dd format
           @param status: search criteria - ticket has this status. Example: 'resolved'.
           @type status: string
           @param priority: search criteria - ticket priority number.
           @type priority: number
           @param queue: search criteria - specific queue to search within
           @type queue: string
        """
        raise NotImplementedError("This class cannot be instantiated")

    def ticket_submit(self, uid=None, subject="", recordid=-1, text="", queue="", priority="", owner="",requestor=""):
        """submit a ticket. Return ticket_id on success, otherwise None
           @param uid: invenio user id. optional
           @type uid: number
           @param subject: set this as the ticket's subject.
           @type subject: string
           @param recordid: ticket concerns this record.
           @type recordid: number
           @param text: ticket body.
           @type text: string
           @param queue: the queue for this ticket (if supported).
           @type queue: string
           @param priority: ticket priority.
           @type priority: number
           @param owner: set ticket owner to this uid.
           @type owner: number
           @param requestor: set ticket requestor to this email.
           @type requestor: string
           @return: new ticket_id or None
        """
        raise NotImplementedError("This class cannot be instantiated")

    def ticket_assign(self, uid, ticketid, to_user):
        """assign a ticket to a user. Return 1 on success
           @param uid: invenio user id
           @type uid: number
           @param ticketid: ticket id
           @type ticketid: number
           @param to_user: assign ticket to this user
           @type to_user: number
           @return: 1 on success, 0 otherwise
           @rtype: number
        """
        raise NotImplementedError("This class cannot be instantiated")

    def ticket_steal(self, uid, ticketid):
        """Steal a ticket from a user.
           @param uid: invenio user id
           @type uid: number
           @param ticketid: ticket id
           @type ticketid: number
           @return: 1 on success, 0 otherwise
           @rtype: number
        """
        raise NotImplementedError("This class cannot be instantiated")

    def ticket_set_attribute(self, uid, ticketid, attribute, new_value):
        """set an attribute of a ticket. Return 1 on success
           @param uid: invenio user id
           @type uid: number
           @param ticketid: ticket id
           @type ticketid: number
           @param attribute: This is a member of TICKET_ATTRIBUTES.
           @type attribute: string
           @param new_value: new value for this attribute.
           @type new_value: string
           @return: 1 on success, 0 otherwise
           @rtype: number
        """
        raise NotImplementedError("This class cannot be instantiated")

    def ticket_get_attribute(self, uid, ticketid, attribute):
        """return an attribute
           @param uid: invenio user id
           @type uid: number
           @param ticketid: ticket id
           @type ticketid: number
           @param attribute: attribute name.
           @type attribute: string
           @return: the value of the attribute, or None if the ticket or attribute does not exist
           @rtype: string
        """
        raise NotImplementedError("This class cannot be instantiated")

    def ticket_get_info(self, uid, ticketid, attributes = None):
        """Return the attributes of a ticket as a dictionary whose fields are TICKET_ATTRIBUTES.
           @param uid: user id
           @type uid: number
           @param ticketid: ticket id
           @type ticketid: number
           @param attributes: a list of attributes, each in TICKET_ATTRIBUTES.
           @type attributes: list
           @return: dictionary whose fields are TICKET_ATTRIBUTES
           @rtype: dictionary
        """
        raise NotImplementedError("This class cannot be instantiated")

    def get_queues(self, uid):
        """Return a list of all available queues
           @param uid: user id
           @type uid: number
           @return: list whose every element is a dictionary representing a queue
           e.g {'id': '35', 'name': 'Admins'}
           @rtype: list
        """
        raise NotImplementedError("This class cannot be instantiated")

    def ticket_comment(self, uid, ticketid, comment):
        """Submit a comment to specified ticket. Accepts multi-line text.
           @param uid: user id
           @type uid: number
           @param ticketid: ticket id
           @type ticketid: number
           @param comment: the comment to send.
           @type comment: string
           @return: 1 on success, otherwise 0
           @rtype: int
        """
        raise NotImplementedError("This class cannot be instantiated")


def get_bibcat_from_prefs(uid):
    """gets username and pw from user prefs as a tuple.
       if not successfull, returns None
       @param uid: user id
       @type uid: number
       @return: ('bibcatalog_username', 'bibcatalog_password')
       @rtype: tuple
    """
    user_pref = get_user_preferences(uid)
    if 'bibcatalog_username' not in user_pref:
        return (None, None)
    if 'bibcatalog_password' not in user_pref:
        return (None, None)
    return (user_pref['bibcatalog_username'], user_pref['bibcatalog_password'])

