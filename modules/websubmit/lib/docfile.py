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
from xml.sax.saxutils import quoteattr
from mimetypes import MimeTypes

from invenio.dbquery import run_sql
from invenio.errorlib import register_exception
from invenio.access_control_engine import acc_authorize_action
from invenio.config import cdslang, images, weburl, webdir, filedir, filedirsize

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

class InvenioWebSubmitFileError(Exception):
    pass

def file_strip_ext(file):
    """Strip in the best way the extension from a filename"""
    lowfile = file.lower()
    ext = '.'
    while ext:
        ext = ''
        for c_ext in _extensions:
            if lowfile.endswith(c_ext):
                lowfile = lowfile[0:-len(c_ext)]
                ext = c_ext
                break
    return file[:len(lowfile)]

def normalize_format(format):
    """Normalize the format."""
    format = format.lower()
    if format and format[0] != '.':
        format = '.' + format
    return format

def normalize_version(version):
    """Normalize the version."""
    try:
        int(version)
    except ValueError:
        if version.lower().strip() == 'all':
            return 'all'
        else:
            return ''
    return version

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
        self.build_bibdoc_list()

    def build_bibdoc_list(self):
        """This function must be called everytime a bibdoc connected to this
        recid is added, removed or modified.
        """
        self.bibdocs = []
        res = run_sql("select id_bibdoc,type,status from bibrec_bibdoc,bibdoc "
            "where id=id_bibdoc and id_bibrec=%s and status<>'DELETED'", (self.id,))
        for row in res:
            cur_doc = BibDoc(docid=row[0], recid=self.id, doctype=row[1])
            self.bibdocs.append(cur_doc)

    def list_bibdocs(self, doctype=''):
        """Returns the list all bibdocs object belonging to a recid.
        If doctype is set, it returns just the bibdocs of that doctype.
        """
        if not doctype:
            return self.bibdocs
        else:
            return [bibdoc for bibdoc in self.bibdocs if doctype == bibdoc.doctype]

    def get_bibdoc_names(self, doctype=''):
        """Returns the names of the files associated with the bibdoc of a
        paritcular doctype"""
        return [bibdoc.docname for bibdoc in self.list_bibdocs(doctype)]

    def check_file_exists(self, path):
        """Returns 1 if the recid has a file identical to the one stored in path."""
        size = os.path.getsize(path)

        # Let's consider all the latest files
        files = self.list_latest_files()

        # Let's consider all the latest files with same size
        potential = [file for file in files if file.get_size() == size]

        if potential:
            content = open(path, 'rb').read()
            checksum = md5.new(content).hexdigest()

            # Let's consider all the latest files with the same size and the
            # same checksum
            potential = [file for file in potential if file.get_checksum() == checksum]

            if potential:
                potential = [file for file in potential if file.get_content() == content]

                if potential:
                    return True
                else:
                    # Gosh! How unlucky, same size, same checksum but not same
                    # content!
                    pass
        return False

    def propose_unique_docname(self, docname):
        """Propose a unique docname."""
        goodname = docname
        i = 1
        while goodname in self.get_bibdoc_names():
            i += 1
            goodname = "%s_%s" % (docname, i)
        return goodname

    def get_docid(self, docname):
        """Returns the docid corresponding to the given docname, if the docname
        is valid.
        """
        for bibdoc in self.bibdocs:
            if bibdoc.docname == docname:
                return bibdoc.id
        raise InvenioWebSubmitFileError, "Recid '%s' is not connected with a " \
            "docname '%s'" % (self.id, docname)

    def get_docname(self, docid):
        """Returns the docname corresponding to the given docid, if the docid
        is valid.
        """
        for bibdoc in self.bibdocs:
            if bibdoc.id == docid:
                return bibdoc.docname
        raise InvenioWebSubmitFileError, "Recid '%s' is not connected with a " \
            "docid '%s'" % (self.id, docid)

    def get_bibdoc(self, docname):
        """Returns the bibdoc with a particular docname associated with
        this recid"""
        for bibdoc in self.bibdocs:
            if bibdoc.docname == docname:
                return bibdoc
        raise InvenioWebSubmitFileError, "Recid '%s' is not connected with " \
            " docname '%s'" % (self.id, docname)

    def delete_bibdoc(self, docname):
        """Deletes a docname associated with the recid."""
        for bibdoc in self.bibdocs:
            if bibdoc.docname == docname:
                bibdoc.delete()
        self.build_bibdoc_list()

    def add_bibdoc(self, doctype="Main", docname='file', never_fail=False):
        """Creates a new bibdoc associated with the recid, with a file
        called docname and a particular doctype. It returns the bibdoc object
        which was just created.
        If never_fail is True then the system will always be able
        to create a bibdoc.
        """
        if never_fail:
            docname = self.propose_unique_docname(docname)
        if docname in self.get_bibdoc_names():
            raise InvenioWebSubmitFileError, "%s has already a bibdoc with docname %s" % (self.id, docname)
        else:
            bibdoc = BibDoc(recid=self.id, doctype=doctype, docname=docname)
            self.build_bibdoc_list()
            return bibdoc

    def add_new_file(self, fullpath, doctype="Main", docname='', never_fail=False):
        """Adds a new file with the following policy: if the docname is not set
        it is retrieved from the name of the file. If bibdoc with the given
        docname doesn't exist, it is created and the file is added to it.
        It it exist but it doesn't contain the format that is being added, the
        new format is added. If the format already exists then if never_fail
        is True a new bibdoc is created with a similar name but with a progressive
        number as a suffix and the file is added to it. The elaborated bibdoc
        is returned.
        """
        if not docname:
            docname = decompose_file(fullpath)[1]
        try:
            bibdoc = self.get_bibdoc(docname)
        except InvenioWebSubmitFileError:
            # bibdoc doesn't already exists!
            bibdoc = self.add_bibdoc(doctype, docname, False)
            bibdoc.add_file_new_version(fullpath)
        else:
            try:
                bibdoc.add_file_new_format(fullpath)
            except InvenioWebSubmitFileError, e:
                # Format already exist!
                if never_fail:
                    bibdoc = self.add_bibdoc(doctype, docname, True)
                    bibdoc.add_file_new_version(fullpath)
                else:
                    raise e
        return bibdoc

    def add_new_version(self, fullpath, docname):
        """Adds a new fullpath file to an already existent docid making the
        previous files associated with the same bibdocids obsolete.
        It returns the bibdoc object.
        """
        bibdoc = self.get_bibdoc(docname=docname)
        bibdoc.add_file_new_version(fullpath)
        return bibdoc

    def add_new_format(self, fullpath, docname):
        """Adds a new format for a fullpath file to an already existent
        docid along side already there files.
        It returns the bibdoc object.
        """
        bibdoc = self.get_bibdoc(docname=docname)
        bibdoc.add_file_new_format(fullpath)
        return bibdoc

    def list_latest_files(self, doctype=''):
        """Returns a list which is made up by all the latest docfile of every
        bibdoc (of a particular doctype).
        """
        docfiles = []
        for bibdoc in self.list_bibdocs(doctype):
            for docfile in bibdoc.list_latest_files():
                docfiles.append(docfile)
        return docfiles

    def display(self, docname="", version="", doctype="", ln=cdslang):
        """Returns a formatted panel with information and links about a given
        docid of a particular version (or any), of a particular doctype (or any)
        """
        t = ""
        if docname:
            try:
                bibdocs = [self.get_bibdoc(docname)]
            except InvenioWebSubmitFileError:
                bibdocs = self.list_bibdocs(doctype)
        else:
            bibdocs = self.list_bibdocs(doctype)
        if bibdocs:
            types = list_types_from_array(bibdocs)
            fulltypes = []
            for mytype in types:
                fulltype = {
                            'name' : mytype,
                            'content' : [],
                           }
                for bibdoc in bibdocs:
                    if mytype == bibdoc.get_type():
                        fulltype['content'].append(bibdoc.display(version,
                            ln = ln))
                fulltypes.append(fulltype)

            t = websubmit_templates.tmpl_bibrecdoc_filelist(
                  ln=ln,
                  types = fulltypes,
                )
        return t

    def fix(self, docname):
        """Algorithm that transform an a broken/old bibdoc into a coherent one:
        i.e. the corresponding folder will have files named after the bibdoc
        name. All extensions will be lowercase. Proper .recid, .type,
        .doc_checksum files will be created/updated.
        In case of more than one file with the same format revision a new bibdoc
        will be created in order to put does files.
        Returns the list of newly created bibdocs if any.
        """
        bibdoc = self.get_bibdoc(docname)
        versions = {}
        res = []
        new_bibdocs = [] # List of files with the same version/format of
                        # existing file which need new bibdoc.
        counter = 0
        if os.path.exists(bibdoc.basedir):
            for filename in os.listdir(bibdoc.basedir):
                if filename[0] != '.' and ';' in filename:
                    name, version = filename.split(';')
                    format = name[len(file_strip_ext(name)):]
                    format = normalize_format(format)
                    if not versions.has_key(version):
                        versions[version] = {}
                    new_name = 'FIXING-%s-%s' % (str(counter), name)
                    try:
                        shutil.move('%s/%s' % (bibdoc.basedir, filename), '%s/%s' % (bibdoc.basedir, new_name))
                    except Exception, e:
                        register_exception()
                        raise InvenioWebSubmitFileError, "Error in renaming '%s' to '%s': '%s'" % ('%s/%s' % (bibdoc.basedir, filename), '%s/%s' % (bibdoc.basedir, new_name), e)
                    if versions[version].has_key(format):
                        new_bibdocs.append((new_name, version))
                    else:
                        versions[version][format] = new_name
                    counter += 1

        if not versions:
            bibdoc.delete()
        else:
            for version, formats in versions.iteritems():
                for format, filename in formats.iteritems():
                    destination = '%s%s;%s' % (docname, format, version)
                    try:
                        shutil.move('%s/%s' % (bibdoc.basedir, filename), '%s/%s' % (bibdoc.basedir, destination))
                    except Exception, e:
                        register_exception()
                        raise InvenioWebSubmitFileError, "Error in renaming '%s' to '%s': '%s'" % ('%s/%s' % (bibdoc.basedir, filename), '%s/%s' % (bibdoc.basedir, destination), e)

            try:
                open("%s/.recid" % bibdoc.basedir, "w").write(str(self.id))
                open("%s/.type" % bibdoc.basedir, "w").write(str(bibdoc.doctype))
            except Exception, e:
                register_exception()
                raise InvenioWebSubmitFileError, "Error in creating .recid and .type file for '%s' folder: '%s'" % (bibdoc.basedir, e)

            self.build_bibdoc_list()

            res = []

            for (filename, version) in new_bibdocs:
                new_bibdoc = self.add_bibdoc(doctype=bibdoc.doctype, docname=docname, never_fail=True)
                new_bibdoc.add_file_new_format('%s/%s' % (bibdoc.basedir, filename), version)
                res.append(new_bibdoc)
                try:
                    os.remove('%s/%s' % (bibdoc.basedir, filename))
                except Exception, e:
                    register_exception()
                    raise InvenioWebSubmitFileError, "Error in removing '%s': '%s'" % ('%s/%s' % (bibdoc.basedir, filename), e)

            Md5Folder(bibdoc.basedir).update(only_new=False)

        self.build_bibdoc_list()

        return res

