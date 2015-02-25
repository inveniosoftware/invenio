# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011 CERN.
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

   ##
   ## Name:          Get_Report_Number.py
   ## Description:   function Get_Report_Number
   ##                This function retrieves the reference of the document from
   ##                the name of the file it is stored in.
   ## Author:         T.Baron
   ## PARAMETERS:    edsrn: name of the file in which the reference is stored
   ## OUTPUT: HTML
   ##

import os
import re

def Get_Report_Number(parameters, curdir, form, user_info=None):
    """
    This function gets the value contained in the [edsrn] file and
    stores it in the 'rn' global variable.

    Parameters:

        * edsrn: Name of the file which stores the reference.  This
                 value depends on the web form configuration you
                 did. It should contain the name of the form element
                 used for storing the reference of the document.
    """
    global rn

    #Path of file containing report number
    if os.path.exists("%s/%s" % (curdir,parameters['edsrn'])):
        fp = open("%s/%s" % (curdir,parameters['edsrn']),"r")
        rn = fp.read()
        rn = rn.replace("/","_")
        rn = re.sub("[\n\r ]+","",rn)
    else:
        rn = ""
    return ""

