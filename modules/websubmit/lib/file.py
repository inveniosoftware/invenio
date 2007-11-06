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

## import interesting modules:
import os
import re
import shutil
import md5
import urllib
from xml.sax.saxutils import quoteattr

from invenio.config import \
     cdslang, \
     filedir, \
     filedirsize, \
     images, \
     weburl
from invenio.dbquery import run_sql
from mimetypes import MimeTypes
from invenio.access_control_engine import acc_authorize_action

import invenio.template
websubmit_templates = invenio.template.load('websubmit')

_mimes = MimeTypes()
_mimes.suffix_map.update({'.tbz2' : '.tar.bz2'})
_mimes.encodings_map.update({'.bz2' : 'bzip2'})
_extensions = _mimes.encodings_map.keys() + \
              _mimes.suffix_map.keys() + \
              _mimes.types_map[1].keys()
_extensions.sort()
_extensions.reverse()

def file_strip_ext(file):
    """Strip in the best way the extension from a filename"""
    ext = '.'
    while ext:
        ext = ''
        for c_ext in _extensions:
            if file.endswith(c_ext):
                file = file[0:-len(c_ext)]
                ext = c_ext
                break
    return file

_path_re = re.compile(r'.*[\\/:]')
def decompose_file(file):
    """Decompose a file into dirname, basename and extension"""
    basename = _path_re.sub('', file)
    dirname = file[:-len(basename)-1]
    base = file_strip_ext(basename)
    extension = basename[len(base) + 1:]
    return (dirname, base, extension)

def propose_unique_name(file, use_version=False):
    """Propose a unique name, taking in account the version"""
    if use_version:
        version = ';'+re.sub('.*;', '', file)
        file = file[:-len(version)]
    else:
        version = ''
    (basedir, basename, extension) = decompose_file(file)
    if extension: # Sometimes the extension wasn't guessed
        extension = '.' + extension
    goodname = "%s%s%s" % (basename, extension, version)
    i = 1
    listdir = os.listdir(basedir)
    while goodname in listdir:
        i += 1
        goodname = "%s_%s%s%s" % (basename, i, extension, version)
    return "%s/%s" % (basedir, goodname)

