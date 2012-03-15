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

"""WebSubmit function - Set the global variable 'rn' to the report
                        number of the record identified by sysno
"""
import os, cgi
from invenio.config import CFG_SITE_SUPPORT_EMAIL
from invenio.search_engine import get_fieldvalues, record_exists
from invenio.websubmit_functions.Shared_Functions import ParamFromFile
from invenio.websubmit_functions.Get_Recid import is_record_matching_pattern

## JavaScript action and message to be passed to "InvenioWebSubmitFunctionStop"
## when a record does not exist or has been deleted.
CFG_ALERT_DOCUMENT_NOT_FOUND = """\n<script type="text/javascript">
document.forms[0].action="/submit";
document.forms[0].curpage.value=1;
document.forms[0].step.value=0;
user_must_confirm_before_leaving_page = false;
alert('The document with record ID [%s] cannot be found in our """ \
"""database.\\nPerhaps it has been deleted or has not yet been integrated? """ \
"""You can choose another record ID or retry this action in a few minutes.');\n
document.forms[0].submit();
</script>"""

## JavaScript action and message to be passed to "InvenioWebSubmitFunctionStop"
## when it seems that we try to access an invalid path.
CFG_ALERT_INVALID_EDSRN_PATH = """\n<script type="text/javascript">
document.forms[0].action="/submit";
document.forms[0].curpage.value=1;
document.forms[0].step.value=0;
user_must_confirm_before_leaving_page = false;
alert('It is not possible to access path [%s]. Please contact %s');\n
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
alert('This document can not be handled using this submission interface.\\n""" \
"""You can choose another record ID or retry this action in a few """ \
"""minutes.');\n
document.forms[0].submit();
</script>"""

## JavaScript action and message to be passed to "InvenioWebSubmitFunctionStop"
## when the recid found is not an integer
CFG_ALERT_RECORD_ID_MUST_BE_INT = """
<script type="text/javascript">
document.forms[0].action="/submit";
document.forms[0].curpage.value=1;
document.forms[0].step.value=0;
user_must_confirm_before_leaving_page = false;
alert('The provided record ID [%s] must be an integer.');\n
document.forms[0].submit();
</script>"""

# Where to look for report numbers (in this order)
CFG_DEFAULT_RN_TAGS = ['037__a', '088__a', '021__a']

def Set_RN_From_Sysno(parameters, curdir, form, user_info=None):
    """
    Set the global variable 'rn' to the report number of the record
    identified by 'sysno' (recid) global variable.

    Useful at MBI step when the user specifies the record to modify
    using the recid instead of the report number.  Since most
    WebSubmit functions relies on the global 'rn' variable, it is
    necessary in these cases to include this function.

    This function MUST be preceded by 'Get_Recid' function.

    To identify the record to update via 'recid' instead of report
    number, one MUST on the MBI form request the recid/sysno using a
    form element named 'SN'.

    Parameters:

         edsrn - file where to write the report number if found

      rep_tags - comma-separater list of tags where the report number
                 can be found. Default is '037__a', '088__a', '021__a'
                 if no value is specified.

  record_search_pattern - this enforces restrictions on which type of
                 documents can be modified via a certain submission
                 interface. If the record_search_pattern is not
                 defined, no restriction will be enforced.  The
                 record_search_pattern can be anything that can be
                 used by search_pattern to search for. Also, one can
                 use variables stored locally, like
                 &lt;comboDEMOJRN&gt; to denote the category or
                 subcategory.
                 Ex:
                    reportnumber:DEMO-&lt;comboDEMOJRN&gt;-*
                    collection:ATLANTISTIMESNEWS
                    reportnumber:DEMO-&lt;comboDEMOJRN&gt;-* | collection:ATLANTISTIMESNEWS

                 As a note, you can test your pattern, using the
                 search engine and see if it retrieves the expected
                 results.

                 WARNING: this check is not applied if the report
                 number has already been written to 'edsrn' file.

    Exceptions raised:
        + InvenioWebSubmitFunctionStop
              - if trying to access unauthorized path to read/write report number;
              - if accessing a recid that does not exist or is deleted;
              - if recid should not be handled by the current submission;
    """
    global rn, sysno
    if not sysno:
        return

    try:
        sysno = int(sysno)
    except:
        raise InvenioWebSubmitFunctionStop(CFG_ALERT_RECORD_ID_MUST_BE_INT % \
                                           cgi.escape((sysno)))

    edsrn = parameters['edsrn']
    path_to_repnum_file = os.path.join(curdir, edsrn)

    if not os.path.abspath(path_to_repnum_file).startswith(curdir):
        # Trying to access invalid path...
        raise InvenioWebSubmitFunctionStop(CFG_ALERT_INVALID_EDSRN_PATH % \
                                           (cgi.escape(path_to_repnum_file),
                                            cgi.escape(CFG_SITE_SUPPORT_EMAIL)))

    if os.path.exists(path_to_repnum_file):
        # Have we already written RN to disk? If so, read from there
        possible_rn = ParamFromFile(path_to_repnum_file)
        if possible_rn.strip():
            # No empty
            rn = possible_rn
            return

    if record_exists(sysno) != 1:
        # Record does not exist
        raise InvenioWebSubmitFunctionStop(CFG_ALERT_DOCUMENT_NOT_FOUND % sysno)

    ## Check if the record needs to comply to any restriction.
    ## Basically checks if this record can/should be handled by this submission
    if parameters['record_search_pattern']:
        if not is_record_matching_pattern(parameters['record_search_pattern'], sysno, curdir):
            # delete the SN file and reset the sysno,
            # because this record is not the good record to be hadled by this submission
            os.rename("%s/SN" % curdir, "%s/SN_WRONG" % curdir)
            sysno = ""
            raise InvenioWebSubmitFunctionStop(CFG_ALERT_WRONG_RECORD_FOR_THIS_SUBMISSION)

    rn_tags = [tag.strip() for tag in parameters['rep_tags'].split(',') \
               if tag.strip()]
    if not rn_tags:
        rn_tags  = CFG_DEFAULT_RN_TAGS

    # Retrieve report number in metadata
    for rn_tag in rn_tags:
        possible_report_numbers = get_fieldvalues(sysno, rn_tag)
        if possible_report_numbers:
            rn = possible_report_numbers[0].strip()
            break

    edsrn = parameters['edsrn']
    path_to_repnum_file = os.path.join(curdir, edsrn)

    if rn and not os.path.exists(path_to_repnum_file):
        # Write report number to specified file
        fp = open(path_to_repnum_file, 'w')
        fp.write(rn)
        fp.close()
