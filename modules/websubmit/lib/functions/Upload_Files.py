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
"""Function for the upload of files"""

__revision__ = "$Id$"

from invenio.config import \
     CFG_PATH_ACROREAD, \
     CFG_PATH_CONVERT, \
     CFG_PATH_DISTILLER, \
     CFG_PATH_GUNZIP, \
     CFG_PATH_GZIP, \
     CFG_SITE_URL
import os
import re
from invenio.bibdocfile import BibRecDocs, list_versions_from_array, list_types_from_array
from invenio.websubmit_functions.Shared_Functions import createRelatedFormats, createIcon

def Upload_Files(parameters, curdir, form, user_info=None):
    """DEPRECATED: Use FFT instead."""
    global doctype,access,act,dir
    minsize=parameters['minsize']
    maxsize=parameters['maxsize']
    iconsize=parameters['iconsize']
    type=parameters['type']
    t=""
    bibrecdocs = BibRecDocs(sysno)
    # first check if a file has been requested for deletion
    if form.has_key("deleted"):
        deleted = form['deleted']
    else:
        deleted = "no"
    if form.has_key("deletedfile"):
        deletedfile = form['deletedfile']
    else:
        deletedfile = ""
    if form.has_key("mybibdocname"):
        mybibdocname = form['mybibdocname']
    else:
        mybibdocname = ""
    if form.has_key("fileAction"):
        fileAction = form['fileAction']
    else:
        fileAction = ""
    if deleted == "yes":
        bibrecdocs.delete_bibdoc(deletedfile)
    # then check if a file has been requested for addition
    if os.path.exists("%s/myfile" % curdir):
        fp = open("%s/myfile" % curdir,"r")
        myfile=fp.read()
        fp.close()
        extension = re.sub("^[^\.]*\.","",myfile)
        filename = re.sub("\..*","",os.path.basename(myfile))
        fullpath = "%s/files/myfile/%s" % (curdir,myfile)
        if os.path.getsize(fullpath) < int(minsize):
            os.unlink("%s/myfile" % curdir)
            os.unlink(fullpath)
            t+= """<script>alert("your file was too small (<%s o) and was deleted");</script>""" % minsize
        elif os.path.getsize(fullpath) > int(maxsize):
            os.unlink("%s/myfile" % curdir)
            os.unlink(fullpath)
            t+= """<script>alert("your file was too big (>%s o) and was deleted");</script>""" % maxsize
        else:
            bibdoc = None
            if fileAction == "AddMain":
                if not bibrecdocs.check_file_exists(fullpath):
                    bibdoc = bibrecdocs.add_new_file(fullpath, "Main", never_fail=True)
            if fileAction == "AddAdditional":
                if not bibrecdocs.check_file_exists(fullpath):
                    bibdoc = bibrecdocs.add_new_file(fullpath, "Additional", never_fail=True)
            if fileAction == "ReviseAdditional" and mybibdocname != "":
                if not bibrecdocs.check_file_exists(fullpath):
                    bibdoc = bibrecdocs.add_new_version(fullpath, mybibdocname)
            if fileAction == "AddAdditionalFormat" and mybibdocname != "":
                bibdoc = bibrecdocs.add_new_format(fullpath, mybibdocname)
            if type == "fulltext" and fileAction != "AddMainFormat" and fileAction != "AddAdditionalFormat":
                additionalformats = createRelatedFormats(fullpath)
                if len(additionalformats) > 0 and bibdoc is not None:
                    for additionalformat in additionalformats:
                        bibdoc.add_file_new_format(additionalformat)
            if type == "picture" and fileAction != "AddMainFormat" and fileAction != "AddAdditionalFormat":
                iconpath = createIcon(fullpath,iconsize)
                if iconpath is not None and bibdoc is not None:
                    bibdoc.add_icon(iconpath)
                    os.unlink(iconpath)
                elif bibdoc is not None:
                    bibdoc.delete_icon()
                bibrecdocs.build_bibdoc_list()
            os.unlink(fullpath)
            os.unlink("%s/myfile" % curdir)
    t+="<form>"
    t=t+Display_Form(bibrecdocs)
    t=t+Display_File_List(bibrecdocs)
    t=t+ "<br /><CENTER><small><INPUT TYPE=\"button\" HEIGHT=35 WIDTH=250 NAME=\"Submit\" VALUE=\"End Submission\" onClick=\"step2();\"></small></CENTER>"
    t+="</form>"
    return t

