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
import random
import socket
import urllib2
import urllib
import tempfile
import cPickle
import base64
import binascii
import cgi

try:
    import magic
    CFG_HAS_MAGIC = True
except ImportError:
    CFG_HAS_MAGIC = False
from datetime import datetime
from mimetypes import MimeTypes
from thread import get_ident

try:
    from mod_python import apache
except ImportError:
    pass

## Let's set a reasonable timeout for URL request (e.g. FFT)
socket.setdefaulttimeout(40)

try:
    set
except NameError:
    from sets import Set as set

from invenio.shellutils import escape_shell_arg
from invenio.dbquery import run_sql, DatabaseError, blob_to_string
from invenio.errorlib import register_exception
from invenio.bibrecord import record_get_field_instances, \
    field_get_subfield_values, field_get_subfield_instances, \
    encode_for_xml
from invenio.access_control_engine import acc_authorize_action
from invenio.config import CFG_SITE_LANG, CFG_SITE_URL, \
    CFG_WEBDIR, CFG_WEBSUBMIT_FILEDIR,\
    CFG_WEBSUBMIT_ADDITIONAL_KNOWN_FILE_EXTENSIONS, \
    CFG_WEBSUBMIT_FILESYSTEM_BIBDOC_GROUP_LIMIT, CFG_SITE_SECURE_URL, \
    CFG_BIBUPLOAD_FFT_ALLOWED_LOCAL_PATHS, \
    CFG_TMPDIR, CFG_PATH_MD5SUM, \
    CFG_WEBSUBMIT_STORAGEDIR
from invenio.bibformat import format_record
import invenio.template
websubmit_templates = invenio.template.load('websubmit')
websearch_templates = invenio.template.load('websearch')

CFG_BIBDOCFILE_MD5_THRESHOLD = 256 * 1024
CFG_BIBDOCFILE_MD5_BUFFER = 1024 * 1024
CFG_BIBDOCFILE_STRONG_FORMAT_NORMALIZATION = False

KEEP_OLD_VALUE = 'KEEP-OLD-VALUE'
_mimes = MimeTypes(strict=False)
_mimes.suffix_map.update({'.tbz2' : '.tar.bz2'})
_mimes.encodings_map.update({'.bz2' : 'bzip2'})

_magic_cookies = {}
def get_magic_cookies():
    """Return a tuple of magic object.
    ... not real magic. Just see: man file(1)"""
    thread_id = get_ident()
    if thread_id not in _magic_cookies:
        _magic_cookies[thread_id] = {
            magic.MAGIC_NONE : magic.open(magic.MAGIC_NONE),
            magic.MAGIC_COMPRESS : magic.open(magic.MAGIC_COMPRESS),
            magic.MAGIC_MIME : magic.open(magic.MAGIC_MIME),
            magic.MAGIC_COMPRESS + magic.MAGIC_MIME : magic.open(magic.MAGIC_COMPRESS + magic.MAGIC_MIME)
        }
        for key in _magic_cookies[thread_id].keys():
            _magic_cookies[thread_id][key].load()
    return _magic_cookies[thread_id]

def _generate_extensions():
    _tmp_extensions = _mimes.encodings_map.keys() + \
                _mimes.suffix_map.keys() + \
                _mimes.types_map[1].keys() + \
                CFG_WEBSUBMIT_ADDITIONAL_KNOWN_FILE_EXTENSIONS
    extensions = []
    for ext in _tmp_extensions:
        if ext.startswith('.'):
            extensions.append(ext)
        else:
            extensions.append('.' + ext)
    extensions.sort()
    extensions.reverse()
    extensions = set([ext.lower() for ext in extensions])
    extensions = '\\' + '$|\\'.join(extensions) + '$'
    extensions = extensions.replace('+', '\\+')
    return re.compile(extensions, re.I)

_extensions = _generate_extensions()


class InvenioWebSubmitFileError(Exception):
    pass

def file_strip_ext(afile, skip_version=False):
    """Strip in the best way the extension from a filename"""
    if skip_version:
        afile = afile.split(';')[0]
    nextfile = _extensions.sub('', afile)
    while nextfile != afile:
        nextfile = _extensions.sub('', afile)
        afile = nextfile
    else:
        nextfile = afile.split('.')[0]
    return nextfile

def normalize_format(format):
    """Normalize the format."""
    if format and format[0] != '.':
        format = '.' + format
    if CFG_BIBDOCFILE_STRONG_FORMAT_NORMALIZATION:
        if format not in ('.Z', '.H', '.C', '.CC'):
            format = format.lower()
        format = format.replace('.jpg', '.jpeg')
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

def decompose_file(afile, skip_version=False):
    """Decompose a file into dirname, basename and extension.
    Note that if provided with a URL, the scheme in front will be part
    of the dirname."""
    if skip_version:
        version = afile.split(';')[-1]
        try:
            int(version)
            afile = afile[:-len(version)-1]
        except ValueError:
            pass
    basename = os.path.basename(afile)
    dirname = afile[:-len(basename)-1]
    base = file_strip_ext(basename)
    extension = basename[len(base) + 1:]
    if extension:
        extension = '.' + extension
    return (dirname, base, extension)

def decompose_file_with_version(afile):
    """Decompose a file into dirname, basename, extension and version.
    In case version does not exist it will raise ValueError.
    Note that if provided with a URL, the scheme in front will be part
    of the dirname."""
    version_str = afile.split(';')[-1]
    version = int(version_str)
    afile = afile[:-len(version_str)-1]
    basename = os.path.basename(afile)
    dirname = afile[:-len(basename)-1]
    base = file_strip_ext(basename)
    extension = basename[len(base) + 1:]
    if extension:
        extension = '.' + extension
    return (dirname, base, extension, version)


