# -*- coding: utf-8 -*-
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import time
import re
from invenio.webjournal_config import InvenioWebJournalIssueNumberBadlyFormedError, \
                                    InvenioWebJournalNoArticleNumberError, \
                                    InvenioWebJournalArchiveDateWronglyFormedError, \
                                    IvenioWebJournalNoPopupTypeError, \
                                    InvenioWebJournalNoPopupRecordError
from invenio.webjournal_utils import get_current_issue, \
                                    guess_journal_name

from invenio.config import CFG_SITE_LANG

# precompiled patterns for the parameters
issue_number_pattern = re.compile("^\d{1,2}/\d{4}$")

def wash_journal_language(language):
    """
    Washes the language parameter. If there is a language, return this,
    otherwise return CFG_SITE_LANG constant
    """
    if language == "":
        return CFG_SITE_LANG
    else:
        return language

def wash_journal_name(language, journal_name):
    """
    Washes the journal name parameter. In case of non-empty string, returns it,
    otherwise redirects to a guessing function.
    """
    if journal_name == "":
        return guess_journal_name(language)
    else:
        return journal_name

def wash_issue_number(language, journal_name, issue_number):
    """
    Washes an issue number to fit the pattern ww/YYYY, e.g. 50/2007
    w/YYYY is also accepted and transformed to 0w/YYYY, e.g. 2/2007 -> 02/2007
    If no issue number is found, tries to get the current issue
    """
    if issue_number == "":
        return get_current_issue(language, journal_name)
    else:
        issue_number_match = issue_number_pattern.match(issue_number)
        if issue_number_match:
            issue_number = issue_number_match.group()
            if len(issue_number.split("/")[0]) == 1:
                issue_number = "0%s" % issue_number
            return issue_number
        else:
            raise InvenioWebJournalIssueNumberBadlyFormedError(language,
                                                               issue_number)

def wash_category(language, category):
    """
    Wahses a category name. No washing criterions so far.
    """
    return category

def wash_article_number(language, number, journal_name):
    """
    Washes an article number. First checks if it is non-empty, then if it is
    convertable to int. If all passes, returns the number, else throws
    exception.
    """
    if number == "":
        raise InvenioWebJournalNoArticleNumberError(language, journal_name)
    try:
        int(number)
    except:
        raise InvenioWebJournalNoArticleNumberError(language, journal_name)
    return number

def wash_popup_type(language, type, journal_name):
    """
    """
    if type == "":
        raise IvenioWebJournalNoPopupTypeError(language, journal_name)
    else:
        return type

def wash_popup_record(language, record, journal_name):
    """
    """
    if record == "":
        raise InvenioWebJournalNoPopupRecordError(language, journal_name,
                                                  "no recid")
    try:
        int(record)
    except:
        raise InvenioWebJournalNoPopupRecordError(language, journal_name,
                                                  record)
    return record

def wash_archive_date(language, journal_name, archive_date):
    """
    Washes an archive date to the form dd/mm/yyyy or empty.
    """
    if archive_date == "":
        return ""
    try:
        time.strptime(archive_date, "%d/%m/%Y")
    except:
        raise InvenioWebJournalArchiveDateWronglyFormedError(language,
                                                             archive_date)
    return archive_date
