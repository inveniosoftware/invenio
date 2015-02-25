# This file is part of Invenio.
# Copyright (C) 2008, 2009, 2010, 2011 CERN.
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

"""Mail_Approval_Request_to_Referee: A function to send an email to the referee
   of a document informing him/her that a request for its approval has been
   submitted by the user.
"""


__revision__ = "$Id$"

import os
import re
import sre_constants
from invenio.legacy.websubmit.db_layer import get_approval_request_notes
from invenio.legacy.websubmit.config import InvenioWebSubmitFunctionError, \
                                     CFG_WEBSUBMIT_COPY_MAILS_TO_ADMIN
from invenio.config import CFG_CERN_SITE, \
                           CFG_SITE_NAME, \
                           CFG_SITE_URL, \
                           CFG_SITE_SUPPORT_EMAIL, \
                           CFG_SITE_RECORD
from invenio.modules.access.control import acc_get_role_users, acc_get_role_id
from invenio.legacy.websubmit.functions.Shared_Functions import ParamFromFile
from invenio.ext.logging import register_exception
from invenio.legacy.search_engine import print_record
from invenio.ext.email import send_email


CFG_MAIL_BODY = """
A request for the approval of a document in the %(site-name)s has been
made and requires your attention as a referee.  The details are as
follows:

 Reference Number: [%(report-number)s]
 Title: %(title)s
 Author(s): %(authors)s

You can see the details of the record at the following address:
 <%(site-url)s/%(CFG_SITE_RECORD)s/%(record-id)s>

Please register your decision by following the instructions at the
following address:
 <%(site-url)s/submit/direct?%(report-number-fieldname)s=%(report-number)s&sub=%(approval-action)s%(doctype)s&combo%(doctype)s=%(category)s>

Below, you may find some additional information about the approval request:

%(notes)s
"""



def Mail_Approval_Request_to_Referee(parameters, curdir, form, user_info=None):
    """
    This function sends an email to the referee of a document informing
    him/her that a request for its approval has been submitted by the
    user.

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

    @param edsrn: (string) - the name of the field in which the report
          number should be placed when the referee visits the form for making
          a decision.

    @return: (string) - empty string.
    """
    ## Get the reference number (as global rn - sorry!) and the document type:
    global sysno, rn
    doctype = form['doctype']

    ########
    ## Get the parameters from the list:

    ########
    ## Get the name of the report-number file:
    ########
    try:
        edsrn_file = parameters["edsrn"]
    except KeyError:
        ## No value given for the edsrn file:
        msg = "Error in Mail_Approval_Request_to_Referee function: unable " \
              "to determine the name of the file in which the document's " \
              "report number should be stored."
        raise InvenioWebSubmitFunctionError(msg)
    else:
        edsrn_file = str(edsrn_file)
        edsrn_file = os.path.basename(edsrn_file).strip()
        if edsrn_file == "":
            msg = "Error in Mail_Approval_Request_to_Referee function: " \
                  "unable to determine the name of the file in which " \
                  "the document's report number should be stored."
            raise InvenioWebSubmitFunctionError(msg)
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
    ## Get the title and author(s) from the record:
    #######
    ## Author(s):
    rec_authors = ""
    rec_first_author    = print_record(int(sysno), 'tm', "100__a")
    rec_other_authors   = print_record(int(sysno), 'tm', "700__a")
    if rec_first_author != "":
        rec_authors += "".join(["%s\n" % author.strip() for \
                                author in rec_first_author.split("\n")])
    if rec_other_authors != "":
        rec_authors += "".join(["%s\n" % author.strip() for \
                                author in rec_other_authors.split("\n")])
    ## Title:
    rec_title = "".join(["%s\n" % title.strip() for title in \
                          print_record(int(sysno), 'tm', "245__a").split("\n")])
    ##
    #######
    ## the normal approval action
    approve_act = 'APP'
    ## Get notes about the approval request:
    approval_notes = get_approval_request_notes(doctype, rn)
    ## Get the referee email address:
    if CFG_CERN_SITE:
        ## The referees system in CERN now works with listbox membership.
        ## List names should take the format
        ## "service-cds-referee-doctype-category@cern.ch"
        ## Make sure that your list exists!
        ## FIXME - to be replaced by a mailing alias in webaccess in the
        ## future.
        if doctype == 'ATN':  ## Special case of 'RPR' action for doctype ATN
            action = ParamFromFile("%s/%s" % (curdir,'act')).strip()
            if action == 'RPR':
                notetype = ParamFromFile("%s/%s" % (curdir,'ATN_NOTETYPE')).strip()
                if notetype not in ('SLIDE','PROC'):
                    raise InvenioWebSubmitFunctionError('ERROR function Mail_Approval_Request_to_Referee:: do not recognize notetype ' + notetype)
                if notetype == 'PROC':
                    approve_act = 'APR'  # RPR PROC requires APR action to approve
                    referee_listname = "service-cds-referee-atn-proc@cern.ch"
                elif notetype == 'SLIDE':  ## SLIDES approval
                    approve_act = 'APS'  # RPR SLIDE requires APS action to approve
                    referee_listname = "atlas-speakers-comm@cern.ch"
                else:
                    raise InvenioWebSubmitFunctionError('ERROR function Mail_Approval_Request_to_Referee:: do not understand notetype: ' +notetype)
            else:
                referee_listname = "service-cds-referee-%s" % doctype.lower()
                if category != "":
                    referee_listname += "-%s" % category.lower()
            mailto_addresses = referee_listname + "@cern.ch"
            if category == 'CDSTEST':
                referee_listname = "service-cds-referee-%s" % doctype.lower()
                referee_listname += "-%s" % category.lower()
                mailto_addresses = referee_listname + "@cern.ch"
    else:
        referee_address = ""
        ## Try to retrieve the referee's email from the referee's database:
        for user in \
            acc_get_role_users(acc_get_role_id("referee_%s_%s" \
                                               % (doctype, category))):
            referee_address += user[1] + ","
        ## And if there are general referees:
        for user in \
            acc_get_role_users(acc_get_role_id("referee_%s_*" % doctype)):
            referee_address += user[1] + ","
        referee_address = re.sub(",$", "", referee_address)
        # Creation of the mail for the referee
        mailto_addresses = ""
        if referee_address != "":
            mailto_addresses = referee_address + ","
        else:
            mailto_addresses = re.sub(",$", "", mailto_addresses)
    ##
    ## Send the email:
    mail_subj = "Request for approval of [%s]" % rn
    mail_body = CFG_MAIL_BODY % \
                { 'site-name'               : CFG_SITE_NAME,
                  'CFG_SITE_RECORD'          : CFG_SITE_RECORD,
                  'report-number-fieldname' : edsrn_file,
                  'report-number'           : rn,
                  'title'                   : rec_title,
                  'authors'                 : rec_authors,
                  'site-url'                : CFG_SITE_URL,
                  'record-id'               : sysno,
                  'approval-action'         : approve_act,
                  'doctype'                 : doctype,
                  'notes'                   : approval_notes,
                  'category'                : category,
                }
    send_email(CFG_SITE_SUPPORT_EMAIL,
               mailto_addresses,
               mail_subj,
               mail_body,
               copy_to_admin=CFG_WEBSUBMIT_COPY_MAILS_TO_ADMIN)
    ##
    return ""
