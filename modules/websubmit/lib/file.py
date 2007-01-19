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

## import interesting modules:
import string
import os
import sys
import time
import types
import re
import mimetypes
import shutil
import md5
import urllib
from xml.sax.saxutils import quoteattr
from mod_python import apache

from invenio.config import \
     cdslang, \
     filedir, \
     filedirsize, \
     images, \
     storage, \
     version, \
     weburl
from invenio.access_control_engine import acc_authorize_action
from invenio.access_control_admin import acc_isRole
from invenio.webpage import page, create_error_box
from invenio.webuser import getUid, get_email
from invenio.dbquery import run_sql
from invenio.websubmit_config import *

from invenio.messages import gettext_set_language
import invenio.template
websubmit_templates = invenio.template.load('websubmit')

archivepath = filedir
archivesize = filedirsize

# sort compressed file extensions list to get lengthy ones first:
CFG_COMPRESSED_FILE_EXTENSIONS_SORTED = CFG_COMPRESSED_FILE_EXTENSIONS
CFG_COMPRESSED_FILE_EXTENSIONS_SORTED.sort()

def file_strip_ext(file):
    for c_ext in CFG_KNOWN_FILE_EXTENSIONS:
        if file[-len(c_ext):len(file)]==c_ext and file[-len(c_ext)-1]==".":
            file = file[0:-len(c_ext)-1]
    return file
			    
class BibRecDocs:
    """this class represents all the files attached to one record"""
    def __init__(self,recid):
        self.id = recid
        self.bibdocs = []
        self.buildBibDocList()

    def buildBibDocList(self):
        self.bibdocs = []
        res = run_sql("select id_bibdoc,type,status from bibrec_bibdoc,bibdoc where id=id_bibdoc and id_bibrec=%s", (self.id,))
        for row in res:
            if row[2] == "":
                status = 0
            else:
                status = int(row[2])
            if status & 1 == 0:
                self.bibdocs.append(BibDoc(bibdocid=row[0],recid=self.id))

    def listBibDocs(self,type=""):
        tmp=[]
        for bibdoc in self.bibdocs:
            if type=="" or type == bibdoc.getType():
                tmp.append(bibdoc)
        return tmp

    def getBibDocNames(self,type="Main"):
        names = []
        for bibdoc in self.listBibDocs(type):
            names.append(bibdoc.getDocName())
        return names

    def getBibDoc(self,bibdocid):
        for bibdoc in self.bibdocs:
            if bibdoc.getId() == bibdocid:
                return bibdoc
        return None

    def deleteBibDoc(self,bibdocid):
        for bibdoc in self.bibdocs:
            if bibdoc.getId() == bibdocid:
                bibdoc.delete()
        self.buildBibDocList()

    def addBibDoc(self,type="Main",docname="file"):
        while docname in self.getBibDocNames(type):
            match = re.match("(.*_)([^_]*)",docname)
            if match:
                try:
                    docname = match.group(1)+str(int(match.group(2)) + 1)
                except:
                    docname = docname + "_2"
            else:
                docname = docname + "_2"
        bibdoc = BibDoc(recid=self.id,type=type,docname=docname)
        if bibdoc is not None:
            self.bibdocs.append(bibdoc)
        return bibdoc

    def addNewFile(self,fullpath,type="Main"):
        filename = re.sub("\..*","",re.sub(r".*[\\/:]", "", fullpath))
        bibdoc = self.addBibDoc(type,filename)
        if bibdoc is not None:
            bibdoc.addFilesNewVersion(files=[fullpath])
            return bibdoc
        return None

    def addNewVersion(self,fullpath,bibdocid):
        bibdoc = self.getBibDoc(bibdocid)
        if bibdoc is not None:
            bibdoc.addFilesNewVersion(files=[fullpath])
            docname = re.sub("\..*","",re.sub(r".*[\\/:]", "", fullpath))
            if docname != bibdoc.getDocName():
                while docname in self.getBibDocNames(bibdoc.getType()):
                    match = re.match("(.*_)([^_]*)",docname)
                    if match:
                        try:
                            docname = match.group(1)+str(int(match.group(2)) + 1)
                        except:
                            docname = docname + "_2"
                    else:
                        docname = docname + "_2"
                bibdoc.changeName(docname)
            return bibdoc
        return None

    def addNewFormat(self,fullpath,bibdocid):
        bibdoc = self.getBibDoc(bibdocid)
        if bibdoc is not None:
            bibdoc.addFilesNewFormat(files=[fullpath])
            return bibdoc
        return None

    def listLatestFiles(self,type=""):
        docfiles = []
        for bibdoc in self.listBibDocs(type):
            for docfile in bibdoc.listLatestFiles():
                docfiles.append(docfile)
        return docfiles

    def checkFileExists(self,fullpath,type=""):
        if os.path.exists(fullpath):
            docfiles = self.listLatestFiles(type)
            for docfile in docfiles:
                if md5.new(readfile(fullpath)).digest() == md5.new(readfile(docfile.getPath())).digest():
                    return docfile.getBibDocId()
        else:
            return 0

    def display(self,bibdocid="",version="",type="", ln = cdslang):
        t=""
        bibdocs = []
        if bibdocid!="":
            for bibdoc in self.bibdocs:
                if bibdoc.getId() == bibdocid:
                    bibdocs.append(bibdoc)
        else:
            bibdocs = self.listBibDocs(type)
        if len(bibdocs) > 0:
            types = listTypesFromArray(bibdocs)
            fulltypes = []
            for mytype in types:
                fulltype = {
                            'name' : mytype,
                            'content' : [],
                           }
                for bibdoc in bibdocs:
                    if mytype == bibdoc.getType():
                        fulltype['content'].append(bibdoc.display(version, ln = ln))
                fulltypes.append(fulltype)

            t = websubmit_templates.tmpl_bibrecdoc_filelist(
                  ln = ln,
                  types = fulltypes,
                )
        return t

