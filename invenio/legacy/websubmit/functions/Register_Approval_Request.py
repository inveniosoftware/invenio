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

"""At the time of a "request for approval" submission, register the request in
   the WebSubmit "Approvals" DB (sbmAPPROVAL).
"""

__revision__ = "$Id$"

import sre_constants
import os
import cgi
import re
from invenio.legacy.websubmit.db_layer import register_new_approval_request, \
                                      get_simple_approval_status, \
                                      update_approval_request_status
from invenio.legacy.websubmit.functions.Shared_Functions import ParamFromFile
from invenio.legacy.websubmit.config import InvenioWebSubmitFunctionError, \
                                     InvenioWebSubmitFunctionStop
from invenio.ext.logging import register_exception
from invenio.config import CFG_SITE_SUPPORT_EMAIL

def Register_Approval_Request(parameters, curdir, form, user_info=None):
    """
    This function is used at the time of a "request for approval" submission
    in order to register the request in the WebSubmit "Approvals" DB
    (sbmAPPROVAL).
    At the time of approval request, the document could be in one of
    several different approval "states" and depending upon that state,
    the action taken by this function differs. The states are as
    follows:
          * Approval for the document has never been requested.
             -> In this case, a new row for the document is inserted into the
                approvals table with the "waiting" state.
          * Approval of the document has previously been requested and it is
            still in the "waiting" state.
             -> In this case, the date of last request for the document is
                updated in the approvals table.
          * Approval of the document has previously been requested, but the
            document was rejected.
             -> In this case, the function will halt the submission with a
                message informing the user that approval of the document was
                already rejected.
          * Approval of the document has previously been requested and it has
            been approved.
             -> In this case, the function will halt the submission with a
                message informing the user that the document has already
                been approved and that no further action is necessary.
          * Approval of the document has previously been requested, but the
            request withdrawn.
             -> In this case, the function will update the "approval status"
                of the document to "waiting" and will return a message
                informing the user that although the approval request was
                previously withdrawn, it has been requested again.

    @param categ_file_appreq: (string) - some document types are
           separated into different categories, each of which has its own
           referee(s).
           In such document types, it's necessary to know the document-
           type's category in order to choose the referee.
           This parameter provides a means by which the category information
           can be extracted from a file in the current submission's working
           directory. It should therefore be a filename.

    @param categ_rnseek_appreq: (string) - some document types are
           separated into different categories, each of which has its own
           referee(s).
           In such document types, it's necessary to know the document-
           type's category in order to choose the referee.
           This parameter provides a means by which the category information
           can be extracted from the document's reference number.
           It is infact a string that will be compiled into a regexp and
           an attempt will be made to match it agains the document's reference
           number starting from the left-most position.
           The only pre-requisite is that the segment in which the category is
           sought should be indicated with <CATEGORY>.
           Thus, an example might be as follows:
              ATL(-COM)?-<CATEGORY>-.+
           This would allow "PHYS" in the following reference number to be
           recognised as the category:
              ATL-COM-PHYS-2008-001

    @param note_file_appreq: (string) - the name of the file from which
           any "notes" to be added into the approval request's "note" field in
           the database are to be read. (File must be in the current submission's
           working directory.)

    @return: (string) - a message for the user.

    @Exceptions raised: + InvenioWebSubmitFunctionStop when the submission
                          should be halted.
                        + InvenioWebSubmitFunctionError when an unexpected
                          error has been encountered and execution cannot
                          continue.
    """
    ## Get the reference number (as global rn - sorry!) and the document type:
    global rn
    doctype = form['doctype']

    ## A string variable to contain any information that should be displayed
    ## in the user's browser:
    info_out = ""

    ########
    ## Get the parameters from the list:

    ########
    ## Get the name of the category file:
    #######
    try:
        ## If it has been provided, get the name of the file in which the
        ## category is stored:
        category_file = parameters["categ_file_appreq"]
    except KeyError:
        ## No value given for the category file:
        category_file = None
    else:
        if category_file is not None:
            category_file = str(category_file)
            category_file = os.path.basename(category_file).strip()
            if category_file == "":
                category_file = None
    ########
    ## Get the name of the "note" file and read its value:
    ########
    note = "" ## variable to hold a note to be added to the approval request's
              ## details in the DB.
    try:
        note_file = parameters["note_file_appreq"]
    except KeyError:
        ## No value given for the category file:
        note_file = None
    else:
        if note_file is not None:
            note_file = str(note_file)
            note_file = os.path.basename(note_file).strip()
            if note_file == "":
                note_file = None
    if note_file is not None:
        note = ParamFromFile("%s/%s" % (curdir, note_file))
    ########
    ## Get the regexp that is used to find the category in the report number:
    ########
    try:
        ## If it has been provided, get the regexp used for identifying
        ## a document-type's category from its reference number:
        category_rn_regexp = parameters["categ_rnseek_appreq"]
    except KeyError:
        ## No value given for the category regexp:
        category_rn_regexp = None
    else:
        if category_rn_regexp is not None:
            category_rn_regexp = str(category_rn_regexp).strip()
        if category_rn_regexp == "":
            category_rn_regexp = None

    #######
    ## Resolve the document type's category:
    ##
    ## This is a long process. The end result is that the category is extracted
    ## either from a file in curdir, or from the report number.
    ## If it's taken from the report number, the admin must configure the
    ## function to accept a regular expression that is used to find the
    ## category in the report number.
    ##
    if category_file is not None and category_rn_regexp is not None:
        ## It is not valid to have both a category file and a pattern
        ## describing how to extract the category from a report number.
        ## raise an InvenioWebSubmitFunctionError
        msg = "Error in Register_Approval_Request function: received " \
              "instructions to search for the document's category in " \
              "both its report number AND in a category file. Could " \
              "not determine which to use - please notify the " \
              "administrator."
        raise InvenioWebSubmitFunctionError(msg)
    elif category_file is not None:
        ## Attempt to recover the category information from a file in the
        ## current submission's working directory:
        category = ParamFromFile("%s/%s" % (curdir, category_file))
        if category is not None:
            category = category.strip()
        if category in (None, ""):
            ## The category cannot be resolved.
            msg = "Error in Register_Approval_Request function: received " \
                  "instructions to search for the document's category in " \
                  "a category file, but could not recover the category " \
                  "from that file. An approval request therefore cannot " \
                  "be registered for the document."
            raise InvenioWebSubmitFunctionError(msg)
    elif category_rn_regexp is not None:
        ## Attempt to recover the category information from the document's
        ## reference number using the regexp in category_rn_regexp:
        ##
        ## Does the category regexp contain the key-phrase "<CATEG>"?
        if category_rn_regexp.find("<CATEG>") != -1:
            ## Yes. Replace "<CATEG>" with "(?P<category>.+?)".
            ## For example, this:
            ##    ATL(-COM)?-<CATEG>-
            ## Will be transformed into this:
            ##    ATL(-COM)?-(?P<category>.+?)-
            category_rn_final_regexp = \
                category_rn_regexp.replace("<CATEG>", r"(?P<category>.+?)", 1)
        else:
            ## The regexp for category didn't contain "<CATEG>", but this is
            ## mandatory.
            msg = "Error in Register_Approval_Request function: The " \
                  "[%(doctype)s] submission has been configured to search " \
                  "for the document type's category in its reference number, " \
                  "using a poorly formed search expression (no marker for " \
                  "the category was present.) Since the document's category " \
                  "therefore cannot be retrieved, an approval request cannot " \
                  "be registered for it. Please report this problem to the " \
                  "administrator." \
                  % { 'doctype' : doctype, }
            raise InvenioWebSubmitFunctionError(msg)
        ##
        try:
            ## Attempt to compile the regexp for finding the category:
            re_categ_from_rn = re.compile(category_rn_final_regexp)
        except sre_constants.error:
            ## The expression passed to this function could not be compiled
            ## into a regexp. Register this exception and raise an
            ## InvenioWebSubmitFunctionError:
            exception_prefix = "Error in Register_Approval_Request function: " \
                               "The [%(doctype)s] submission has been " \
                               "configured to search for the document type's " \
                               "category in its reference number, using the " \
                               "following regexp: /%(regexp)s/. This regexp, " \
                               "however, could not be compiled correctly " \
                               "(created it from %(categ-search-term)s.)" \
                               % { 'doctype'       : doctype, \
                                   'regexp'        : category_rn_final_regexp, \
                                   'categ-search-term' : category_rn_regexp, }
            register_exception(prefix=exception_prefix)
            msg = "Error in Register_Approval_Request function: The " \
                  "[%(doctype)s] submission has been configured to search " \
                  "for the document type's category in its reference number, " \
                  "using a poorly formed search expression. Since the " \
                  "document's category therefore cannot be retrieved, an " \
                  "approval request cannot be registered for it. Please " \
                  "report this problem to the administrator." \
                  % { 'doctype' : doctype, }
            raise InvenioWebSubmitFunctionError(msg)
        else:
            ## Now attempt to recover the category from the RN string:
            m_categ_from_rn = re_categ_from_rn.match(rn)
            if m_categ_from_rn is not None:
                ## The pattern matched in the string.
                ## Extract the category from the match:
                try:
                    category = m_categ_from_rn.group("category")
                except IndexError:
                    ## There was no "category" group. That group is mandatory.
                    exception_prefix = \
                       "Error in Register_Approval_Request function: The " \
                       "[%(doctype)s] submission has been configured to " \
                       "search for the document type's category in its " \
                       "reference number using the following regexp: " \
                       "/%(regexp)s/. The search produced a match, but " \
                       "there was no \"category\" group in the match " \
                       "object although this group is mandatory. The " \
                       "regexp was compiled from the following string: " \
                       "[%(categ-search-term)s]." \
                       % { 'doctype'           : doctype, \
                           'regexp'            : category_rn_final_regexp, \
                           'categ-search-term' : category_rn_regexp, }
                    register_exception(prefix=exception_prefix)
                    msg = "Error in Register_Approval_Request function: The " \
                          "[%(doctype)s] submission has been configured to " \
                          "search for the document type's category in its " \
                          "reference number, using a poorly formed search " \
                          "expression (there was no category marker). Since " \
                          "the document's category therefore cannot be " \
                          "retrieved, an approval request cannot be " \
                          "registered for it. Please report this problem to " \
                          "the administrator." \
                          % { 'doctype' : doctype, }
                    raise InvenioWebSubmitFunctionError(msg)
                else:
                    category = category.strip()
                    if category == "":
                        msg = "Error in Register_Approval_Request function: " \
                              "The [%(doctype)s] submission has been " \
                              "configured to search for the document type's " \
                              "category in its reference number, but no " \
                              "category was found. The request for approval " \
                              "cannot be registered. Please report this " \
                              "problem to the administrator." \
                              % { 'doctype' : doctype, }
                        raise InvenioWebSubmitFunctionError(msg)
            else:
                ## No match. Cannot find the category and therefore cannot
                ## continue:
                msg = "Error in Register_Approval_Request function: The " \
                      "[%(doctype)s] submission has been configured to " \
                      "search for the document type's category in its " \
                      "reference number, but no match was made. The request " \
                      "for approval cannot be registered. Please report " \
                      "this problem to the administrator." \
                      % { 'doctype' : doctype, }
                raise InvenioWebSubmitFunctionError(msg)
    else:
        ## The document type has no category.
        category = ""
    ##
    ## End of category recovery
    #######

    #######
    ##
    ## Query the "approvals" DB table to determine whether approval of this
    ## document has already been requested:
    approval_status = get_simple_approval_status(doctype, rn)
    if approval_status is None:
        ## Approval has never been requested for this document. Register the
        ## new request.
        register_new_approval_request(doctype, category, rn, note)
    elif approval_status.lower() == "approved":
        ## This document has already been approved. Stop and inform the user
        ## of this.
        msg = """
<br />
<div>
<span style="color: red;">Note:</span> The document %s has already been
 Approved.<br />
No further approval is necessary - no further action will be taken.
</div>
""" % cgi.escape(rn)
        raise InvenioWebSubmitFunctionStop(msg)
    elif approval_status.lower() == "rejected":
        ## This document has already been rejected. Stop and inform the user
        ## of this.
        msg = """
<br />
<div>
<span style="color: red;">Note:</span> Approval of the document [%s] has
 previously been rejected.<br />
Approval has NOT been resubmitted and no further action will be taken.<br />
If you believe this to be an error, please contact %s, quoting the<br />
document's report-number [%s] and describing the problem.
</div>
""" % (cgi.escape(rn), cgi.escape(CFG_SITE_SUPPORT_EMAIL), cgi.escape(rn))
        raise InvenioWebSubmitFunctionStop(msg)
    elif approval_status.lower() == "withdrawn":
        ## An approval request for this document type was already made at some
        ## point. Update it and inform the user that the approval request has
        ## been logged despite having been previously withdrawn:
        update_approval_request_status(doctype, rn, note=note)
        info_out += """
<br />
<div>
<span style="color: red;">Note:</span> An approval request for this document
 had previously been withdrawn.<br />
Approval has been requested again.
</div>
"""
    elif approval_status.lower() == "waiting":
        ## An approval request for this document has already been registered
        ## but it is awaiting a decision.
        ## Update the date/time of the last request and inform the user that
        ## although approval had already been requested for this document,
        ## their approval request has been made again.
        update_approval_request_status(doctype, rn, note=note)
        info_out += """
<br />
<div>
<span style="color: red;">Note:</span> Although a request for the approval
 of this document had already been submitted, your new request has been
 registered.<br />
</div>
"""
    else:
        ## The document had an unrecognised "status". Raise an error.
        msg = "Error in Register_Approval_Request function: The " \
              "[%(reportnum)s] document has an unknown approval status " \
              "(%(status)s). Unable to request its approval. Please report " \
              "this problem to the administrator." \
              % { 'reportnum' : rn,
                  'status'    : approval_status, }
        raise InvenioWebSubmitFunctionError(msg)
    ##
    ## Finished - return any message to be displayed on the user's screen.
    return info_out
