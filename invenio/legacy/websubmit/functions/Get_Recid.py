## This file is part of Invenio.
## Copyright (C) 2007, 2008, 2009, 2010, 2011 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Get the recid of a record with a given report-number (from the global 'rn'),
   and store it into the global 'sysno'.
"""

__revision__ = "$Id$"

from os import access, rename, F_OK, R_OK
import re
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
alert('The document with report-number [%s] cannot be found in our """ \
"""database.\\nPerhaps it has not yet been integrated?\\nYou can choose """ \
"""another report number or retry this action in a few minutes.');\n
document.forms[0].submit();
</script>"""

## JavaScript action and message to be passed to "InvenioWebSubmitFunctionStop"
## when multiple document recids for the given report-number are found found:
CFG_ALERT_MULTIPLE_DOCUMENTS_FOUND = """\n<script type="text/javascript">
document.forms[0].action="/submit";
document.forms[0].curpage.value=1;
document.forms[0].step.value=0;
user_must_confirm_before_leaving_page = false;
alert('Multiple documents with the report number [%s] have been found.\\n""" \
"""You can choose another report number or retry this action in a few """ \
"""minutes.');\n
document.forms[0].submit();
</script>"""

## JavaScript action and message to be passed to "InvenioWebSubmitFunctionStop"
## when the recid found doesn't match the type of document that should be
## handled by this submission
CFG_ALERT_WRONG_RECORD_FOR_THIS_SUBMISSION = """
<script type="text/javascript">
document.forms[0].action="/submit";
document.forms[0].curpage.value=1;
document.forms[0].step.value=0;
user_must_confirm_before_leaving_page = false;
document.forms[0].submit();
alert('This document can not be handled using this submission interface.\\n""" \
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
    recid of a record. In this case, a check will be done in order to assure
    that the recid can be handled by this submission.

    Parameters: record_search_pattern - this enforces restrictions on which type
    of documents can be modified via a certain submission interface. If the
    record_search_pattern is not defined, no restriction will be enforced.
    The record_search_pattern can be anything that can be used by
    search_pattern to search for. Also, one can use variables stored locally,
    like &lt;comboDEMOJRN&gt; to denote the category or subcategory.
    Ex:
        reportnumber:DEMO-&lt;comboDEMOJRN&gt;-*
        collection:ATLANTISTIMESNEWS
        reportnumber:DEMO-&lt;comboDEMOJRN&gt;-* | collection:ATLANTISTIMESNEWS
    As a note, you can test your pattern, using the search engine
    and see if it retrieves the expected results.

    WARNING: this check is not applied if a SN file already exists in
    curdir.

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
                          - if recid should not be handled by the current submission;
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
        ## check if the record needs to comply to any restriction
        ## basically checks if this record can/should be handled by this submission
        if parameters['record_search_pattern']:
            if not is_record_matching_pattern(parameters['record_search_pattern'], sysno, curdir):
                # delete the SN file and reset the sysno,
                # because this record is not the good record to be hadled by this submission
                rename("%s/SN" % curdir, "%s/SN_WRONG" % curdir)
                sysno = ""
                raise InvenioWebSubmitFunctionStop(CFG_ALERT_WRONG_RECORD_FOR_THIS_SUBMISSION)
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

def is_record_matching_pattern(record_pattern, recid, curdir):
    """Given a pattern and a recid, returns True if the recid
       can be retrieved using the record_pattern. This enforces
       restrictions on which type of documents can be modified via a
       certain submission interface.
       The record_pattern can be anything that can be used by
       search_pattern to search for.
       Also, one can use variables stored locally, like <comboDEMOJRN>
       to denote the category or subcategory.
       Ex:
           reportnumber:DEMO-<comboDEMOJRN>-*
           collection:ATLANTISTIMESNEWS
           reportnumber:DEMO-<comboDEMOJRN>-* | collection:ATLANTISTIMESNEWS
       As a note, you can test your pattern, using the search engine
       and see if it retrieves the expected results.

    """
    # if no pattern is configured, then do not do any checks
    if not record_pattern:
        return True
    # check for local variables embedded in the pattern (ex: <comboXYZ>)
    # and  replace them with the value read from the corresponding file
    pattern_local_variables = '<\w+>'
    local_vars = re.findall(pattern_local_variables, record_pattern)
    final_record_pattern = record_pattern
    if local_vars:
        for local_var in local_vars:
             if record_pattern.find(local_var) > -1:
                 file_name = local_var[1:-1].strip()
                 try:
                     f = open("%s/%s" %(curdir, file_name), "r")
                     local_variable_content = f.read().strip()
                     final_record_pattern = final_record_pattern.replace(local_var, local_variable_content)
                     f.close()
                 except IOError:
                     msg = "Record pattern badly defined. There is no local file: %s." % file_name
                     raise InvenioWebSubmitFunctionError(msg)
    # check to see if nested <> tags were used, in this case throw an error -not supported
    if final_record_pattern.find('<') > -1 or final_record_pattern.find('>') > -1:
        msg = "Record pattern badly defined -> the local variables tags should be revised." % file_name
        raise InvenioWebSubmitFunctionError(msg)
    # get the list of records that match the final record pattern
    reclist = list(search_pattern(p=final_record_pattern))
    # check to see if our recid is part of this list or not
    if recid in reclist:
        return True
    else:
        return False