class BibDoc:
    """this class represents one file attached to a record
        there is a one to one mapping between an instance of this class and
        an entry in the bibdoc db table"""

    def __init__ (self,bibdocid="",recid="",docname="file",type="Main"):
        # bibdocid is known, the document already exists
        if bibdocid != "":
            if recid == "":
                res = run_sql("select id_bibrec,type from bibrec_bibdoc where id_bibdoc=%s",(bibdocid,))
                if len(res) > 0:
                    recid = res[0][0]
                    self.type = res[0][1]
                else:
                    recid = None
                    self.type = ""
            else:
                res = run_sql("select type from bibrec_bibdoc where id_bibrec=%s and id_bibdoc=%s",(recid,bibdocid,))
                self.type = res[0][0]
            # gather the other information
            res = run_sql("select * from bibdoc where id=%s", (bibdocid,))
            self.cd = res[0][3]
            self.md = res[0][4]
            self.recid = recid
            self.docname = res[0][2]
            self.id = bibdocid
	    self.status = int(res[0][1])
            group = "g"+str(int(int(self.id)/archivesize))
            self.basedir = "%s/%s/%s" % (archivepath,group,self.id)
        # else it is a new document
        else:
            if docname == "" or type == "":
                return None
            else:
                self.recid = recid
                self.type = type
                self.docname = docname
		self.status = 0
                self.id = run_sql("insert into bibdoc (status,docname,creation_date,modification_date) values(%s,%s,NOW(),NOW())", (str(self.status), docname,))
                if self.id is not None:
                    #we link the document to the record if a recid was specified
                    if self.recid != "":
                        run_sql("insert into bibrec_bibdoc values(%s,%s,%s)", (recid,self.id,self.type,))
                else:
                    return None
                group = "g"+str(int(int(self.id)/archivesize))
                self.basedir = "%s/%s/%s" % (archivepath,group,self.id)
                # we create the corresponding storage directory
                if not os.path.exists(self.basedir):
                    os.makedirs(self.basedir)
                    # and save the father record id if it exists
                    if self.recid!="":
                        fp = open("%s/.recid" % self.basedir,"w")
                        fp.write(str(self.recid))
                        fp.close()
        # build list of attached files
        self.docfiles = {}
        self.BuildFileList()
        # link with relatedFiles
        self.relatedFiles = {}
        self.BuildRelatedFileList()

    def addFilesNewVersion(self,files=[]):
        """add a new version of a file to an archive"""
        latestVersion = self.getLatestVersion()
        if latestVersion == "0":
            myversion = "1"
        else:
            myversion = str(int(latestVersion)+1)
        for file in files:
            if os.path.exists(file):
                filename = re.sub(r".*[\\/:]", "", file)
                shutil.copy(file,"%s/%s;%s" % (self.basedir,filename,myversion))
        self.BuildFileList()

    def addFilesNewFormat(self,files=[],version=""):
        """add a new format of a file to an archive"""
        if version == "":
            version = self.getLatestVersion()
        for file in files:
            if os.path.exists(file):
                filename = re.sub(r".*[\\/:]", "", file)
                shutil.copy(file,"%s/%s;%s" % (self.basedir,filename,version))
        self.BuildFileList()

    def getIcon(self):
        if self.relatedFiles.has_key('Icon'):
            return self.relatedFiles['Icon'][0]
        else:
            return None

    def addIcon(self,file):
        """link an icon with the bibdoc object"""
        #first check if an icon already exists
        existingIcon = self.getIcon()
        if existingIcon is not None:
            existingIcon.delete()
        #then add the new one
        filename = re.sub("\..*","",re.sub(r".*[\\/:]", "", file))
        newicon = BibDoc(type='Icon',docname=filename)
        if newicon is not None:
            newicon.addFilesNewVersion(files=[file])
            run_sql("insert into bibdoc_bibdoc values(%s,%s,'Icon')", (self.id,newicon.getId(),))
            if os.path.exists(newicon.getBaseDir()):
                fp = open("%s/.docid" % newicon.getBaseDir(),"w")
                fp.write(str(self.id))
                fp.close()
        self.BuildRelatedFileList()

    def deleteIcon(self):
        existingIcon = self.getIcon()
        if existingIcon is not None:
            existingIcon.delete()
        self.BuildRelatedFileList()

    def display(self,version="", ln = cdslang):
        t=""
        if version == "all":
            docfiles = self.listAllFiles()
        elif version != "":
            docfiles = self.listVersionFiles(version)
        else:
            docfiles = self.listLatestFiles()
        existingIcon = self.getIcon()
        if existingIcon is not None:
            imagepath = "%s/getfile.py?docid=%s&name=%s&format=gif" % (weburl,existingIcon.getId(),urllib.quote(existingIcon.getDocName()))
        else:
            imagepath = "%s/smallfiles.gif" % images

        versions = []
        for version in listVersionsFromArray(docfiles):
            currversion = {
                            'version' : version,
                            'previous' : 0,
                            'content' : []
                          }
            if version == self.getLatestVersion() and version != "1":
                currversion['previous'] = 1
            for docfile in docfiles:
                if docfile.getVersion() == version:
                    currversion['content'].append(docfile.display(ln = ln))
            versions.append(currversion)

        t = websubmit_templates.tmpl_bibdoc_filelist(
              ln = ln,
              weburl = weburl,
              versions = versions,
              imagepath = imagepath,
              docname = self.docname,
              id = self.id,
            )
        return t

    def changeName(self,newname):
        run_sql("update bibdoc set docname=%s where id=%s",(newname,self.id,))
        self.docname = newname

    def getDocName(self):
        """retrieve bibdoc name"""
        return self.docname

    def getBaseDir(self):
        """retrieve bibdoc base directory"""
        return self.basedir

    def getType(self):
        """retrieve bibdoc type"""
        return self.type

    def getRecid(self):
        """retrieve bibdoc recid"""
        return self.recid

    def getId(self):
        """retrieve bibdoc id"""
        return self.id
	
    def getFile(self,name,format,version):
        if version == "":
            docfiles = self.listLatestFiles()
        else:
            docfiles = self.listVersionFiles(version)
        for docfile in docfiles:
            if docfile.getName()==name and docfile.getFormat()==format:
                return docfile
        return None

    def listVersions(self):
        versions = []
        for docfile in self.docfiles:
            if not docfile.getVersion() in versions:
                versions.append(docfile.getVersion())
        return versions

    def delete(self):
        """delete the current bibdoc instance"""
	self.status = self.status | 1
        run_sql("update bibdoc set status='" + str(self.status) + "' where id=%s",(self.id,))

    def BuildFileList(self):
        """lists all files attached to the bibdoc"""
        self.docfiles = []
        if os.path.exists(self.basedir):
            for fil in os.listdir(self.basedir):
                if fil != ".recid" and fil != ".docid" and fil != "." and fil != "..":
                    filepath = "%s/%s" % (self.basedir,fil)
                    fileversion = re.sub(".*;","",fil)
                    fullname = fil.replace(";%s" % fileversion,"")
                    # detect fullname's basename and extension:
                    fullname_lowercase = fullname.lower()
                    fullname_extension_postition = -1
                    # first try to detect compressed file extensions:
                    for compressed_file_extension in CFG_COMPRESSED_FILE_EXTENSIONS_SORTED:
                        if fullname_lowercase.endswith("." + compressed_file_extension):
                            fullname_extension_postition = fullname[:-len(compressed_file_extension)-1].rfind(".")
                            break
                    if fullname_extension_postition == -1:
                        # okay, no compressed extension found, so try to find last dot:
                        fullname_extension_postition = len(file_strip_ext(fullname))
                    # okay, fullname_extension_postition should now indicate where extension starts (incl. compressed ones)
                    if fullname_extension_postition == -1:
                        fullname_basename = fullname
                        fullname_extension = ""
                    else:
                        fullname_basename = fullname[:fullname_extension_postition]
                        fullname_extension = fullname[fullname_extension_postition+1:]
                    # we can append file:		    
                    self.docfiles.append(BibDocFile(filepath,self.type,fileversion,fullname_basename,fullname_extension,self.id,self.status))

    def BuildRelatedFileList(self):
        res = run_sql("select ln.id_bibdoc2,ln.type,bibdoc.status from bibdoc_bibdoc as ln,bibdoc where id=ln.id_bibdoc2 and ln.id_bibdoc1=%s",(self.id,))
        for row in res:
            bibdocid = row[0]
            type = row[1]
	    if row[2] == "":
	        status = 0
	    else:
	        status = int(row[2])
	    if status & 1 == 0:
                if not self.relatedFiles.has_key(type):
                    self.relatedFiles[type] = []
                self.relatedFiles[type].append(BibDoc(bibdocid=bibdocid))

    def listAllFiles(self):
        return self.docfiles

    def listLatestFiles(self):
        return self.listVersionFiles(self.getLatestVersion())

    def listVersionFiles(self,version):
        tmp = []
        for docfile in self.docfiles:
            if docfile.getVersion() == version:
                tmp.append(docfile)
        return tmp

    def getLatestVersion(self):
        if len(self.docfiles) > 0:
            self.docfiles.sort(orderFilesWithVersion)
            return self.docfiles[0].getVersion()
        else:
            return 0

    def getFileNumber(self):
        return len(self.files)

    def registerDownload(self,addressIp,version,format,userid=0):
        return run_sql("INSERT INTO rnkDOWNLOADS (id_bibrec,id_bibdoc,file_version,file_format,id_user,client_host,download_time) VALUES (%s,%s,%s,%s,%s,INET_ATON(%s),NOW())",
                       (self.recid,self.id,version,string.upper(format),userid,addressIp,))

