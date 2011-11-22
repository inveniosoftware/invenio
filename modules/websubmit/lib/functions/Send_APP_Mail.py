## This file is part of Invenio.
## Copyright (C) 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

__revision__ = "$Id$"

   ## Description:   function Send_APP_Mail
   ##                This function send an email informing the original
   ##             submitter of a document that the referee has approved/
   ##             rejected the document. The email is also sent to the
   ##             referee for checking.
   ## Author:         T.Baron
   ## PARAMETERS:
   ##                newrnin: name of the file containing the 2nd reference
   ##             addressesAPP: email addresses to which the email will
   ##                    be sent (additionally to the author)
   ##             categformatAPP: variable needed to derive the addresses
   ##                    mentioned above

import os
import re

from invenio.config import CFG_SITE_NAME, \
     CFG_SITE_URL, \
     CFG_SITE_SUPPORT_EMAIL,  \
     CFG_CERN_SITE, \
     CFG_SITE_RECORD
from invenio.access_control_admin import acc_get_role_users, acc_get_role_id
from invenio.dbquery import run_sql
from invenio.websubmit_config import CFG_WEBSUBMIT_COPY_MAILS_TO_ADMIN
from invenio.mailutils import send_email
from invenio.errorlib import register_exception
from invenio.search_engine import print_record


## The field in which to search for the record submitter/owner's email address:
if CFG_CERN_SITE:
    ## This is a CERN site - we use 859__f for submitter/record owner's email:
    CFG_WEBSUBMIT_RECORD_OWNER_EMAIL = "859__f"
else:
    ## Non-CERN site. Use 8560_f for submitter/record owner's email:
    CFG_WEBSUBMIT_RECORD_OWNER_EMAIL = "8560_f"

