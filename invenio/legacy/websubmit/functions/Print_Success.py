# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011, 2014 CERN.
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

import os

from invenio.config import CFG_SITE_NAME, CFG_SITE_URL, CFG_SITE_RECORD
from invenio.legacy.websubmit.functions.Shared_Functions import get_nice_bibsched_related_message, txt2html, ParamFromFile

# FIXME: cannot import Request_Print(), is defined in websubmit_engine.py

def Print_Success(parameters, curdir, form, user_info=None):
    """
    This function simply displays a text on the screen, telling the
    user the submission went fine. To be used in the 'Submit New
    Record' action.

    Parameters:

       * status: Depending on the value of this parameter, the
         function adds an additional text to the email.
         This parameter can be one of:
           - ADDED: The file has been integrated in the database.
           - APPROVAL: The file has been sent for approval to a referee.
                       or can stay empty.

       * edsrn: Name of the file containing the reference of the
                document

       * newrnin: Name of the file containing the 2nd reference of the
                  document (if any)
    """
    t=""
    edsrn = parameters['edsrn']
    newrnin = parameters['newrnin']
    status = parameters['status']
    sysno=ParamFromFile("%s/%s" % (curdir,'SN')).strip()
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
    t=t+Request_Print("A",  "<br /><br /><b>Submission Complete!</b><br /><br />")
    t=t+Request_Print("A",  "Your document has the following reference(s): <b>%s%s</b><br /><br />" % (rn,additional_rn))
    if sysno:
        url = '%s/%s/%s' % (CFG_SITE_URL, CFG_SITE_RECORD, sysno)
        t=t+Request_Print('A',  'Your document has the following URL: <b><a href="%s">%s</a></b><br /><br />' % (url, url))
    if status == "APPROVAL":
        t=t+Request_Print("A",  "An email has been sent to the referee. You will be warned by email as soon as the referee takes his/her decision regarding your document.<br /><br />\n")
    if status == "ADDED":
        t=t+Request_Print("A",  "It will soon appear on our server.<br /><br />\n")
    t=t+Request_Print("A",  "Thank you for using %s!" % CFG_SITE_NAME)
    t=t+Request_Print("A",  "<br /><br /><br /><br />")
    t += txt2html(get_nice_bibsched_related_message(curdir))
    return t