class BibDocFile:
    """this class represents a physical file in the CDS Invenio filesystem"""

    def __init__(self,fullpath,type,version,name,format,bibdocid,status):
        self.fullpath = fullpath
        self.type = type
        self.bibdocid = bibdocid
        self.version = version
	self.status = status
        self.size = os.path.getsize(fullpath)
        self.md = os.path.getmtime(fullpath)
        try:
            self.cd = os.path.getctime(fullpath)
        except:
            self.cd = self.md
        self.name = name
        self.format = format
        self.dir = os.path.dirname(fullpath)
        if format == "":
            self.mime = "text/plain"
            self.encoding = ""
            self.fullname = name
        else:
            self.fullname = "%s.%s" % (name,format)
            (self.mime,self.encoding) = mimetypes.guess_type(self.fullname)
            if self.mime is None:
                self.mime = "text/plain"

    def display(self, ln = cdslang):
        if self.format != "":
            format = ".%s" % self.format
        else:
            format = ""
        return websubmit_templates.tmpl_bibdocfile_filelist(
                 ln = ln,
                 weburl = weburl,
                 id = self.bibdocid,
                 selfformat = self.format,
                 version = self.version,
                 name = self.name,
                 format = format,
                 size = self.size,
               )

    def isRestricted(self):
        """return restriction state"""
	if int(self.status) & 10 == 10:
	    return 1
	return 0
	
    def getType(self):
        return self.type

    def getPath(self):
        return self.fullpath

    def getBibDocId(self):
        return self.bibdocid

    def getName(self):
        return self.name

    def getFormat(self):
        return self.format

    def getSize(self):
        return self.size

    def getVersion(self):
        return self.version

    def getRecid(self):
        return run_sql("select id_bibrec from bibrec_bibdoc where id_bibdoc=%s",(self.bibdocid,))[0][0]

    def stream(self,req):
        if os.path.exists(self.fullpath):
            req.content_type = self.mime
            req.encoding = self.encoding
            req.filename = self.fullname
            req.headers_out["Content-Disposition"] = "attachment; filename=%s" % quoteattr(self.fullname)
            req.send_http_header()
            fp = file(self.fullpath,"r")
            content = fp.read()
            fp.close()
            return content

def readfile(path):
    if os.path.exists(path):
        fp = open(path,"r")
        content = fp.read()
        fp.close()
    return content

def listTypesFromArray(bibdocs):
    types = []
    for bibdoc in bibdocs:
        if not bibdoc.getType() in types:
            types.append(bibdoc.getType())
    return types

def listVersionsFromArray(docfiles):
    versions = []
    for docfile in docfiles:
        if not docfile.getVersion() in versions:
            versions.append(docfile.getVersion())
    return versions

def orderFilesWithVersion(docfile1,docfile2):
    """order docfile objects according to their version"""
    version1 = int(docfile1.getVersion())
    version2 = int(docfile2.getVersion())
    return cmp(version2,version1)

