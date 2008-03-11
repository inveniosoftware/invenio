## $Id$

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

__revision__ = "$Id$"

   ## Description:   function Send_SRV_Mail
   ##                This function sends an email confirming the revision
   ##             has been carried on with success
   ## Author:         T.Baron
   ## PARAMETERS:    addressesSRV: list of addresses to send this email to.
   ##                categformatDAM: variable used to derive the category of
   ##             the document from its reference. This value might then
   ##             be used to derive the list of addresses
   ##             emailFile: name of the file in which the user's email is
   ##             noteFile: name of the file containing a note from the user

import os
import re

from invenio.config import \
     accessurl, \
     CFG_SITE_ADMIN_EMAIL, \
     CFG_SITE_NAME, \
     CFG_SITE_SUPPORT_EMAIL, \
     weburl
from invenio.websubmit_config import CFG_WEBSUBMIT_COPY_MAILS_TO_ADMIN
from invenio.mailutils import send_email
from invenio.websubmit_functions.Retrieve_Data import Get_Field

def Send_SRV_Mail(parameters, curdir, form, user_info=None):
    global rn,doctype,sysno
    # variables declaration
    FROMADDR = '%s Submission Engine <%s>' % (CFG_SITE_NAME,CFG_SITE_SUPPORT_EMAIL)
    addresses = parameters['addressesSRV']
    addresses = addresses.strip()
    if parameters['emailFile'] is not None and parameters['emailFile']!="" and os.path.exists("%s/%s" % (curdir,parameters['emailFile'])):
        fp = open("%s/%s" % (curdir,parameters['emailFile']), "r")
        SuE = fp.read()
        fp.close()
    else:
        SuE = ""
    SuE = SuE.replace("\n",",")
    if parameters['noteFile'] is not None and parameters['noteFile']!= "" and os.path.exists("%s/%s" % (curdir,parameters['noteFile'])):
        fp = open("%s/%s" % (curdir,parameters['noteFile']), "r")
        note = fp.read()
        fp.close()
    else:
        note = ""
    title = Get_Field("245__a",sysno)
    author = Get_Field('100__a',sysno)
    author += Get_Field('700__a',sysno)
    # create message
    message = "A revised version of document %s has been submitted.\n\nTitle: %s\nAuthor(s): %s\nURL: <%s/record/%s>%s" % (rn,title,author,weburl,sysno,note)

    # send the email
    send_email(FROMADDR, SuE, "%s revised" % rn, message, copy_to_admin=CFG_WEBSUBMIT_COPY_MAILS_TO_ADMIN)
    return ""

