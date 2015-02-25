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

"""The function in this module sends a mail to the user (and admins if
   required) saying that a record has been deleted from the repository.
"""

__revision__ = "$Id$"

import os
from invenio.ext.logging import register_exception
from invenio.legacy.webuser import email_valid_p
from invenio.config import CFG_SITE_SUPPORT_EMAIL, CFG_SITE_NAME
from invenio.legacy.websubmit.config import CFG_WEBSUBMIT_COPY_MAILS_TO_ADMIN
from invenio.ext.email import send_email

CFG_MAIL_BODY = """
**This is an automated mail from %(site-name)s**

The following record was deleted from %(site-name)s:

 Report number: %(report-number)s

It was deleted by %(deleter)s.

Please note that there may be a short delay before the record
disappears from its collection. It should be gone by tomorrow morning
at the latest.

Thankyou."""


def Send_Delete_Mail(parameters, curdir, form, user_info=None):
    """
    In the event of a record having been deleted, this function is used
    to the mail the submitter (and possibly the record "managers")
    informing them about the record's deletion.

    @parameters:

         + edsrn: The name of the file in the current submission's
                  working directory, in which the record's report number
                  is stored.

         + record_managers: A comma-separated string of the email
                            addresses of the record's managers. If given,
                            they will be (blind*) copied into the mail.
                            * At this time, they are only blind copied
                              because of send_email's behaviour of
                              blind copying everyone if "To" contains
                              multiple addresses. Anyway, blind was
                              wanted . . .

       @return: empty string.

       @Exceptions raised: None.
    """
    ## Get any addresses to which the mail should be copied:
    ## Get report number:
    report_number_file = parameters["edsrn"]
    report_number   = \
     Send_Delete_Mail_read_file("%s/%s" % \
                                (curdir, \
                                 report_number_file)).strip()
    ########
    ## Get the "record_managers" parameter AND WASH THE EMAIL ADDRESSES
    ## TO BE SURE THAT THEY'RE VALID:
    raw_record_managers   = parameters["record_managers"]
    record_managers = ""
    try:
        ## We assume that the email addresses of item managers are
        ## separated by commas.
        raw_record_managers_list = raw_record_managers.split(",")
        for manager in raw_record_managers_list:
            manager_address = manager.strip()
            ## Test that this manager's email address is OK, adding it if so:
            if email_valid_p(manager_address):
                ## This address is OK - add it to the string of manager
                ## addresses:
                record_managers += "%s," % manager_address
        ## Strip the trailing comma from record_managers (if there is one):
        record_managers = record_managers.strip().rstrip(",")
    except AttributeError:
        ## record_managers doesn't seem to be a string? Treat it as
        ## though it were empty:
        record_managers = ""
    ##
    ########
    ## User email address:
    user_email = user_info["email"]

    ## Concatenate the user's email address with the managers' addresses.
    ## Note: What we want to do here is send the mail to the user as "To"
    ## and to the managers as "bcc". At the time of writing though,
    ## send_email doesn't appear to allow email headers. It does have a
    ## strange behaviour though: If "To" contains more than one address,
    ## comma separated, ALL addresses will be put in "bcc" and the mail
    ## will appear to be sent to "undisclosed recipients".
    if record_managers != "":
        if user_email != "guest":
            email_recipients = "%s,%s" % (user_email, record_managers)
        else:
            ## Can't send mails to "guest"! Send only to managers.
            email_recipients = record_managers
    elif user_email == "guest":
        ## The user is a guest and there are no managers to send the mail
        ## to. Drop out quietly.
        return ""
    else:
        ## No managers to send the mail to. Send it only to the user.
        email_recipients = user_email

    mail_subj = "Document %s deleted from %s" \
                % (report_number, CFG_SITE_NAME)
    mail_body = CFG_MAIL_BODY % \
                { 'report-number'   : report_number,
                  'deleter'         : user_email,
                  'site-name'       : CFG_SITE_NAME,
                }
    send_email(CFG_SITE_SUPPORT_EMAIL,
               email_recipients,
               mail_subj,
               mail_body,
               copy_to_admin=CFG_WEBSUBMIT_COPY_MAILS_TO_ADMIN)
    ##
    return ""

def Send_Delete_Mail_read_file(filename):
    """Read a file from a path and return it as a string.
       @param filename: (string) - the full path to the file to be read.
       @return: (string) - the file's contents.
    """
    file_contents = ""
    if os.access("%s" % filename, os.R_OK):
        try:
            file_contents = open("%s" % filename, "r").read()
        except IOError:
            ## There was a problem reading the file. Register the exception
            ## so that the admin is informed.
            err_msg = """Error in a WebSubmit function. An unexpected """ \
                      """error was encountered when trying to read from """ \
                      """the file [%s].""" % filename
            register_exception(prefix=err_msg)
    return file_contents