class BibRecDocs:
    """this class represents all the files attached to one record"""
    def __init__(self, recid):
        self.id = recid
        self.bibdocs = []
        self.buildBibDocList()

    def buildBibDocList(self):
        self.bibdocs = []
        res = run_sql("select id_bibdoc,type,status from bibrec_bibdoc,bibdoc "
            "where id=id_bibdoc and id_bibrec=%s", (self.id,))
        for row in res:
            if row[2] != 'DELETED':
                try:
                    cur_doc = BibDoc(bibdocid=row[0], recid=self.id)
                    self.bibdocs.append(cur_doc)
                except StandardError:
                    pass

    def listBibDocs(self, type=""):
        """Returns the list all bibdocs object belonging to a recid.
        If type is set, it returns just the bibdocs of that type.
        """
        tmp = []
        for bibdoc in self.bibdocs:
            if type == "" or type == bibdoc.getType():
                tmp.append(bibdoc)
        return tmp

    def getBibDocNames(self, type="Main"):
        """Returns the names of the files associated with the bibdoc of a
        paritcular type"""
        names = []
        for bibdoc in self.listBibDocs(type):
            names.append(bibdoc.getDocName())
        return names

    def getBibDoc(self, bibdocid):
        """Returns the bibdoc with a particular bibdocid associated with
        this recid"""
        for bibdoc in self.bibdocs:
            if bibdoc.getId() == bibdocid:
                return bibdoc
        return None

    def deleteBibDoc(self, bibdocid):
        """Delete a bibdocid associated with the recid."""
        for bibdoc in self.bibdocs:
            if bibdoc.getId() == bibdocid:
                bibdoc.delete()
        self.buildBibDocList()

    def addBibDoc(self, type="Main", docname="file"):
        """Creates a new bibdoc associated with the recid, with a file
        called docname and a particular type. It returns the bibdoc object
        which was just created.
        ###"""
        #goodname = docname
        #i = 1
        #while goodname in self.getBibDocNames(type):
            #i += 1
            #goodname = "%s_%s" % (docname, i)
        #try:
            #bibdoc = BibDoc(recid=self.id, type=type, docname=goodname)
        #except StandardError, e:
            #raise
        #else:
            #self.bibdocs.append(bibdoc)
            #return bibdoc
        if docname in self.getBibDocNames(type):
            raise StandardError, "%s has already a bibdoc with docname %s" % (self.id, docname)
        else:
            return BibDoc(recid=self.id, type=type, docname=docname)

    def addNewFile(self, fullpath, type="Main"):
        """Creates a new bibdoc given a fullpath file and store the file in it.
        It returns the bibdoc object.
        """
        basename = decompose_file(fullpath)[1]
        bibdoc = self.addBibDoc(type, basename)
        if bibdoc is not None:
            bibdoc.addFilesNewVersion([fullpath])
            return bibdoc
        return None

    def addNewVersion(self, fullpath, bibdocid):
        """Adds a new fullpath file to an already existent bibdocid making the
        previous files associated with the same bibdocids obsolete.
        It returns the bibdoc object.
        """
        bibdoc = self.getBibDoc(bibdocid)
        if bibdoc is not None:
            bibdoc.addFilesNewVersion([fullpath])
            return bibdoc
        return None

    def addNewFormat(self, fullpath, bibdocid):
        """Adds a new format for a fullpath file to an already existent
        bibdocid along side already there files.
        It returns the bibdoc object.
        """
        bibdoc = self.getBibDoc(bibdocid)
        if bibdoc is not None:
            bibdoc.addFilesNewFormat([fullpath])
            return bibdoc
        return None

    def listLatestFiles(self, type=""):
        docfiles = []
        for bibdoc in self.listBibDocs(type):
            for docfile in bibdoc.listLatestFiles():
                docfiles.append(docfile)
        return docfiles

    def checkFileExists(self, fullpath, type=""):
        """Check if the file pointed by fullpath corresponds to some existant
        file, either by name or by content."""
        basename = decompose_file(fullpath)[1]
        if os.path.exists(fullpath):
            docfiles = self.listLatestFiles(type)
            for docfile in docfiles:
                if docfile.name == basename or \
                        md5.new(readfile(fullpath)).digest() == \
                        md5.new(readfile(docfile.getPath())).digest():
                    return docfile.getBibDocId()
        else:
            return 0


    def display(self, bibdocid="", version="", type="", ln = cdslang):
        t = ""
        bibdocs = []
        if bibdocid != "":
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
                        fulltype['content'].append(bibdoc.display(version,
                            ln = ln))
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

    def __init__ (self, bibdocid="", recid="", docname="file", type="Main"):
        # bibdocid is known, the document already exists
        if bibdocid != "":
            if recid == "":
                recid = None
                self.type = ""
                res = run_sql("select id_bibrec,type from bibrec_bibdoc "
                    "where id_bibdoc=%s", (bibdocid,))
                if len(res) > 0:
                    recid = res[0][0]
                    self.type = res[0][1]
                else:
                    res = run_sql("select id_bibdoc1 from bibdoc_bibdoc "
                                  "where id_bibdoc2=%s", (bibdocid,))
                    if len(res) > 0 :
                        main_bibdoc = res[0][0]
                        res = run_sql("select id_bibrec,type from bibrec_bibdoc "
                                      "where id_bibdoc=%s", (main_bibdoc,))
                        if len(res) > 0:
                            recid = res[0][0]
                            self.type = res[0][1]

            else:
                res = run_sql("select type from bibrec_bibdoc "
                    "where id_bibrec=%s and id_bibdoc=%s", (recid, bibdocid,))
                if len(res) > 0:
                    self.type = res[0][0]
                else:
                    #this bibdoc isn't associated with the corresponding bibrec.
                    raise StandardError, "No docid associated with the recid %s" % recid
            # gather the other information
            res = run_sql("select id,status,docname,creation_date,"
                "modification_date from bibdoc where id=%s", (bibdocid,))
            if len(res) > 0:
                self.cd = res[0][3]
                self.md = res[0][4]
                self.recid = recid
                self.docname = res[0][2]
                self.id = bibdocid
                self.status = res[0][1]
                group = "g" + str(int(int(self.id) / filedirsize))
                self.basedir = "%s/%s/%s" % (filedir, group, self.id)
            else:
                # this bibdoc doesn't exist
                raise StandardError, "The docid %s does not exist." % bibdocid
        # else it is a new document
        else:
            if docname == "" or type == "":
                raise StandardError, "Argument missing for creating a new bibdoc"
            else:
                self.recid = recid
                self.type = type
                self.docname = docname
                self.status = ''
                res = run_sql("SELECT b.id FROM bibrec_bibdoc bb JOIN bibdoc b on bb.id_bibdoc=b.id WHERE bb.id_bibrec=%s AND b.docname=%s", (recid, docname))
                if res:
                    raise StandardError, "A bibdoc called %s already exists for recid %s" % (docname, recid)
                self.id = run_sql("insert into bibdoc "
                    "(status,docname,creation_date,modification_date) "
                    "values(%s,%s,NOW(),NOW())", (self.status, docname,))
                if self.id is not None:
                    # we link the document to the record if a recid was
                    # specified
                    if self.recid != "":
                        run_sql("insert into bibrec_bibdoc values(%s,%s,%s)",
                            (recid, self.id, self.type,))
                else:
                    raise StandardError, "New docid cannot be created"
                group = "g" + str(int(int(self.id) / filedirsize))
                self.basedir = "%s/%s/%s" % (filedir, group, self.id)
                # we create the corresponding storage directory
                if not os.path.exists(self.basedir):
                    old_umask = os.umask(022)
                    os.makedirs(self.basedir)
                    # and save the father record id if it exists
                    if self.recid != "":
                        fp = open("%s/.recid" % self.basedir, "w")
                        fp.write(str(self.recid))
                        fp.close()
                    if self.type != "":
                        fp = open("%s/.type" % self.basedir, "w")
                        fp.write(str(self.type))
                        fp.close()
                    os.umask(old_umask)
        # build list of attached files
        self.BuildFileList()
        # link with relatedFiles
        self.BuildRelatedFileList()

    def getStatus(self):
        """Retrieve the status."""
        return self.status

    def touch(self):
        """Update the modification time of the bibdoc."""
        run_sql('UPDATE bibdoc SET modification_date=NOW() WHERE id=%s', self.id)

    def setStatus(self, new_status):
        """Set a new status."""
        run_sql('UPDATE bibdoc SET status=%s WHERE id=%s', (new_status, self.id))
        self.BuildFileList()
        self.BuildRelatedFileList()

    def addFilesNewVersion(self, files=[]):
        """add a new version of a file to an archive"""
        latestVersion = self.getLatestVersion()
        if latestVersion == "0":
            myversion = "1"
        else:
            myversion = str(int(latestVersion) + 1)
        for file in files:
            if os.path.exists(file):
                dummy, basename, extension = decompose_file(file)
                if extension:
                    extension = '.' + extension
                #self.changeName(basename)
                #destination = propose_unique_name("%s/%s%s;%s" %
                    #(self.basedir, basename, extension, myversion), True)
                destination = "%s/%s%s;%s" % (self.basedir, self.docname, extension, myversion)
                shutil.copyfile(file, destination)
                os.chmod(destination, 0644)
        self.touch()
        self.BuildFileList()

    def purge(self):
        """Phisically Remove all the previous version of the given bibdoc"""
        version = self.getLatestVersion()
        if version > 1:
            for file in self.docfiles:
                if file.getVersion() < version:
                    os.remove(file.getFullPath())
            Md5Folder(self.basedir).update()
            self.touch()
            self.BuildFileList()
            self.BuildRelatedFileList()

    def expunge(self):
        """Phisically remove all the traces of a given bibdoc"""
        for file in self.docfiles:
            os.remove(file.getFullPath())
        Md5Folder(self.basedir).update()
        self.touch()
        self.BuildFileList()
        self.BuildRelatedFileList()


    def addFilesNewFormat(self, files=[], version=""):
        """add a new format of a file to an archive"""
        if version == "":
            version = self.getLatestVersion()
        for file in files:
            if os.path.exists(file):
                dummy, basename, extension = decompose_file(file)
                if extension:
                    extension = '.' + extension
                destination = "%s/%s%s;%s" % (self.basedir, self.docname, extension, version)
                if os.path.exists(destination):
                    raise StandardError, "A file for docname '%s' for the recid '%s' already exists for the format '%s'" % (self.docname, self.recid, extension)
                #destination = propose_unique_name("%s/%s%s;%s" %
                    #(self.basedir, basename, extension, version), True)
                shutil.copyfile(file, destination)
                os.chmod(destination, 0644)
        self.touch()
        self.BuildFileList()

    def getIcon(self):
        if self.relatedFiles.has_key('Icon'):
            return self.relatedFiles['Icon'][0]
        else:
            return None

    def addIcon(self, file, basename=''):
        """link an icon with the bibdoc object"""
        #first check if an icon already exists
        existingIcon = self.getIcon()
        if existingIcon is not None:
            existingIcon.delete()
        #then add the new one
        if not basename:
            basename = decompose_file(file)[1]
        try:
            newicon = BibDoc(type='Icon', docname=basename)
        except StandardError:
            pass
        else:
            newicon.addFilesNewVersion([file])
            run_sql("insert into bibdoc_bibdoc values(%s,%s,'Icon')",
                (self.id, newicon.getId(),))
            if os.path.exists(newicon.getBaseDir()):
                old_umask = os.umask(022)
                fp = open("%s/.docid" % newicon.getBaseDir(), "w")
                fp.write(str(self.id))
                fp.close()
                fp = open("%s/.type" % newicon.getBaseDir(), "w")
                fp.write(str(self.type))
                fp.close()
                os.umask(old_umask)
        self.touch()
        self.BuildRelatedFileList()

    def deleteIcon(self):
        existingIcon = self.getIcon()
        if existingIcon is not None:
            existingIcon.delete()
        self.touch()
        self.BuildRelatedFileList()

    def display(self, version="", ln = cdslang):
        t = ""
        if version == "all":
            docfiles = self.listAllFiles()
        elif version != "":
            docfiles = self.listVersionFiles(version)
        else:
            docfiles = self.listLatestFiles()
        existingIcon = self.getIcon()
        if existingIcon is not None:
            imagepath = "%s/getfile.py?docid=%s&name=%s&format=gif" % \
                (weburl, existingIcon.getId(),
                urllib.quote(existingIcon.getDocName()))
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
              recid = self.recid
            )
        return t

    def changeName(self, newname):
        """Rename the bibdoc name. New name must not be already used by the linked
        bibrecs."""
        res = run_sql("SELECT b.id FROM bibrec_bibdoc bb JOIN bibdoc b on bb.id_bibdoc=b.id WHERE bb.id_bibrec=%s AND b.docname=%s", (self.recid, self.docname))
        if res:
            raise StandardError, "A bibdoc called %s already exists for recid %s" % (self.docname, self.recid)
        run_sql("update bibdoc set docname=%s where id=%s", (newname, self.id,))
        for f in os.listdir(self.basedir):
            if f.startswith(self.docname):
                shutil.move('%s/%s' % (self.basedir, f), '%s/%s' % (self.basedir, f.replace(self.docname, newname, 1)))
        self.docname = newname
        Md5Folder(self.basedir).update()
        self.touch()
        self.BuildFileList()
        self.BuildRelatedFileList()

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

    def getFile(self, name, format, version):
        if version == "":
            docfiles = self.listLatestFiles()
        else:
            docfiles = self.listVersionFiles(version)
        for docfile in docfiles:
            if docfile.getName()==name and (docfile.getFormat()==format or not format):
                return docfile
        raise StandardError, "No file called '%s' of format '%s', version '%s'" % (name, format, version)

    def listVersions(self):
        versions = []
        for docfile in self.docfiles:
            if not docfile.getVersion() in versions:
                versions.append(docfile.getVersion())
        return versions

    def delete(self):
        """delete the current bibdoc instance"""
        run_sql("update bibdoc set status='DELETED' where id=%s", (self.id,))

    def BuildFileList(self):
        """lists all files attached to the bibdoc"""
        self.docfiles = []
        if os.path.exists(self.basedir):
            self.md5s = Md5Folder(self.basedir)
            for fil in os.listdir(self.basedir):
                if fil not in (".recid", ".docid", ".", "..",
                        '.doc_checksum', '.type'):
                    filepath = "%s/%s" % (self.basedir, fil)
                    fileversion = re.sub(".*;", "", fil)
                    fullname = fil.replace(";%s" % fileversion, "")
                    checksum = self.md5s.get_checksum(fil)
                    (dirname, basename, extension) = decompose_file(fullname)
                    # we can append file:
                    self.docfiles.append(BibDocFile(filepath, self.type,
                        fileversion, basename, extension,
                        self.id, self.status, checksum))

    def BuildRelatedFileList(self):
        self.relatedFiles = {}
        res = run_sql("select ln.id_bibdoc2,ln.type,bibdoc.status from "
            "bibdoc_bibdoc as ln,bibdoc where id=ln.id_bibdoc2 and "
            "ln.id_bibdoc1=%s", (self.id,))
        for row in res:
            bibdocid = row[0]
            type = row[1]
            if row[2] != 'DELETED':
                if not self.relatedFiles.has_key(type):
                    self.relatedFiles[type] = []
                try:
                    cur_doc = BibDoc(bibdocid=bibdocid)
                    self.relatedFiles[type].append(cur_doc)
                except StandardError:
                    pass

    def listAllFiles(self):
        return self.docfiles

    def listLatestFiles(self):
        return self.listVersionFiles(self.getLatestVersion())

    def listVersionFiles(self, version):
        tmp = []
        for docfile in self.docfiles:
            if docfile.getVersion() == str(version):
                tmp.append(docfile)
        return tmp

    def getLatestVersion(self):
        if len(self.docfiles) > 0:
            self.docfiles.sort(orderFilesWithVersion)
            return self.docfiles[0].getVersion()
        else:
            return 0

    def getFileNumber(self):
        return len(self.docfiles)

    def registerDownload(self, addressIp, version, format, userid=0):
        return run_sql("INSERT INTO rnkDOWNLOADS "
            "(id_bibrec,id_bibdoc,file_version,file_format,"
            "id_user,client_host,download_time) VALUES "
            "(%s,%s,%s,%s,%s,INET_ATON(%s),NOW())",
            (self.recid, self.id, version, format.upper(),
            userid, addressIp,))