def Send_APP_Mail (parameters, curdir, form, user_info=None):
    """
    This function send an email informing the original submitter of a
    document that the referee has approved/ rejected the document. The
    email is also sent to the referee for checking.

    Parameters:

       * addressesAPP: email addresses of the people who will receive
         this email (comma separated list). this parameter may contain
         the <CATEG> string. In which case the variable computed from
         the [categformatAFP] parameter replaces this string.
         eg.: "<CATEG>-email@cern.ch"

       * categformatAPP contains a regular expression used to compute
         the category of the document given the reference of the
         document.
         eg.: if [categformatAFP]="TEST-<CATEG>-.*" and the reference
         of the document is "TEST-CATEGORY1-2001-001", then the computed
         category equals "CATEGORY1"

       * newrnin: Name of the file containing the 2nd reference of the
                  approved document (if any).

       * edsrn: Name of the file containing the reference of the
                approved document.
    """
    global titlevalue,authorvalue,sysno,rn
    FROMADDR = '%s Submission Engine <%s>' % (CFG_SITE_NAME,CFG_SITE_SUPPORT_EMAIL)
    doctype = form['doctype']
    titlevalue = titlevalue.replace("\n"," ")
    authorvalue = authorvalue.replace("\n","; ")
    # variables declaration
    categformat = parameters['categformatAPP']
    otheraddresses = parameters['addressesAPP']
    newrnpath = parameters['newrnin']
    ## Get the name of the decision file:
    try:
        decision_filename = parameters['decision_file']
    except KeyError:
        decision_filename = ""
    ## Get the name of the comments file:
    try:
        comments_filename = parameters['comments_file']
    except KeyError:
        comments_filename = ""

    ## Now try to read the comments from the comments_filename:
    if comments_filename in (None, "", "NULL"):
        ## We don't have a name for the comments file.
        ## For backward compatibility reasons, try to read the comments from
        ## a file called 'COM' in curdir:
        if os.path.exists("%s/COM" % curdir):
            try:
                fh_comments = open("%s/COM" % curdir, "r")
                comment = fh_comments.read()
                fh_comments.close()
            except IOError:
                ## Unable to open the comments file
                exception_prefix = "Error in WebSubmit function " \
                                   "Send_APP_Mail. Tried to open " \
                                   "comments file [%s/COM] but was " \
                                   "unable to." % curdir
                register_exception(prefix=exception_prefix)
                comment = ""
            else:
                comment = comment.strip()
        else:
            comment = ""
    else:
        ## Try to read the comments from the comments file:
        if os.path.exists("%s/%s" % (curdir, comments_filename)):
            try:
                fh_comments = open("%s/%s" % (curdir, comments_filename), "r")
                comment = fh_comments.read()
                fh_comments.close()
            except IOError:
                ## Oops, unable to open the comments file.
                comment = ""
                exception_prefix = "Error in WebSubmit function " \
                                "Send_APP_Mail. Tried to open comments " \
                                "file [%s/%s] but was unable to." \
                                % (curdir, comments_filename)
                register_exception(prefix=exception_prefix)
            else:
                comment = comment.strip()
        else:
            comment = ""

    ## Now try to read the decision from the decision_filename:
    if decision_filename in (None, "", "NULL"):
        ## We don't have a name for the decision file.
        ## For backward compatibility reasons, try to read the decision from
        ## a file called 'decision' in curdir:
        if os.path.exists("%s/decision" % curdir):
            try:
                fh_decision = open("%s/decision" % curdir, "r")
                decision = fh_decision.read()
                fh_decision.close()
            except IOError:
                ## Unable to open the decision file
                exception_prefix = "Error in WebSubmit function " \
                                   "Send_APP_Mail. Tried to open " \
                                   "decision file [%s/decision] but was " \
                                   "unable to." % curdir
                register_exception(prefix=exception_prefix)
                decision = ""
            else:
                decision = decision.strip()
        else:
            decision = ""
    else:
        ## Try to read the decision from the decision file:
        try:
            fh_decision = open("%s/%s" % (curdir, decision_filename), "r")
            decision = fh_decision.read()
            fh_decision.close()
        except IOError:
            ## Oops, unable to open the decision file.
            decision = ""
            exception_prefix = "Error in WebSubmit function " \
                               "Send_APP_Mail. Tried to open decision " \
                               "file [%s/%s] but was unable to." \
                               % (curdir, decision_filename)
            register_exception(prefix=exception_prefix)
        else:
            decision = decision.strip()

    if os.path.exists("%s/%s" % (curdir,newrnpath)):
        fp = open("%s/%s" % (curdir,newrnpath) , "r")
        newrn = fp.read()
        fp.close()
    else:
        newrn = ""
    # Document name
    res = run_sql("SELECT ldocname FROM sbmDOCTYPE WHERE sdocname=%s", (doctype,))
    docname = res[0][0]
    # retrieve category
    categformat = categformat.replace("<CATEG>", "([^-]*)")
    m_categ_search = re.match(categformat, rn)
    if m_categ_search is not None:
        if len(m_categ_search.groups()) > 0:
            ## Found a match for the category of this document. Get it:
            category = m_categ_search.group(1)
        else:
            ## This document has no category.
            category = "unknown"
    else:
        category = "unknown"
    ## Get the referee email address:
    if CFG_CERN_SITE:
        ## The referees system in CERN now works with listbox membership.
        ## List names should take the format
        ## "service-cds-referee-doctype-category@cern.ch"
        ## Make sure that your list exists!
        ## FIXME - to be replaced by a mailing alias in webaccess in the
        ## future.
        referee_listname = "service-cds-referee-%s" % doctype.lower()
        if category != "":
            referee_listname += "-%s" % category.lower()
        referee_listname += "@cern.ch"
        addresses = referee_listname
    else:
        # Build referee's email address
        refereeaddress = ""
        # Try to retrieve the referee's email from the referee's database
        for user in acc_get_role_users(acc_get_role_id("referee_%s_%s" % (doctype,category))):
            refereeaddress += user[1] + ","
        # And if there is a general referee
        for user in acc_get_role_users(acc_get_role_id("referee_%s_*" % doctype)):
            refereeaddress += user[1] + ","
        refereeaddress = re.sub(",$","",refereeaddress)
        # Creation of the mail for the referee
        otheraddresses = otheraddresses.replace("<CATEG>",category)
        addresses = ""
        if refereeaddress != "":
            addresses = refereeaddress + ","
        if otheraddresses != "":
            addresses += otheraddresses
        else:
            addresses = re.sub(",$","",addresses)
    ## Add the record's submitter(s) into the list of recipients:
    ## Get the email address(es) of the record submitter(s)/owner(s) from
    ## the record itself:
    record_owners = print_record(sysno, 'tm', \
                                 [CFG_WEBSUBMIT_RECORD_OWNER_EMAIL]).strip()
    if record_owners != "":
        record_owners_list = record_owners.split("\n")
        record_owners_list = [email.lower().strip() \
                              for email in record_owners_list]
    else:
        record_owners_list = []
    record_owners = ",".join([owner for owner in record_owners_list])
    if record_owners != "":
        addresses += ",%s" % record_owners

    if decision == "approve":
        mailtitle = "%s has been approved" % rn
        mailbody = "The %s %s has been approved." % (docname,rn)
        mailbody += "\nIt will soon be accessible here:\n\n<%s/%s/%s>" % (CFG_SITE_URL,CFG_SITE_RECORD,sysno)
    else:
        mailtitle = "%s has been rejected" % rn
        mailbody = "The %s %s has been rejected." % (docname,rn)
    if rn != newrn and decision == "approve" and newrn != "":
        mailbody += "\n\nIts new reference number is: %s" % newrn
    mailbody += "\n\nTitle: %s\n\nAuthor(s): %s\n\n" % (titlevalue,authorvalue)
    if comment != "":
        mailbody += "Comments from the referee:\n%s\n" % comment
    # Send mail to referee if any recipients or copy to admin
    if addresses or CFG_WEBSUBMIT_COPY_MAILS_TO_ADMIN:
        send_email(FROMADDR,addresses,mailtitle,mailbody, copy_to_admin=CFG_WEBSUBMIT_COPY_MAILS_TO_ADMIN)
    return ""
