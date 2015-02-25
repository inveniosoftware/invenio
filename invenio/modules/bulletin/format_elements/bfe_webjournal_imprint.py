# -*- coding: utf-8 -*-
# $Id: bfe_webjournal_CERNBulletinIssueNumber.py,v 1.10 2008/06/03 09:52:11 jerome Exp $
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
"""W
ebJournal Element - Prints issue number
"""
from invenio.legacy.webjournal.utils import \
     parse_url_string, \
     get_issue_number_display, \
     make_journal_url, \
     issue_to_datetime, \
     MONTHLY, WEEKLY, DAILY, \
     get_grouped_issues, \
     get_release_datetime
from invenio.legacy.webjournal.config import InvenioWebJournalJournalIdNotFoundDBError
from invenio.base.i18n import gettext_set_language
from invenio.utils.date import \
     get_i18n_month_name, \
     get_i18n_day_name

def format_element(bfo, display_date='yes', display_issue_number='yes',
           estimate_release_date='No', granularity='',
           group_issues_date='yes', display_month='long',
           display_week_day='long'):
    """
    Returns the string used for the issue number in the format:<br/>
    Issue No.<is1>-<is2>/<year> - <date>, <br/>
    e.g. Issue No.32-33/2007 – Tuesday 6 August 2007

    if <code>estimate_release_date</code> is set to <code>yes</code>,
    a 'theoretical' release date is shown instead of the release date:
    if issue if released on Friday, display next week date. Also if
    journal has not been released, display an approximative release
    date (based on history and config)

    @param display_date: if 'yes', display issue date
    @param display_issue_number: if 'yes', display issue date
    @param estimate_release_date: if 'yes', display the theoretical release date
    @param granularity: <code>day</code>, <code>week</code> or <code>month</code>
    @param group_issues_date: if 'yes' and issue are grouped, display first issue date of the group
    @param display_month: type of display for month: 'short' ('Jan', 'Feb', etc.) or 'long' ('January', 'February', etc.)
    @param display_week_day: Can display day of the week ('Monday', etc.). Parameter can be 'short' ('Mon', 'Tue' etc), 'long' ('Monday', 'Tuesday', etc.) or '' (no value displayed)
    """
    args = parse_url_string(bfo.user_info['uri'])
    journal_name = args["journal_name"]
    issue_number = args["issue"]
    ln = bfo.lang
    _ = gettext_set_language(ln)

    try:
        issue_display = get_issue_number_display(issue_number,
                                                 journal_name,
                                                 ln)
    except InvenioWebJournalJournalIdNotFoundDBError as e:
        return e.user_box()
    except Exception as e:
        issue_display = issue_number

    issues = issue_display.split("/")[0]
    year = issue_display.split("/")[1]
    week_numbers = issues.split("-")

    if group_issues_date.lower() == 'yes':
        # Get release time of this issue (do not consider issue
        # "updates": take the earliest issue number of this group of
        # issues)
        grouped_issues = get_grouped_issues(journal_name, issue_number)
        if grouped_issues:
            issue_number = grouped_issues[0]

    if estimate_release_date.lower() == 'yes':
        # Get theoretical release date
        if granularity.lower() == 'day':
            granularity = DAILY
        elif granularity.lower() == 'week':
            granularity = WEEKLY
        elif granularity.lower() == 'month':
            granularity = MONTHLY
        else:
            granularity = None
        issue_release_time = issue_to_datetime(issue_number,
                                               journal_name,
                                               granularity)
    else:
        issue_release_time = get_release_datetime(issue_number,
                                                  journal_name)

    # Get a nice internationalized representation of this date
    date_text = ''
    if issue_release_time:
        if display_week_day:
            date_text = get_i18n_day_name(issue_release_time.isoweekday(),
                                          display_week_day,
                                          ln) + ' '
        month = get_i18n_month_name(issue_release_time.month,
                                    display_month,
                                    ln=ln)
        date_text += issue_release_time.strftime("%d " + month + " %Y").lstrip('0')

    issue_url = make_journal_url(bfo.user_info['uri'],
                                 {'recid': '',
                                  'ln': bfo.lang,
                                  'category': ''})
    out = '<a class="issue" href="%s">' % issue_url
    if display_issue_number.lower() == 'yes':
        out += _("Issue No.") + ' ' + issue_display + ' - '

    if display_date.lower() == 'yes':
        out += date_text

    out += '</a>'

    return out

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0

