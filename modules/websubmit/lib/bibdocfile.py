## $Id$

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

__revision__ = "$Id$"

import os
import re
import shutil
import md5
import filecmp
import time
import socket
import urllib2
import urllib
import tempfile
import cPickle
from datetime import datetime
from xml.sax.saxutils import quoteattr
from mimetypes import MimeTypes

## Let's set a reasonable timeout for URL request (e.g. FFT)
socket.setdefaulttimeout(40)

try:
    set
except NameError:
    from sets import Set as set

from invenio.dbquery import run_sql, DatabaseError, blob_to_string
from invenio.errorlib import register_exception
from invenio.bibrecord import create_record, record_get_field_instances, \
    field_get_subfield_values, field_get_subfield_instances
from invenio.access_control_engine import acc_authorize_action
from invenio.config import CFG_SITE_LANG, CFG_SITE_URL, CFG_SITE_URL, \
    CFG_WEBDIR, CFG_WEBSUBMIT_FILEDIR,\
    CFG_WEBSUBMIT_ADDITIONAL_KNOWN_FILE_EXTENSIONS, \
    CFG_WEBSUBMIT_FILESYSTEM_BIBDOC_GROUP_LIMIT, CFG_SITE_SECURE_URL, \
    CFG_BIBUPLOAD_FFT_ALLOWED_LOCAL_PATHS, \
    CFG_TMPDIR
from invenio.bibformat import format_record
import invenio.template
websubmit_templates = invenio.template.load('websubmit')
websearch_templates = invenio.template.load('websearch')

CFG_BIBDOCFILE_MD5_THRESHOLD = 256 * 1024
CFG_BIBDOCFILE_MD5_BUFFER = 1024 * 1024
CFG_BIBDOCFILE_MD5SUM_EXISTS = os.system('which md5sum 2>&1 > /dev/null') == 0

KEEP_OLD_VALUE = 'KEEP-OLD-VALUE'

_mimes = MimeTypes()
_mimes.suffix_map.update({'.tbz2' : '.tar.bz2'})
_mimes.encodings_map.update({'.bz2' : 'bzip2'})
_extensions = _mimes.encodings_map.keys() + \
              _mimes.suffix_map.keys() + \
              _mimes.types_map[1].keys() + \
              CFG_WEBSUBMIT_ADDITIONAL_KNOWN_FILE_EXTENSIONS
_extensions.sort()
_extensions.reverse()
_extensions = set([ext.lower() for ext in _extensions])

class InvenioWebSubmitFileError(Exception):
    pass

def file_strip_ext(afile):
    """Strip in the best way the extension from a filename"""
    lowfile = afile.lower()
    ext = '.'
    while ext:
        ext = ''
        for c_ext in _extensions:
            if lowfile.endswith(c_ext):
                lowfile = lowfile[0:-len(c_ext)]
                ext = c_ext
                break
    return afile[:len(lowfile)]

def normalize_format(format):
    """Normalize the format."""
    #format = format.lower()
    if format and format[0] != '.':
        format = '.' + format
    #format = format.replace('.jpg', '.jpeg')
    return format

_docname_re = re.compile(r'[^-\w.]*')
def normalize_docname(docname):
    """Normalize the docname (only digit and alphabetic letters and underscore are allowed)"""
    #return _docname_re.sub('', docname)
    return docname

def normalize_version(version):
    """Normalize the version."""
    try:
        int(version)
    except ValueError:
        if version.lower().strip() == 'all':
            return 'all'
        else:
            return ''
    return str(version)

_path_re = re.compile(r'.*[\\/:]')
def decompose_file(afile):
    """Decompose a file into dirname, basename and extension"""
    basename = _path_re.sub('', afile)
    dirname = afile[:-len(basename)-1]
    base = file_strip_ext(basename)
    extension = basename[len(base) + 1:]
    if extension:
        extension = '.' + extension
    return (dirname, base, extension)

def propose_unique_name(afile, use_version=False):
    """Propose a unique name, taking in account the version"""
    if use_version:
        version = ';'+re.sub('.*;', '', afile)
        afile = afile[:-len(version)]
    else:
        version = ''
    (basedir, basename, extension) = decompose_file(afile)
    goodname = "%s%s%s" % (basename, extension, version)
    i = 1
    listdir = os.listdir(basedir)
    while goodname in listdir:
        i += 1
        goodname = "%s_%s%s%s" % (basename, i, extension, version)
    return "%s/%s" % (basedir, goodname)