class BibDoc:
    """this class represents one file attached to a record
        there is a one to one mapping between an instance of this class and
        an entry in the bibdoc db table"""

    def __init__ (self, docid="", recid="", docname="file", doctype="Main"):
        """Constructor of a bibdoc. At least the docid or the recid/docname
        pair is needed."""
        # docid is known, the document already exists
        if docid != "":
            if recid == "":
                recid = None
                self.doctype = ""
                res = run_sql("select id_bibrec,type from bibrec_bibdoc "
                    "where id_bibdoc=%s", (docid,))
                if len(res) > 0:
                    recid = res[0][0]
                    self.doctype = res[0][1]
                else:
                    res = run_sql("select id_bibdoc1 from bibdoc_bibdoc "
                                  "where id_bibdoc2=%s", (docid,))
                    if len(res) > 0 :
                        main_bibdoc = res[0][0]
                        res = run_sql("select id_bibrec,type from bibrec_bibdoc "
                                      "where id_bibdoc=%s", (main_bibdoc,))
                        if len(res) > 0:
                            recid = res[0][0]
                            self.doctype = res[0][1]

            else:
                res = run_sql("select type from bibrec_bibdoc "
                    "where id_bibrec=%s and id_bibdoc=%s", (recid, docid,))
                if len(res) > 0:
                    self.doctype = res[0][0]
                else:
                    #this bibdoc isn't associated with the corresponding bibrec.
                    raise InvenioWebSubmitFileError, "No docid associated with the recid %s" % recid
            # gather the other information
            res = run_sql("select id,status,docname,creation_date,"
                "modification_date from bibdoc where id=%s", (docid,))
            if len(res) > 0:
                self.cd = res[0][3]
                self.md = res[0][4]
                self.recid = recid
                self.docname = res[0][2]
                self.id = docid
                self.status = res[0][1]
                self.basedir = _make_base_dir(self.id)
            else:
                # this bibdoc doesn't exist
                raise InvenioWebSubmitFileError, "The docid %s does not exist." % docid
        # else it is a new document
        else:
            if docname == "" or doctype == "":
                raise InvenioWebSubmitFileError, "Argument missing for creating a new bibdoc"
            else:
                self.recid = recid
                self.doctype = doctype
                self.docname = docname
                self.status = ''
                if recid:
                    res = run_sql("SELECT b.id FROM bibrec_bibdoc bb JOIN bibdoc b on bb.id_bibdoc=b.id WHERE bb.id_bibrec=%s AND b.docname=%s", (recid, docname))
                    if res:
                        raise InvenioWebSubmitFileError, "A bibdoc called %s already exists for recid %s" % (docname, recid)
                self.id = run_sql("INSERT INTO bibdoc (status,docname,creation_date,modification_date) "
                    "values(%s,%s,NOW(),NOW())", (self.status, docname,))
                if self.id is not None:
                    # we link the document to the record if a recid was
                    # specified
                    if self.recid != "":
                        run_sql("INSERT INTO bibrec_bibdoc (id_bibrec, id_bibdoc, type) VALUES (%s,%s,%s)",
                            (recid, self.id, self.doctype,))
                else:
                    raise InvenioWebSubmitFileError, "New docid cannot be created"
                self.basedir = _make_base_dir(self.id)
                # we create the corresponding storage directory
                if not os.path.exists(self.basedir):
                    old_umask = os.umask(022)
                    os.makedirs(self.basedir)
                    # and save the father record id if it exists
                    try:
                        if self.recid != "":
                            open("%s/.recid" % self.basedir, "w").write(str(self.recid))
                        if self.doctype != "":
                            open("%s/.type" % self.basedir, "w").write(str(self.doctype))
                    except Exception, e:
                        register_exception()
                        raise InvenioWebSubmitFileError, e
                    os.umask(old_umask)
        # build list of attached files
        self.build_file_list()
        # link with related_files
        self.build_related_file_list()

    def get_status(self):
        """Retrieve the status."""
        return self.status

    def touch(self):
        """Update the modification time of the bibdoc."""
        run_sql('UPDATE bibdoc SET modification_date=NOW() WHERE id=%s', (self.id, ))

    def set_status(self, new_status):
        """Set a new status."""
        run_sql('UPDATE bibdoc SET status=%s WHERE id=%s', (new_status, self.id))
        self.status = new_status
        self.build_file_list()
        self.build_related_file_list()

    def add_file_new_version(self, filename):
        """Add a new version of a file."""
        try:
            latestVersion = self.get_latest_version()
            if int(latestVersion) == 0:
                myversion = "1"
            else:
                myversion = str(int(latestVersion) + 1)
            if os.path.exists(filename):
                dummy, basename, format = decompose_file(filename)
                format = normalize_format(format)
                destination = "%s/%s%s;%s" % (self.basedir, self.docname, format, myversion)
                try:
                    shutil.copyfile(filename, destination)
                    os.chmod(destination, 0644)
                except Exception, e:
                    register_exception()
                    raise InvenioWebSubmitFileError, "Encountered an exception while copying '%s' to '%s': '%s'" % (file, destination, e)
            else:
                raise InvenioWebSubmitFileError, "'%s' does not exists!" % file
        finally:
            self.touch()
            Md5Folder(self.basedir).update()
            self.build_file_list()

    def purge(self):
        """Phisically Remove all the previous version of the given bibdoc"""
        version = self.get_latest_version()
        if version > 1:
            for file in self.docfiles:
                if file.get_version() < version:
                    try:
                        os.remove(file.get_full_path())
                    except Exception, e:
                        register_exception()
            Md5Folder(self.basedir).update()
            self.touch()
            self.build_file_list()
            self.build_related_file_list()

    def expunge(self):
        """Phisically remove all the traces of a given bibdoc"""
        for file in self.docfiles:
            try:
                os.remove(file.get_full_path())
            except Exception, e:
                register_exception()
        Md5Folder(self.basedir).update()
        self.touch()
        self.build_file_list()
        self.build_related_file_list()

    def add_file_new_format(self, filename, version=""):
        """add a new format of a file to an archive"""
        try:
            if version == "":
                version = self.get_latest_version()
            if int(version) == 0:
                version = '1'
            if os.path.exists(filename):
                dummy, basename, format = decompose_file(filename)
                format = normalize_format(format)
                destination = "%s/%s%s;%s" % (self.basedir, self.docname, format, version)
                if os.path.exists(destination):
                    raise InvenioWebSubmitFileError, "A file for docname '%s' for the recid '%s' already exists for the format '%s'" % (self.docname, self.recid, format)
                try:
                    shutil.copyfile(filename, destination)
                    os.chmod(destination, 0644)
                except Exception, e:
                    register_exception()
                    raise InvenioWebSubmitFileError, "Encountered an exception while copying '%s' to '%s': '%s'" % (file, destination, e)
            else:
                raise InvenioWebSubmitFileError, "'%s' does not exists!" % file
        finally:
            Md5Folder(self.basedir).update()
            self.touch()
            self.build_file_list()

    def get_icon(self):
        """Returns the bibdoc corresponding to an icon of the given bibdoc."""
        if self.related_files.has_key('Icon'):
            return self.related_files['Icon'][0]
        else:
            return None

    def add_icon(self, filename, basename=''):
        """Links an icon with the bibdoc object. Return the icon bibdoc"""
        #first check if an icon already exists
        existing_icon = self.get_icon()
        if existing_icon is not None:
            existing_icon.delete()
        #then add the new one
        if not basename:
            basename = decompose_file(filename)[1]
        newicon = BibDoc(doctype='Icon', docname=basename)
        newicon.add_file_new_version(filename)
        run_sql("INSERT INTO bibdoc_bibdoc (id_bibdoc1, id_bibdoc2, type) VALUES (%s,%s,'Icon')",
            (self.id, newicon.get_id(),))
        try:
            try:
                old_umask = os.umask(022)
                open("%s/.docid" % newicon.get_base_dir(), "w").write(str(self.id))
                open("%s/.type" % newicon.get_base_dir(), "w").write(str(self.doctype))
                os.umask(old_umask)
            except Exception, e:
                register_exception()
                raise InvenioWebSubmitFileError, "Encountered an exception while writing .docid and .doctype for folder '%s': '%s'" % (newicon.get_base_dir(), e)
        finally:
            Md5Folder(newicon.basedir).update()
            self.touch()
            self.build_related_file_list()
        return newicon

    def delete_icon(self):
        """Removes the current icon if it exists."""
        existing_icon = self.get_icon()
        if existing_icon is not None:
            existing_icon.delete()
        self.touch()
        self.build_related_file_list()

    def display(self, version="", ln = cdslang):
        """Returns a formatted representation of the files linked with
        the bibdoc.
        """
        t = ""
        if version == "all":
            docfiles = self.list_all_files()
        elif version != "":
            docfiles = self.list_version_files(version)
        else:
            docfiles = self.list_latest_files()
        existing_icon = self.get_icon()
        if existing_icon is not None:
            existing_icon = existing_icon.list_all_files()[0]
            imagepath = "%s/record/%s/files/%s" % \
                (weburl, self.recid, existing_icon.get_full_name())
        else:
            imagepath = "%s/smallfiles.gif" % images

        versions = []
        for version in list_versions_from_array(docfiles):
            currversion = {
                            'version' : version,
                            'previous' : 0,
                            'content' : []
                          }
            if version == self.get_latest_version() and version != "1":
                currversion['previous'] = 1
            for docfile in docfiles:
                if docfile.get_version() == version:
                    currversion['content'].append(docfile.display(ln = ln))
            versions.append(currversion)

        t = websubmit_templates.tmpl_bibdoc_filelist(
              ln = ln,
              weburl = weburl,
              versions = versions,
              imagepath = imagepath,
              docname = self.docname,
              recid = self.recid
            )
        return t

    def change_name(self, newname):
        """Rename the bibdoc name. New name must not be already used by the linked
        bibrecs."""
        res = run_sql("SELECT b.id FROM bibrec_bibdoc bb JOIN bibdoc b on bb.id_bibdoc=b.id WHERE bb.id_bibrec=%s AND b.docname=%s", (self.recid, newname))
        if res:
            raise InvenioWebSubmitFileError, "A bibdoc called %s already exists for recid %s" % (newname, self.recid)
        run_sql("update bibdoc set docname=%s where id=%s", (newname, self.id,))
        for f in os.listdir(self.basedir):
            if f.startswith(self.docname):
                shutil.move('%s/%s' % (self.basedir, f), '%s/%s' % (self.basedir, f.replace(self.docname, newname, 1)))
        self.docname = newname
        Md5Folder(self.basedir).update()
        self.touch()
        self.build_file_list()
        self.build_related_file_list()

    def get_docname(self):
        """retrieve bibdoc name"""
        return self.docname

    def get_base_dir(self):
        """retrieve bibdoc base directory, e.g. /soft/cdsweb/var/data/files/123"""
        return self.basedir

    def get_type(self):
        """retrieve bibdoc doctype"""
        return self.doctype

    def get_recid(self):
        """retrieve bibdoc recid"""
        return self.recid

    def get_id(self):
        """retrieve bibdoc id"""
        return self.id

    def get_file(self, name, format, version):
        """Return a DocFile with docname name, with format (the extension), and
        with the given version.
        """
        if version == "":
            docfiles = self.list_latest_files()
        else:
            docfiles = self.list_version_files(version)

        format = normalize_format(format)

        for docfile in docfiles:
            if docfile.get_name()==name and (docfile.get_format()==format or not format):
                return docfile
        raise InvenioWebSubmitFileError, "No file called '%s' of format '%s', version '%s'" % (name, format, version)

    def list_versions(self):
        """Returns the list of existing version numbers for a given bibdoc."""
        versions = []
        for docfile in self.docfiles:
            if not docfile.get_version() in versions:
                versions.append(docfile.get_version())
        return versions

    def delete(self):
        """delete the current bibdoc instance"""
        run_sql("UPDATE bibdoc SET status='DELETED' WHERE id=%s", (self.id,))

    def undelete(self, previous_status=''):
        """undelete a deleted file (only if it was actually deleted). The
        previous status, i.e. the restriction key can be provided.
        Otherwise the bibdoc will pe public."""
        run_sql("UPDATE bibdoc SET status=%s WHERE id=%s AND status='DELETED'", (self.id, previous_status))

    def build_file_list(self):
        """Lists all files attached to the bibdoc. This function should be
        called everytime the bibdoc is modified"""
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
                    (dirname, basename, format) = decompose_file(fullname)

                    # we can append file:
                    self.docfiles.append(BibDocFile(filepath, self.doctype,
                        fileversion, basename, format,
                        self.id, self.status, checksum))

    def build_related_file_list(self):
        """Lists all files attached to the bibdoc. This function should be
        called everytime the bibdoc is modified within e.g. its icon.
        """
        self.related_files = {}
        res = run_sql("select ln.id_bibdoc2,ln.type,bibdoc.status from "
            "bibdoc_bibdoc as ln,bibdoc where id=ln.id_bibdoc2 and "
            "ln.id_bibdoc1=%s", (self.id,))
        for row in res:
            docid = row[0]
            doctype = row[1]
            if row[2] != 'DELETED':
                if not self.related_files.has_key(doctype):
                    self.related_files[doctype] = []
                cur_doc = BibDoc(docid=docid)
                self.related_files[doctype].append(cur_doc)

    def list_all_files(self):
        """Returns all the docfiles linked with the given bibdoc."""
        return self.docfiles

    def list_latest_files(self):
        """Returns all the docfiles within the last version."""
        return self.list_version_files(self.get_latest_version())

    def list_version_files(self, version):
        """Return all the docfiles of a particular version."""
        tmp = []
        for docfile in self.docfiles:
            if docfile.get_version() == str(version):
                tmp.append(docfile)
        return tmp

    def get_latest_version(self):
        """ Returns the latest existing version number for the given bibdoc.
        If no file is associated to this bibdoc, returns '0'.
        """
        if len(self.docfiles) > 0:
            self.docfiles.sort(order_files_with_version)
            return self.docfiles[0].get_version()
        else:
            return '0'

    def get_file_number(self):
        """Return the total number of files."""
        return len(self.docfiles)

    def register_download(self, ip_address, version, format, userid=0):
        """Register the information about a download of a particular file."""
        format = normalize_format(format)
        return run_sql("INSERT INTO rnkDOWNLOADS "
            "(id_bibrec,id_bibdoc,file_version,file_format,"
            "id_user,client_host,download_time) VALUES "
            "(%s,%s,%s,%s,%s,INET_ATON(%s),NOW())",
            (self.recid, self.id, version, format,
            userid, ip_address,))

