# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2009, 2010, 2011 CERN.
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
This is a dummy class that does not nothing. This is used when
not ticketing system is set.
"""
# pylint: disable=W0613
# pylint: disable=R0201

class BibCatalogSystemDummy(object):
    """ A dummy class for ticket support."""

    def check_system(self, uid=None):
        return ""

    def ticket_search(self, uid, recordid=-1, subject="", text="", creator="",
                      owner="", date_from="", date_until="", status="",
                      priority="", queue=""):
        return []

    def ticket_submit(self, uid=None, subject="", recordid=-1, text="",
                      queue="", priority="", owner="", requestor=""):
        pass

    def ticket_assign(self, uid, ticketid, to_user):
        pass

    def ticket_steal(self, uid, ticketid):
        pass

    def ticket_set_attribute(self, uid, ticketid, attribute, new_value):
        pass

    def ticket_get_attribute(self, uid, ticketid, attribute):
        pass

    def ticket_get_info(self, uid, ticketid, attributes = None):
        pass

    def get_queues(self, uid):
        pass

    def ticket_comment(self, uid, ticketid, comment):
        pass

# pylint: enable=W0613
