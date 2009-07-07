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
from invenio.bibformat_engine import BibFormatObject
from invenio.webjournal_utils import get_current_issue
from invenio.webjournal import perform_request_index

from invenio.config import weburl


localized_strings = {}
localized_strings["archive_title"] = {"en": "Archive", "fr": "Archives"}
localized_strings["selectyear"] = {"en": "Select Year:", "fr": "Choisir une année:"}
localized_strings["selectissue"] = {"en": "Select Issue:", "fr": "Choisir un numéro:"}
localized_strings["customdate"] = {"en": "Select Date", "fr": "Choisir une date"}
CFG_LOWEST_BULLETIN_ISSUE = "34/2001"

def format(bfo):
    """
    """
    journal_name = bfo.req.journal_defaults["name"]
    archive_year = bfo.req.journal_defaults["archive_year"]
    archive_issue = bfo.req.journal_defaults["archive_issue"]
    archive_select = bfo.req.journal_defaults["archive_select"]
    language = bfo.req.journal_defaults["language"]
    #debugging
    #journal_name = "CERNBulletin"
    #archive_year = "2008"
    #archive_issue = ""
    #archive_select = ""
    #language = "en"

    # get data for lowest and highest issue
    lowest_year = CFG_LOWEST_BULLETIN_ISSUE.split("/")[1]
    lowest_year_lowest_issue = CFG_LOWEST_BULLETIN_ISSUE.split("/")[0]
    latest_issue = get_current_issue(language, journal_name)
    latest_year = latest_issue.split("/")[1]
    latest_year_latest_issue = latest_issue.split("/")[0]
    # init lists
    journal_years = [str(year) for year in range(int(lowest_year), int(latest_year)+1)]
    journal_years.sort()
    journal_years.reverse()
    selected_year = (archive_year != "") and archive_year or latest_year
    # get all weeks up to 53 or now in the current year
    if selected_year == latest_year:
        #latest_issue = int(get_current_issue(language, journal_name).split("/")[0])
        journal_years_issues = ["%s/%s" % ((len(str(issue))==1) and "0"+str(issue) or issue,
                            selected_year) for issue in range(1, int(latest_year_latest_issue))]
    elif selected_year == lowest_year:
        journal_years_issues = ["%s/%s" % ((len(str(issue))==1) and "0"+str(issue) or issue,
                            selected_year) for issue in range(int(lowest_year_lowest_issue), 53)]
    else:
        journal_years_issues = ["%s/%s" % ((len(str(issue))==1) and "0"+str(issue) or issue,
                                selected_year) for issue in range(1, 53)]
    journal_years_issues.sort()
    journal_years_issues.reverse()
    # todo: javascript submit the form with id instead of form nr.
    archive_title = "<h2>%s</h2>" % localized_strings["archive_title"][language]
    archive_form = '''
    <form id="archiveselectform" class="archiveform" action="search" name="search" method="get">
        <em>%s </em>
        <select name="archive_year" onchange="document.forms[1].submit();">  
            %s  
        </select>
        <br />
        <br />
        <em>%s </em>
        <select name="archive_issue">
                %s
        </select>
        <input type="hidden" value="CERNBulletin" name="name" />
        <input type="hidden" value="%s" name="ln" />
        <input type="submit" value="Go" name="archive_select" />
    </form>
    <hr />
    <form class="archiveform" action="search" name="search" method="get">
        <em>%s <small>(dd/mm/yyyy  -> e.g. 01/03/2006)</small>: </em>
   	<input type="text" value="" maxlength="10" size="10" name="archive_date" />
        <input type="hidden" value="CERNBulletin" name="name" />
   	<input type="hidden" value="%s" name="ln" />
        <input type="submit" value="Go" name="archive_search" />
    </form>
    ''' % (localized_strings["selectyear"][bfo.lang],
           
"\n".join(['<option value="%s" %s>%s</option>' % (year,
                        (year==archive_year) and 'selected="selected"' or "",
                         year)
           for year in journal_years]),
    
            localized_strings["selectissue"][bfo.lang],

"\n".join(['<option value="%s">%s</option>' %
           (issue, issue) for issue in journal_years_issues]),

bfo.lang,
localized_strings["customdate"][bfo.lang],
bfo.lang
           )

    return "%s %s" % (archive_title, archive_form)
        
        #return perform_request_index(req, journal_name,
        #                             archive_issue, language, "News Articles")
#    <h2>Archives</h2>
#    <form id="archiveform" class="archiveform" action="search" name="search" method="get">
#      <em>Select the Year: </em>
#      <select name="archive_year">
#		<option value="2008">2008</option>
#
#		<option value="2007">2007</option>
#		<option value="2006">2006</option>
#	  </select>
#      <br />
#      <br />
#      <em>Select the Issue: </em>
#      <select name="archive_issue onchange="document.archiveform.submit()">
#
#		<option value="01/2008">01/2008</option>
#		<option value="02/2008">02/2008</option>
#		<option value="03/2008">03/2008</option>
#	  </select>
#      <input type="hidden" value="CERNBulletin" name="name" />
#      <input type="submit" value="Go" name="archive_select" />
#    </form>
#
#    <hr />
#    <form class="archiveform" action="search" name="search" method="get">
#      <em>Custom Date <small>(dd/mm/yyyy  -> e.g. 01/03/2006)</small>: </em>
#   	  <input type="text" value="" maxlength="10" size="10" name="archive_date" />
#      <input type="hidden" value="CERNBulletin" name="name" />
#   	  <input type="submit" value="Go" name="archive_search" />
#    </form>
def escape_values(bfo):
    """
    """
    return 0

if __name__ == "__main__":
    myrec = BibFormatObject(87)
    format(myrec)