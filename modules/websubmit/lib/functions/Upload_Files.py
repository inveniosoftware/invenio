## $Id$

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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

from invenio.config import \
     CFG_PATH_ACROREAD, \
     CFG_PATH_CONVERT, \
     CFG_PATH_DISTILLER, \
     CFG_PATH_GUNZIP, \
     CFG_PATH_GZIP, \
     images
from invenio.file import *

def Upload_Files(parameters,curdir,form):
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
    if form.has_key("mybibdocid"):
        mybibdocid = form['mybibdocid']
    else:
        mybibdocid = ""
    if form.has_key("fileAction"):
        fileAction = form['fileAction']
    else:
        fileAction = ""
    if deleted == "yes":
        bibrecdocs.deleteBibDoc(int(deletedfile))
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
                if not bibrecdocs.checkFileExists(fullpath,"Main"):
                    bibdoc = bibrecdocs.addNewFile(fullpath,"Main")
            if fileAction == "AddAdditional":
                if not bibrecdocs.checkFileExists(fullpath,"Additional"):
                    bibdoc = bibrecdocs.addNewFile(fullpath,"Additional")
            if fileAction == "ReviseAdditional" and mybibdocid != "":
                if not bibrecdocs.checkFileExists(fullpath,"Additional"):
                    bibdoc = bibrecdocs.addNewVersion(fullpath,int(mybibdocid))
            if fileAction == "AddAdditionalFormat" and mybibdocid != "":
                bibdoc = bibrecdocs.addNewFormat(fullpath,int(mybibdocid))
            if type == "fulltext" and fileAction != "AddMainFormat" and fileAction != "AddAdditionalFormat":
                additionalformats = createRelatedFormats(fullpath)
                if len(additionalformats) > 0 and bibdoc is not None:
                    bibdoc.addFilesNewFormat(additionalformats)
            if type == "picture" and fileAction != "AddMainFormat" and fileAction != "AddAdditionalFormat":
                iconpath = createIcon(fullpath,iconsize)
                if iconpath is not None and bibdoc is not None:
                    bibdoc.addIcon(iconpath)
                    os.unlink(iconpath)
                elif bibdoc is not None:
                    bibdoc.deleteIcon()
                bibrecdocs.buildBibDocList()
            os.unlink(fullpath)
            os.unlink("%s/myfile" % curdir)
    t+="<form>"
    t=t+Display_Form(bibrecdocs)
    t=t+Display_File_List(bibrecdocs)
    t=t+ "<br><CENTER><small><INPUT TYPE=\"button\" HEIGHT=35 WIDTH=250 NAME=\"Submit\" VALUE=\"End Submission\" onClick=\"step2();\"></small></CENTER>"
    t+="</form>"
    return t

def Display_File_List(bibrecdocs):
    t="""<br><br><table cellpadding=0 cellspacing=0 border=0 bgcolor=#dddddd width=80% align=center><tr><td>"""
    bibdocs = bibrecdocs.listBibDocs()
    if len(bibdocs) > 0:
        types = listTypesFromArray(bibdocs)
        for mytype in types:
            if len(bibrecdocs.listBibDocs(mytype)) > 1:
                plural = "s"
            else:
                plural = ""
            t+="<small><b>%s</b> document%s:</small>" % (mytype,plural)
            for bibdoc in bibdocs:
                if mytype == bibdoc.getType():
                    t+="<table cellpadding=0 cellspacing=1 border=0><tr><td bgcolor=\"white\">"
                    t+="<center><input type=radio name=mybibdocid value=%s><br><br><A href=\"\" onClick=\"if (confirm('Are you sure you want to delete this file?')) { document.forms[0].deletedfile.value='%s';document.forms[0].deleted.value='yes';document.forms[0].submit();return false;} else { return false; }\"><IMG src=%s/smallbin.gif border=0 align=center></a><br></small></center>" % (bibdoc.getId(),bibdoc.getId(),images)
                    t+="</td><td>"
                    t+=bibdoc.display()
                    t+="</td></tr></table>"
    t+="""</td></tr></table>"""
    return t
    
def Display_Form(bibrecdocs):
    #output the upload files form.
    t=""
    t=t+"""
<B>Don't forget to click on the \"End Submission\" button when you have finished managing the files.</b><br><br>
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
    if len(bibrecdocs.listBibDocs("Main")) == 0:
        t+="\n<option value=AddMain> Add Main Document"
    t+= "<option value=AddAdditional> Add Additional Document"
    if len(bibrecdocs.listBibDocs()) != 0:
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
        if (getRadioValue(document.forms[0].mybibdocid) == null) {
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
          document.forms[0].submit();
      }
    return true;
}
</SCRIPT> """
    return t

def createRelatedFormats(fullpath):
    createdpaths = []
    filename = re.sub("\..*","",os.path.basename(fullpath))
    extension = re.sub("^[^\.]*.","",os.path.basename(fullpath)).lower()
    basedir = os.path.dirname(fullpath)
    if extension == "pdf":
        # Create PostScript
        os.system("%s -toPostScript %s" % (CFG_PATH_ACROREAD,fullpath))
        if os.path.exists("%s/%s.ps" % (basedir,filename)):
            os.system("%s %s/%s.ps" % (CFG_PATH_GZIP,basedir,filename))
            createdpaths.append("%s/%s.ps.gz" % (basedir,filename))
    if extension == "ps":
        # Create PDF
        os.system("%s %s %s/%s.pdf" % (CFG_PATH_DISTILLER,fullpath,basedir,filename))
        if os.path.exists("%s/%s.pdf" % (basedir,filename)):
            createdpaths.append("%s/%s.pdf" % (basedir,filename))
    if extension == "ps.gz":
        #gunzip file
        os.system("%s %s" % (CFG_PATH_GUNZIP,fullpath))
        # Create PDF
        os.system("%s %s/%s.ps %s/%s.pdf" % (CFG_PATH_DISTILLER,basedir,filename,basedir,filename))
        if os.path.exists("%s/%s.pdf" % (basedir,filename)):
            createdpaths.append("%s/%s.pdf" % (basedir,filename))
        #gzip file
        os.system("%s %s/%s.ps" % (CFG_PATH_GZIP,basedir,filename))
    return createdpaths

def createIcon(fullpath,iconsize):
    global CFG_PATH_CONVERT
    basedir = os.path.dirname(fullpath)
    filename = os.path.basename(fullpath)
    extension = re.sub("^[^\.]*\.","",filename)
    if extension == filename:
        extension == ""
    iconpath = "%s/icon-%s.gif" % (basedir,re.sub("\..*","",filename))
    if os.path.exists(fullpath) and extension.lower() in ['pdf','gif','jpg','jpeg','ps']:
        os.system("%s -scale %s %s %s" % (CFG_PATH_CONVERT,iconsize,fullpath,iconpath))
    if os.path.exists(iconpath):
        return iconpath
    else:
        return None
