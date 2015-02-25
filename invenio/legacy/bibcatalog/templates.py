# This file is part of Invenio.
# Copyright (C) 2009, 2010, 2011, 2014 CERN.
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

"""Invenio BibCatalog HTML generator."""

from invenio.legacy.bibcatalog.api import BIBCATALOG_SYSTEM
from invenio.base.i18n import wash_language, gettext_set_language
from invenio.config import CFG_SITE_LANG
from invenio.legacy.webstyle.templates import Template as DefaultTemplate

class Template(DefaultTemplate):
    """ HTML generators for BibCatalog """

    SHOW_MAX_TICKETS = 25

    def tmpl_your_tickets(self, uid, ln=CFG_SITE_LANG, start=1):
        """ make a pretty html body of tickets that belong to the user given as param """
        ln = wash_language(ln)
        _ = gettext_set_language(ln)
        if BIBCATALOG_SYSTEM is None:
            return _("Error: No BibCatalog system configured.")
        #errors? tell what happened and get out
        bibcat_probs = BIBCATALOG_SYSTEM.check_system(uid)
        if bibcat_probs:
            return _("Error")+" "+bibcat_probs

        tickets = BIBCATALOG_SYSTEM.ticket_search(uid, owner=uid) # get ticket id's
        lines = "" # put result here
        i = 1

        lines += (_("You have %(x_num)i tickets.", x_num=len(tickets))) + "<br/>"

        #make a prev link if needed
        if (start > 1):
            newstart = start - self.SHOW_MAX_TICKETS
            if (newstart < 1):
                newstart = 1
            lines += '<a href="/yourtickets/display?start='+str(newstart)+'">'+_("Previous")+'</a>'
        lines += """<table border="1">"""
        lastshown = len(tickets) # what was the number of the last shown ticket?
        for ticket in tickets:
            #get info and show only for those that within the show range
            if (i >= start) and (i < start+self.SHOW_MAX_TICKETS):
                ticket_info = BIBCATALOG_SYSTEM.ticket_get_info(uid, ticket)
                subject = ticket_info['subject']
                status = ticket_info['status']
                text = ""
                if 'text' in ticket_info:
                    text = ticket_info['text']
                display = '<a href="'+ticket_info['url_display']+'">'+_("show")+'</a>'
                close = '<a href="'+ticket_info['url_close']+'">'+_("close")+'</a>'
                lines += "<tr><td>"+str(ticket)+"</td><td>"+subject+" "+text+"</td><td>"+status+"</td><td>"+display+"</td><td>"+close+"</td></tr>\n"
                lastshown = i
            i = i+1
        lines += "</table>"

        #make next link if needed
        if (len(tickets) > lastshown):
            newstart = lastshown+1
            lines += '<a href="/yourtickets/display?start='+str(newstart)+'">'+_("Next")+'</a>'
        return lines


