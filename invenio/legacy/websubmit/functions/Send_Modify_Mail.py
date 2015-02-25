# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011 CERN.
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

   ## Description:   function Send_Modify_Mail
   ##                This function sends an email saying the document has been
   ##             correctly updated
   ## Author:         T.Baron
   ## PARAMETERS:    addressesMBI: email addresses to which the mail is sent
   ##                fieldnameMBI: name of the file containing the modified
   ##                           fields
   ##             sourceDoc: name of the type of document
   ##             emailFile: name of the file containing the email of the
   ##                        user

import os
import re

from invenio.config import CFG_SITE_URL, \
     CFG_SITE_NAME, \
     CFG_SITE_SUPPORT_EMAIL, \
     CFG_SITE_RECORD
from invenio.legacy.websubmit.config import CFG_WEBSUBMIT_COPY_MAILS_TO_ADMIN
from invenio.ext.email import send_email

def Send_Modify_Mail (parameters, curdir, form, user_info=None):
    """
    This function sends an email to warn people a document has been
    modified and the user his modifications have been taken into
    account..

    Parameters:

       * addressesMBI: email addresses of the people who will receive
                       this email (comma separated list).

       * fieldnameMBI: name of the file containing the modified
                       fields.

       * sourceDoc: Long name for the type of document. This name will
                    be displayed in the mail.

       * emailfile: name of the file in which the email of the modifier
                    will be found.
    """
    FROMADDR = '%s Submission Engine <%s>' % (CFG_SITE_NAME,CFG_SITE_SUPPORT_EMAIL)
    global sysno,rn
    if parameters['emailFile'] is not None and parameters['emailFile']!= "" and os.path.exists("%s/%s" % (curdir,parameters['emailFile'])):
        fp = open("%s/%s" % (curdir,parameters['emailFile']),"r")
        sub = fp.read()
        fp.close()
        sub = sub.replace ("\n","")
    else:
        sub = ""
    # Copy mail to:
    addresses = parameters['addressesMBI']
    addresses = addresses.strip()
    m_fields = parameters['fieldnameMBI']
    type = parameters['sourceDoc']
    rn = re.sub("[\n\r ]+","",rn)
    if os.path.exists("%s/%s" % (curdir,m_fields)):
        fp = open("%s/%s" % (curdir,m_fields),"r")
        fields = fp.read()
        fp.close()
        fields = fields.replace ("\n"," | ")
        fields = re.sub("[| \n\r]+$","",fields)
    else:
        fields = ""
    email_txt = "Dear Sir or Madam, \n%s %s has just been modified.\nModified fields: %s\n\n" % (type,rn,fields)
    if CFG_SITE_URL != "" and sysno != "":
        email_txt += "You can check the modified document here:\n"
        email_txt += "<%s/%s/%s>\n\n" % (CFG_SITE_URL,CFG_SITE_RECORD,sysno)
    email_txt += "Please note that the modifications will be taken into account in a couple of minutes.\n\nBest regards,\nThe %s Server support Team" % CFG_SITE_NAME
    # send the mail if any recipients or copy to admin
    if sub or CFG_WEBSUBMIT_COPY_MAILS_TO_ADMIN:
        send_email(FROMADDR,sub,"%s modified" % rn,email_txt,copy_to_admin=CFG_WEBSUBMIT_COPY_MAILS_TO_ADMIN)
    return ""


