#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
WebJournal Element - return trackback auto discovery tag
"""
import cgi
from invenio.legacy.webjournal.utils import parse_url_string
from invenio.legacy.weblinkback.templates import get_trackback_auto_discovery_tag
from invenio.config import CFG_WEBLINKBACK_TRACKBACK_ENABLED

def format_element(bfo):
    """
    Return trackback auto discovery tag if recid != -1, will return "" for recid == -1 like index pages
    """
    html = ""
    if CFG_WEBLINKBACK_TRACKBACK_ENABLED:
        # Retrieve context (journal, issue and category) from URI
        args = parse_url_string(bfo.user_info['uri'])
        recid = args["recid"]

        if recid != -1:
            html = get_trackback_auto_discovery_tag(recid)

    return html


def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
