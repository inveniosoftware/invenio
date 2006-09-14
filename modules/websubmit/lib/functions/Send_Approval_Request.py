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

   ## Description:   function Send_Approval_Request
   ##                This function sends an email to the referee asking him/her
   ##             to approve/reject a document
   ## Author:         T.Baron
   ## PARAMETERS:    directory: parameter to the link manager program
   ##                addressesDAM: address of the referee(s)
   ##             categformatDAM: variable needed to extract the category
   ##                        of the document and use it to derive the
   ##                address.
   ##             authorfile: name of the file containing the author list
   ##             titleFile: name of the file containing the title

from invenio.access_control_admin import acc_getRoleUsers,acc_getRoleId
from invenio.websubmit_config import CFG_WEBSUBMIT_COPY_MAILS_TO_ADMIN

execfile("%s/invenio/websubmit_functions/mail.py" % pylibdir)

def Send_Approval_Request (parameters,curdir,form):
    global rn,sysno
    # variables declaration
    doctype = re.search(".*/([^/]*)/([^/]*)/[^/]*$",curdir).group(2)
    FROMADDR = '%s Submission Engine <%s>' % (cdsname,supportemail)
    otheraddresses = parameters['addressesDAM']
    categformat = parameters['categformatDAM']
    # retrieve category
    categformat = categformat.replace("<CATEG>","([^-]*)")
    categs = re.match(categformat,rn)
    if categs != None:
        category = categs.group(1)
    else:
        category = "unknown"
    # create TI
    if os.path.exists("%s/date" % curdir):
        fp = open("%s/date" % curdir, "r")
        date = fp.read()
        fp.close()
    else:
        date = ""
    if os.path.exists("%s/%s" % (curdir,parameters['titleFile'])):
        fp = open("%s/%s" % (curdir,parameters['titleFile']),"r")
        title = fp.read()
        fp.close()
        title = title.replace("\n","")
    else:
        title = ""
    title += " - %s" % date
    # create AU
    if os.path.exists("%s/%s" % (curdir,parameters['authorfile'])):
        fp = open("%s/%s" % (curdir,parameters['authorfile']), "r")
        author = fp.read()
        fp.close()
    else:
        author = ""
    # we get the referee password
    sth = run_sql("SELECT access FROM sbmAPPROVAL WHERE rn=%s", (rn,))
    if len(sth) >0:
        access = sth[0][0]
    # Build referee's email address
    refereeaddress = ""
    # Try to retrieve the referee's email from the referee's database
    for user in acc_getRoleUsers(acc_getRoleId("referee_%s_%s" % (doctype,category))):
        refereeaddress += user[1] + ","
    # And if there are general referees
    for user in acc_getRoleUsers(acc_getRoleId("referee_%s_*" % doctype)):
        refereeaddress += user[1] + ","
    refereeaddress = re.sub(",$","",refereeaddress)
    # Creation of the mail for the referee
    addresses = ""
    if refereeaddress != "":
        addresses = refereeaddress + ","
    if otheraddresses != "":
        addresses += otheraddresses
    else:
        addresses = re.sub(",$","",addresses)
    title_referee = "Request for approval of %s" % rn
    mail_referee = "The document %s has been submitted to the %s Server..\nYour approval is requested on it.\n\n" % (rn,cdsname)
    mail_referee +="Title: %s\n\nAuthor(s): %s\n\n" % (title,author)
    mail_referee +="To access the document(s), select the file(s) from the location:<%s/getfile.py?recid=%s>\n\n" % (htdocsurl,sysno)
    mail_referee +="To approve/reject the document, you should go to this URL:\n<%s/approve.py?%s>\n" % (urlpath,access)
    mail_referee +="---------------------------------------------\nBest regards.\nThe submission team.\n"
    #Send mail to referee
    tostring = addresses.strip()
    if CFG_WEBSUBMIT_COPY_MAILS_TO_ADMIN:
        # Copy mail to admins:
        if len(tostring) > 0:
            tostring += ",%s" % (adminemail,)
        else:
            tostring = adminemail
    body = forge_email(FROMADDR,addresses,"",title_referee,mail_referee)
    tolist = re.split(",",tostring)
    if len(tolist[0]) > 0:
        send_email(FROMADDR,tolist,body,0)
    return ""