def propose_next_docname(docname):
    """Propose a next docname docname"""
    if '_' in docname:
        split_docname = docname.split('_')
        try:
            split_docname[-1] = str(int(split_docname[-1]) + 1)
            docname = '_'.join(split_docname)
        except ValueError:
            docname += '_1'
    else:
        docname += '_1'
    return docname

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
        from invenio.search_engine import get_record
        out = ''
        record = get_record(self.id)
        fields = record_get_field_instances(record, '856', '4', ' ')
        for field in fields:
            url = field_get_subfield_values(field, 'u')
            if not bibdocfile_url_p(url):
                out += '\t<datafield tag="856" ind1="4" ind2=" ">\n'
                for subfield, value in field_get_subfield_instances(field):
                    out += '\t\t<subfield code="%s">%s</subfield>\n' % (subfield, encode_for_xml(value))
                out += '\t</datafield>\n'

        for afile in self.list_latest_files():
            out += '\t<datafield tag="856" ind1="4" ind2=" ">\n'
            url = afile.get_url()
            description = afile.get_description()
            comment = afile.get_comment()
            if url:
                out += '\t\t<subfield code="u">%s</subfield>\n' % encode_for_xml(url)
            if description:
                out += '\t\t<subfield code="y">%s</subfield>\n' % encode_for_xml(description)
            if comment:
                out += '\t\t<subfield code="z">%s</subfield>\n' % encode_for_xml(comment)
            out += '\t</datafield>\n'

        for bibdoc in self.bibdocs:
            icon = bibdoc.get_icon()
            if icon:
                icon = icon.list_all_files()
                if icon:
                    out += '\t<datafield tag="856" ind1="4" ind2=" ">\n'
                    out += '\t\t<subfield code="q">%s</subfield>\n' % encode_for_xml(icon[0].get_url())
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

    def merge_bibdocs(self, docname1, docname2):
        """This method merge docname2 into docname1.
        Given all the formats of the latest version of docname2 the files
        are added as new formats into docname1.
        Docname2 is marked as deleted.
        This method fails if at least one format in docname2 already exists
        in docname1. (In this case the two bibdocs are preserved)
        Comments and descriptions are also copied and if docname2 has an icon
        and docname1 has not, the icon is imported.
        If docname2 has a restriction(status) and docname1 has not the
        restriction is imported."""

        bibdoc1 = self.get_bibdoc(docname1)
        bibdoc2 = self.get_bibdoc(docname2)

        ## Check for possibility
        for bibdocfile in bibdoc2.list_latest_files():
            format = bibdocfile.get_format()
            if bibdoc1.format_already_exists_p(format):
                raise InvenioWebSubmitFileError('Format %s already exists in bibdoc %s of record %s. It\'s impossible to merge bibdoc %s into it.' % (format, docname1, self.id, docname2))

        ## Importing Icon if needed.
        icon1 = bibdoc1.get_icon()
        icon2 = bibdoc2.get_icon()
        if icon2 is not None and icon1 is None:
            icon = icon2.list_latest_files()[0]
            bibdoc1.add_icon(icon.get_full_path(), format=icon.get_format())

        ## Importing restriction if needed.
        restriction1 = bibdoc1.get_status()
        restriction2 = bibdoc2.get_status()
        if restriction2 and not restriction1:
            bibdoc1.set_status(restriction2)

        ## Importing formats
        for bibdocfile in bibdoc2.list_latest_files():
            format = bibdocfile.get_format()
            comment = bibdocfile.get_comment()
            description = bibdocfile.get_description()
            bibdoc1.add_file_new_format(bibdocfile.get_full_path(), description=description, comment=comment, format=format)

        ## Finally deleting old bibdoc2
        bibdoc2.delete()
        self.build_bibdoc_list()

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
        except Exception, e:
            register_exception()
            raise InvenioWebSubmitFileError(str(e))

    def add_new_file(self, fullpath, doctype="Main", docname=None, never_fail=False, description=None, comment=None, format=None):
        """Adds a new file with the following policy: if the docname is not set
        it is retrieved from the name of the file. If bibdoc with the given
        docname doesn't exist, it is created and the file is added to it.
        It it exist but it doesn't contain the format that is being added, the
        new format is added. If the format already exists then if never_fail
        is True a new bibdoc is created with a similar name but with a progressive
        number as a suffix and the file is added to it. The elaborated bibdoc
        is returned.
        """
        if docname is None:
            docname = decompose_file(fullpath)[1]
        if format is None:
            format = decompose_file(fullpath)[2]
        docname = normalize_docname(docname)
        try:
            bibdoc = self.get_bibdoc(docname)
        except InvenioWebSubmitFileError:
            # bibdoc doesn't already exists!
            bibdoc = self.add_bibdoc(doctype, docname, False)
            bibdoc.add_file_new_version(fullpath, description=description, comment=comment, format=format)
        else:
            try:
                bibdoc.add_file_new_format(fullpath, description=description, comment=comment, format=format)
            except InvenioWebSubmitFileError, e:
                # Format already exist!
                if never_fail:
                    bibdoc = self.add_bibdoc(doctype, docname, True)
                    bibdoc.add_file_new_version(fullpath, description=description, comment=comment, format=format)
                else:
                    raise e
        return bibdoc

    def add_new_version(self, fullpath, docname=None, description=None, comment=None, format=None, hide_previous_versions=False):
        """Adds a new fullpath file to an already existent docid making the
        previous files associated with the same bibdocids obsolete.
        It returns the bibdoc object.
        """
        if docname is None:
            docname = decompose_file(fullpath)[1]
        if format is None:
            format = decompose_file(fullpath)[2]
        bibdoc = self.get_bibdoc(docname=docname)
        bibdoc.add_file_new_version(fullpath, description=description, comment=comment, format=format, hide_previous_versions=hide_previous_versions)
        return bibdoc

    def add_new_format(self, fullpath, docname=None, description=None, comment=None, format=None):
        """Adds a new format for a fullpath file to an already existent
        docid along side already there files.
        It returns the bibdoc object.
        """
        if docname is None:
            docname = decompose_file(fullpath)[1]
        if format is None:
            format = decompose_file(fullpath)[2]
        bibdoc = self.get_bibdoc(docname=docname)
        bibdoc.add_file_new_format(fullpath, description=description, comment=comment, format=format)
        return bibdoc

    def list_latest_files(self, doctype=''):
        """Returns a list which is made up by all the latest docfile of every
        bibdoc (of a particular doctype).
        """
        docfiles = []
        for bibdoc in self.list_bibdocs(doctype):
            docfiles += bibdoc.list_latest_files()
        return docfiles

    def display(self, docname="", version="", doctype="", ln=CFG_SITE_LANG, verbose=0, display_hidden=True):
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
                            ln=ln, display_hidden=display_hidden))
                fulltypes.append(fulltype)

            if verbose >= 9:
                verbose_files = str(self)
            else:
                verbose_files = ''

            t = websubmit_templates.tmpl_bibrecdoc_filelist(
                  ln=ln,
                  types = fulltypes,
                  verbose_files=verbose_files
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
                        # Strange name
                        register_exception()
                        raise InvenioWebSubmitFileError, "A file called %s exists under %s. This is not a valid name. After the ';' there must be an integer representing the file revision. Please, manually fix this file either by renaming or by deleting it." % (filename, bibdoc.basedir)
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
                elif filename[0] != '.':
                    # Strange name
                    register_exception()
                    raise InvenioWebSubmitFileError, "A file called %s exists under %s. This is not a valid name. There should be a ';' followed by an integer representing the file revision. Please, manually fix this file either by renaming or by deleting it." % (filename, bibdoc.basedir)
        else:
            # we create the corresponding storage directory
            old_umask = os.umask(022)
            os.makedirs(bibdoc.basedir)
            # and save the father record id if it exists
            try:
                if self.id != "":
                    recid_fd = open("%s/.recid" % bibdoc.basedir, "w")
                    recid_fd.write(str(self.id))
                    recid_fd.close()
                if bibdoc.doctype != "":
                    type_fd = open("%s/.type" % bibdoc.basedir, "w")
                    type_fd.write(str(bibdoc.doctype))
                    type_fd.close()
            except Exception, e:
                register_exception()
                raise InvenioWebSubmitFileError, e
            os.umask(old_umask)


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
                recid_fd = open("%s/.recid" % bibdoc.basedir, "w")
                recid_fd.write(str(self.id))
                recid_fd.close()
                type_fd = open("%s/.type" % bibdoc.basedir, "w")
                type_fd.write(str(bibdoc.doctype))
                type_fd.close()
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

    def check_format(self, docname):
        """In case CFG_WEBSUBMIT_ADDITIONAL_KNOWN_FILE_EXTENSIONS is
        altered or Python version changes, it might happen that a docname
        contains files which are no more docname + .format ; version, simply
        because the .format is now recognized (and it was not before, so
        it was contained into the docname).
        This algorithm verify if it is necessary to fix.
        Return True if format is correct. False if a fix is needed."""
        bibdoc = self.get_bibdoc(docname)
        correct_docname = decompose_file(docname)[1]
        if docname != correct_docname:
            return False
        for filename in os.listdir(bibdoc.basedir):
            if not filename.startswith('.'):
                try:
                    dummy, dummy, format, version = decompose_file_with_version(filename)
                except:
                    raise InvenioWebSubmitFileError('Incorrect filename "%s" for docname %s for recid %i' % (filename, docname, self.id))
                if '%s%s;%i' % (correct_docname, format, version) != filename:
                    return False
        return True

    def check_duplicate_docnames(self):
        """Check wethever the record is connected with at least tho bibdoc
        with the same docname.
        Return True if everything is fine.
        """
        docnames = set()
        for docname in self.get_bibdoc_names():
            if docname in docnames:
                return False
            else:
                docnames.add(docname)
        return True

    def uniformize_bibdoc(self, docname):
        """This algorithm correct wrong file name belonging to a bibdoc."""
        bibdoc = self.get_bibdoc(docname)
        for filename in os.listdir(bibdoc.basedir):
            if not filename.startswith('.'):
                try:
                    dummy, dummy, format, version = decompose_file_with_version(filename)
                except ValueError:
                    register_exception(alert_admin=True, prefix= "Strange file '%s' is stored in %s" % (filename, bibdoc.basedir))
                else:
                    os.rename(os.path.join(bibdoc.basedir, filename), os.path.join(bibdoc.basedir, '%s%s;%i' % (docname, format, version)))
        Md5Folder(bibdoc.basedir).update()
        bibdoc.touch()
        bibdoc._build_file_list('rename')

    def fix_format(self, docname, skip_check=False):
        """ Fixing this situation require
        different steps, because docname might already exists.
        This algorithm try to fix this situation.
        In case a merging is needed the algorithm return False if the merging
        is not possible.
        """
        if not skip_check:
            if self.check_format(docname):
                return True
        bibdoc = self.get_bibdoc(docname)
        correct_docname = decompose_file(docname)[1]
        need_merge = False
        if correct_docname != docname:
            need_merge = self.has_docname_p(correct_docname)
            if need_merge:
                proposed_docname = self.propose_unique_docname(correct_docname)
                run_sql('UPDATE bibdoc SET docname=%s WHERE id=%s', (proposed_docname, bibdoc.id))
                self.build_bibdoc_list()
                self.uniformize_bibdoc(proposed_docname)
                try:
                    self.merge_bibdocs(docname, proposed_docname)
                except InvenioWebSubmitFileError:
                    return False
            else:
                run_sql('UPDATE bibdoc SET docname=%s WHERE id=%s', (correct_docname, bibdoc.id))
                self.build_bibdoc_list()
                self.uniformize_bibdoc(correct_docname)
        else:
            self.uniformize_bibdoc(docname)
        return True

    def fix_duplicate_docnames(self, skip_check=False):
        """Algotirthm to fix duplicate docnames.
        If a record is connected with at least two bibdoc having the same
        docname, the algorithm will try to merge them.
        """
        if not skip_check:
            if self.check_duplicate_docnames():
                return
        docnames = set()
        for bibdoc in self.list_bibdocs():
            docname = bibdoc.docname
            if docname in docnames:
                new_docname = self.propose_unique_docname(bibdoc.docname)
                bibdoc.change_name(new_docname)
                self.merge_bibdocs(docname, new_docname)
            docnames.add(docname)

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
                    res = run_sql("SELECT creation_date, modification_date FROM bibdoc WHERE id=%s", (self.id,))
                    self.cd = res[0][0]
                    self.md = res[0][0]
                else:
                    raise InvenioWebSubmitFileError, "New docid cannot be created"
                try:
                    self.basedir = _make_base_dir(self.id)
                    # we create the corresponding storage directory
                    if not os.path.exists(self.basedir):
                        old_umask = os.umask(022)
                        os.makedirs(self.basedir)
                        # and save the father record id if it exists
                        try:
                            if self.recid != "":
                                recid_fd = open("%s/.recid" % self.basedir, "w")
                                recid_fd.write(str(self.recid))
                                recid_fd.close()
                            if self.doctype != "":
                                type_fd = open("%s/.type" % self.basedir, "w")
                                type_fd.write(str(self.doctype))
                                type_fd.close()
                        except Exception, e:
                            register_exception()
                            raise InvenioWebSubmitFileError, e
                        os.umask(old_umask)
                    if self.recid != "":
                        run_sql("INSERT INTO bibrec_bibdoc (id_bibrec, id_bibdoc, type) VALUES (%s,%s,%s)",
                            (recid, self.id, self.doctype,))
                except Exception, e:
                    run_sql('DELETE FROM bibdoc WHERE id=%s', (self.id, ))
                    run_sql('DELETE FROM bibrec_bibdoc WHERE id_bibdoc=%s', (self.id, ))
                    register_exception()
                    raise InvenioWebSubmitFileError, e
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

    def format_already_exists_p(self, format):
        """Return True if the given format already exists among the latest files."""
        format = normalize_format(format)
        for afile in self.list_latest_files():
            if format == afile.get_format():
                return True
        return False

    def get_status(self):
        """Retrieve the status."""
        return self.status

    def touch(self):
        """Update the modification time of the bibdoc."""
        run_sql('UPDATE bibdoc SET modification_date=NOW() WHERE id=%s', (self.id, ))
        #if self.recid:
            #run_sql('UPDATE bibrec SET modification_date=NOW() WHERE id=%s', (self.recid, ))

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

    def add_file_new_version(self, filename, description=None, comment=None, format=None, hide_previous_versions=False):
        """Add a new version of a file."""
        try:
            latestVersion = self.get_latest_version()
            if latestVersion == 0:
                myversion = 1
            else:
                myversion = latestVersion + 1
            if os.path.exists(filename):
                if not os.path.getsize(filename) > 0:
                    raise InvenioWebSubmitFileError, "%s seems to be empty" % filename
                if format is None:
                    format = decompose_file(filename)[2]
                destination = "%s/%s%s;%i" % (self.basedir, self.docname, format, myversion)
                try:
                    shutil.copyfile(filename, destination)
                    os.chmod(destination, 0644)
                except Exception, e:
                    register_exception()
                    raise InvenioWebSubmitFileError, "Encountered an exception while copying '%s' to '%s': '%s'" % (filename, destination, e)
                self.more_info.set_description(description, format, myversion)
                self.more_info.set_comment(comment, format, myversion)
                for afile in self.list_all_files():
                    format = afile.get_format()
                    version = afile.get_version()
                    if version < myversion:
                        self.more_info.set_hidden(hide_previous_versions, format, myversion)
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
                    self.more_info.unset_hidden(afile.get_format(), afile.get_version())
                    try:
                        os.remove(afile.get_full_path())
                    except Exception, e:
                        register_exception()
            Md5Folder(self.basedir).update()
            self.touch()
            self._build_file_list()

    def expunge(self):
        """Phisically remove all the traces of a given bibdoc
        note that you should not use any more this object or unpredictable
        things will happen."""
        del self.md5s
        del self.more_info
        os.system('rm -rf %s' % escape_shell_arg(self.basedir))
        run_sql('DELETE FROM bibrec_bibdoc WHERE id_bibdoc=%s', (self.id, ))
        run_sql('DELETE FROM bibdoc_bibdoc WHERE id_bibdoc1=%s OR id_bibdoc2=%s', (self.id, self.id))
        run_sql('DELETE FROM bibdoc WHERE id=%s', (self.id, ))
        run_sql('INSERT DELAYED INTO hstDOCUMENT(action, id_bibdoc, docname, doctimestamp) VALUES("EXPUNGE", %s, %s, NOW())', (self.id, self.docname))

        del self.docfiles
        del self.id
        del self.cd
        del self.md
        del self.basedir
        del self.recid
        del self.doctype
        del self.docname

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

    def import_descriptions_and_comments_from_marc(self, record=None):
        """Import description & comment from the corresponding marc.
        if record is passed it is directly used, otherwise it is
        calculated after the xm stored in the database."""
        ## Let's get the record
        from invenio.search_engine import get_record
        if record is None:
            record = get_record(self.id)
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

    def add_file_new_format(self, filename, version=None, description=None, comment=None, format=None):
        """add a new format of a file to an archive"""
        try:
            if version is None:
                version = self.get_latest_version()
            if version == 0:
                version = 1
            if os.path.exists(filename):
                if not os.path.getsize(filename) > 0:
                    raise InvenioWebSubmitFileError, "%s seems to be empty" % filename
                if format is None:
                    format = decompose_file(filename)[2]
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

    def add_icon(self, filename, basename=None, format=None):
        """Links an icon with the bibdoc object. Return the icon bibdoc"""
        #first check if an icon already exists
        existing_icon = self.get_icon()
        if existing_icon is not None:
            existing_icon.delete()
        #then add the new one
        if basename is None:
            basename = 'icon-%s' % self.docname
        if format is None:
            format = decompose_file(filename)[2]
        newicon = BibDoc(doctype='Icon', docname=basename)
        newicon.add_file_new_version(filename, format=format)
        try:
            try:
                old_umask = os.umask(022)
                recid_fd = open("%s/.docid" % newicon.get_base_dir(), "w")
                recid_fd.write(str(self.id))
                recid_fd.close()
                type_fd = open("%s/.type" % newicon.get_base_dir(), "w")
                type_fd.write(str(self.doctype))
                type_fd.close()
                os.umask(old_umask)
                run_sql("INSERT INTO bibdoc_bibdoc (id_bibdoc1, id_bibdoc2, type) VALUES (%s,%s,'Icon')", (self.id, newicon.get_id(),))
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

    def display(self, version="", ln=CFG_SITE_LANG, display_hidden=True):
        """Returns a formatted representation of the files linked with
        the bibdoc.
        """
        t = ""
        if version == "all":
            docfiles = self.list_all_files(list_hidden=display_hidden)
        elif version != "":
            version = int(version)
            docfiles = self.list_version_files(version, list_hidden=display_hidden)
        else:
            docfiles = self.list_latest_files()
        existing_icon = self.get_icon()
        if existing_icon is not None:
            existing_icon = existing_icon.list_all_files()[0]
            imageurl = "%s/record/%s/files/%s" % \
                (CFG_SITE_URL, self.recid, urllib.quote(existing_icon.get_full_name()))
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
        try:
            newname = normalize_docname(newname)
            res = run_sql("SELECT b.id FROM bibrec_bibdoc bb JOIN bibdoc b on bb.id_bibdoc=b.id WHERE bb.id_bibrec=%s AND b.docname=%s", (self.recid, newname))
            if res:
                raise InvenioWebSubmitFileError, "A bibdoc called %s already exists for recid %s" % (newname, self.recid)
            try:
                for f in os.listdir(self.basedir):
                    if not f.startswith('.'):
                        try:
                            (dummy, base, extension, version) = decompose_file_with_version(f)
                        except ValueError:
                            register_exception(alert_admin=True, prefix="Strange file '%s' is stored in %s" % (f, self.basedir))
                        else:
                            shutil.move(os.path.join(self.basedir, f), os.path.join(self.basedir, '%s%s;%i' % (newname, extension, version)))
            except Exception, e:
                register_exception()
                raise InvenioWebSubmitFileError("Error in renaming the bibdoc %s to %s for recid %s: %s" % (self.docname, newname, self.recid, e))
            run_sql("update bibdoc set docname=%s where id=%s", (newname, self.id,))
            self.docname = newname
        finally:
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

    def set_hidden(self, hidden, format, version=None):
        """Update the hidden flag for format/version."""
        if version is None:
            version = self.get_latest_version()
        self.more_info.set_hidden(hidden, format, version)
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

    def hidden_p(self, format, version=None):
        """Is the format/version hidden?"""
        if version is None:
            version = self.get_latest_version()
        return self.more_info.hidden_p(format, version)

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
            today = datetime.today()
            self.change_name('DELETED-%s%s-%s' % (today.strftime('%Y%m%d%H%M%S'), today.microsecond, self.docname))
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
        bibrecdocs = BibRecDocs(self.recid)
        try:
            run_sql("UPDATE bibdoc SET status=%s WHERE id=%s AND status='DELETED'", (self.id, previous_status))
        except Exception, e:
            register_exception()
            raise InvenioWebSubmitFileError, "It's impossible to undelete bibdoc %s: %s" % (self.id, e)
        if self.docname.startswith('DELETED-'):
            try:
                # Let's remove DELETED-20080214144322- in front of the docname
                original_name = '-'.join(self.docname.split('-')[2:])
                original_name = bibrecdocs.propose_unique_docname(original_name)
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
                        hidden = self.more_info.hidden_p(format, fileversion)
                        # we can append file:
                        self.docfiles.append(BibDocFile(filepath, self.doctype,
                            fileversion, basename, format,
                            self.recid, self.id, self.status, checksum, description, comment, hidden))
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

    def list_all_files(self, list_hidden=True):
        """Returns all the docfiles linked with the given bibdoc."""
        if list_hidden:
            return self.docfiles
        else:
            return [afile for afile in self.docfiles if not afile.hidden_p()]

    def list_latest_files(self):
        """Returns all the docfiles within the last version."""
        return self.list_version_files(self.get_latest_version())

    def list_version_files(self, version, list_hidden=True):
        """Return all the docfiles of a particular version."""
        version = int(version)
        return [docfile for docfile in self.docfiles if docfile.get_version() == version and (list_hidden or not docfile.hidden_p)]

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

    def __init__(self, fullpath, doctype, version, name, format, recid, docid, status, checksum, description=None, comment=None, hidden=False):
        self.fullpath = fullpath
        self.doctype = doctype
        self.docid = docid
        self.recid = recid
        self.version = version
        self.status = status
        self.checksum = checksum
        self.description = description
        self.comment = comment
        self.hidden = hidden
        self.size = os.path.getsize(fullpath)
        self.md = datetime.fromtimestamp(os.path.getmtime(fullpath))
        try:
            self.cd = datetime.fromtimestamp(os.path.getctime(fullpath))
        except OSError:
            self.cd = self.md
        self.name = name
        self.format = normalize_format(format)
        self.dir = os.path.dirname(fullpath)
        self.url = '%s/record/%s/files/%s%s' % (CFG_SITE_URL, self.recid, urllib.quote(self.name), urllib.quote(self.format))
        self.fullurl = '%s?version=%s' % (self.url, self.version)
        self.etag = '"%i%s%i"' % (self.docid, self.format, self.version)
        if format == "":
            self.mime = "application/octet-stream"
            self.encoding = ""
            self.fullname = name
        else:
            self.fullname = "%s%s" % (name, self.format)
            (self.mime, self.encoding) = _mimes.guess_type(self.fullname)
            if self.mime is None:
                self.mime = "application/octet-stream"
        self.magic = None

    def __repr__(self):
        return ('BibDocFile(%s, %s, %i, %s, %s, %i, %i, %s, %s, %s, %s, %s)' % (repr(self.fullpath), repr(self.doctype), self.version, repr(self.name), repr(self.format), self.recid, self.docid, repr(self.status), repr(self.checksum), repr(self.description), repr(self.comment), repr(self.hidden)))

    def __str__(self):
        out = '%s:%s:%s:%s:fullpath=%s\n' % (self.recid, self.docid, self.version, self.format, self.fullpath)
        out += '%s:%s:%s:%s:fullname=%s\n' % (self.recid, self.docid, self.version, self.format, self.fullname)
        out += '%s:%s:%s:%s:name=%s\n' % (self.recid, self.docid, self.version, self.format, self.name)
        out += '%s:%s:%s:%s:status=%s\n' % (self.recid, self.docid, self.version, self.format, self.status)
        out += '%s:%s:%s:%s:checksum=%s\n' % (self.recid, self.docid, self.version, self.format, self.checksum)
        out += '%s:%s:%s:%s:size=%s\n' % (self.recid, self.docid, self.version, self.format, nice_size(self.size))
        out += '%s:%s:%s:%s:creation time=%s\n' % (self.recid, self.docid, self.version, self.format, self.cd)
        out += '%s:%s:%s:%s:modification time=%s\n' % (self.recid, self.docid, self.version, self.format, self.md)
        out += '%s:%s:%s:%s:magic=%s\n' % (self.recid, self.docid, self.version, self.format, self.get_magic())
        out += '%s:%s:%s:%s:mime=%s\n' % (self.recid, self.docid, self.version, self.format, self.mime)
        out += '%s:%s:%s:%s:encoding=%s\n' % (self.recid, self.docid, self.version, self.format, self.encoding)
        out += '%s:%s:%s:%s:url=%s\n' % (self.recid, self.docid, self.version, self.format, self.url)
        out += '%s:%s:%s:%s:fullurl=%s\n' % (self.recid, self.docid, self.version, self.format, self.fullurl)
        out += '%s:%s:%s:%s:description=%s\n' % (self.recid, self.docid, self.version, self.format, self.description)
        out += '%s:%s:%s:%s:comment=%s\n' % (self.recid, self.docid, self.version, self.format, self.comment)
        out += '%s:%s:%s:%s:hidden=%s\n' % (self.recid, self.docid, self.version, self.format, self.hidden)
        out += '%s:%s:%s:%s:etag=%s\n' % (self.recid, self.docid, self.version, self.format, self.etag)
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

    def hidden_p(self):
        return self.hidden

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
        content_fd = open(self.fullpath, 'rb')
        content = content_fd.read()
        content_fd.close()
        return content

    def get_recid(self):
        """Returns the recid connected with the bibdoc of this file."""
        return self.recid

    def get_status(self):
        """Returns the status of the file, i.e. either '', 'DELETED' or a
        restriction keyword."""
        return self.status

    def get_magic(self):
        """Return all the possible guesses from the magic library about
        the content of the file."""
        if self.magic is None and CFG_HAS_MAGIC:
            magic_cookies = get_magic_cookies()
            magic_result = []
            for key in magic_cookies.keys():
                magic_result.append(magic_cookies[key].file(self.fullpath))
            self.magic = tuple(magic_result)
        return self.magic

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
                if random.random() < 0.25 and calculate_md5(self.fullpath) != self.checksum:
                    raise InvenioWebSubmitFileError, "File %s, version %i, for record %s is corrupted!" % (self.fullname, self.version, self.recid)
                stream_file(req, self.fullpath, self.fullname, self.mime, self.encoding, self.etag, self.checksum, self.fullurl)
                raise apache.SERVER_RETURN, apache.DONE
            else:
                req.status = apache.HTTP_NOT_FOUND
                raise InvenioWebSubmitFileError, "%s does not exists!" % self.fullpath
        else:
            raise InvenioWebSubmitFileError, "You are not authorized to download %s: %s" % (self.fullname, auth_message)

def stream_file(req, fullpath, fullname=None, mime=None, encoding=None, etag=None, md5=None, location=None):
    """This is a generic function to stream a file to the user.
    If fullname, mime, encoding, and location are not provided they will be
    guessed based on req and fullpath.
    md5 should be passed as an hexadecimal string.
    """
    def normal_streaming(size):
        req.set_content_length(size)
        req.send_http_header()
        if not req.header_only:
            req.sendfile(fullpath)
        return ""

    def single_range(size, the_range):
        req.set_content_length(the_range[1])
        req.headers_out['Content-Range'] = 'bytes %d-%d/%d' % (the_range[0], the_range[0] + the_range[1] - 1, size)
        req.status = apache.HTTP_PARTIAL_CONTENT
        req.send_http_header()
        if not req.header_only:
            req.sendfile(fullpath, the_range[0], the_range[1])
        return ""

    def multiple_ranges(size, ranges, mime):
        req.status = apache.HTTP_PARTIAL_CONTENT
        boundary = '%s%04d' % (time.strftime('THIS_STRING_SEPARATES_%Y%m%d%H%M%S'), random.randint(0, 9999))
        req.content_type = 'multipart/byteranges; boundary=%s' % boundary
        content_length = 0
        for arange in ranges:
            content_length += len('--%s\r\n' % boundary)
            content_length += len('Content-Type: %s\r\n' % mime)
            content_length += len('Content-Range: bytes %d-%d/%d\r\n' % (arange[0], arange[0] + arange[1] - 1, size))
            content_length += len('\r\n')
            content_length += arange[1]
            content_length += len('\r\n')
        content_length += len('--%s--\r\n' % boundary)
        req.set_content_length(content_length)
        req.send_http_header()
        if not req.header_only:
            for arange in ranges:
                req.write('--%s\r\n' % boundary, 0)
                req.write('Content-Type: %s\r\n' % mime, 0)
                req.write('Content-Range: bytes %d-%d/%d\r\n' % (arange[0], arange[0] + arange[1] - 1, size), 0)
                req.write('\r\n', 0)
                req.sendfile(fullpath, arange[0], arange[1])
                req.write('\r\n', 0)
            req.write('--%s--\r\n' % boundary)
            req.flush()
        return ""

    def parse_date(date):
        """According to <http://www.w3.org/Protocols/rfc2616/rfc2616-sec3.html#sec3.3>
        a date can come in three formats (in order of preference):
            Sun, 06 Nov 1994 08:49:37 GMT  ; RFC 822, updated by RFC 1123
            Sunday, 06-Nov-94 08:49:37 GMT ; RFC 850, obsoleted by RFC 1036
            Sun Nov  6 08:49:37 1994       ; ANSI C's asctime() format
        Moreover IE is adding some trailing information after a ';'.
        Wrong dates should be simpled ignored.
        This function return the time in seconds since the epoch GMT or None
        in case of errors."""
        if not date:
            return None
        try:
            date = date.split(';')[0].strip() # Because of IE
            ## Sun, 06 Nov 1994 08:49:37 GMT
            return time.mktime(time.strptime(date, '%a, %d %b %Y %X %Z'))
        except:
            try:
                ## Sun, 06 Nov 1994 08:49:37 GMT
                return time.mktime(time.strptime(date, '%A, %d-%b-%y %H:%M:%S %Z'))
            except:
                try:
                    ## Sun, 06 Nov 1994 08:49:37 GMT
                    return time.mktime(date)
                except:
                    return None

    def parse_ranges(ranges):
        """According to <http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.35>
        a (multiple) range request comes in the form:
            bytes=20-30,40-60,70-,-80
        with the meaning:
            from byte to 20 to 30 inclusive (11 bytes)
            from byte to 40 to 60 inclusive (21 bytes)
            from byte 70 to (size - 1) inclusive (size - 70 bytes)
            from byte size - 80 to (size - 1) inclusive (80 bytes)
        This function will return the list of ranges in the form:
            [[first_byte, last_byte], ...]
        If first_byte or last_byte aren't specified they'll be set to None
        If the list is not well formatted it will return None
        """
        try:
            if ranges.startswith('bytes') and '=' in ranges:
                ranges = ranges.split('=')[1].strip()
            else:
                return None
            ret = []
            for arange in ranges.split(','):
                arange = arange.strip()
                if arange.startswith('-'):
                    ret.append([None, int(arange[1:])])
                elif arange.endswith('-'):
                    ret.append([int(arange[:-1]), None])
                else:
                    ret.append(map(int, arange.split('-')))
            return ret
        except:
            return None

    def parse_tags(tags):
        """Return a list of tags starting from a comma separated list."""
        return [tag.strip() for tag in tags.split(',')]

    def fix_ranges(ranges, size):
        """Complementary to parse_ranges it will transform all the ranges
        into (first_byte, length), adjusting all the value based on the
        actual size provided.
        """
        ret = []
        for arange in ranges:
            if (arange[0] is None and arange[1] > 0) or arange[0] < size:
                if arange[0] is None:
                    arange[0] = size - arange[1]
                elif arange[1] is None:
                    arange[1] = size - arange[0]
                else:
                    arange[1] = arange[1] - arange[0] + 1
                arange[0] = max(0, arange[0])
                arange[1] = min(size - arange[0], arange[1])
                if arange[1] > 0:
                    ret.append(arange)
        return ret

    def get_normalized_headers(headers):
        """Strip and lowerize all the keys of the headers dictionary plus
        strip, lowerize and transform known headers value into their value."""
        ret = {
            'if-match' : None,
            'unless-modified-since' : None,
            'if-modified-since' : None,
            'range' : None,
            'if-range' : None,
            'if-none-match' : None,
        }
        for key, value in req.headers_in.iteritems():
            key = key.strip().lower()
            value = value.strip()
            if key in ('unless-modified-since', 'if-modified-since'):
                value = parse_date(value)
            elif key == 'range':
                value = parse_ranges(value)
            elif key == 'if-range':
                value = parse_date(value) or parse_tags(value)
            elif key in ('if-match', 'if-none-match'):
                value = parse_tags(value)
            if value:
                ret[key] = value
        return ret

    headers = get_normalized_headers(req.headers_in)
    if headers['if-match']:
        if etag is not None and etag not in headers['if-match']:
            raise apache.SERVER_RETURN, apache.HTTP_PRECONDITION_FAILED

    if os.path.exists(fullpath):
        mtime = os.path.getmtime(fullpath)
        if fullname is None:
            fullname = os.path.basename(fullpath)
        if mime is None:
            format = decompose_file(fullpath)[2]
            (mime, encoding) = _mimes.guess_type(fullpath)
            if mime is None:
                mime = "application/octet-stream"
        if location is None:
            location = req.uri
        req.content_type = mime
        req.encoding = encoding
        req.filename = fullname
        req.headers_out["Last-Modified"] = time.strftime('%a, %d %b %Y %X GMT', time.gmtime(mtime))
        req.headers_out["Accept-Ranges"] = "bytes"
        req.headers_out["Content-Location"] = location
        if etag is not None:
            req.headers_out["ETag"] = etag
        if md5 is not None:
            req.headers_out["Content-MD5"] = base64.encodestring(binascii.unhexlify(md5.upper()))[:-1]
        req.headers_out["Content-Disposition"] = 'inline; filename="%s"' % fullname.replace('"', '\\"')
        size = os.path.getsize(fullpath)
        if not size:
            try:
                raise Exception, '%s exists but is empty' % fullpath
            except Exception:
                register_exception(req=req, alert_admin=True)
            raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND
        if headers['if-modified-since'] and headers['if-modified-since'] >= mtime:
            raise apache.SERVER_RETURN, apache.HTTP_NOT_MODIFIED
        if headers['if-none-match']:
            if etag is not None and etag in headers['if-none-match']:
                raise apache.SERVER_RETURN, apache.HTTP_NOT_MODIFIED
        if headers['unless-modified-since'] and headers['unless-modified-since'] < mtime:
            return normal_streaming(size)
        if headers['range']:
            try:
                if headers['if-range']:
                    if etag is None or etag not in headers['if-range']:
                        return normal_streaming(size)
                ranges = fix_ranges(headers['range'], size)
            except:
                return normal_streaming(size)
            if len(ranges) > 1:
                return multiple_ranges(size, ranges, mime)
            elif ranges:
                return single_range(size, ranges[0])
            else:
                raise apache.SERVER_RETURN, apache.HTTP_RANGE_NOT_SATISFIABLE
        else:
            return normal_streaming(size)
    else:
        raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND

def stream_restricted_icon(req):
    """Return the content of the "Restricted Icon" file."""
    stream_file(req, '%s/img/restricted.gif' % CFG_WEBDIR)
    raise apache.SERVER_RETURN, apache.DONE

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
            md5file.close()
            os.umask(old_umask)
        except Exception, e:
            register_exception()
            raise InvenioWebSubmitFileError, "Encountered an exception while storing .md5 for folder '%s': '%s'" % (self.folder, e)

    def load(self):
        """Load .md5 into the md5 dictionary"""
        self.md5s = {}
        try:
            md5file = open(os.path.join(self.folder, ".md5"), "r")
            for row in md5file:
                md5hash = row[:32]
                filename = row[34:].strip()
                self.md5s[filename] = md5hash
            md5file.close()
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
        md5_result = os.popen(CFG_PATH_MD5SUM + ' -b %s' % escape_shell_arg(filename))
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
    if not CFG_PATH_MD5SUM or force_internal or os.path.getsize(filename) < CFG_BIBDOCFILE_MD5_THRESHOLD:
        try:
            to_be_read = open(filename, "rb")
            computed_md5 = md5.new()
            while True:
                buf = to_be_read.read(CFG_BIBDOCFILE_MD5_BUFFER)
                if buf:
                    computed_md5.update(buf)
                else:
                    break
            to_be_read.close()
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
    if url.startswith('%s/getfile.py' % CFG_SITE_URL) or url.startswith('%s/getfile.py' % CFG_SITE_SECURE_URL):
        return True
    if not (url.startswith('%s/record/' % CFG_SITE_URL) or url.startswith('%s/record/' % CFG_SITE_SECURE_URL)):
        return False
    splitted_url = url.split('/files/')
    return len(splitted_url) == 2 and splitted_url[0] != '' and splitted_url[1] != ''

def decompose_bibdocfile_url(url):
    """Given a bibdocfile_url return a triple (recid, docname, format)."""
    if url.startswith('%s/getfile.py' % CFG_SITE_URL) or url.startswith('%s/getfile.py' % CFG_SITE_SECURE_URL):
        return decompose_bibdocfile_very_old_url(url)
    if url.startswith('%s/record/' % CFG_SITE_URL):
        recid_file = url[len('%s/record/' % CFG_SITE_URL):]
    elif url.startswith('%s/record/' % CFG_SITE_SECURE_URL):
        recid_file = url[len('%s/record/' % CFG_SITE_SECURE_URL):]
    else:
        raise InvenioWebSubmitFileError, "Url %s doesn't correspond to a valid record inside the system." % url
    recid_file = recid_file.replace('/files/', '/')
    recid, docname, format = decompose_file(urllib.unquote(recid_file))
    if not recid and docname.isdigit():
        ## If the URL was something similar to CFG_SITE_URL/record/123
        return (int(docname), '', '')
    return (int(recid), docname, format)

re_bibdocfile_old_url = re.compile(r'/record/(\d*)/files/')
def decompose_bibdocfile_old_url(url):
    """Given a bibdocfile old url (e.g. CFG_SITE_URL/record/123/files)
    it returns the recid."""
    g = re_bibdocfile_old_url.search(url)
    if g:
        return int(g.group(1))
    raise InvenioWebSubmitFileError('%s is not a valid old bibdocfile url' % url)

def decompose_bibdocfile_very_old_url(url):
    """Decompose an old /getfile.py? URL"""
    if url.startswith('%s/getfile.py' % CFG_SITE_URL) or url.startswith('%s/getfile.py' % CFG_SITE_SECURE_URL):
        params = urllib.splitquery(url)[1]
        if params:
            try:
                params = cgi.parse_qs(params)
                if 'docid' in params:
                    docid = int(params['docid'][0])
                    bibdoc = BibDoc(docid)
                    recid = bibdoc.get_recid()
                    docname = bibdoc.get_docname()
                elif 'recid' in params:
                    recid = int(params['recid'][0])
                    if 'name' in params:
                        docname = params['name'][0]
                    else:
                        docname = ''
                else:
                    raise InvenioWebSubmitFileError('%s has not enough params to correspond to a bibdocfile.' % url)
                format = normalize_format(params.get('format', [''])[0])
                return (recid, docname, format)
            except Exception, e:
                raise InvenioWebSubmitFileError('Problem with %s: %s' % (url, e))
        else:
            raise InvenioWebSubmitFileError('%s has no params to correspond to a bibdocfile.' % url)
    else:
        raise InvenioWebSubmitFileError('%s is not a valid very old bibdocfile url' % url)



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
    path = urllib2.urlparse.urlsplit(urllib.unquote(url))[2]
    filename = os.path.split(path)[-1]
    return file_strip_ext(filename)

def get_format_from_url(url):
    """Return a potential format given a url"""
    path = urllib2.urlparse.urlsplit(urllib.unquote(url))[2]
    filename = os.path.split(path)[-1]
    return filename[len(file_strip_ext(filename)):]

def clean_url(url):
    """Given a local url e.g. a local path it render it a realpath."""
    protocol = urllib2.urlparse.urlsplit(url)[0]
    if protocol in ('', 'file'):
        path = urllib2.urlparse.urlsplit(urllib.unquote(url))[2]
        return os.path.realpath(path)
    else:
        return url

def check_valid_url(url):
    """Check for validity of a url or a file."""
    try:
        protocol = urllib2.urlparse.urlsplit(url)[0]
        if protocol in ('', 'file'):
            path = urllib2.urlparse.urlsplit(urllib.unquote(url))[2]
            if os.path.realpath(path) != path:
                raise StandardError, "%s is not a normalized path (would be %s)." % (path, os.path.normpath(path))
            for allowed_path in CFG_BIBUPLOAD_FFT_ALLOWED_LOCAL_PATHS + [CFG_TMPDIR, CFG_WEBSUBMIT_STORAGEDIR]:
                if path.startswith(allowed_path):
                    dummy_fd = open(path)
                    dummy_fd.close()
                    return
            raise StandardError, "%s is not in one of the allowed paths." % path
        else:
            urllib2.urlopen(url)
    except Exception, e:
        raise StandardError, "%s is not a correct url: %s" % (url, e)

def safe_mkstemp(suffix):
    """Create a temporary filename that don't have any '.' inside a part
    from the suffix."""
    tmpfd, tmppath = tempfile.mkstemp(suffix=suffix, dir=CFG_TMPDIR)
    if '.' not in suffix:
        # Just in case format is empty
        return tmpfd, tmppath
    while '.' in os.path.basename(tmppath)[:-len(suffix)]:
        os.close(tmpfd)
        os.remove(tmppath)
        tmpfd, tmppath = tempfile.mkstemp(suffix=suffix, dir=CFG_TMPDIR)
    return (tmpfd, tmppath)

def download_url(url, format, user=None, password=None, sleep=2):
    """Download a url (if it corresponds to a remote file) and return a local url
    to it."""
    class my_fancy_url_opener(urllib.FancyURLopener):
        def __init__(self, user, password):
            urllib.FancyURLopener.__init__(self)
            self.fancy_user = user
            self.fancy_password = password

        def prompt_user_passwd(self, host, realm):
            return (self.fancy_user, self.fancy_password)

    format = normalize_format(format)
    protocol = urllib2.urlparse.urlsplit(url)[0]
    tmpfd, tmppath = safe_mkstemp(format)
    try:
        try:
            if protocol in ('', 'file'):
                path = urllib2.urlparse.urlsplit(urllib.unquote(url))[2]
                if os.path.realpath(path) != path:
                    raise StandardError, "%s is not a normalized path (would be %s)." % (path, os.path.normpath(path))
                for allowed_path in CFG_BIBUPLOAD_FFT_ALLOWED_LOCAL_PATHS + [CFG_TMPDIR, CFG_WEBSUBMIT_STORAGEDIR]:
                    if path.startswith(allowed_path):
                        shutil.copy(path, tmppath)
                        if os.path.getsize(tmppath) > 0:
                            return tmppath
                        else:
                            raise StandardError, "%s seems to be empty" % url
                raise StandardError, "%s is not in one of the allowed paths." % path
            else:
                if user is not None:
                    urlopener = my_fancy_url_opener(user, password)
                    urlopener.retrieve(url, tmppath)
                else:
                    urllib.urlretrieve(url, tmppath)
                #cmd_exit_code, cmd_out, cmd_err = run_shell_command(CFG_PATH_WGET + ' %s -O %s -t 2 -T 40' % \
                                                                    #(escape_shell_arg(url), escape_shell_arg(tmppath)))
                #if cmd_exit_code:
                    #raise StandardError, "It's impossible to download %s: %s" % (url, cmd_err)
                if os.path.getsize(tmppath) > 0:
                    return tmppath
                else:
                    raise StandardError, "%s seems to be empty" % url
        except:
            os.remove(tmppath)
            raise
    finally:
        os.close(tmpfd)

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
            if 'hidden' not in self.more_info:
                self.more_info['hidden'] = {}
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
            format = normalize_format(format)
            return self.more_info['comments'].get(version, {}).get(format)
        except:
            register_exception()
            raise

    def get_description(self, format, version):
        """Return the description corresponding to the given docid/format/version."""
        try:
            assert(type(version) is int)
            format = normalize_format(format)
            return self.more_info['descriptions'].get(version, {}).get(format)
        except:
            register_exception()
            raise

    def hidden_p(self, format, version):
        """Is the format/version hidden?"""
        try:
            assert(type(version) is int)
            format = normalize_format(format)
            return self.more_info['hidden'].get(version, {}).get(format, False)
        except:
            register_exception()
            raise

    def set_comment(self, comment, format, version):
        """Store a comment corresponding to the given docid/format/version."""
        try:
            assert(type(version) is int and version > 0)
            format = normalize_format(format)
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
            format = normalize_format(format)
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

    def set_hidden(self, hidden, format, version):
        """Store wethever the docid/format/version is hidden."""
        try:
            assert(type(version) is int and version > 0)
            format = normalize_format(format)
            if not hidden:
                self.unset_hidden(format, version)
                self.flush()
                return
            if not version in self.more_info['hidden']:
                self.more_info['hidden'][version] = {}
            self.more_info['hidden'][version][format] = hidden
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

    def unset_hidden(self, format, version):
        """Remove hidden flag."""
        try:
            assert(type(version) is int and version > 0)
            del self.more_info['hidden'][version][format]
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
        fd = open(filename)
        content = fd.read()
        fd.close()
        return content
    except:
        return ''
