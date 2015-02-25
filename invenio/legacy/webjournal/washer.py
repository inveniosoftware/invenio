# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2007, 2008, 2009, 2010, 2011 CERN.
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
WebJournal input parameters washing related functions
"""
import time
import re
from invenio.legacy.webjournal.config import \
     InvenioWebJournalIssueNumberBadlyFormedError, \
     InvenioWebJournalNoArticleNumberError, \
     InvenioWebJournalArchiveDateWronglyFormedError, \
     InvenioWebJournalNoPopupRecordError, \
     InvenioWebJournalNoCategoryError
from invenio.legacy.webjournal.utils import \
     get_current_issue, \
     guess_journal_name, \
     get_journal_categories, \
     get_journal_nb_issues_per_year
from invenio.config import CFG_SITE_LANG

# precompiled patterns for the parameters
issue_number_pattern = re.compile("^\d{1,3}/\d{4}$")

def wash_journal_language(ln):
    """
    Washes the language parameter. If there is a language, return this,
    otherwise return CFG_SITE_LANG constant
    """
    if ln == "":
        return CFG_SITE_LANG
    else:
        return ln

def wash_journal_name(ln, journal_name, guess=True):
    """
    Washes the journal name parameter. In case of non-empty string,
    returns it, otherwise redirects to a guessing function.

    If 'guess' is True the function tries to fix the capitalization of
    the journal name.
    """
    if guess or not journal_name:
        return guess_journal_name(ln, journal_name)
    else:
        return journal_name

def wash_issue_number(ln, journal_name, issue_number):
    """
    Washes an issue number to fit the pattern ww/YYYY, e.g. 50/2007
    w/YYYY is also accepted and transformed to 0w/YYYY, e.g. 2/2007 -> 02/2007
    If no issue number is found, tries to get the current issue
    """
    if issue_number == "":
        return get_current_issue(ln, journal_name)
    else:
        issue_number_match = issue_number_pattern.match(issue_number)
        if issue_number_match:
            issue_number = issue_number_match.group()
            number, year = issue_number.split('/')
            number_issues_per_year = get_journal_nb_issues_per_year(journal_name)
            precision = len(str(number_issues_per_year))
            return ("%0" + str(precision) + "i/%s") % (int(number), year)
        else:
            raise InvenioWebJournalIssueNumberBadlyFormedError(ln,
                                                               issue_number)

def wash_category(ln, category, journal_name, issue):
    """
    Washes a category name.
    """
    categories = get_journal_categories(journal_name, issue=None)
    if category in categories:
        return category
    elif category == "" and len(categories) > 0:
        return categories[0]
    else:
        raise InvenioWebJournalNoCategoryError(ln,
                                               category,
                                               categories)

def wash_article_number(ln, number, journal_name):
    """
    Washes an article number. First checks if it is non-empty, then if it is
    convertable to int. If all passes, returns the number, else throws
    exception.
    """
    if number == "":
        raise InvenioWebJournalNoArticleNumberError(ln, journal_name)
    try:
        int(number)
    except:
        raise InvenioWebJournalNoArticleNumberError(ln, journal_name)
    return number

def wash_popup_record(ln, record, journal_name):
    """
    """
    if record == "":
        raise InvenioWebJournalNoPopupRecordError(ln, journal_name,
                                                  "no recid")
    try:
        int(record)
    except:
        raise InvenioWebJournalNoPopupRecordError(ln, journal_name,
                                                  record)
    return record

def wash_archive_date(ln, journal_name, archive_date):
    """
    Washes an archive date to the form dd/mm/yyyy or empty.
    """
    if archive_date == "":
        return ""
    try:
        time.strptime(archive_date, "%d/%m/%Y")
    except:
        raise InvenioWebJournalArchiveDateWronglyFormedError(ln,
                                                             archive_date)
    return archive_date