class BibRecDocs:
    """this class represents all the files attached to one record"""
    def __init__(self, recid, deleted_too=False):
        self.id = recid
        self.deleted_too = deleted_too
        self.bibdocs = []
        self.build_bibdoc_list()

    def __repr__(self):
        if self.deleted_too:
            return 'BibRecDocs(%s, True)' % self.id
        else:
            return 'BibRecDocs(%s)' % self.id

    def __str__(self):
        out = '%i::::total bibdocs attached=%i\n' % (self.id, len(self.bibdocs))
        out += '%i::::total size latest version=%s\n' % (self.id, nice_size(self.get_total_size_latest_version()))
        out += '%i::::total size all files=%s\n' % (self.id, nice_size(self.get_total_size()))
        for bibdoc in self.bibdocs:
            out += str(bibdoc)
        return out

    def empty_p(self):
        """Return True if the bibrec is empty, i.e. it has no bibdocs
        connected."""
        return len(self.bibdocs) == 0

    def deleted_p(self):
        """Return True if the bibrec has been deleted."""
        from invenio.search_engine import record_exists
        return record_exists(self.id) == -1

    def get_xml_8564(self):
        """Return a snippet of XML representing the 8564 corresponding to the
        current state"""
        out = ''
        xml = format_record(self.id, of='xm')
        record = create_record(xml)[0]
        fields = record_get_field_instances(record, '856', '4', ' ')
        for field in fields:
            url = field_get_subfield_values(field, 'u')
            if not bibdocfile_url_p(url):
                out += '\t<datafield tag="856" ind1="4" ind2=" ">\n'
                for subfield, value in field_get_subfield_instances(field):
                    out += '\t\t<subfield code="%s">%s</subfield>\n' % (subfield, value)
                out += '\t</datafield>\n'

        for afile in self.list_latest_files():
            out += '\t<datafield tag="856" ind1="4" ind2=" ">\n'
            url = afile.get_url()
            description = afile.get_description()
            comment = afile.get_comment()
            if url:
                out += '\t\t<subfield code="u">%s</subfield>\n' % url
            if description:
                out += '\t\t<subfield code="y">%s</subfield>\n' % description
            if comment:
                out += '\t\t<subfield code="z">%s</subfield>\n' % comment
            out += '\t</datafield>\n'

        for bibdoc in self.bibdocs:
            icon = bibdoc.get_icon()
            if icon:
                icon = icon.list_all_files()
                if icon:
                    out += '\t<datafield tag="856" ind1="4" ind2=" ">\n'
                    out += '\t\t<subfield code="q">%s</subfield>\n' % icon[0].get_url()
                    out += '\t\t<subfield code="x">icon</subfield>\n'
                    out += '\t</datafield>\n'

        return out

    def get_total_size_latest_version(self):
        """Return the total size used on disk of all the files belonging
        to this record and corresponding to the latest version."""
        size = 0
        for bibdoc in self.bibdocs:
            size += bibdoc.get_total_size_latest_version()
        return size

    def get_total_size(self):
        """Return the total size used on disk of all the files belonging
        to this record of any version."""
        size = 0
        for bibdoc in self.bibdocs:
            size += bibdoc.get_total_size()
        return size

    def build_bibdoc_list(self):
        """This function must be called everytime a bibdoc connected to this
        recid is added, removed or modified.
        """
        self.bibdocs = []
        if self.deleted_too:
            res = run_sql("""SELECT id_bibdoc, type FROM bibrec_bibdoc JOIN
                         bibdoc ON id=id_bibdoc WHERE id_bibrec=%s
                         ORDER BY docname ASC""", (self.id,))
        else:
            res = run_sql("""SELECT id_bibdoc, type FROM bibrec_bibdoc JOIN
                         bibdoc ON id=id_bibdoc WHERE id_bibrec=%s AND
                         status<>'DELETED' ORDER BY docname ASC""", (self.id,))
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
        potential = [afile for afile in files if afile.get_size() == size]

        if potential:
            checksum = calculate_md5(path)

            # Let's consider all the latest files with the same size and the
            # same checksum
            potential = [afile for afile in potential if afile.get_checksum() == checksum]

            if potential:
                potential = [afile for afile in potential if filecmp.cmp(afile.get_full_path(), path)]

                if potential:
                    return True
                else:
                    # Gosh! How unlucky, same size, same checksum but not same
                    # content!
                    pass
        return False

    def propose_unique_docname(self, docname):
        """Propose a unique docname."""
        docname = normalize_docname(docname)
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

    def has_docname_p(self, docname):
        """Return True if a bibdoc with a particular docname belong to this
        record."""
        for bibdoc in self.bibdocs:
            if bibdoc.docname == docname:
                return True
        return False

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
        try:
            docname = normalize_docname(docname)
            if never_fail:
                docname = self.propose_unique_docname(docname)
            if docname in self.get_bibdoc_names():
                raise InvenioWebSubmitFileError, "%s has already a bibdoc with docname %s" % (self.id, docname)
            else:
                bibdoc = BibDoc(recid=self.id, doctype=doctype, docname=docname)
                self.build_bibdoc_list()
                return bibdoc
        except:
            register_exception()
            raise

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
        docname = normalize_docname(docname)
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

    def add_new_version(self, fullpath, docname, description=None, comment=None):
        """Adds a new fullpath file to an already existent docid making the
        previous files associated with the same bibdocids obsolete.
        It returns the bibdoc object.
        """
        bibdoc = self.get_bibdoc(docname=docname)
        bibdoc.add_file_new_version(fullpath, description, comment)
        return bibdoc

    def add_new_format(self, fullpath, docname, description=None, comment=None):
        """Adds a new format for a fullpath file to an already existent
        docid along side already there files.
        It returns the bibdoc object.
        """
        bibdoc = self.get_bibdoc(docname=docname)
        bibdoc.add_file_new_format(fullpath, description, comment)
        return bibdoc

    def list_latest_files(self, doctype=''):
        """Returns a list which is made up by all the latest docfile of every
        bibdoc (of a particular doctype).
        """
        docfiles = []
        for bibdoc in self.list_bibdocs(doctype):
            docfiles += bibdoc.list_latest_files()
        return docfiles

    def display(self, docname="", version="", doctype="", ln=CFG_SITE_LANG):
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
        name. Proper .recid, .type, .md5 files will be created/updated.
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
        zero_version_bug = False
        if os.path.exists(bibdoc.basedir):
            for filename in os.listdir(bibdoc.basedir):
                if filename[0] != '.' and ';' in filename:
                    name, version = filename.split(';')
                    try:
                        version = int(version)
                    except ValueError:
                        # Strange name, let's skip it...
                        register_exception()
                        continue
                    if version == 0:
                        zero_version_bug = True
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
                if zero_version_bug:
                    version += 1
                for format, filename in formats.iteritems():
                    destination = '%s%s;%i' % (docname, format, version)
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
                if zero_version_bug:
                    version += 1
                new_bibdoc = self.add_bibdoc(doctype=bibdoc.doctype, docname=docname, never_fail=True)
                new_bibdoc.add_file_new_format('%s/%s' % (bibdoc.basedir, filename), version)
                res.append(new_bibdoc)
                try:
                    os.remove('%s/%s' % (bibdoc.basedir, filename))
                except Exception, e:
                    register_exception()
                    raise InvenioWebSubmitFileError, "Error in removing '%s': '%s'" % ('%s/%s' % (bibdoc.basedir, filename), e)

            Md5Folder(bibdoc.basedir).update(only_new=False)
        bibdoc._build_file_list()
        self.build_bibdoc_list()

        for bibdoc in self.bibdocs:
            if not run_sql('SELECT more_info FROM bibdoc WHERE id=%s', (bibdoc.id,)):
                ## Import from MARC only if the bibdoc has never had
                ## its more_info initialized.
                try:
                    bibdoc.import_descriptions_and_comments_from_marc()
                except Exception, e:
                    register_exception()
                    raise InvenioWebSubmitFileError, "Error in importing description and comment from %s for record %s: %s" % (repr(bibdoc), self.id, e)
        return res

