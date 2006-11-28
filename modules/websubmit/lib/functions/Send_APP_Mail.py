## $Id$

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
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

from invenio.config import \
     adminemail, \
     cdsname, \
     htdocsurl, \
     pylibdir, \
     supportemail

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

from invenio.access_control_admin import acc_getRoleUsers,acc_getRoleId
from invenio.websubmit_config import CFG_WEBSUBMIT_COPY_MAILS_TO_ADMIN

execfile("%s/invenio/websubmit_functions/mail.py" % pylibdir)

def Send_APP_Mail (parameters,curdir,form):
    global emailvalue,titlevalue,authorvalue,sysno,rn
    FROMADDR = '%s Submission Engine <%s>' % (cdsname,supportemail)
    doctype = form['doctype']
    emailvalue = emailvalue.replace("\n","")
    titlevalue = titlevalue.replace("\n","")
    authorvalue = authorvalue.replace("\n","")
    # variables declaration
    categformat = parameters['categformatAPP']
    otheraddresses = parameters['addressesAPP']
    newrnpath = parameters['newrnin']
    # retrieve values stored into files
    if os.path.exists("%s/COM" % curdir):
        fp = open("%s/COM" % curdir, "r")
        comment = fp.read()
        fp.close()
    else:
        comment = ""
    if os.path.exists("%s/decision" % curdir):
        fp = open("%s/decision" % curdir,"r")
        decision = fp.read()
        fp.close()
    else:
        decision = ""
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
    categformat = categformat.replace("<CATEG>","([^-]*)")
    categs = re.match(categformat,rn)
    if categs is not None:
        category = categs.group(1)
    else:
        category = "unknown"
    # Build referee's email address
    refereeaddress = ""
    # Try to retrieve the referee's email from the referee's database
    for user in acc_getRoleUsers(acc_getRoleId("referee_%s_%s" % (doctype,category))):
        refereeaddress += user[1] + ","
    # And if there is a general referee
    for user in acc_getRoleUsers(acc_getRoleId("referee_%s_*" % doctype)):
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
    if decision == "approve":
        mailtitle = "%s has been approved" % rn
        mailbody = "The %s %s has been approved." % (docname,rn)
        mailbody += "\nIt will soon be accessible here:\n<%s/record/%s>" % (htdocsurl,sysno)
    else:
        mailtitle = "%s has been rejected" % rn
        mailbody = "The %s %s has been rejected." % (docname,rn)
    if rn != newrn and decision == "approve" and newrn != "":
        mailbody += "Its new reference number is: %s" % newrn
    mailbody += "\n\nTitle: %s\n\nAuthor(s): %s\n\n" % (titlevalue,authorvalue)
    if comment != "":
        mailbody += "Comments from the referee:\n%s\n" % comment
    mailbody += "---------------------------------------------\nBest regards.\nThe submission team.\n"
    #Send mail to referee
    tostring = addresses.strip()
    if CFG_WEBSUBMIT_COPY_MAILS_TO_ADMIN:
        # Copy mail to admins:
        if len(tostring) > 0:
            tostring += ",%s" % (adminemail,)
        else:
            tostring = adminemail
    body = forge_email(FROMADDR,addresses,"",mailtitle,mailbody)
    tolist = re.split(",",tostring)
    if len(tolist[0]) > 0:
        send_email(FROMADDR,tolist,body,0)
    return ""
