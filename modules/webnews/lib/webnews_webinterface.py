## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""WebNews Web Interface."""

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

# INVENIO IMPORTS
from invenio.webinterface_handler import wash_urlargd, WebInterfaceDirectory
from invenio.config import CFG_ACCESS_CONTROL_LEVEL_SITE, \
                           CFG_SITE_LANG
from invenio.webuser import getUid, page_not_authorized

# MODULE IMPORTS
from invenio.webnews import perform_request_tooltips, \
                            perform_request_dismiss

class WebInterfaceWebNewsPages(WebInterfaceDirectory):
    """
    Defines the set of /news pages.
    """

    _exports = ["tooltips", "dismiss"]

    def tooltips(self, req, form):
        """
        Returns the news tooltips information in JSON.
        """

        argd = wash_urlargd(form, {'story_id'   : (int, 0),
                                   'tooltip_id' : (int, 0),
                                   'ln'         : (str, CFG_SITE_LANG)})

        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../news/tooltip",
                                       navmenuid = 'news')

        tooltips_json = perform_request_tooltips(req = req,
                                                 uid=uid,
                                                 story_id=argd['story_id'],
                                                 tooltip_id=argd['tooltip_id'],
                                                 ln=argd['ln'])

        return tooltips_json

    def dismiss(self, req, form):
        """
        Dismiss the given tooltip for the current user.
        """

        argd = wash_urlargd(form, {'story_id'                : (int, 0),
                                   'tooltip_notification_id' : (str, None)})

        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../news/dismiss",
                                       navmenuid = 'news')

        dismissed_p_json = perform_request_dismiss(req = req,
                                                   uid=uid,
                                                   story_id=argd['story_id'],
                                                   tooltip_notification_id=argd['tooltip_notification_id'])

        return dismissed_p_json
