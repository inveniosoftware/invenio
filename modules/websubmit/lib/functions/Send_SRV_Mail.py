## $Id$

## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002, 2003, 2004, 2005 CERN.
##
## The CDSware is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## The CDSware is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDSware; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

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

execfile("%s/cdsware/websubmit_functions/mail.py" % pylibdir)
execfile("%s/cdsware/websubmit_functions/Retrieve_Data.py" % pylibdir)

def Send_SRV_Mail(parameters,curdir,form):
    global rn,doctype,sysno
    # variables declaration
    FROMADDR = '%s Submission Engine <%s>' % (cdsname,supportemail)
    addresses = parameters['addressesSRV']
    if parameters['emailFile']!=None and parameters['emailFile']!="" and os.path.exists("%s/%s" % (curdir,parameters['emailFile'])):
        fp = open("%s/%s" % (curdir,parameters['emailFile']), "r")
        SuE = fp.read()
        fp.close()
    else:
        SuE = ""
    SuE = SuE.replace("\n",",")
    if parameters['noteFile']!=None and parameters['noteFile']!= "" and os.path.exists("%s/%s" % (curdir,parameters['noteFile'])):
        fp = open("%s/%s" % (curdir,parameters['noteFile']), "r")
        note = fp.read()
        fp.close()
    else:
        note = ""
    title = Get_Field("245__a",sysno)
    author = Get_Field('100__a',sysno)
    author += Get_Field('700__a',sysno)
    # create message
    message = "A revised version of document %s has been submitted.\n\nTitle: %s\nAuthor(s): %s\nURL: <%s?id=%s>%s" % (rn,title,author,accessurl,sysno,note)
    
    # Actually send the email
    body = forge_email(FROMADDR,SuE,addresses,"%s revised" % rn,message)
    tostring = "%s,%s" % (SuE,addresses)
    tolist = re.split(",",tostring)
    send_email(FROMADDR,tolist,body,0)
    return ""