class BibDoc:
    """this class represents one file attached to a record
        there is a one to one mapping between an instance of this class and
        an entry in the bibdoc db table"""

    def __init__ (self, docid="", recid="", docname="file", doctype="Main"):
        """Constructor of a bibdoc. At least the docid or the recid/docname
        pair is needed."""
        # docid is known, the document already exists
        docname = normalize_docname(docname)
        self.docfiles = []
        self.md5s = None
        self.related_files = []
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
                "modification_date,more_info from bibdoc where id=%s", (docid,))
            if len(res) > 0:
                self.cd = res[0][3]
                self.md = res[0][4]
                self.recid = recid
                self.docname = res[0][2]
                self.id = docid
                self.status = res[0][1]
                self.more_info = BibDocMoreInfo(docid, blob_to_string(res[0][5]))
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
                    "values(%s,%s,NOW(),NOW())", (self.status, docname))
                if self.id is not None:
                    # we link the document to the record if a recid was
                    # specified
                    self.more_info = BibDocMoreInfo(self.id)
                    if self.recid != "":
                        run_sql("INSERT INTO bibrec_bibdoc (id_bibrec, id_bibdoc, type) VALUES (%s,%s,%s)",
                            (recid, self.id, self.doctype,))
                    res = run_sql("select creation_date, modification_date from bibdoc where id=%s", (self.id,))
                    self.cd = res[0][0]
                    self.md = res[0][0]
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
        self._build_file_list('init')
        # link with related_files
        self._build_related_file_list()

    def __repr__(self):
        return 'BibDoc(%s, %s, %s, %s)' % (repr(self.id), repr(self.recid), repr(self.docname), repr(self.doctype))

    def __str__(self):
        out = '%s:%i:::docname=%s\n' % (self.recid or '', self.id, self.docname)
        out += '%s:%i:::doctype=%s\n' % (self.recid or '', self.id, self.doctype)
        out += '%s:%i:::status=%s\n' % (self.recid or '', self.id, self.status)
        out += '%s:%i:::basedir=%s\n' % (self.recid or '', self.id, self.basedir)
        out += '%s:%i:::creation date=%s\n' % (self.recid or '', self.id, self.cd)
        out += '%s:%i:::modification date=%s\n' % (self.recid or '', self.id, self.md)
        out += '%s:%i:::total file attached=%s\n' % (self.recid or '', self.id, len(self.docfiles))
        out += '%s:%i:::total size latest version=%s\n' % (self.recid or '', self.id, nice_size(self.get_total_size_latest_version()))
        out += '%s:%i:::total size all files=%s\n' % (self.recid or '', self.id, nice_size(self.get_total_size()))
        for docfile in self.docfiles:
            out += str(docfile)
        icon = self.get_icon()
        if icon:
            out += str(self.get_icon())
        return out

    def get_status(self):
        """Retrieve the status."""
        return self.status

    def touch(self):
        """Update the modification time of the bibdoc."""
        run_sql('UPDATE bibdoc SET modification_date=NOW() WHERE id=%s', (self.id, ))
        if self.recid:
            run_sql('UPDATE bibrec SET modification_date=NOW() WHERE id=%s', (self.recid, ))

    def set_status(self, new_status):
        """Set a new status."""
        if new_status != KEEP_OLD_VALUE:
            if new_status == 'DELETED':
                raise InvenioWebSubmitFileError('DELETED is a reserved word and can not be used for setting the status')
            run_sql('UPDATE bibdoc SET status=%s WHERE id=%s', (new_status, self.id))
            self.status = new_status
            self.touch()
            self._build_file_list()
            self._build_related_file_list()

    def add_file_new_version(self, filename, description=None, comment=None):
        """Add a new version of a file."""
        try:
            latestVersion = self.get_latest_version()
            if latestVersion == 0:
                myversion = 1
            else:
                myversion = latestVersion + 1
            if os.path.exists(filename):
                dummy, dummy, format = decompose_file(filename)
                destination = "%s/%s%s;%i" % (self.basedir, self.docname, format, myversion)
                try:
                    shutil.copyfile(filename, destination)
                    os.chmod(destination, 0644)
                except Exception, e:
                    register_exception()
                    raise InvenioWebSubmitFileError, "Encountered an exception while copying '%s' to '%s': '%s'" % (filename, destination, e)
                self.more_info.set_description(description, format, myversion)
                self.more_info.set_comment(comment, format, myversion)
            else:
                raise InvenioWebSubmitFileError, "'%s' does not exists!" % filename
        finally:
            self.touch()
            Md5Folder(self.basedir).update()
            self._build_file_list()

    def purge(self):
        """Phisically Remove all the previous version of the given bibdoc"""
        version = self.get_latest_version()
        if version > 1:
            for afile in self.docfiles:
                if afile.get_version() < version:
                    self.more_info.unset_comment(afile.get_format(), afile.get_version())
                    self.more_info.unset_description(afile.get_format(), afile.get_version())
                    try:
                        os.remove(afile.get_full_path())
                    except Exception, e:
                        register_exception()
            Md5Folder(self.basedir).update()
            self.touch()
            self._build_file_list()

    def expunge(self):
        """Phisically remove all the traces of a given bibdoc"""
        for afile in self.docfiles:
            try:
                self.more_info.unset_comment(afile.get_format(), afile.get_version())
                self.more_info.unset_description(afile.get_format(), afile.get_version())
                os.remove(afile.get_full_path())
            except Exception, e:
                register_exception()
        Md5Folder(self.basedir).update()
        self.touch()
        self._build_file_list()

    def revert(self, version):
        """Revert to a given version by copying its differnt formats to a new
        version."""
        try:
            version = int(version)
            new_version = self.get_latest_version() + 1
            for docfile in self.list_version_files(version):
                destination = "%s/%s%s;%i" % (self.basedir, self.docname, docfile.get_format(), new_version)
                if os.path.exists(destination):
                    raise InvenioWebSubmitFileError, "A file for docname '%s' for the recid '%s' already exists for the format '%s'" % (self.docname, self.recid, docfile.get_format())
                try:
                    shutil.copyfile(docfile.get_full_path(), destination)
                    os.chmod(destination, 0644)
                    self.more_info.set_comment(self.more_info.get_comment(docfile.get_format(), version), docfile.get_format(), new_version)
                    self.more_info.set_description(self.more_info.get_description(docfile.get_format(), version), docfile.get_format(), new_version)
                except Exception, e:
                    register_exception()
                    raise InvenioWebSubmitFileError, "Encountered an exception while copying '%s' to '%s': '%s'" % (docfile.get_full_path(), destination, e)
        finally:
            Md5Folder(self.basedir).update()
            self.touch()
            self._build_file_list()

    def import_descriptions_and_comments_from_marc(self):
        """Import description & comment from the corresponding marc."""
        ## Let's get the record
        xml = format_record(self.id, of='xm')
        record = create_record(xml)[0]
        fields = record_get_field_instances(record, '856', '4', ' ')

        global_comment = None
        global_description = None
        local_comment = {}
        local_description = {}

        for field in fields:
            url = field_get_subfield_values(field, 'u')
            if url:
                ## Given a url
                url = url[0]
                if url == '%s/record/%s/files/' % (CFG_SITE_URL, self.recid):
                    ## If it is a traditional /record/1/files/ one
                    ## We have global description/comment for all the formats
                    description = field_get_subfield_values(field, 'y')
                    if description:
                        global_description = description[0]
                    comment = field_get_subfield_values(field, 'z')
                    if comment:
                        global_comment = comment[0]
                elif bibdocfile_url_p(url):
                    ## Otherwise we have description/comment per format
                    dummy, docname, format = decompose_bibdocfile_url(url)
                    if docname == self.docname:
                        description = field_get_subfield_values(field, 'y')
                        if description:
                            local_description[format] = description[0]
                        comment = field_get_subfield_values(field, 'z')
                        if comment:
                            local_comment[format] = comment[0]

        ## Let's update the tables
        version = self.get_latest_version()
        for docfile in self.list_latest_files():
            format = docfile.get_format()
            if format in local_comment:
                self.set_comment(local_comment[format], format, version)
            else:
                self.set_comment(global_comment, format, version)
            if format in local_description:
                self.set_description(local_description[format], format, version)
            else:
                self.set_description(global_description, format, version)
        self._build_file_list('init')

    def add_file_new_format(self, filename, version=None, description=None, comment=None):
        """add a new format of a file to an archive"""
        try:
            if version is None:
                version = self.get_latest_version()
            if version == 0:
                version = 1
            if os.path.exists(filename):
                dummy, dummy, format = decompose_file(filename)
                destination = "%s/%s%s;%i" % (self.basedir, self.docname, format, version)
                if os.path.exists(destination):
                    raise InvenioWebSubmitFileError, "A file for docname '%s' for the recid '%s' already exists for the format '%s'" % (self.docname, self.recid, format)
                try:
                    shutil.copyfile(filename, destination)
                    os.chmod(destination, 0644)
                except Exception, e:
                    register_exception()
                    raise InvenioWebSubmitFileError, "Encountered an exception while copying '%s' to '%s': '%s'" % (filename, destination, e)
                self.more_info.set_comment(comment, format, version)
                self.more_info.set_description(description, format, version)
            else:
                raise InvenioWebSubmitFileError, "'%s' does not exists!" % filename
        finally:
            Md5Folder(self.basedir).update()
            self.touch()
            self._build_file_list()

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
            self._build_related_file_list()
        return newicon

    def delete_icon(self):
        """Removes the current icon if it exists."""
        existing_icon = self.get_icon()
        if existing_icon is not None:
            existing_icon.delete()
        self.touch()
        self._build_related_file_list()

    def display(self, version="", ln = CFG_SITE_LANG):
        """Returns a formatted representation of the files linked with
        the bibdoc.
        """
        t = ""
        if version == "all":
            docfiles = self.list_all_files()
        elif version != "":
            version = int(version)
            docfiles = self.list_version_files(version)
        else:
            docfiles = self.list_latest_files()
        existing_icon = self.get_icon()
        if existing_icon is not None:
            existing_icon = existing_icon.list_all_files()[0]
            imageurl = "%s/record/%s/files/%s" % \
                (CFG_SITE_URL, self.recid, existing_icon.get_full_name())
        else:
            imageurl = "%s/img/smallfiles.gif" % CFG_SITE_URL

        versions = []
        for version in list_versions_from_array(docfiles):
            currversion = {
                            'version' : version,
                            'previous' : 0,
                            'content' : []
                          }
            if version == self.get_latest_version() and version != 1:
                currversion['previous'] = 1
            for docfile in docfiles:
                if docfile.get_version() == version:
                    currversion['content'].append(docfile.display(ln = ln))
            versions.append(currversion)

        t = websubmit_templates.tmpl_bibdoc_filelist(
              ln = ln,
              versions = versions,
              imageurl = imageurl,
              docname = self.docname,
              recid = self.recid
            )
        return t

    def change_name(self, newname):
        """Rename the bibdoc name. New name must not be already used by the linked
        bibrecs."""
        newname = normalize_docname(newname)
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
        self._build_file_list('rename')
        self._build_related_file_list()

    def set_comment(self, comment, format, version=None):
        """Update the comment of a format/version."""
        if version is None:
            version = self.get_latest_version()
        self.more_info.set_comment(comment, format, version)
        self.touch()
        self._build_file_list('init')

    def set_description(self, description, format, version=None):
        """Update the description of a format/version."""
        if version is None:
            version = self.get_latest_version()
        self.more_info.set_description(description, format, version)
        self.touch()
        self._build_file_list('init')

    def get_comment(self, format, version=None):
        """Get a comment for a given format/version."""
        if version is None:
            version = self.get_latest_version()
        return self.more_info.get_comment(format, version)

    def get_description(self, format, version=None):
        """Get a description for a given format/version."""
        if version is None:
            version = self.get_latest_version()
        return self.more_info.get_description(format, version)

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

    def get_file(self, format, version=""):
        """Return a DocFile with docname name, with format (the extension), and
        with the given version.
        """
        if version == "":
            docfiles = self.list_latest_files()
        else:
            version = int(version)
            docfiles = self.list_version_files(version)

        format = normalize_format(format)

        for docfile in docfiles:
            if (docfile.get_format()==format or not format):
                return docfile
        raise InvenioWebSubmitFileError, "No file called '%s' of format '%s', version '%s'" % (self.docname, format, version)

    def list_versions(self):
        """Returns the list of existing version numbers for a given bibdoc."""
        versions = []
        for docfile in self.docfiles:
            if not docfile.get_version() in versions:
                versions.append(docfile.get_version())
        return versions

    def delete(self):
        """delete the current bibdoc instance."""
        try:
            self.change_name('DELETED-%s-%s' % (datetime.today().strftime('%Y%m%d%H%M%S'), self.docname))
            run_sql("UPDATE bibdoc SET status='DELETED' WHERE id=%s", (self.id,))
        except Exception, e:
            register_exception()
            raise InvenioWebSubmitFileError, "It's impossible to delete bibdoc %s: %s" % (self.id, e)

    def deleted_p(self):
        """Return True if the bibdoc has been deleted."""
        return self.status == 'DELETED'

    def empty_p(self):
        """Return True if the bibdoc is empty, i.e. it has no bibdocfile
        connected."""
        return len(self.docfiles) == 0

    def undelete(self, previous_status=''):
        """undelete a deleted file (only if it was actually deleted). The
        previous status, i.e. the restriction key can be provided.
        Otherwise the bibdoc will pe public."""
        try:
            run_sql("UPDATE bibdoc SET status=%s WHERE id=%s AND status='DELETED'", (self.id, previous_status))
        except Exception, e:
            register_exception()
            raise InvenioWebSubmitFileError, "It's impossible to undelete bibdoc %s: %s" % (self.id, e)
        if self.docname.startswith('DELETED-'):
            try:
                # Let's remove DELETED-20080214144322- in front of the docname
                original_name = '-'.join(self.docname.split('-')[2:])
                self.change_name(original_name)
            except Exception, e:
                register_exception()
                raise InvenioWebSubmitFileError, "It's impossible to restore the previous docname %s. %s kept as docname because: %s" % (original_name, self.docname, e)
        else:
            raise InvenioWebSubmitFileError, "Strange just undeleted docname isn't called DELETED-somedate-docname but %s" % self.docname

    def delete_file(self, format, version):
        """Delete on the filesystem the particular format version.
        Note, this operation is not reversible!"""
        try:
            afile = self.get_file(format, version)
        except InvenioWebSubmitFileError:
            return
        try:
            os.remove(afile.get_full_path())
        except OSError:
            pass
        self.touch()
        self._build_file_list()

    def get_history(self):
        """Return a string with a line for each row in the history for the
        given docid."""
        ret = []
        hst = run_sql("""SELECT action, docname, docformat, docversion,
                docsize, docchecksum, doctimestamp
                FROM hstDOCUMENT
                WHERE id_bibdoc=%s ORDER BY doctimestamp ASC""", (self.id, ))
        for row in hst:
            ret.append("%s %s '%s', format: '%s', version: %i, size: %s, checksum: '%s'" % (row[6].strftime('%Y-%m-%d %H:%M:%S'), row[0], row[1], row[2], row[3], nice_size(row[4]), row[5]))
        return ret

    def _build_file_list(self, context=''):
        """Lists all files attached to the bibdoc. This function should be
        called everytime the bibdoc is modified.
        As a side effect it log everything that has happened to the bibdocfiles
        in the log facility, according to the context:
        "init": means that the function has been called;
        for the first time by a constructor, hence no logging is performed
        "": by default means to log every deleted file as deleted and every
        added file as added;
        "rename": means that every appearently deleted file is logged as
        renamef and every new file as renamet.
        """

        def log_action(action, docid, docname, format, version, size, checksum, timestamp=''):
            """Log an action into the bibdoclog table."""
            try:
                if timestamp:
                    run_sql('INSERT DELAYED INTO hstDOCUMENT(action, id_bibdoc, docname, docformat, docversion, docsize, docchecksum, doctimestamp) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)', (action, docid, docname, format, version, size, checksum, timestamp))
                else:
                    run_sql('INSERT DELAYED INTO hstDOCUMENT(action, id_bibdoc, docname, docformat, docversion, docsize, docchecksum, doctimestamp) VALUES(%s, %s, %s, %s, %s, %s, %s, NOW())', (action, docid, docname, format, version, size, checksum))
            except DatabaseError:
                register_exception()

        def make_removed_added_bibdocfiles(previous_file_list):
            """Internal function for build the log of changed files."""

            # Let's rebuild the previous situation
            old_files = {}
            for bibdocfile in previous_file_list:
                old_files[(bibdocfile.name, bibdocfile.format, bibdocfile.version)] = (bibdocfile.size, bibdocfile.checksum, bibdocfile.md)

            # Let's rebuild the new situation
            new_files = {}
            for bibdocfile in self.docfiles:
                new_files[(bibdocfile.name, bibdocfile.format, bibdocfile.version)] = (bibdocfile.size, bibdocfile.checksum, bibdocfile.md)

            # Let's subtract from added file all the files that are present in
            # the old list, and let's add to deleted files that are not present
            # added file.
            added_files = dict(new_files)
            deleted_files = {}
            for key, value in old_files.iteritems():
                if added_files.has_key(key):
                    del added_files[key]
                else:
                    deleted_files[key] = value
            return (added_files, deleted_files)

        if context != 'init':
            previous_file_list = list(self.docfiles)
        self.docfiles = []
        if os.path.exists(self.basedir):
            self.md5s = Md5Folder(self.basedir)
            files = os.listdir(self.basedir)
            files.sort()
            for afile in files:
                if not afile.startswith('.'):
                    try:
                        filepath = os.path.join(self.basedir, afile)
                        fileversion = int(re.sub(".*;", "", afile))
                        fullname = afile.replace(";%s" % fileversion, "")
                        checksum = self.md5s.get_checksum(afile)
                        (dirname, basename, format) = decompose_file(fullname)
                        comment = self.more_info.get_comment(format, fileversion)
                        description = self.more_info.get_description(format, fileversion)
                        # we can append file:
                        self.docfiles.append(BibDocFile(filepath, self.doctype,
                            fileversion, basename, format,
                            self.recid, self.id, self.status, checksum, description, comment))
                    except Exception, e:
                        register_exception()
        if context == 'init':
            return
        else:
            added_files, deleted_files = make_removed_added_bibdocfiles(previous_file_list)
            deletedstr = "DELETED"
            addedstr = "ADDED"
            if context == 'rename':
                deletedstr = "RENAMEDFROM"
                addedstr = "RENAMEDTO"
            for (docname, format, version), (size, checksum, md) in added_files.iteritems():
                if context == 'rename':
                    md = '' # No modification time
                log_action(addedstr, self.id, docname, format, version, size, checksum, md)
            for (docname, format, version), (size, checksum, md) in deleted_files.iteritems():
                if context == 'rename':
                    md = '' # No modification time
                log_action(deletedstr, self.id, docname, format, version, size, checksum, md)

    def _build_related_file_list(self):
        """Lists all files attached to the bibdoc. This function should be
        called everytime the bibdoc is modified within e.g. its icon.
        """
        self.related_files = {}
        res = run_sql("SELECT ln.id_bibdoc2,ln.type,bibdoc.status FROM "
            "bibdoc_bibdoc AS ln,bibdoc WHERE id=ln.id_bibdoc2 AND "
            "ln.id_bibdoc1=%s", (self.id,))
        for row in res:
            docid = row[0]
            doctype = row[1]
            if row[2] != 'DELETED':
                if not self.related_files.has_key(doctype):
                    self.related_files[doctype] = []
                cur_doc = BibDoc(docid=docid)
                self.related_files[doctype].append(cur_doc)

    def get_total_size_latest_version(self):
        """Return the total size used on disk of all the files belonging
        to this bibdoc and corresponding to the latest version."""
        ret = 0
        for bibdocfile in self.list_latest_files():
            ret += bibdocfile.get_size()
        return ret

    def get_total_size(self):
        """Return the total size used on disk of all the files belonging
        to this bibdoc."""
        ret = 0
        for bibdocfile in self.list_all_files():
            ret += bibdocfile.get_size()
        return ret

    def list_all_files(self):
        """Returns all the docfiles linked with the given bibdoc."""
        return self.docfiles

    def list_latest_files(self):
        """Returns all the docfiles within the last version."""
        return self.list_version_files(self.get_latest_version())

    def list_version_files(self, version):
        """Return all the docfiles of a particular version."""
        version = int(version)
        return [docfile for docfile in self.docfiles if docfile.get_version() == version]

    def get_latest_version(self):
        """ Returns the latest existing version number for the given bibdoc.
        If no file is associated to this bibdoc, returns '0'.
        """
        version = 0
        for bibdocfile in self.docfiles:
            if bibdocfile.get_version() > version:
                version = bibdocfile.get_version()
        return version

    def get_file_number(self):
        """Return the total number of files."""
        return len(self.docfiles)

    def register_download(self, ip_address, version, format, userid=0):
        """Register the information about a download of a particular file."""
        format = normalize_format(format)
        if format[:1] == '.':
            format = format[1:]
        format = format.upper()
        return run_sql("INSERT INTO rnkDOWNLOADS "
            "(id_bibrec,id_bibdoc,file_version,file_format,"
            "id_user,client_host,download_time) VALUES "
            "(%s,%s,%s,%s,%s,INET_ATON(%s),NOW())",
            (self.recid, self.id, version, format,
            userid, ip_address,))

