# -*- coding: utf-8 -*-
##
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

""" Database related functions for the WebNews module """

__revision__ = "$Id$"

# INVENIO IMPORTS
from invenio.dbquery import run_sql

# MODULE IMPORTS
from invenio.webnews_utils import convert_xpath_expression_to_jquery_selector
from invenio.webnews_config import CFG_WEBNEWS_TOOLTIPS_COOKIE_LONGEVITY

def get_latest_story_id():
    """
    Returns the id of the latest news story available.
    """

    query = """ SELECT      id
                FROM        nwsSTORY
                WHERE       created >= DATE_SUB(CURDATE(),INTERVAL %s DAY)
                ORDER BY    created DESC
                LIMIT       1"""

    params = (CFG_WEBNEWS_TOOLTIPS_COOKIE_LONGEVITY,)

    res = run_sql(query, params)

    if res:
        return res[0][0]

    return None

def get_story_tooltips(story_id):
    """
    Returns all the available tooltips for the given story ID.
    """

    query = """ SELECT      id,
                            body,
                            target_element,
                            target_page
                FROM        nwsTOOLTIP
                WHERE       id_story=%s"""

    params = (story_id,)

    res = run_sql(query, params)

    if res:
        return res
    return None

def update_tooltip(story_id,
                   tooltip_id,
                   tooltip_body,
                   tooltip_target_element,
                   tooltip_target_page,
                   is_tooltip_target_xpath = False):
    """
    Updates the tooltip information.
    XPath expressions are automatically translated to the equivalent jQuery
    selector if so chosen by the user.
    """

    query = """ UPDATE  nwsTOOLTIP
                SET     body=%s,
                        target_element=%s,
                        target_page=%s
                WHERE   id=%s
                    AND id_story=%s"""

    tooltip_target_element = is_tooltip_target_xpath and \
                             convert_xpath_expression_to_jquery_selector(tooltip_target_element) or \
                             tooltip_target_element

    params = (tooltip_body, tooltip_target_element, tooltip_target_page, tooltip_id, story_id)

    res = run_sql(query, params)

    return res

