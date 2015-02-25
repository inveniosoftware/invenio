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

"""Register a referee's decision on a document (i.e. it is approved or
   rejected) in the submission approvals database (sbmAPPROVALS).
"""

__revision__ = "$Id$"

import cgi
import os.path
from invenio.config import CFG_SITE_SUPPORT_EMAIL
from invenio.legacy.websubmit.functions.Shared_Functions import ParamFromFile
from invenio.legacy.websubmit.config import InvenioWebSubmitFunctionError, \
                                     InvenioWebSubmitFunctionStop
from invenio.legacy.websubmit.db_layer import get_simple_approval_status, \
                                      update_approval_request_status

def Register_Referee_Decision(parameters, curdir, form, user_info=None):
    """
    A referee may either "accept" or "reject" a refereed document.
    The referee's decision is stored in a file in the submission's working
    directory and it is this function's job to read the contents of that
    file and update the status of the document's entry in the approvals
    table (sbmAPPROVAL) to be either "accepted" or "rejected" depending
    upon the referee's decision.

    @param decision_file: (string) - the name of the file in which the
        referee's decision is to be found.
        NOTE: A referee's decision _MUST_ be either "accept" or "reject".
              If not, an InvenioWebSubmitFunctionError will be raised.
              If a document's "approval status" is not "waiting" at the
              time of the referee's decision, the decision will not be
              taken into account and the submission will be halted.
              (This is because it's not appropriate to approve a document
              that has already been approved or rejected, has been
              withdrawn, etc.)

    @return: empty string.

    @Exceptions raised: InvenioWebSubmitFunctionError on unexpected error.
                        InvenioWebSubmitFunctionStop in the case where the
                        approval should be stopped for whatever reason.
                        (E.g. when it has already been approved.)
    """
    global rn
    doctype = form['doctype']
    ########
    ## Get the parameters from the list:
    ########
    ## Get the name of the "decision" file and read its value:
    ########
    decision = "" ## variable to hold the referee's decision
    try:
        decision_file = parameters["decision_file"]
    except KeyError:
        ## No value given for the decision file:
        decision_file = None
    else:
        if decision_file is not None:
            decision_file = os.path.basename(decision_file).strip()
            if decision_file == "":
                decision_file = None
    if decision_file is None:
        ## Unable to obtain the name of the file in which the referee's
        ## decision is stored. Halt.
        err_msg = "Error in Register_Referee_Decision: Function was not " \
                  "configured with a valid value for decision_file - the " \
                  "file in which the referee's decision is stored. " \
                  "The referee's decision has not been processed for " \
                  "[%s]. Please inform the administrator." \
                  % rn
        raise InvenioWebSubmitFunctionError(err_msg)
    ## Read in the referee's decision:
    decision = ParamFromFile("%s/%s" % (curdir, decision_file)).lower()
    ##
    ########
    if decision not in ("approve", "reject"):
        ## Invalid value for the referee's decision.
        err_msg = "Error in Register_Referee_Decision: The value for the " \
                  "referee's decision (%s) was invalid. Please inform the " \
                  "administrator." % decision
        raise InvenioWebSubmitFunctionError(err_msg)
    ##
    ## Get the status of the approval request for this document from the DB:
    document_status = get_simple_approval_status(doctype, rn)
    if document_status is None:
        ## No information about this document in the approval database.
        ## Its approval has never been requested.
        msg = """
<br />
<div>
<span style="color: red;">Note:</span> No details about an approval request
 for the document [%s] have been found in the database.<br />
Before a decision can be made about it, a request for its approval must have
 been submitted.<br />
If you feel that there is a problem, please contact &lt;%s&gt;, quoting the
document's report number.
</div>""" % (cgi.escape(rn), cgi.escape(CFG_SITE_SUPPORT_EMAIL))
        raise InvenioWebSubmitFunctionStop(msg)
    elif document_status in ("approved", "rejected"):
        ## If a document was already approved or rejected, halt the approval
        ## process with a message for the referee:
        msg = """
<br />
<div>
<span style="color: red;">Note:</span> The document [%s] has
 already been %s.<br />
There is nothing more to be done in this case and your decision
 has <b>NOT</b> been taken into account.<br />
If you believe this to be an error, please contact &lt;%s&gt;, quoting the<br />
document's report-number [%s] and describing the problem.
</div>""" % (cgi.escape(rn), \
             cgi.escape(document_status), \
             cgi.escape(CFG_SITE_SUPPORT_EMAIL), \
             cgi.escape(rn))
        raise InvenioWebSubmitFunctionStop(msg)
    elif document_status == "withdrawn":
        ## Somebody had withdrawn the approval request for this document
        ## before the referee made this decision. Halt the approval process
        ## with a message for the referee:
        msg = """
<br />
<div>
<span style="color: red;">Note:</span> The request for the approval of the
 document [%s] had been withdrawn prior to the submission of your
 decision.<br />
Before a decision can be made regarding its status, a new request for its
 approval must be submitted by the author.<br />
Your decision has therefore <b>NOT</b> been taken into account.<br />
If you believe this to be an error, please contact &lt;%s&gt;, quoting the
 document's report-number [%s] and describing the problem.
</div>
""" % (cgi.escape(rn), \
       cgi.escape(CFG_SITE_SUPPORT_EMAIL), \
       cgi.escape(rn))
        raise InvenioWebSubmitFunctionStop(msg)
    elif document_status == "waiting":
        ## The document is awaiting approval. Register the referee's decision:
        if decision == "approve":
            ## Register the approval:
            update_approval_request_status(doctype, \
                                           rn, \
                                           note="",
                                           status="approved")
        else:
            ## Register the rejection:
            update_approval_request_status(doctype, \
                                           rn, \
                                           note="",
                                           status="rejected")
        ## Now retrieve the status of the document once more and check that
        ## it is either approved or rejected.  If not, the decision couldn't
        ## be registered and an error should be raised.
        status_after_update = get_simple_approval_status(doctype, rn)
        if status_after_update not in ("approved", "rejected"):
            msg = "Error in Register_Referee_Decision function: It was " \
                  "not possible to update the approvals database when " \
                  "trying to register the referee's descision of [%s] " \
                  "for the document [%s]. Please report this this " \
                  "problem to [%s], quoting the document's " \
                  "report-number [%s]." \
                  % (decision, rn, CFG_SITE_SUPPORT_EMAIL, rn)
            raise InvenioWebSubmitFunctionError(msg)
    else:
        ## The document had an unrecognised "status". Halt with an error.
        msg = "Error in Register_Referee_Decision function: The " \
              "document [%s] has an unknown approval status " \
              "[%s]. Unable to process the referee's decision. Please " \
              "report this problem to [%s], quoting the document's " \
              "report-number [%s] and describing the problem." \
              % (rn, document_status, CFG_SITE_SUPPORT_EMAIL, rn)
        raise InvenioWebSubmitFunctionError(msg)
    ## Finished.
    return ""
