# -*- coding: utf-8 -*-
# $Id: bfe_webjournal_CERN_Bulletin_Archive.py,v 1.8 2008/06/03 09:12:18 jerome Exp $
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
WebJournal Element - Prints a form that redirects to specified Bulletin
issue.
"""
import datetime
from invenio.base.i18n import gettext_set_language
from invenio.config import CFG_SITE_URL
from invenio.legacy.webjournal.utils import \
     parse_url_string, \
     get_all_released_issues, \
     compare_issues, \
     get_journal_nb_issues_per_year

def format_element(bfo, lowest_issue):
    """
    Prints a form that redirects to specified journal issue

    You should specify <code>lowest_issue</code> only if it is not
    possible for WebJourbal to retrieved released issues (eg. when you
    have imported journal articles that have not been released with
    this WebJournal, and therefore not record in the database)

    @param lowest_issue: earliest existing issue. If not given, find out by checking released issues
    """
    args = parse_url_string(bfo.user_info['uri'])
    journal_name = args["journal_name"]
    archive_year = args["archive_year"] # None if not specified
    # Note that you can also access the argument 'archive_search'
    ln = bfo.lang
    _ = gettext_set_language(ln)

    released_issues = get_all_released_issues(journal_name)

    # If we do not have any clue about lowest issue, return nothing
    if not lowest_issue and not released_issues:
        return ''

    # Collect released issues by year
    issues_by_year = {}
    for issue_number in released_issues:
        number, year = issue_number.split('/')
        year = int(year)
        if year not in issues_by_year:
            issues_by_year[year] = []
        issues_by_year[year].append(issue_number)

    # If lowest issue was specified, then it means that some issues
    # are archived even if they have not been released in the DB (that
    # happens when some records have been imported from another
    # system, but not declared as released). We need to 'invent' these
    # issues
    if lowest_issue:
        min_number, min_year = lowest_issue.split('/')
        min_number = int(min_number)
        min_year = int(min_year)

        # If we have some released issues in DB, create up to the
        # first release. Else up to now
        years = issues_by_year.keys()
        if years:
            max_year = min(years)
        else:
            max_year = datetime.datetime.now().year

        max_issues = get_journal_nb_issues_per_year(journal_name)
        for year in range(min_year, max_year + 1):
            for number in range(1, max_issues + 1):
                if year not in issues_by_year:
                    issues_by_year[year] = []
                issue_number = ("%0" + str(len(str(max_issues))) + "i/%i") % \
                               (number, year)
                if not issue_number in issues_by_year[year]:
                    issues_by_year[year].append(issue_number)


    journal_years = issues_by_year.keys()
    journal_years.sort()

    if archive_year is None:
        archive_year = max(journal_years)

    journal_years_issues = issues_by_year[archive_year]
    journal_years_issues.sort(compare_issues)


    # FIXME: Submit the form with id instead of form nr.
    archive_title = "<h2>%s</h2>" % _("Archive")
    archive_form = '''
    <form id="archiveselectform" class="archiveform" action="%(CFG_SITE_URL)s/journal/search" name="searchbyissue" method="get">
        <em>%(select_year_label)s </em>
        <select name="archive_year" onchange="document.searchbyissue.submit();">
            %(select_year_list)s
        </select>
        <br />
        <br />
        <em>%(select_issue_label)s </em>
        <select name="archive_issue">
                %(select_issue_list)s
        </select>
        <input type="hidden" value="%(journal_name)s" name="name" />
        <input type="hidden" value="%(ln)s" name="ln" />
        <input type="submit" value="Go" name="archive_select" />
    </form>
    <hr />
    <form class="archiveform" action="%(CFG_SITE_URL)s/journal/search" name="searchbydate" method="get">
        <em>%(custom_date_label)s <small>(dd/mm/yyyy  -> e.g. 01/03/2006)</small>: </em>
        <input type="text" value="" maxlength="10" size="10" name="archive_date" />
        <input type="hidden" value="%(journal_name)s" name="name" />
        <input type="hidden" value="%(ln)s" name="ln" />
        <input type="submit" value="Go" name="archive_search" />
    </form>
    ''' % {'CFG_SITE_URL': CFG_SITE_URL,
           'journal_name': journal_name,
           'select_year_label': _("Select Year:"),
           'select_year_list' : "\n".join(['<option value="%s" %s>%s</option>' % \
                                           (year,
                                            (year == archive_year) and 'selected="selected"' or "",
                                            year)
                                           for year in journal_years]),
           'select_issue_label': _("Select Issue:"),
           'select_issue_list' : "\n".join(['<option value="%s">%s</option>' % (issue, issue) \
                                            for issue in journal_years_issues]),
           'ln': bfo.lang,
           'custom_date_label': _("Select Date:"),
           }

    return archive_title + archive_form

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
