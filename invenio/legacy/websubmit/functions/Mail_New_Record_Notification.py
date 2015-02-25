# -*- coding: utf-8 -*-

# This file is part of Invenio.
# Copyright (C) 2007, 2008, 2010, 2011 CERN.
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

"""This module contains the WebSubmit function "Mail_New_Record_Notification",
   which should be called when a new record has been submitted to the repository
   and notified of the fact should be sent by mail to the submitters/requester/
   admins/other general managers.
"""

__revision__ = "$Id$"

import os
from invenio.config import CFG_SITE_NAME, CFG_SITE_SUPPORT_EMAIL, CFG_SITE_URL, CFG_SITE_ADMIN_EMAIL, \
    CFG_SITE_RECORD
from invenio.legacy.webuser import email_valid_p
from invenio.legacy.websubmit.config import CFG_WEBSUBMIT_COPY_MAILS_TO_ADMIN
from invenio.legacy.websubmit.functions.Shared_Functions import ParamFromFile
from invenio.ext.email import scheduled_send_email
from invenio.legacy.bibsched.bibtask import bibtask_allocate_sequenceid

CFG_EMAIL_FROM_ADDRESS = '%s Submission Engine <%s>' % (CFG_SITE_NAME, CFG_SITE_SUPPORT_EMAIL)

