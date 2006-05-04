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

   ##
   ## Name:          Get_Info.py
   ## Description:   function Get_Info
   ##                This function retrieves some bibliographic data (title,
   ##                submitter email, author and sets global variables with
   ##                the values, so that other functions may use them.
   ## Author:         T.Baron
   ## PARAMETERS:    authorFile: name of the file in which the author is stored
   ##             emailFile: name of the file in which the email is stored
   ##             titleFile: name of the file in which the title is stored
   ## OUTPUT: HTML
   ##

execfile("%s/invenio/websubmit_functions/Retrieve_Data.py" % pylibdir)

titlevalue = ""
emailvalue = ""
authorvalue = ""

def Get_Info(parameters,curdir,form):
    global titlevalue,emailvalue,authorvalue,rn
    doctype = form['doctype']
    titlefile = parameters["titleFile"]
    emailfile = parameters["emailFile"]
    authorfile = parameters["authorFile"]
    if not Get_Info_In_Curdir(rn,titlefile,emailfile,authorfile,doctype):
        if not Get_Info_In_DB(rn,parameters,curdir):
            DocumentNotFound(rn)
    return ""

def Get_Info_In_Curdir(repno,titlefile,emailfile,authorfile,doctype):
    global titlevalue,emailvalue,authorvalue
    if not os.path.exists("%s/%s" % (curdir,titlefile)):
        return 0
    else:
        if os.path.exists("%s/%s" % (curdir,titlefile)):
            fp = open("%s/%s" % (curdir,titlefile),"r")
            titlevalue = fp.read()
            fp.close()
        else :
            titlevalue = "-"
        if os.path.exists("%s/%s" % (curdir,emailfile)):
            fp = open("%s/%s" % (curdir,emailfile),"r")
            emailvalue = fp.read()
            fp.close()
        else :
            emailvalue = "-"
        if os.path.exists("%s/%s" % (curdir,authorfile)):
            fp = open("%s/%s" % (curdir,authorfile),"r")
            authorvalue = fp.read()
            fp.close()
        else :
            authorvalue = "-"
    return 1

def Get_Info_In_DB(rn,parameters,curdir):
    global titlevalue,emailvalue,authorvalue,sysno
    if sysno != "":
        titlevalue = Get_Field('245__a',sysno)
        emailvalue = Get_Field('8560_f',sysno)
        authorvalue = Get_Field('100__a',sysno)
        authorvalue += "\n%s" % Get_Field('700__a',sysno)
        # save result
        fp = open("%s/SN" % curdir,"w")
        fp.write(sysno)
        fp.close()
        return 1
    else:
        return 0

def DocumentNotFound(repno):
    raise functionStop("""
<SCRIPT>
   document.forms[0].action="submit.py";
   document.forms[0].curpage.value = 1;
   document.forms[0].step.value = 0;
   document.forms[0].submit();
   alert('The document %s cannot be found in our database.\\nAnyway, you can still choose another document if you wish.');
</SCRIPT>""" % repno)
    return 0