def readfile(filename):
    """Backward compatible function."""
    return open(filename).read()

class BibDocFile:
    """This class represents a physical file in the CDS Invenio filesystem.
    It should never be instantiated directly"""

    def __init__(self, fullpath, doctype, version, name, format, docid, status, checksum):
        self.fullpath = fullpath
        self.doctype = doctype
        self.docid = docid
        self.version = version
        self.status = status
        self.checksum = checksum
        self.size = os.path.getsize(fullpath)
        self.md = os.path.getmtime(fullpath)
        try:
            self.cd = os.path.getctime(fullpath)
        except OSError:
            self.cd = self.md
        self.name = name
        self.format = normalize_format(format)
        self.dir = os.path.dirname(fullpath)
        if format == "":
            self.mime = "text/plain"
            self.encoding = ""
            self.fullname = name
        else:
            self.fullname = "%s%s" % (name, self.format)
            (self.mime, self.encoding) = _mimes.guess_type(self.fullname)
            if self.mime is None:
                self.mime = "text/plain"

    def display(self, ln = cdslang):
        """Returns a formatted representation of this docfile."""
        return websubmit_templates.tmpl_bibdocfile_filelist(
                 ln = ln,
                 weburl = weburl,
                 recid = BibDoc(self.docid).get_recid(),
                 version = self.version,
                 name = self.name,
                 format = self.format,
                 size = self.size,
               )

    def is_restricted(self, req):
        """Returns restriction state. (see acc_authorize_action return values)"""
        if self.status not in ('', 'DELETED'):
            return acc_authorize_action(req, 'viewrestrdoc', status=self.status)
        elif self.status == 'DELETED':
            return (1, 'File has ben deleted')
        else:
            return (0, '')

    def get_type(self):
        return self.doctype

    def get_path(self):
        return self.fullpath

    def get_bibdocid(self):
        return self.docid

    def get_name(self):
        return self.name

    def get_full_name(self):
        return self.fullname

    def get_full_path(self):
        return self.fullpath

    def get_format(self):
        return self.format

    def get_size(self):
        return self.size

    def get_version(self):
        return self.version

    def get_checksum(self):
        return self.checksum

    def get_content(self):
        """Returns the binary content of the file."""
        return open(self.fullpath, 'rb').read()

    def get_recid(self):
        """Returns the recid connected with the bibdoc of this file."""
        try:
            return run_sql("select id_bibrec from bibrec_bibdoc where "
                "id_bibdoc=%s",(self.docid,))[0][0]
        except Exception, e:
            register_exception()
            raise InvenioWebSubmitFileError, "Encountered an exception when getting the recid of docid %s: '%s'" % (self.docid, e)

    def stream(self, req):
        """Stream the file."""
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
                try:
                    return open(self.fullpath).read()
                except Exception, e:
                    register_exception(req=req)
                    raise InvenioWebSubmitFileError, "Encountered exception while reading '%s': '%s'" % (self.fullpath, e)
            else:
                raise InvenioWebSubmitFileError, "%s does not exists!" % self.fullpath
        else:
            raise InvenioWebSubmitFileError, "You are not authorized to download %s: %s" % (self.fullname, auth_message)

