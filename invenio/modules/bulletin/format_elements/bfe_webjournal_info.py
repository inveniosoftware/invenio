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
WebJournal element - prints journal info
"""

from invenio.legacy.webjournal.utils import \
     parse_url_string, \
     make_journal_url, \
     get_current_issue, \
     get_journal_css_url, \
     get_journal_name_intl

def format_element(bfo, var=''):
    """
    Print several journal specific variables.
    @param var: the name of the desired variable. Can be one of: WEBJOURNAL_CSS_URL, WEBJOURNAL_NAME, WEBJOURNAL_NAME_INTL, WEBJOURNAL_CURRENT_ISSUE_NUMBER, WEBJOURNAL_ISSUE_NUMBER, WEBJOURNAL_URL
    """
    args = parse_url_string(bfo.user_info['uri'])
    journal_name = args["journal_name"]
    this_issue_number = args["issue"]

    if var == '':
        out =  ''
    elif var == 'WEBJOURNAL_NAME':
        out = journal_name
    elif var == 'WEBJOURNAL_NAME_INTL':
        out = get_journal_name_intl(journal_name, bfo.lang)
    elif var == 'WEBJOURNAL_ISSUE_NUMBER':
        out = this_issue_number
    elif var == 'WEBJOURNAL_CURRENT_ISSUE_NUMBER':
        out = get_current_issue(bfo.lang, journal_name)
    elif var == 'WEBJOURNAL_URL':
        out = make_journal_url(bfo.user_info['uri'], {'ln': bfo.lang})
    elif var == 'WEBJOURNAL_CSS_URL':
        out = get_journal_css_url(journal_name)
    elif var == 'WEBJOURNAL_USER_LANG':
        out = bfo.lang

    return out

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
