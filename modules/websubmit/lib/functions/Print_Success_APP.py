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

   ## Description:   function Print_Success_APP
   ##                This function outputs a message telling the user his/her
   ##             decision was taken into account.
   ## Author:         T.Baron
   ## PARAMETERS:    -

import os

from invenio.websubmit_config import InvenioWebSubmitFunctionError

def Print_Success_APP(parameters,curdir,form):
    global rn
    # the field containing the decision of the referee must be called "decision".
    if not os.path.exists("%s/decision" % curdir):
        raise InvenioWebSubmitFunctionError("Could not find decision file")
    else:
        fp = open("%s/decision" % curdir,"r")
        decision = fp.read()
        fp.close()
        t="<br><br><B>Your decision has been taken into account!</B><br><BR>"
        if decision == "approve":
            t+="The document will be soon available with the following reference: <b>%s</b><BR>" % rn
    return t

