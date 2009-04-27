# -*- coding: utf-8 -*-
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

"""
Provide a "ticket" interface with a request tracker.
See: https://twiki.cern.ch/twiki/bin/view/Inspire/SystemDesignBibCatalogue
This is a base class that cannot be instantiated.
"""

from invenio.webuser import get_user_preferences

class BibCatalogSystem:
    """ A template class for ticket support."""

    TICKET_ATTRIBUTES = ['ticketid', 'priority', 'recordid', 'subject', 'text', 'creator', 'owner', 'date', 'status', 'queue', 'url_display', 'url_close']

    def check_system(self, uid):
        """check connectivity. Return a string describing the error or an empty str
           @param uid invenio user id.
        """
        return "this class cannot be instantiated"

    def ticket_search(self, uid, recordid=-1, subject="", text="", creator="", owner="", \
                      date_from="", date_until="", status="", priority=""):
        """search for tickets based on various criteria. Return an array of ticket numbers
           @param uid invenio user id.
           @param recordid search criteria: ticket contains this record id.
           @param subject search criteria: ticket has this subject (substr).
           @param text search criteria: ticket has this text in body (substr).
           @param creator search criteria: ticket creator's id.
           @param owner search criteria: ticket owner's id.
           @param date_from search criteria: ticket created starting from this date. Example: '2009-01-24'
           @param date_until search criteria: ticket created until from this date. Example: '2009-01-24'
           @param status search criteria: ticket has this status. Example: 'resolved'.
           @param priority search criteria: ticket priority number.
        """
        pass

    def ticket_submit(self, uid, subject, recordid, text="", queue="", priority="", owner=""):
        """submit a ticket. Return 1 on success
           @param uid invenio user id.
           @param subject set this as the ticket's subject.
           @param recordid ticket concerns this record.
           @param text ticket body.
           @param queue the queue for this ticket (if supported).
           @param priority ticket priority.
           @param owner set ticket owner to this uid.
        """
        pass

    def ticket_assign(self, uid, ticketid, to_user):
        """assign a ticket to a user. Return 1 on success
           @param uid invenio user id.
           @param tickeid ticket id.
           @param to_user assign ticket to this user.
        """
        pass

    def ticket_set_attribute(self, uid, ticketid, attribute, new_value):
        """set an attribute of a ticket. Return 1 on success
           @param uid invenio user id.
           @param tickeid ticket id.
           @param attribute. This is a member of TICKET_ATTRIBUTES.
           @param new_value new value for this attribute.
        """
        pass

    def ticket_get_attribute(self, uid, ticketid, attrname):
        """return an attribute
           @param uid invenio user id.
           @param tickeid ticket id.
           @param attrname attribute name.
        """
        pass

    def ticket_get_info(self, uid, ticketid, attrlist):
        """Return the attributes of a ticket as a dictionary whose fields are TICKET_ATTRIBUTES.
           @param uid user id.
           @param tickeid ticket id.
           @param attrlist a list of attributes, each in TICKET_ATTRIBUTES.
        """
        pass

def get_bibcat_from_prefs(uid):
    """gets username and pw from user prefs as a tuple.
       if not successfull, returns None
       @param uid user id.
    """
    user_pref = get_user_preferences(uid)
    if not user_pref.has_key('bibcatalog_username'):
        return (None, None)
    if not user_pref.has_key('bibcatalog_password'):
        return (None, None)
    return (user_pref['bibcatalog_username'], user_pref['bibcatalog_password'])