def stream_restricted_icon(req):
    """Return the content of the "Restricted Icon" file."""
    req.content_type = 'image/gif'
    req.encoding = None
    req.filename = 'restricted'
    req.headers_out["Content-Disposition"] = \
        "attachment; filename=%s" % quoteattr('restricted')
    req.send_http_header()
    try:
        return open('%s/img/restricted.gif' % webdir, "r").read()
    except Exception, e:
        register_exception(req=req)
        raise InvenioWebSubmitFileError, "Encountered exception while streaming restricted icon: '%s'" % (e, )

def list_types_from_array(bibdocs):
    """Retrieves the list of types from the given bibdoc list."""
    types = []
    for bibdoc in bibdocs:
        if not bibdoc.get_type() in types:
            types.append(bibdoc.get_type())
    return types

def list_versions_from_array(docfiles):
    """Retrieve the list of existing versions from the given docfiles list."""
    versions = []
    for docfile in docfiles:
        if not docfile.get_version() in versions:
            versions.append(docfile.get_version())
    return versions

def order_files_with_version(docfile1, docfile2):
    """order docfile objects according to their version"""
    version1 = int(docfile1.get_version())
    version2 = int(docfile2.get_version())
    return cmp(version2, version1)

def _make_base_dir(docid):
    """Given a docid it returns the complete path that should host its files."""
    group = "g" + str(int(int(docid) / filedirsize))
    return "%s/%s/%s" % (filedir, group, docid)