class BibDocFile:
    """this class represents a physical file in the CDS Invenio filesystem"""

    def __init__(self, fullpath, type, version, name, format, bibdocid, status, checksum):
        self.fullpath = fullpath
        self.type = type
        self.bibdocid = bibdocid
        self.version = version
        self.status = status
        self.checksum = checksum
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
            self.fullname = "%s.%s" % (name, format)
            (self.mime, self.encoding) = _mimes.guess_type(self.fullname)
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
        return self.status != ''

    def getType(self):
        return self.type

    def getPath(self):
        return self.fullpath

    def getBibDocId(self):
        return self.bibdocid

    def getName(self):
        return self.name

    def getFullName(self):
        return self.fullname

    def getFullPath(self):
        return self.fullpath

    def getFormat(self):
        return self.format

    def getSize(self):
        return self.size

    def getVersion(self):
        return self.version

    def getChecksum(self):
        return self.checksum

    def getRecid(self):
        return run_sql("select id_bibrec from bibrec_bibdoc where "
            "id_bibdoc=%s",(self.bibdocid,))[0][0]

    def stream(self, req):
        if self.status:
            (auth_code, auth_message) = acc_authorize_action(req, 'viewrestrdoc', status=self.status)
        else:
            auth_code = 0
        if auth_code == 0:
            if os.path.exists(self.fullpath):
                req.content_type = self.mime
                req.encoding = self.encoding
                req.filename = self.fullname
                req.headers_out["Content-Disposition"] = \
                    "attachment; filename=%s" % quoteattr(self.fullname)
                req.send_http_header()
                fp = file(self.fullpath, "r")
                content = fp.read()
                fp.close()
                return content
            else:
                raise StandardError, "%s does not exists!" % self.fullpath
        else:
            raise StandardError, "You are not authorized to download %s: %s" % (self.fullname, auth_message)

