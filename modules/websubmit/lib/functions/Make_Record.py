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

   ## Description:   function Make_Weblib_Record
   ##                This function creates the bibliographic record
   ##             using bibConvert and the configuration files passed as
   ##             parameters
   ## Author:         T.Baron
   ##
   ## PARAMETERS:    sourceSubmit: source description file
   ##                mysqlInsert: template description file

import os

from invenio.config import \
     bibconvert, \
     bibconvertconf
from invenio.websubmit_config import functionError

def Make_Record(parameters,curdir,form): 
    # Get rid of "invisible" white spaces
    source = parameters['sourceTemplate'].replace(" ","")
    create = parameters['createTemplate'].replace(" ","")
    # We use bibconvert to create the xml record
    call_uploader_txt = "%s -l1 -d'%s'  -Cs'%s/%s' -Ct'%s/%s' > %s/recmysql" % (bibconvert,curdir,bibconvertconf,source,bibconvertconf,create,curdir)
    os.system(call_uploader_txt)
    # Then we have to format this record (turn & into &amp; and < into &lt;
    # After all we know nothing about the text entered by the users at submission time
    if os.path.exists("%s/recmysql" % curdir):
        fp = open("%s/recmysql" % curdir,"r")
        rectext = fp.read()
        fp.close()
    else:
        raise functionError("Cannot create database record")
    # First of all the &
    rectext = rectext.replace("&amp;","&")
    rectext = rectext.replace("&","&amp;")
    # Then the < - More difficult!
    rectext = rectext.replace("<","&lt;")
    rectext = rectext.replace("&lt;record","<record")
    rectext = rectext.replace("&lt;/record","</record")
    rectext = rectext.replace("&lt;datafield","<datafield")
    rectext = rectext.replace("&lt;/datafield","</datafield")
    rectext = rectext.replace("&lt;controlfield","<controlfield")
    rectext = rectext.replace("&lt;/controlfield","</controlfield")
    rectext = rectext.replace("&lt;subfield","<subfield")
    rectext = rectext.replace("&lt;/subfield","</subfield")
    # Save the record back
    fp = open("%s/recmysql" % curdir,"w")
    fp.write(rectext)
    fp.close()
    return ""
