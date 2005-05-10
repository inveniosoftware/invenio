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

   ## Description:   function Test_Status
   ##                This function checks whether the document is still waiting
   ##             for approval or not.
   ## Author:         T.Baron
   ##
   ## PARAMETERS:    -

def Test_Status(parameters,curdir,form):
    global rn
    res = run_sql("SELECT status, access FROM sbmAPPROVAL WHERE rn=%s", (rn,))
    if len(res) == 0:
        raise functionStop(printNotRequested(rn))
    else:
        if res[0][0] == "approved":
            raise functionStop(printApproved(rn))
        elif res[0][0] == "rejected":
            raise functionStop(printRejected(rn))
    return ""

def printNotRequested(rn):
    t="""
<SCRIPT>
   document.forms[0].action="submit.py";
   document.forms[0].curpage.value = 1;
   document.forms[0].step.value = 0;
   document.forms[0].submit();
   alert('The document %s has never been asked for approval.\\nAnyway, you can still choose another document if you wish.');
</SCRIPT>""" % rn
    return t

def printApproved(rn):
    t="""
<SCRIPT>
   document.forms[0].action="submit.py";
   document.forms[0].curpage.value = 1;
   document.forms[0].step.value = 0;
   document.forms[0].submit();
   alert('The document %s has already been approved.\\nAnyway, you can still choose another document if you wish.');
</SCRIPT>""" % rn
    return t

def printRejected(rn):
    t="""
<SCRIPT>
   document.forms[0].action="submit.py";
   document.forms[0].curpage.value = 1;
   document.forms[0].step.value = 0;
   document.forms[0].submit();
   alert('The document %s has already been rejected.\\nAnyway, you can still choose another document if you wish.');
</SCRIPT>""" % rn
    return t

