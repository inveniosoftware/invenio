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
WebJournal Element - Display admin links
"""
from invenio.config import \
     CFG_SITE_URL, \
     CFG_SITE_NAME, \
     CFG_SITE_NAME_INTL, \
     CFG_SITE_RECORD
from invenio.modules.access.engine import acc_authorize_action
from invenio.legacy.webjournal.utils import \
     parse_url_string, \
     get_journal_submission_params

def format_element(bfo):
    """
    Display administration links for this articles when user is an
    editor of the journal
    """
    out = ''
    stats_admin_link = ''
    if bfo.user_info['uri'].startswith('/journal'):
        # Print editing links
        args = parse_url_string(bfo.user_info['uri'])
        journal_name = args["journal_name"]
        editor = False
        if acc_authorize_action(bfo.user_info['uid'], 'cfgwebjournal',
                                name="%s" % journal_name)[0] == 0:
            editor = True
        issue_number = args["issue"]

        if editor:
            recid = bfo.control_field('001')
            (doctype, identifier_element, identifier_field) = \
                      get_journal_submission_params(journal_name)
            if identifier_field.startswith('00'):
                identifier = bfo.control_field(identifier_field)
            else:
                identifier = bfo.field(identifier_field)

            (auth_code, auth_msg) = acc_authorize_action(bfo.user_info, 'runwebstatadmin')
            if not auth_code:
                # User will be allowed to see stats
                stats_admin_link = '''
                <p>
                    <a href="%(CFG_SITE_URL)s/stats/customevent?ids=journals&amp;cols0=articleid&col_value0=%(recid)s&amp;timespan=last+month"> &raquo; statistics</a>
                </p>
                ''' % {'CFG_SITE_URL': CFG_SITE_URL,
                       'recid': recid}

            out += '''
<div style="float:right;margin-left:5px;font-weight:700;">
  <p>
    <a href="%(CFG_SITE_URL)s/submit/direct?%(identifier_element)s=%(identifier)s&amp;sub=MBI%(doctype)s" target="_blank"> &raquo; edit article</a>
  </p>
  <p>
    <a href="%(CFG_SITE_URL)s/%(CFG_SITE_RECORD)s/%(recid)s" target="_blank"> &raquo; record in %(CFG_SITE_NAME_INTL)s</a>
  </p>
  <p>
    <a href="%(CFG_SITE_URL)s/admin/webjournal/webjournaladmin.py/regenerate?journal_name=%(journal_name)s&amp;issue=%(issue_number)s"> &raquo; publish changes</a>
  </p>
  %(stats_admin_link)s
</div>''' % {'CFG_SITE_URL': CFG_SITE_URL,
             'CFG_SITE_RECORD': CFG_SITE_RECORD,
             'identifier': identifier,
             'recid': recid,
             'journal_name': journal_name,
             'issue_number': issue_number,
             'doctype': doctype,
             'identifier_element': identifier_element,
             'CFG_SITE_NAME_INTL': CFG_SITE_NAME_INTL.get(bfo.lang,
                                                          CFG_SITE_NAME),
             'stats_admin_link': stats_admin_link}

    return out

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
