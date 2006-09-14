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

from invenio.websubmit_config import CFG_WEBSUBMIT_COPY_MAILS_TO_ADMIN

execfile("%s/invenio/websubmit_functions/mail.py" % pylibdir)

def Send_Modify_Mail (parameters,curdir,form):
    FROMADDR = '%s Submission Engine <%s>' % (cdsname,supportemail)
    global sysno,rn
    if parameters['emailFile']!= None and parameters['emailFile']!= "" and os.path.exists("%s/%s" % (curdir,parameters['emailFile'])):
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
    if accessurl != "" and sysno != "":
        email_txt += "You can check the modified document here:\n"
        email_txt += "<%s?id=%s>\n\n" % (accessurl,sysno)
    email_txt += "Please note that the modifications will be taken into account in a couple of minutes.\n\nBest regards,\nThe %s Server support Team" % cdsname
    # send the mail
    tostring = sub.strip()
    if len(addresses) > 0:
        if len(tostring) > 0:
            tostring += ",%s" % (addresses,)
        else:
            tostring = addresses
    if CFG_WEBSUBMIT_COPY_MAILS_TO_ADMIN:
        # Copy mail to admins:
        if len(tostring) > 0:
            tostring += ",%s" % (adminemail,)
        else:
            tostring = adminemail
    body = forge_email(FROMADDR,sub,"","%s modified" % rn,email_txt)
    tolist = tostring.split(",")
    if len(tolist[0]) > 0:
        send_email(FROMADDR,tolist,body,0)
    return ""
   