def readfile(path):
    """Read the contents of a text file and return them as a string.
       Return an empty string if unable to access the file for reading.
       @param path: (string) - path to the file
       @return: (string) contents of file or empty string
    """
    content = ""
    if os.access(path, os.F_OK|os.R_OK):
        try:
            fp = open(path, "r")
        except IOError:
            pass
        else:
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

def orderFilesWithVersion(docfile1, docfile2):
    """order docfile objects according to their version"""
    version1 = int(docfile1.getVersion())
    version2 = int(docfile2.getVersion())
    return cmp(version2, version1)

class Md5Folder:
    """Manage all the Md5 checksum about a folder"""
    def __init__(self, folder):
        """Initialize the class from the md5 checksum of a given path"""
        self.folder = folder
        self.load()

    def update(self, only_new = True):
        """Update the .doc_checksum file with the current files. If only_new
        is specified then only not already calculated file are calculated."""
        self.md5s = {}
        for filename in os.listdir(self.folder):
            if not only_new or self.md5s.get(filename, None) is None and \
                not filename.startswith('.'):
                self.md5s[filename] = md5.new(open("%s/%s" %
                    (self.folder, filename), "rb").read()).hexdigest()
        self.store()

    def store(self):
        """Store the current md5 dictionary into .doc_checksum"""
        old_umask = os.umask(022)
        md5file = open("%s/.doc_checksum" % self.folder, "w")
        for key, value in self.md5s.items():
            md5file.write('%s *%s\n' % (value, key))
        os.umask(old_umask)

    def load(self):
        """Load .doc_checksum into the md5 dictionary"""
        self.md5s = {}
        try:
            for row in open("%s/.doc_checksum" % self.folder, "r"):
                md5hash = row[:32]
                filename = row[34:].strip()
                self.md5s[filename] = md5hash
        except IOError:
            pass

    def check(self, filename = ''):
        """Check the specified file or all the files for which it exists a hash
        for being coherent with the stored hash."""
        if filename and filename in self.md5s.keys():
            return self.md5s[filename] == md5.new(open("%s/%s" %
                    (self.folder, filename), "rb").read()).hexdigest()
        else:
            for filename, md5hash in self.md5s.items():
                if md5.new(open("%s/%s" % (self.folder, filename),
                    "rb").read()).hexdigest() != md5hash:
                        return False
            return True

    def get_checksum(self, filename):
        md5hash = self.md5s.get(filename, None)
        if md5hash is None:
            self.update()
        # Now it should not fail!
        md5hash = self.md5s[filename]
        return md5hash

