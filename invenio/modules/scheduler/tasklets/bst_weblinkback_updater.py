# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2013 CERN.
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

from invenio.legacy.bibsched.bibtask import write_message
from invenio.legacy.weblinkback.config import CFG_WEBLINKBACK_TYPE
from invenio.legacy.weblinkback.api import update_linkbacks, \
                                delete_linkbacks_on_blacklist, \
                                send_pending_linkbacks_notification


def bst_weblinkback_updater(mode):
    """
    Update linkbacks
    @param mode: 1 delete rejected, broken and pending linkbacks whose URLs is on blacklist
                 2 update page titles of new linkbacks
                 3 update page titles of old linkbacks
                 4 update manually set page titles
                 5 detect and disable broken linkbacks
                 6 send notification email for all pending linkbacks
    @type mode: int
    """
    mode = int(mode)
    if mode == 1:
        write_message("Starting to delete rejected and pending linkbacks URLs on blacklist")
        delete_linkbacks_on_blacklist()
        write_message("Completed to delete rejected and pending linkbacks URLs on blacklist")
    elif mode == 2:
        write_message("Starting to update the page titles of new linkbacks")
        update_linkbacks(1)
        write_message("Completed to update the page titles of new linkbacks")
    elif mode == 3:
        write_message("Starting to update the page titles of old linkbacks")
        update_linkbacks(2)
        write_message("Completed to update the page titles of old linkbacks")
    elif mode == 4:
        write_message("Starting to update manually set page titles")
        update_linkbacks(3)
        write_message("Completed to update manually set page titles")
    elif mode == 5:
        write_message("Starting to detect and disable broken linkbacks")
        update_linkbacks(4)
        write_message("Completed to detect and disable broken linkbacks")
    elif mode == 6:
        write_message("Starting to send notification email")
        send_pending_linkbacks_notification(CFG_WEBLINKBACK_TYPE['TRACKBACK'])
        write_message("Completed to send notification email")