def Display_File_List(bibrecdocs):
    t="""<br /><br /><table cellpadding=0 cellspacing=0 border=0 bgcolor=#dddddd width=80% align=center><tr><td>"""
    bibdocs = bibrecdocs.list_bibdocs()
    if len(bibdocs) > 0:
        types = list_types_from_array(bibdocs)
        for mytype in types:
            if len(bibrecdocs.list_bibdocs(mytype)) > 1:
                plural = "s"
            else:
                plural = ""
            t+="<small><b>%s</b> document%s:</small>" % (mytype,plural)
            for bibdoc in bibdocs:
                if mytype == bibdoc.get_type():
                    t+="<table cellpadding=0 cellspacing=1 border=0><tr><td bgcolor=\"white\">"
                    t+="<center><input type=radio name=mybibdocname value=%s><br /><br /><A href=\"\" onClick=\"if (confirm('Are you sure you want to delete this file?')) { document.forms[0].deletedfile.value='%s';document.forms[0].deleted.value='yes';user_must_confirm_before_leaving_page = false;document.forms[0].submit();return false;} else { return false; }\"><IMG src=%s/img/smallbin.gif border=0 align=center></a><br /></small></center>" % (bibdoc.get_docname(),bibdoc.get_docname(),CFG_SITE_URL)
                    t+="</td><td>"
                    t+=bibdoc.display()
                    t+="</td></tr></table>"
    t+="""</td></tr></table>"""
    return t

def Display_Form(bibrecdocs):
    #output the upload files form.
    t=""
    t=t+"""
<B>Don't forget to click on the \"End Submission\" button when you have finished managing the files.</b><br /><br />
<TABLE cellpadding=0 cellspacing=0 border=0 bgcolor=#dddddd width=80% align=center>
<TR>
<TD>
<SMALL>Please complete the form below to upload a new file:</SMALL>
</TD></TR>
<TR><TD>
<INPUT name=deletedfile value=\"\" type=hidden>
<TABLE>
<TR>
    <TD ALIGN=center bgcolor=white width=20>
        <small><B>1</B></small>
    </TD>
    <TD>
        <small><SELECT name=fileAction>
        <option selected> Select:"""
    if len(bibrecdocs.list_bibdocs("Main")) == 0:
        t+="\n<option value=AddMain> Add Main Document"
    t+= "<option value=AddAdditional> Add Additional Document"
    if len(bibrecdocs.list_bibdocs()) != 0:
        t+="\n<option value=ReviseAdditional> Revise Document"
        t+="\n<option value=AddAdditionalFormat> Add new Format to Document"
    t+="""
        </SELECT></small>
    </TD>
    <TD></TD>
</TR>
<TR>
    <TD ALIGN=center bgcolor=white width=20>
        <small><b>2</B></small>
    </TD>
    <TD>
        <small><INPUT NAME=myfile TYPE="file"> </small>
    </TD>
</TR>
<TR>
    <TD ALIGN=center bgcolor=white width=20>
        <small><B>3</B></small>
    </TD>
    <TD ALIGN=LEFT>
        <small><INPUT TYPE="Submit" WIDTH=150 VALUE="Click to send file" onClick="return checkAdd();"></small>
    </TD>
</TR>
</TABLE>
</TD></TR></TABLE>
<SCRIPT LANGUAGE="JavaScript" TYPE="text/javascript">
function checkAdd()
{
    if (document.forms[0].fileAction.value == "ReviseAdditional" || document.forms[0].fileAction.value =="AddAdditionalFormat")
    {
        if (getRadioValue(document.forms[0].mybibdocname) == '') {
            alert("please choose the document you wish to modify");
            return false;
        }
        else
            return true;
    }
    else if (document.forms[0].fileAction.value == "Select:")
    {
        alert("please select the type of action (form field #1)");
        return false;
    }
    else
    {
        return true;
    }
}

function getRadioValue (radioButtonOrGroup) {
  var value = null;
  if (radioButtonOrGroup.length) { // group
    for (var b = 0; b < radioButtonOrGroup.length; b++)
      if (radioButtonOrGroup[b].checked)
        value = radioButtonOrGroup[b].value;
  }
  else if (radioButtonOrGroup.checked)
    value = radioButtonOrGroup.value;
  return value;
}

function step2()
{
      if(confirm(\"You are about to submit the files and end the upload process.\"))
      {
          document.forms[0].step.value = 2;
          user_must_confirm_before_leaving_page = false;
          document.forms[0].submit();
      }
    return true;
}
</SCRIPT> """
    return t

