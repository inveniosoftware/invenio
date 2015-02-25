# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

   ## Description:   function Make_Weblib_Record
   ##                This function creates the bibliographic record
   ##             using bibConvert and the configuration files passed as
   ##             parameters
   ## Author:         T.Baron
   ##
   ## PARAMETERS:    sourceSubmit: source description file
   ##                mysqlInsert: template description file

import os

from invenio.utils.text import wash_for_xml
from invenio.config import \
     CFG_BINDIR, \
     CFG_WEBSUBMIT_BIBCONVERTCONFIGDIR
from invenio.legacy.websubmit.config import InvenioWebSubmitFunctionError

def Make_Record(parameters, curdir, form, user_info=None):
    """
    This function creates the record file formatted for a direct
    insertion in the documents database. It uses the BibConvert tool.  The
    main difference between all the Make_..._Record functions are the
    parameters.

    As its name does not say :), this particular function should be
    used for the submission of a document.

       * createTemplate: Name of bibconvert's configuration file used
                         for creating the mysql record.

       * sourceTemplate: Name of bibconvert's source file.
    """
    # Get rid of "invisible" white spaces
    source = parameters['sourceTemplate'].replace(" ","")
    create = parameters['createTemplate'].replace(" ","")
    # We use bibconvert to create the xml record
    call_uploader_txt = "%s/bibconvert -l1 -d'%s'  -Cs'%s/%s' -Ct'%s/%s' > %s/recmysql" % (CFG_BINDIR,curdir,CFG_WEBSUBMIT_BIBCONVERTCONFIGDIR,source,CFG_WEBSUBMIT_BIBCONVERTCONFIGDIR,create,curdir)
    os.system(call_uploader_txt)
    # Then we have to format this record (turn & into &amp; and < into &lt;
    # After all we know nothing about the text entered by the users at submission time
    if os.path.exists("%s/recmysql" % curdir):
        fp = open("%s/recmysql" % curdir,"r")
        rectext = fp.read()
        fp.close()
    else:
        raise InvenioWebSubmitFunctionError("Cannot create database record")

    if not rectext:
        raise InvenioWebSubmitFunctionError("Empty record!")

    # Escape XML-reserved chars and clean the unsupported ones (mainly
    # control characters)
    rectext = wash_for_xml(rectext)
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