def Mail_New_Record_Notification(parameters, curdir, form, user_info=None):
    """
    This function sends a mail giving notification about the submission
    of a new item to the relevant recipients, including:
       + The record's Submitter(s);
       + The site ADMIN;
       + The record-type's "managers" (signified by the "submit_managers"
           parameter);

    The mail contains details of the new item's reference number(s), its
    title and its author(s). It also contains a link to the item in the
    Invenio repository.

    @param parameters: (dictionary) - contains the following parameter
         strings used by this function:

          + item_status: (string) - the status of the new item. It can be
            either "ADDED" (in which case the new item has been integrated
            into the repository), or "APPROVAL" (in which case the item is
            awaiting a referee's approval before being integrated into the
            repository, and the mail should state this fact);

          + mail_submitters: (string) - a flag containing "Y" or "N" (defaulting
            to "Y"). Determines whether or not the notification mail will be
            sent to the submitters;

          + item_managers:    (string) - a comma-separated list of email
            addresses, each of which corresponds to a "manager" for the class
            of item that has been submitted. These managers will receive the
            notification message sent by this function;

          + author_file: (string) - the name of a file that contains the names
            of the item's authors (one author per line);

          + title_file:  (string) - the name of a file that contains the title
            of the new item;

          + owners_file: (string) - the name of a file that contains the email
            addresses of the "owners" of the submitted item. I.e. those who
            will be classed as "submitters" of the item and will therefore
            have modification rights over it. The mail will be sent to these
            people. There should be one email-address per line in this file;

          + rn_file1: (string) - the name of the the file containing the item's
            principal reference number;

          + rn_file2: (string) - the name of the file containing the item's
            additional reference number(s) (e.g. sometimes two reference numbers
            are allocated during the submission process;

       @param curdir: (string) - the current submission's working directory. All
        files containing data related to the submission are stored here and
        therefore all of the files referred to in the "parameters" dictionary
        are considered to be within "curdir";

       @param form: (string) - a dictionary-like structure containing the fields
        that were present in the WebSubmit submission form;

       @return: (string) - an empty string;
    """
    global sysno ## (I'm really sorry for that! :-O )
    sequence_id = bibtask_allocate_sequenceid(curdir)
    ## Read items from the parameters array into local vars:
    item_status     = parameters["item_status"]
    mail_submitters = parameters["mail_submitters"]
    item_managers   = parameters["item_managers"]
    author_file     = parameters["author_file"]
    title_file      = parameters["title_file"]
    owners_file     = parameters["owners_file"]
    rn_file1        = parameters["rn_file1"]
    rn_file2        = parameters["rn_file2"]

    ## Now wash the parameters' values:
    ##
    ## item_status:
    try:
        ## If item_status isn't "added" or "approval", make it "added" by
        ## default. Else, keep its value:
        item_status = (item_status.upper() in ("ADDED", "APPROVAL") \
                       and item_status.upper()) or "ADDED"
    except AttributeError:
        ## Oops - item_status wasn't a string (NoneType?) Anyway, default
        ## it to "ADDED".
        item_status = "ADDED"

    ## mail_submitters:
    try:
        ## If mail_submitters isn't "Y" or "N", make it "Y" by
        ## default. Else, keep its value:
        mail_submitters = (mail_submitters.upper() in ("Y", "N") \
                       and mail_submitters.upper()) or "Y"
    except AttributeError:
        ## Oops - mail_submitters wasn't a string (NoneType?) Anyway, default
        ## it to "Y".
        mail_submitters = "Y"

    ## item_managers:
    ## A string in which the item_managers' email addresses will be stored:
    managers_email = ""
    try:
        ## We assume that the email addresses of item managers are
        ## separated by commas.
        item_managers_list = item_managers.split(",")
        for manager in item_managers_list:
            manager_address = manager.strip()
            ## Test that this manager's email address is OK, adding it if so:
            if email_valid_p(manager_address):
                ## This address is OK - add it to the string of manager
                ## addresses:
                managers_email += "%s," % manager_address
        ## Strip the trailing comma from managers_email (if there is one):
        managers_email = managers_email.strip().rstrip(",")
    except AttributeError:
        ## Oops - item_managers doesn't seem to be a string? Treat it as
        ## though it were empty:
        managers_email = ""

    ## author_file:
    authors = ""
    try:
        ## Read in the authors from author_file, putting them into the "authors"
        ## variable, one per line:
        fp_author_file = open("%s/%s" % (curdir, author_file), "r")
        for author in fp_author_file:
            authors += "%s\n" % author.strip()
        fp_author_file.close()
    except IOError:
        ## Unable to correctly read from "author_file", Skip it as though
        ## there were no authors:
        authors = "-"

    ## title_file:
    title = ""
    try:
        ## Read in the lines from title_file, putting them into the "title"
        ## variable on one line:
        fp_title_file = open("%s/%s" % (curdir, title_file), "r")
        for line in fp_title_file:
            title += "%s " % line.strip()
        fp_title_file.close()
        title = title.strip()
    except IOError:
        ## Unable to correctly read from "title_file", Skip it as though
        ## there were no title:
        title = "-"

    ## owners_file:
    ## A string in which the item_owners' email addresses will be stored:
    owners_email = ""
    try:
        fp_owners_file = open("%s/%s" % (curdir, owners_file), "r")
        for line in fp_owners_file:
            owner_address = line.strip()
            ## Test that this owner's email address is OK, adding it if so:
            if email_valid_p(owner_address):
                ## This address is OK - add it to the string of item owner
                ## addresses:
                owners_email += "%s," % owner_address
        ## Strip the trailing comma from owners_email (if there is one):
        owners_email = owners_email.strip().rstrip(",")
    except IOError:
        ## Unable to correctly read from "owners_file", Skip it as though
        ## there were no title:
        owners_email = ""

    ## Add "SuE" (the submitter) into the list of document "owners":
    try:
        fp_sue = open("%s/SuE" % curdir, "r")
        sue = fp_sue.readline()
        fp_sue.close()
    except IOError:
        sue = ""
    else:
        if sue.lower() not in owners_email.lower().split(","):
            ## The submitter is not listed in the "owners" mails,
            ## add her:
            owners_email = "%s,%s" % (sue, owners_email)
            owners_email = owners_email.strip().rstrip(",")

    ## rn_file1 & rn_file2:
    reference_numbers = ""
    try:
        fp_rnfile1 = open("%s/%s" % (curdir, rn_file1), "r")
        for line in fp_rnfile1:
            reference_number = line.strip()
            reference_number = \
               reference_number.replace("\n", "").replace("\r", "").\
               replace(" ", "")
            if reference_number != "":
                ## Add this reference number into the "reference numbers"
                ## variable:
                reference_numbers += "%s " % reference_number
        fp_rnfile1.close()
    except IOError:
        reference_numbers = ""
    try:
        fp_rnfile2 = open("%s/%s" % (curdir, rn_file2), "r")
        for line in fp_rnfile2:
            reference_number = line.strip()
            reference_number = \
               reference_number.replace("\n", "").replace("\r", "").\
               replace(" ", "")
            if reference_number != "":
                ## Add this reference number into the "reference numbers"
                ## variable:
                reference_numbers += "%s " % reference_number
        fp_rnfile2.close()
    except IOError:
        pass
    ## Strip any trailing whitespace from the reference numbers:
    reference_numbers = reference_numbers.strip()

    ## Now build the email from the information we've collected:
    email_txt = """
The following item has been submitted to %(sitename)s:
   Reference(s): %(reference)s
   Title:        %(title)s
   Author(s):      %(author)s
""" % { 'sitename'   : CFG_SITE_NAME,
        'reference' : reference_numbers,
        'title'     : title,
        'author'    : authors,
      }
    if item_status == "ADDED":
        ## The item has been added into the repository.
        email_txt += """
It will soon be made available and you will be able to check it at the
following URL:

  <%(siteurl)s/%(CFG_SITE_RECORD)s/%(record-id)s>

Please report any problems to <%(sitesupportemail)s>.
""" % { 'siteurl' : CFG_SITE_URL,
        'CFG_SITE_RECORD' : CFG_SITE_RECORD,
        'record-id' : sysno,
        'sitesupportemail' : CFG_SITE_SUPPORT_EMAIL,
      }
    else:
        ## The item has not yet been added - instead it awaits the
        ## approval of a referee. Let the email reflect this detail:
        email_txt += """
The item is now awaiting a referee's approval before being integrated
into the repository. You will be alerted by email as soon as a decision
has been taken.
"""
    ## Finish the message with a signature:
    email_txt += """

Thank you for submitting your item into %(sitename)s.
""" % { 'sitename' : CFG_SITE_NAME, }


    ## Send the email:
    if mail_submitters == "Y" and len(owners_email) != "":
        ## Mail-to is "owners_email":
        if managers_email != "":
            ## Managers should also be copied into the mail:
            owners_email += ",%s" % managers_email
        ## Post the mail:
        scheduled_send_email(CFG_EMAIL_FROM_ADDRESS, owners_email, \
                   "[%s] Submitted" % reference_numbers, \
                   email_txt, copy_to_admin=CFG_WEBSUBMIT_COPY_MAILS_TO_ADMIN, \
                   other_bibtasklet_arguments=['-I', str(sequence_id)])
    elif managers_email != "":
        ## Although it's not desirable to mail the submitters, if "managers"
        ## have been given, it is reasonable to mail them:
        scheduled_send_email(CFG_EMAIL_FROM_ADDRESS, managers_email, \
                   "[%s] Submitted" % reference_numbers, \
                   email_txt, copy_to_admin=CFG_WEBSUBMIT_COPY_MAILS_TO_ADMIN, \
                   other_bibtasklet_arguments=['-I', str(sequence_id)])
    elif CFG_WEBSUBMIT_COPY_MAILS_TO_ADMIN:
        ## We don't want to mail the "owners". Let's mail the admin instead:
        scheduled_send_email(CFG_EMAIL_FROM_ADDRESS, CFG_SITE_ADMIN_EMAIL, \
                   "[%s] Submitted" % reference_numbers, email_txt, \
                   other_bibtasklet_arguments=['-I', str(sequence_id)])

    ## Return an empty string
    return ""
