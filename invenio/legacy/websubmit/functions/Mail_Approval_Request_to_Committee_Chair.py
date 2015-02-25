# $id: Mail_Approval_Request_to_Committee_Chair.py,v 0.01 2008/07/25 18:33:44 tibor Exp $

# This file is part of Invenio.
# Copyright (C) 2008, 2010, 2011 CERN.
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

__revision__ = "$Id$"

   ##
   ## Name:          Mail_Approval_Request_to_Committee_Chair.py
   ## Description:   function Mail_Approval_Request_to_Committee_Chair.py
   ##                This function sends a confirmation email to the Committee Chair
   ##                when approval for a document is requested.
   ## Author:        T.Baron (first); C.Parker
   ##
   ## PARAMETERS:    authorfile: name of the file containing the author
   ##             titleFile: name of the file containing the title
   ##             emailFile: name of the file containing the email
   ##             status: one of "ADDED" (the document has been integrated
   ##                     into the database) or "APPROVAL" (an email has
   ##                 been sent to a referee - simple approval)
   ##             edsrn: name of the file containing the reference
   ##             newrnin: name of the file containing the 2nd reference
   ##                     (if any)
   ##

from invenio.config import CFG_SITE_NAME, \
     CFG_SITE_URL, \
     CFG_SITE_SUPPORT_EMAIL, \
     CFG_SITE_RECORD

from invenio.ext.email import send_email
from invenio.modules.access.control import acc_get_role_id, acc_get_role_users
from invenio.legacy.search_engine import search_pattern
from invenio.legacy.bibrecord import get_fieldvalues
from invenio.legacy.dbquery import run_sql

#Copied from publiline
def get_brief_doc_details_from_repository(reportnumber):
    """Try to get some brief details about the submission that is awaiting
       the referee's decision.
       Details sought are:
        title
        + Authors
        + recid (why?)
        + report-number (why?)
       This function searches in the Invenio repository, based on
       "reportnumber" for a record and then pulls the interesting fields
       from it.
       @param reportnumber: (string) - the report number of the item for
        which details are to be recovered. It is used in the search.
       @return: (dictionary or None) - If details are found for the item,
        they will be returned in a dictionary structured as follows:
            { 'title'            : '-', ## String - the item's title
              'recid'            : '',  ## String - recid taken from the SN file
              'report-number'    : '',  ## String - the item's report number
              'authors'          : [],  ## List   - the item's authors
            }
        If no details were found a NoneType is returned.
    """
    ## Details of the pending document, as found in the repository:
    pending_doc_details = None
    ## Search for records matching this "report number"
    found_record_ids = list(search_pattern(req=None, \
                                           p=reportnumber, \
                                           f="reportnumber", \
                                           m="e"))
    ## How many records were found?
    if len(found_record_ids) == 1:
        ## Found only 1 record. Get the fields of interest:
        pending_doc_details = { 'title'         : '-',
                                'recid'         : '',
                                'report-number' : '',
                                'authors'       : [],
                              }
        recid = found_record_ids[0]
        ## Authors:
        first_author  = get_fieldvalues(recid, "100__a")
        for author in first_author:
            pending_doc_details['authors'].append(author)
        other_authors = get_fieldvalues(recid, "700__a")
        for author in other_authors:
            pending_doc_details['authors'].append(author)
        ## Title:
        title = get_fieldvalues(recid, "245__a")
        if len(title) > 0:
            pending_doc_details['title'] = title[0]
        else:
            ## There was no value for title - check for an alternative title:
            alt_title = get_fieldvalues(recid, "2641_a")
            if len(alt_title) > 0:
                pending_doc_details['title'] = alt_title[0]
        ## Record ID:
        pending_doc_details['recid'] = recid
        ## Report Number:
        reptnum = get_fieldvalues(recid, "037__a")
        if len(reptnum) > 0:
            pending_doc_details['report-number'] = reptnum[0]
    elif len(found_record_ids) > 1:
        ## Oops. This is unexpected - there shouldn't be me multiple matches
        ## for this item. The old "getInAlice" function would have simply
        ## taken the first record in the list. That's not very nice though.
        ## Some kind of warning or error should be raised here. FIXME.
        pass
    return pending_doc_details

def Mail_Approval_Request_to_Committee_Chair(parameters, curdir, form, user_info=None):
    """
    This function sends a confirmation email to the Committee Chair
    when approval for a document is requested.
    """
    FROMADDR = '%s Submission Engine <%s>' % (CFG_SITE_NAME,CFG_SITE_SUPPORT_EMAIL)

    # retrieve useful information from webSubmit configuration
    res = run_sql("select * from sbmCPLXAPPROVAL where rn=%s", (rn, ))
    categ = res[0][1]

    pubcomchair_address = ""
    # Try to retrieve the committee chair's email from the referee's database
    for user in acc_get_role_users(acc_get_role_id("pubcomchair_%s_%s" % (res[0][0],categ))):
        pubcomchair_address += user[1]

    #Get the document details from the repository - use the function in publiline.py
    item_details = get_brief_doc_details_from_repository(rn)

    #Generate the author list
    authors = ""
    for element in item_details['authors']:
        authors += element + ", "

    message = """
    The document %s has been published as a Communication.
    Please select an appropriate referee for this document.

    Title: %s

    Author(s): %s

    To access the document(s), select the file(s) from the location:
    <%s/%s/%s>

    To select a referee, please go to:
    <%s/publiline.py?flow=cplx&doctype=%s&categ=%s&apptype=%s&RN=%s&ln=en>

    ---------------------------------------------
    Best regards.
    The submission team.""" % (rn,item_details['title'],authors,CFG_SITE_URL,CFG_SITE_RECORD,sysno,CFG_SITE_URL,res[0][0],res[0][1],res[0][3],rn)
    # send the mail

    send_email(FROMADDR,pubcomchair_address,"Request for Referee Selection : Document %s" % rn, message,footer="")
    return ""