class Md5Folder:
    """Manage all the Md5 checksum about a folder"""
    def __init__(self, folder):
        """Initialize the class from the md5 checksum of a given path"""
        self.folder = folder
        try:
            self.load()
        except InvenioWebSubmitFileError:
            self.md5s = {}
            self.update()

    def update(self, only_new = True):
        """Update the .doc_checksum file with the current files. If only_new
        is specified then only not already calculated file are calculated."""
        if os.path.exists(self.folder):
            for filename in os.listdir(self.folder):
                if not only_new or self.md5s.get(filename, None) is None and \
                        not filename.startswith('.'):
                    try:
                        self.md5s[filename] = md5.new(open("%s/%s" %
                            (self.folder, filename), "rb").read()).hexdigest()
                    except Exception, e:
                        register_exception()
                        raise InvenioWebSubmitFileError, "Encountered an exception while updating .doc_checksum for folder '%s' with file '%s': '%s'" % (self.folder, filename, e)
        self.store()

    def store(self):
        """Store the current md5 dictionary into .doc_checksum"""
        try:
            old_umask = os.umask(022)
            md5file = open("%s/.doc_checksum" % self.folder, "w")
            for key, value in self.md5s.items():
                md5file.write('%s *%s\n' % (value, key))
            os.umask(old_umask)
        except Exception, e:
            register_exception()
            raise InvenioWebSubmitFileError, "Encountered an exception while storing .doc_checksum for folder '%s': '%s'" % (self.folder, e)

    def load(self):
        """Load .doc_checksum into the md5 dictionary"""
        self.md5s = {}
        try:
            for row in open("%s/.doc_checksum" % self.folder, "r"):
                md5hash = row[:32]
                filename = row[34:].strip()
                self.md5s[filename] = md5hash
        except IOError:
            self.update()
        except Exception, e:
            register_exception()
            raise InvenioWebSubmitFileError, "Encountered an exception while loading .doc_checksum for folder '%s': '%s'" % (self.folder, e)


    def check(self, filename = ''):
        """Check the specified file or all the files for which it exists a hash
        for being coherent with the stored hash."""
        if filename and filename in self.md5s.keys():
            try:
                return self.md5s[filename] == md5.new(open("%s/%s" %
                        (self.folder, filename), "rb").read()).hexdigest()
            except Exception, e:
                register_exception()
                raise InvenioWebSubmitFileError, "Encountered an exception while loading '%s/%s': '%s'" % (self.folder, filename, e)
        else:
            for filename, md5hash in self.md5s.items():
                try:
                    if md5.new(open("%s/%s" % (self.folder, filename),
                        "rb").read()).hexdigest() != md5hash:
                        return False
                except Exception, e:
                    register_exception()
                    raise InvenioWebSubmitFileError, "Encountered an exception while loading '%s/%s': '%s'" % (self.folder, filename, e)
            return True

    def get_checksum(self, filename):
        """Return the checksum of a physical file."""
        md5hash = self.md5s.get(filename, None)
        if md5hash is None:
            self.update()
        # Now it should not fail!
        md5hash = self.md5s[filename]
        return md5hash