class BibDocFile:
    """This class represents a physical file in the CDS Invenio filesystem.
    It should never be instantiated directly"""

    def __init__(self, fullpath, doctype, version, name, format, recid, docid, status, checksum, description=None, comment=None):
        self.fullpath = fullpath
        self.doctype = doctype
        self.docid = docid
        self.recid = recid
        self.version = version
        self.status = status
        self.checksum = checksum
        self.description = description
        self.comment = comment
        self.size = os.path.getsize(fullpath)
        self.md = datetime.fromtimestamp(os.path.getmtime(fullpath))
        try:
            self.cd = datetime.fromtimestamp(os.path.getctime(fullpath))
        except OSError:
            self.cd = self.md
        self.name = name
        self.format = normalize_format(format)
        self.dir = os.path.dirname(fullpath)
        self.url = '%s/record/%s/files/%s%s' % (CFG_SITE_URL, self.recid, self.name, self.format)
        if format == "":
            self.mime = "text/plain"
            self.encoding = ""
            self.fullname = name
        else:
            self.fullname = "%s%s" % (name, self.format)
            (self.mime, self.encoding) = _mimes.guess_type(self.fullname)
            if self.mime is None:
                self.mime = "text/plain"

    def __repr__(self):
        return ('BibDocFile(%s, %s, %i, %s, %s, %i, %i, %s, %s, %s, %s)' % (repr(self.fullpath), repr(self.doctype), self.version, repr(self.name), repr(self.format), self.recid, self.docid, repr(self.status), repr(self.checksum), repr(self.description), repr(self.comment)))

    def __str__(self):
        out = '%s:%s:%s:%s:fullpath=%s\n' % (self.recid, self.docid, self.version, self.format, self.fullpath)
        out += '%s:%s:%s:%s:fullname=%s\n' % (self.recid, self.docid, self.version, self.format, self.fullname)
        out += '%s:%s:%s:%s:name=%s\n' % (self.recid, self.docid, self.version, self.format, self.name)
        out += '%s:%s:%s:%s:status=%s\n' % (self.recid, self.docid, self.version, self.format, self.status)
        out += '%s:%s:%s:%s:checksum=%s\n' % (self.recid, self.docid, self.version, self.format, self.checksum)
        out += '%s:%s:%s:%s:size=%s\n' % (self.recid, self.docid, self.version, self.format, nice_size(self.size))
        out += '%s:%s:%s:%s:creation time=%s\n' % (self.recid, self.docid, self.version, self.format, self.cd)
        out += '%s:%s:%s:%s:modification time=%s\n' % (self.recid, self.docid, self.version, self.format, self.md)
        out += '%s:%s:%s:%s:encoding=%s\n' % (self.recid, self.docid, self.version, self.format, self.encoding)
        out += '%s:%s:%s:%s:url=%s\n' % (self.recid, self.docid, self.version, self.format, self.url)
        out += '%s:%s:%s:%s:description=%s\n' % (self.recid, self.docid, self.version, self.format, self.description)
        out += '%s:%s:%s:%s:comment=%s\n' % (self.recid, self.docid, self.version, self.format, self.comment)
        return out

    def display(self, ln = CFG_SITE_LANG):
        """Returns a formatted representation of this docfile."""
        return websubmit_templates.tmpl_bibdocfile_filelist(
                 ln = ln,
                 recid = self.recid,
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

    def get_url(self):
        return self.url

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

    def get_description(self):
        return self.description

    def get_comment(self):
        return self.comment

    def get_content(self):
        """Returns the binary content of the file."""
        return open(self.fullpath, 'rb').read()

    def get_recid(self):
        """Returns the recid connected with the bibdoc of this file."""
        return self.recid

    def get_status(self):
        """Returns the status of the file, i.e. either '', 'DELETED' or a
        restriction keyword."""
        return self.status

    def check(self):
        """Return True if the checksum corresponds to the file."""
        return calculate_md5(self.fullpath) == self.checksum

    def stream(self, req):
        """Stream the file."""
        if self.status:
            (auth_code, auth_message) = acc_authorize_action(req, 'viewrestrdoc', status=self.status)
        else:
            auth_code = 0
        if auth_code == 0:
            if os.path.exists(self.fullpath):
                if calculate_md5(self.fullpath) != self.checksum:
                    raise InvenioWebSubmitFileError, "File %s, version %i, for record %s is corrupted!" % (self.fullname, self.version, self.recid)
                req.content_type = self.mime
                req.encoding = self.encoding
                req.filename = self.fullname
                req.headers_out["Content-Disposition"] = \
                    "inline; filename=%s" % quoteattr(self.fullname)
                req.set_content_length(self.size)
                req.send_http_header()
                try:
                    req.sendfile(self.fullpath)
                    return ""
                except IOError, e:
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
        "inline; filename=%s" % quoteattr('restricted')
    req.set_content_length(os.path.getsize('%s/img/restricted.gif' % CFG_WEBDIR))
    req.send_http_header()
    try:
        req.sendfile('%s/img/restricted.gif' % CFG_WEBDIR)
        return ""
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
    version1 = docfile1.get_version()
    version2 = docfile2.get_version()
    return cmp(version2, version1)

def _make_base_dir(docid):
    """Given a docid it returns the complete path that should host its files."""
    group = "g" + str(int(int(docid) / CFG_WEBSUBMIT_FILESYSTEM_BIBDOC_GROUP_LIMIT))
    return os.path.join(CFG_WEBSUBMIT_FILEDIR, group, str(docid))


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
        """Update the .md5 file with the current files. If only_new
        is specified then only not already calculated file are calculated."""
        if not only_new:
            self.md5s = {}
        if os.path.exists(self.folder):
            for filename in os.listdir(self.folder):
                if filename not in self.md5s and not filename.startswith('.'):
                    self.md5s[filename] = calculate_md5(os.path.join(self.folder, filename))
        self.store()

    def store(self):
        """Store the current md5 dictionary into .md5"""
        try:
            old_umask = os.umask(022)
            md5file = open(os.path.join(self.folder, ".md5"), "w")
            for key, value in self.md5s.items():
                md5file.write('%s *%s\n' % (value, key))
            os.umask(old_umask)
        except Exception, e:
            register_exception()
            raise InvenioWebSubmitFileError, "Encountered an exception while storing .md5 for folder '%s': '%s'" % (self.folder, e)

    def load(self):
        """Load .md5 into the md5 dictionary"""
        self.md5s = {}
        try:
            for row in open(os.path.join(self.folder, ".md5"), "r"):
                md5hash = row[:32]
                filename = row[34:].strip()
                self.md5s[filename] = md5hash
        except IOError:
            self.update()
        except Exception, e:
            register_exception()
            raise InvenioWebSubmitFileError, "Encountered an exception while loading .md5 for folder '%s': '%s'" % (self.folder, e)

    def check(self, filename = ''):
        """Check the specified file or all the files for which it exists a hash
        for being coherent with the stored hash."""
        if filename and filename in self.md5s.keys():
            try:
                return self.md5s[filename] == calculate_md5(os.path.join(self.folder, filename))
            except Exception, e:
                register_exception()
                raise InvenioWebSubmitFileError, "Encountered an exception while loading '%s': '%s'" % (os.path.join(self.folder, filename), e)
        else:
            for filename, md5hash in self.md5s.items():
                try:
                    if calculate_md5(os.path.join(self.folder, filename)) != md5hash:
                        return False
                except Exception, e:
                    register_exception()
                    raise InvenioWebSubmitFileError, "Encountered an exception while loading '%s': '%s'" % (os.path.join(self.folder, filename), e)
            return True

    def get_checksum(self, filename):
        """Return the checksum of a physical file."""
        md5hash = self.md5s.get(filename, None)
        if md5hash is None:
            self.update()
        # Now it should not fail!
        md5hash = self.md5s[filename]
        return md5hash

def calculate_md5_external(filename):
    """Calculate the md5 of a physical file through md5sum Command Line Tool.
    This is suitable for file larger than 256Kb."""
    try:
        md5_result = os.popen('md5sum -b "%s"' % filename)
        ret = md5_result.read()[:32]
        md5_result.close()
        if len(ret) != 32:
            # Error in running md5sum. Let's fallback to internal
            # algorithm.
            return calculate_md5(filename, force_internal=True)
        else:
            return ret
    except Exception, e:
        raise InvenioWebSubmitFileError, "Encountered an exception while calculating md5 for file '%s': '%s'" % (filename, e)

def calculate_md5(filename, force_internal=False):
    """Calculate the md5 of a physical file. This is suitable for files smaller
    than 256Kb."""
    if not CFG_BIBDOCFILE_MD5SUM_EXISTS or force_internal or os.path.getsize(filename) < CFG_BIBDOCFILE_MD5_THRESHOLD:
        try:
            to_be_read = open(filename, "rb")
            computed_md5 = md5.new()
            while True:
                buf = to_be_read.read(CFG_BIBDOCFILE_MD5_BUFFER)
                if buf:
                    computed_md5.update(buf)
                else:
                    break
            return computed_md5.hexdigest()
        except Exception, e:
            register_exception()
            raise InvenioWebSubmitFileError, "Encountered an exception while calculating md5 for file '%s': '%s'" % (filename, e)
    else:
        return calculate_md5_external(filename)


def bibdocfile_url_to_bibrecdocs(url):
    """Given an URL in the form CFG_SITE_[SECURE_]URL/record/xxx/files/... it returns
    a BibRecDocs object for the corresponding recid."""

    recid = decompose_bibdocfile_url(url)[0]
    return BibRecDocs(recid)

def bibdocfile_url_to_bibdoc(url):
    """Given an URL in the form CFG_SITE_[SECURE_]URL/record/xxx/files/... it returns
    a BibDoc object for the corresponding recid/docname."""

    docname = decompose_bibdocfile_url(url)[1]
    return bibdocfile_url_to_bibrecdocs(url).get_bibdoc(docname)

def bibdocfile_url_to_bibdocfile(url):
    """Given an URL in the form CFG_SITE_[SECURE_]URL/record/xxx/files/... it returns
    a BibDocFile object for the corresponding recid/docname/format."""
    dummy, dummy, format = decompose_bibdocfile_url(url)
    return bibdocfile_url_to_bibdoc(url).get_file(format)

def bibdocfile_url_to_fullpath(url):
    """Given an URL in the form CFG_SITE_[SECURE_]URL/record/xxx/files/... it returns
    the fullpath for the corresponding recid/docname/format."""

    return bibdocfile_url_to_bibdocfile(url).get_full_path()

def bibdocfile_url_p(url):
    """Return True when the url is a potential valid url pointing to a
    fulltext owned by a system."""
    if not (url.startswith('%s/record/' % CFG_SITE_URL) or url.startswith('%s/record/' % CFG_SITE_SECURE_URL)):
        return False
    splitted_url = url.split('/files/')
    return len(splitted_url) == 2 and splitted_url[0] != '' and splitted_url[1] != ''

def decompose_bibdocfile_url(url):
    """Given a bibdocfile_url return a triple (recid, docname, format)."""
    if url.startswith('%s/record/' % CFG_SITE_URL):
        recid_file = url[len('%s/record/' % CFG_SITE_URL):]
    elif url.startswith('%s/record/' % CFG_SITE_SECURE_URL):
        recid_file = url[len('%s/record/' % CFG_SITE_SECURE_URL):]
    else:
        raise InvenioWebSubmitFileError, "Url %s doesn't correspond to a valid record inside the system." % url
    recid_file = recid_file.replace('/files/', '/')
    recid, docname, format = decompose_file(recid_file)
    return (int(recid), docname, format)

def nice_size(size):
    """Return a nicely printed size in kilo."""
    unit = 'B'
    if size > 1024:
        size /= 1024.0
        unit = 'KB'
        if size > 1024:
            size /= 1024.0
            unit = 'MB'
            if size > 1024:
                size /= 1024.0
                unit = 'GB'
    return '%s %s' % (websearch_templates.tmpl_nice_number(size, max_ndigits_after_dot=2), unit)

def get_docname_from_url(url):
    """Return a potential docname given a url"""
    path = urllib2.urlparse.urlsplit(url)[2]
    filename = os.path.split(path)[-1]
    return file_strip_ext(filename)

def get_format_from_url(url):
    """Return a potential format given a url"""
    path = urllib2.urlparse.urlsplit(url)[2]
    filename = os.path.split(path)[-1]
    return filename[len(file_strip_ext(filename)):]

def clean_url(url):
    """Given a local url e.g. a local path it render it a realpath."""
    protocol = urllib2.urlparse.urlsplit(url)[0]
    if protocol in ('', 'file'):
        path = urllib2.urlparse.urlsplit(url)[2]
        return os.path.realpath(path)
    else:
        return url

def check_valid_url(url):
    """Check for validity of a url or a file."""
    try:
        protocol = urllib2.urlparse.urlsplit(url)[0]
        if protocol in ('', 'file'):
            path = urllib2.urlparse.urlsplit(url)[2]
            if os.path.realpath(path) != path:
                raise StandardError, "%s is not a normalized path (would be %s)." % (path, os.path.normpath(path))
            for allowed_path in CFG_BIBUPLOAD_FFT_ALLOWED_LOCAL_PATHS + [CFG_TMPDIR]:
                if path.startswith(allowed_path):
                    open(path)
                    return
            raise StandardError, "%s is not in one of the allowed paths." % path
        else:
            urllib2.urlopen(url)
    except Exception, e:
        raise StandardError, "%s is not a correct url: %s" % (url, e)

def download_url(url, format):
    """Download a url (if it corresponds to a remote file) and return a local url
    to it."""
    protocol = urllib2.urlparse.urlsplit(url)[0]
    tmppath = tempfile.mkstemp(suffix=format, dir=CFG_TMPDIR)[1]
    try:
        if protocol in ('', 'file'):
            path = urllib2.urlparse.urlsplit(url)[2]
            if os.path.realpath(path) != path:
                raise StandardError, "%s is not a normalized path (would be %s)." % (path, os.path.normpath(path))
            for allowed_path in CFG_BIBUPLOAD_FFT_ALLOWED_LOCAL_PATHS + [CFG_TMPDIR]:
                if path.startswith(allowed_path):
                    shutil.copy(path, tmppath)
                    return tmppath
            raise StandardError, "%s is not in one of the allowed paths." % path
        else:
            urllib.urlretrieve(url, tmppath)
            return tmppath
    except:
        os.remove(tmppath)
        raise

class BibDocMoreInfo:
    """Class to wrap the serialized bibdoc more_info. At the moment
    it stores descriptions and comments for each BibDoc."""
    def __init__(self, docid, more_info=None):
        try:
            assert(type(docid) in (long, int) and docid > 0)
            self.docid = docid
            try:
                if more_info is None:
                    res = run_sql('SELECT more_info FROM bibdoc WHERE id=%s', (docid, ))
                    if res and res[0][0]:
                        self.more_info = cPickle.loads(blob_to_string(res[0][0]))
                    else:
                        self.more_info = {}
                else:
                    self.more_info = cPickle.loads(more_info)
            except:
                self.more_info = {}
            if 'descriptions' not in self.more_info:
                self.more_info['descriptions'] = {}
            if 'comments' not in self.more_info:
                self.more_info['comments'] = {}
        except:
            register_exception()
            raise

    def flush(self):
        """if __dirty is True reserialize di DB."""
        run_sql('UPDATE bibdoc SET more_info=%s WHERE id=%s', (cPickle.dumps(self.more_info), self.docid))

    def get_comment(self, format, version):
        """Return the comment corresponding to the given docid/format/version."""
        try:
            assert(type(version) is int)
            return self.more_info['comments'].get(version, {}).get(format)
        except:
            register_exception()
            raise

    def get_description(self, format, version):
        """Return the description corresponding to the given docid/format/version."""
        try:
            assert(type(version) is int)
            return self.more_info['descriptions'].get(version, {}).get(format)
        except:
            register_exception()
            raise

    def set_comment(self, comment, format, version):
        """Store a comment corresponding to the given docid/format/version."""
        try:
            assert(type(version) is int and version > 0)
            if comment == KEEP_OLD_VALUE:
                comment = self.get_comment(format, version) or self.get_comment(format, version - 1)
            if not comment:
                self.unset_comment(format, version)
                self.flush()
                return
            if not version in self.more_info['comments']:
                self.more_info['comments'][version] = {}
            self.more_info['comments'][version][format] = comment
            self.flush()
        except:
            register_exception()
            raise

    def set_description(self, description, format, version):
        """Store a description corresponding to the given docid/format/version."""
        try:
            assert(type(version) is int and version > 0)
            if description == KEEP_OLD_VALUE:
                description = self.get_description(format, version) or self.get_description(format, version - 1)
            if not description:
                self.unset_description(format, version)
                self.flush()
                return
            if not version in self.more_info['descriptions']:
                self.more_info['descriptions'][version] = {}
            self.more_info['descriptions'][version][format] = description
            self.flush()
        except:
            register_exception()
            raise

    def unset_comment(self, format, version):
        """Remove a comment."""
        try:
            assert(type(version) is int and version > 0)
            del self.more_info['comments'][version][format]
            self.flush()
        except KeyError:
            pass
        except:
            register_exception()
            raise

    def unset_description(self, format, version):
        """Remove a description."""
        try:
            assert(type(version) is int and version > 0)
            del self.more_info['descriptions'][version][format]
            self.flush()
        except KeyError:
            pass
        except:
            register_exception()
            raise

    def serialize(self):
        """Return the serialized version of the more_info."""
        return cPickle.dumps(self.more_info)

def readfile(filename):
    """Try to read a file. Return '' in case of any error.
    This function is useful for quick implementation of websubmit functions.
    """
    try:
        return open(filename).read()
    except:
        return ''
