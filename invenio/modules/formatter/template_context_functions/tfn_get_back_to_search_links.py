# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013 CERN.
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

from flask import session
from invenio.base.globals import cfg
from invenio.ext.template import render_template_to_string

"""
Template context function - Display links (previous, next, back-to-search)
to navigate through the records.
"""


def template_context_function(recID):
    """
    Displays next-hit/previous-hit/back-to-search links
    on the detailed record pages in order to be able to quickly
    flip between detailed record pages
    :param recID: detailed record ID
    :type recID: string
    :return: html output
    """
    if recID is None:
        return ""
    # this variable is set to zero so nothing is displayed
    if not cfg['CFG_WEBSEARCH_PREV_NEXT_HIT_LIMIT']:
        return ""

    # search for a specific record having not done
    # any search before
    try:
        last_query = session['websearch-last-query']
        recids = session["websearch-last-query-hits"]
    except:
        return ""

    if recids:
        return render_template_to_string('records/back_to_search_links.html',
                                         recID=int(recID),
                                         last_query=cfg['CFG_SITE_URL'] + last_query,
                                         recids=recids)
    else:
        # did not rich the limit CFG_WEBSEARCH_PREV_NEXT_HIT_LIMIT,
        # so nothing is displayed
        return ""

