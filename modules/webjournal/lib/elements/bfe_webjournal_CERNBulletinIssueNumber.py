# -*- coding: utf-8 -*-
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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

from invenio.webjournal_utils import parse_url_string, \
                                        get_monday_of_the_week, \
                                        get_issue_number_display
from invenio.webjournal_config import InvenioWebJournalJournalIdNotFoundDBError
from invenio.config import etcdir, weburl
from invenio.search_engine import search_pattern

cfg_strings = {}
cfg_strings["issue_title"] = {"en":"Issue No.", "fr": "Numéro"}
cfg_strings["monday"] = {"en":"Monday", "fr": "Lundi"}
cfg_strings["months"] = [{"en":"January", "fr": "janvier"},
    {"en":"February", "fr": "février"},
    {"en":"March", "fr": "mars"},
    {"en":"April", "fr": "avril"},
    {"en":"May", "fr": "may"},
    {"en":"June", "fr": "juin"},
    {"en":"July", "fr": "juillet"},
    {"en":"August", "fr": "août"},
    {"en":"September", "fr": "septembre"},
    {"en":"October", "fr": "octobre"},
    {"en":"November", "fr": "novembre"},
    {"en":"December", "fr": "décembre"}]

def format(bfo):
    """
    Returns the string used for the issue number in the format:
    Issue No.<is1>-<is2>/<year> - <exact date>,
    e.g. Issue No.32-33/2007 – Tuesday 6 August 2007
    """
    journal_name = bfo.req.journal_defaults["name"]
    issue_number = bfo.req.journal_defaults["issue"]
    try:
        issue_display = get_issue_number_display(issue_number,
                                                        journal_name,
                                                        bfo.lang)
    except InvenioWebJournalJournalIdNotFoundDBError, e:
        register_exception(req=req)
        return e.user_box()
    except Exception, e:
        issue_display = issue_number    
    issues = issue_display.split("/")[0]
    year = issue_display.split("/")[1]
    week_numbers = issues.split("-")

    if len(week_numbers) == 2:
        low_bound = week_numbers[0]
        high_bound = week_numbers[1]
        if int(low_bound) < int(high_bound):
            date = get_monday_of_the_week(low_bound, year)
        else:
            date = get_monday_of_the_week(low_bound, str(int(year)-1))
    else:
        date = get_monday_of_the_week(week_numbers[0], year)
            
    if bfo.lang == "fr":
        date = date.replace(cfg_strings["monday"]["en"], cfg_strings["monday"]["fr"])
        for entry in cfg_strings["months"]:
            date = date.replace(entry["en"], entry["fr"])
    issue_number_format = '%s - %s' % (issue_display, date)
    out = '<a class="issue" href="%s/journal/?name=%s&issue=%s&ln=%s">%s %s</a>' % (weburl,
                                                             journal_name,
                                                             issue_number,
                                                             bfo.lang,
                                                             cfg_strings["issue_title"][bfo.lang],
                                                             issue_number_format)
    return out

    
def escape_values(bfo):
    """
    """
    return 0

if __name__ == "__main__":
    from invenio.bibformat_engine import BibFormatObject
    myrec = BibFormatObject(51)
    format(myrec)
