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

def Print_Success(parameters,curdir,form): 
    t=""
    edsrn = parameters['edsrn']
    newrnin = parameters['newrnin']
    status = parameters['status']
    fp = open("%s/%s" % (curdir,edsrn),"r")
    rn = fp.read()
    fp.close()
    if newrnin != "" and os.path.exists("%s/%s" % (curdir,newrnin)):
        fp = open("%s/%s" % (curdir,newrnin),"r")
        additional_rn = fp.read()
        fp.close()
        additional_rn = " and %s" % additional_rn
    else:
        additional_rn = ""
    t=t+Request_Print("A",  "<br><br><B>Submission Complete!!</B><br><BR>")
    t=t+Request_Print("A",  "Your document has the following reference(s): <b>%s%s</b><br><br>" % (rn,additional_rn))
    if status == "APPROVAL":
        t=t+Request_Print("A",  "An email has been sent to the referee. You will be warned by email as soon as the referee takes his/her decision regarding your document.<br><br>\n")
    if status == "ADDED":
        t=t+Request_Print("A",  "It will soon appear on our server.<br><br>\n")
    t=t+Request_Print("A",  "Thank you for using %s!" % cdsname)
    t=t+Request_Print("A",  "<br><br><br><br>")
    return t
