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

"""Get the recid of a record with a given report-number (from the global 'rn'),
   and store it into the global 'sysno'.
"""

__revision__ = "$Id$"

from os import access, F_OK, R_OK
from invenio.search_engine import \
     record_exists, \
     search_pattern, \
     get_field_tags
from invenio.websubmit_config import \
     InvenioWebSubmitFunctionStop, \
     InvenioWebSubmitFunctionError


## JavaScript action and message to be passed to "InvenioWebSubmitFunctionStop"
## when a document recid for the given report-number cannot be found:
CFG_ALERT_DOCUMENT_NOT_FOUND = """\n<script type="text/javascript">
document.forms[0].action="/submit";
document.forms[0].curpage.value=1;
document.forms[0].step.value=0;
user_must_confirm_before_leaving_page = false;
document.forms[0].submit();
alert('The document with report-number [%s] cannot be found in our """ \
"""database.\\nPerhaps it has not yet been integrated?\\nYou can choose """ \
"""another report number or retry this action in a few minutes.');\n</script>"""

## JavaScript action and message to be passed to "InvenioWebSubmitFunctionStop"
## when multiple document recids for the given report-number are found found:
CFG_ALERT_MULTIPLE_DOCUMENTS_FOUND = """\n<script type="text/javascript">
document.forms[0].action="/submit";
document.forms[0].curpage.value=1;
document.forms[0].step.value=0;
user_must_confirm_before_leaving_page = false;
document.forms[0].submit();
alert('Multiple documents with the report number [%s] have been found.\\n""" \
"""You can choose another report number or retry this action in a few """ \
"""minutes.');\n</script>"""


def Get_Recid(parameters, curdir, form, user_info=None):
    """
    Given the report number of a record (the global "rn"), retrieve the
    "recid" (001).
    The function first of all checks for the existence of the file "SN" in
    the current submission's working directory. If it exists, it is read in
    and used as the "recid".
    Otherwise, this function will contact the database in order to obtain the
    recid of a record.

    Unless file curdir/SN exists, the function depends upon the global
    value 'rn' having been set (for eg. by calling Get_Report_Number'
    prior to this function) It will use this value when searching for
    a record. Note: If 'rn' is empty, the search for the document will
    not be conducted.

    Exceptions raised:
        + InvenioWebSubmitFunctionError:
                          - if unable to open curdir/SN for reading;
                          - if unable to open curdir/SN for writing;
        + InvenioWebSubmitFunctionStop:
                          - if the global 'rn' is empty (no rn to search with);
                          - if no recid found for 'rn' value;
                          - if multiple recids found for 'rn' value;
    """
    global rn, sysno
    ## initialize sysno
    sysno = ""

    if access("%s/SN" % curdir, F_OK|R_OK):
        ## SN exists and should contain the recid; get it from there.
        try:
            fptr = open("%s/SN" % curdir, "r")
        except IOError:
            ## Unable to read the SN file's contents
            msg = """Unable to correctly read the current submission's recid"""
            raise InvenioWebSubmitFunctionError(msg)
        else:
            ## read in the submission details:
            sysno = fptr.read().strip()
            fptr.close()
    else:
        ## SN doesn't exist; Check the DB for a record with this reportnumber.

        ## First, if rn is empty, don't conduct the search:
        if rn.strip() in ("", None):
            ## No report-numer provided:
            raise InvenioWebSubmitFunctionStop(CFG_ALERT_DOCUMENT_NOT_FOUND \
                                               % "NO REPORT NUMBER PROVIDED")

        ## Get a list of recids of LIVE records associated with the report num
        recids = get_existing_records_for_reportnumber(rn)

        ## There should only be 1 _existing_ record for the report-number:
        if len(recids) == 1:
            ## Only one record found - save it to a text file called SN
            ## in the current submission's working directory:
            try:
                fptr = open("%s/SN" % curdir, "w")
            except IOError:
                ## Unable to read the SN file's contents
                msg = """Unable to save the recid for report [%s]""" \
                         % rn
                raise InvenioWebSubmitFunctionError(msg)
            else:
                ## Save recid to SN and to the global scope:
                sysno = recids[0]
                fptr.write("%s" % sysno)
                fptr.flush()
                fptr.close()
        elif len(recids) < 1:
            ## No recid found for this report number:
            msg = CFG_ALERT_DOCUMENT_NOT_FOUND % rn
            raise InvenioWebSubmitFunctionStop(msg)
        else:
            ## Multiple recids found for this report-number:
            msg = CFG_ALERT_MULTIPLE_DOCUMENTS_FOUND % rn
            raise InvenioWebSubmitFunctionStop(msg)

    ## Everything seems to have run smoothly:
    return ""

def get_existing_records_for_reportnumber(reportnum):
    """Given a report number, return a list of recids of real (live) records
       that are associated with it.
       That's to say if the record does not exist (prehaps deleted, for example)
       its recid will now be returned in the list.

       @param reportnum: the report number for which recids are to be returned.
       @type reportnum: string
       @return: list of recids.
       @rtype: list
       @note: If reportnum was not found in phrase indexes, the function searches
           directly in bibxxx tables via MARC tags, so that the record does not
           have to be phrase-indexed.
    """
    existing_records = []  ## List of the report numbers of existing records

    ## Get list of records with the report-number: (first in phrase indexes)
    reclist = list(search_pattern(req=None,
                                  p=reportnum,
                                  f="reportnumber",
                                  m="e"))
    if not reclist:
        # Maybe the record has not been indexed yet? (look in bibxxx tables)
        tags = get_field_tags("reportnumber")
        for tag in tags:
            recids = list(search_pattern(req=None,
                                         p=reportnum,
                                         f=tag,
                                         m="e"))
            reclist.extend(recids)

        reclist = dict.fromkeys(reclist).keys() # Remove duplicates

    ## Loop through all recids retrieved and testing to see whether the record
    ## actually exists or not. If none of the records exist, there is no record
    ## with this reportnumber; If more than one of the records exists, then
    ## there are multiple records with the report-number; If only one record
    ## exists, then everything is OK,
    for rec in reclist:
        rec_exists = record_exists(rec)
        if rec_exists == 1:
            ## This is a live record record the recid and augment the counter of
            ## records found:
            existing_records.append(rec)
    return existing_records

