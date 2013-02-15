## This file is part of Invenio.
## Copyright (C) 2007, 2008, 2009, 2010, 2011, 2012, 2013 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
This module implements the low-level API for dealing with fulltext files.
    - All the files associated to a I{record} (identified by a I{recid}) can be
      managed via an instance of the C{BibRecDocs} class.
    - A C{BibRecDocs} is a wrapper of the list of I{documents} attached to the
      record.
    - Each document is represented by an instance of the C{BibDoc} class.
    - A document is identified by a C{docid} and name (C{docname}). The docname
      must be unique within the record. A document is the set of all the
      formats and revisions of a piece of information.
    - A document has a type called C{doctype} and can have a restriction.
    - Each physical file, i.e. the concretization of a document into a
      particular I{version} and I{format} is represented by an instance of the
      C{BibDocFile} class.
    - The format is infact the extension of the physical file.
    - A comment and a description and other information can be associated to a
      BibDocFile.
    - A C{bibdoc} is a synonim for a document, while a C{bibdocfile} is a
      synonim for a physical file.

@group Main classes: BibRecDocs,BibDoc,BibDocFile
@group Other classes: BibDocMoreInfo,Md5Folder,InvenioBibDocFileError
@group Main functions: decompose_file,stream_file,bibdocfile_*,download_url
@group Configuration Variables: CFG_*
"""

__revision__ = "$Id$"

import os
import re
import shutil
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
import sys
from warnings import warn

if sys.hexversion < 0x2060000:
    from md5 import md5
else:
    from hashlib import md5

try:
    import magic
    if hasattr(magic, "open"):
        CFG_HAS_MAGIC = 1
    elif hasattr(magic, "Magic"):
        CFG_HAS_MAGIC = 2
except ImportError:
    CFG_HAS_MAGIC = 0

## The above flag controls whether HTTP range requests are supported or not
## when serving static files via Python. This is disabled by default as
## it currently breaks support for opening PDF files on Windows platforms
## using Acrobat reader brower plugin.
CFG_ENABLE_HTTP_RANGE_REQUESTS = False

from datetime import datetime
from mimetypes import MimeTypes
from thread import get_ident

from invenio import webinterface_handler_config as apache

## Let's set a reasonable timeout for URL request (e.g. FFT)
socket.setdefaulttimeout(40)

if sys.hexversion < 0x2040000:
    # pylint: disable=W0622
    from sets import Set as set
    # pylint: enable=W0622

from invenio.shellutils import escape_shell_arg
from invenio.dbquery import run_sql, DatabaseError, blob_to_string
from invenio.errorlib import register_exception
from invenio.bibrecord import record_get_field_instances, \
    field_get_subfield_values, field_get_subfield_instances, \
    encode_for_xml
from invenio.urlutils import create_url, make_user_agent_string
from invenio.textutils import nice_size
from invenio.access_control_engine import acc_authorize_action
from invenio.webuser import collect_user_info
from invenio.access_control_admin import acc_is_user_in_role, acc_get_role_id
from invenio.access_control_firerole import compile_role_definition, acc_firerole_check_user
from invenio.access_control_config import SUPERADMINROLE, CFG_WEBACCESS_WARNING_MSGS
from invenio.config import CFG_SITE_LANG, CFG_SITE_URL, \
    CFG_WEBDIR, CFG_BIBDOCFILE_FILEDIR,\
    CFG_BIBDOCFILE_ADDITIONAL_KNOWN_FILE_EXTENSIONS, \
    CFG_BIBDOCFILE_FILESYSTEM_BIBDOC_GROUP_LIMIT, CFG_SITE_SECURE_URL, \
    CFG_BIBUPLOAD_FFT_ALLOWED_LOCAL_PATHS, \
    CFG_TMPDIR, CFG_TMPSHAREDDIR, CFG_PATH_MD5SUM, \
    CFG_WEBSUBMIT_STORAGEDIR, \
    CFG_BIBDOCFILE_USE_XSENDFILE, \
    CFG_BIBDOCFILE_MD5_CHECK_PROBABILITY, \
    CFG_SITE_RECORD, \
    CFG_BIBUPLOAD_FFT_ALLOWED_EXTERNAL_URLS, \
    CFG_BIBDOCFILE_ENABLE_BIBDOCFSINFO_CACHE

from invenio.bibdocfile_config import CFG_BIBDOCFILE_ICON_SUBFORMAT_RE, \
    CFG_BIBDOCFILE_DEFAULT_ICON_SUBFORMAT
import invenio.template
bibdocfile_templates = invenio.template.load('bibdocfile')

#: block size when performing I/O.
CFG_BIBDOCFILE_BLOCK_SIZE = 1024 * 8

#: threshold used do decide when to use Python MD5 of CLI MD5 algorithm.
CFG_BIBDOCFILE_MD5_THRESHOLD = 256 * 1024

#: chunks loaded by the Python MD5 algorithm.
CFG_BIBDOCFILE_MD5_BUFFER = 1024 * 1024

#: whether to normalize e.g. ".JPEG" and ".jpg" into .jpeg.
CFG_BIBDOCFILE_STRONG_FORMAT_NORMALIZATION = False

#: flags that can be associated to files.
CFG_BIBDOCFILE_AVAILABLE_FLAGS = (
    'PDF/A',
    'STAMPED',
    'PDFOPT',
    'HIDDEN',
    'CONVERTED',
    'PERFORM_HIDE_PREVIOUS',
    'OCRED'
)

#: constant used if FFT correct with the obvious meaning.
KEEP_OLD_VALUE = 'KEEP-OLD-VALUE'

_CFG_BIBUPLOAD_FFT_ALLOWED_EXTERNAL_URLS = [(re.compile(_regex), _headers)
        for _regex, _headers in CFG_BIBUPLOAD_FFT_ALLOWED_EXTERNAL_URLS]

_mimes = MimeTypes(strict=False)
_mimes.suffix_map.update({'.tbz2' : '.tar.bz2'})
_mimes.encodings_map.update({'.bz2' : 'bzip2'})

_magic_cookies = {}

if CFG_HAS_MAGIC == 1:
    def _get_magic_cookies():
        """
        @return: a tuple of magic object.
        @rtype: (MAGIC_NONE, MAGIC_COMPRESS, MAGIC_MIME, MAGIC_COMPRESS + MAGIC_MIME)
        @note: ... not real magic. Just see: man file(1)
        """
        thread_id = get_ident()
        if thread_id not in _magic_cookies:
            _magic_cookies[thread_id] = {
                magic.MAGIC_NONE: magic.open(magic.MAGIC_NONE),
                magic.MAGIC_COMPRESS: magic.open(magic.MAGIC_COMPRESS),
                magic.MAGIC_MIME: magic.open(magic.MAGIC_MIME),
                magic.MAGIC_COMPRESS + magic.MAGIC_MIME: magic.open(magic.MAGIC_COMPRESS + magic.MAGIC_MIME),
                magic.MAGIC_MIME_TYPE: magic.open(magic.MAGIC_MIME_TYPE),
            }
            for key in _magic_cookies[thread_id].keys():
                _magic_cookies[thread_id][key].load()
        return _magic_cookies[thread_id]
elif CFG_HAS_MAGIC == 2:
    def _magic_wrapper(local_path, mime=True, mime_encoding=False):
        thread_id = get_ident()
        if (thread_id, mime, mime_encoding) not in _magic_cookies:
            magic_object = _magic_cookies[thread_id, mime, mime_encoding] = magic.Magic(mime=mime, mime_encoding=mime_encoding)
        else:
            magic_object = _magic_cookies[thread_id, mime, mime_encoding]
        return magic_object.from_file(local_path)

def _generate_extensions():
    """
    Generate the regular expression to match all the known extensions.

    @return: the regular expression.
    @rtype: regular expression object
    """
    _tmp_extensions = _mimes.encodings_map.keys() + \
                _mimes.suffix_map.keys() + \
                _mimes.types_map[1].keys() + \
                CFG_BIBDOCFILE_ADDITIONAL_KNOWN_FILE_EXTENSIONS
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

#: Regular expression to recognized extensions.
_extensions = _generate_extensions()

class InvenioBibDocFileError(Exception):
    """
    Exception raised in case of errors related to fulltext files.
    """
    pass

class InvenioWebSubmitFileError(InvenioBibDocFileError):
    """
    Exception raised in case of errors related to fulltext files.
    """
    ## NOTE: this is a legacy Exception
    pass

class InvenioBibdocfileUnauthorizedURL(Exception):
    """
    Exception raised in case it is not possible to access a certain URL
    """
    pass
def file_strip_ext(afile, skip_version=False, only_known_extensions=False, allow_subformat=True):
    """
    Strip in the best way the extension from a filename.

    >>> file_strip_ext("foo.tar.gz")
    'foo'
    >>> file_strip_ext("foo.buz.gz")
    'foo.buz'
    >>> file_strip_ext("foo.buz")
    'foo'
    >>> file_strip_ext("foo.buz", only_known_extensions=True)
    'foo.buz'
    >>> file_strip_ext("foo.buz;1", skip_version=False,
    ... only_known_extensions=True)
    'foo.buz;1'
    >>> file_strip_ext("foo.gif;icon")
    'foo'
    >>> file_strip_ext("foo.gif:icon", allow_subformat=False)
    'foo.gif:icon'

    @param afile: the path/name of a file.
    @type afile: string
    @param skip_version: whether to skip a trailing ";version".
    @type skip_version: bool
    @param only_known_extensions: whether to strip out only known extensions or
        to consider as extension anything that follows a dot.
    @type only_known_extensions: bool
    @param allow_subformat: whether to consider also subformats as part of
        the extension.
    @type allow_subformat: bool
    @return: the name/path without the extension (and version).
    @rtype: string
    """
    if skip_version or allow_subformat:
        afile = afile.split(';')[0]
    nextfile = _extensions.sub('', afile)
    if nextfile == afile and not only_known_extensions:
        nextfile = os.path.splitext(afile)[0]
    while nextfile != afile:
        afile = nextfile
        nextfile = _extensions.sub('', afile)
    return nextfile

def normalize_format(format, allow_subformat=True):
    """
    Normalize the format, e.g. by adding a dot in front.

    @param format: the format/extension to be normalized.
    @type format: string
    @param allow_subformat: whether to consider also subformats as part of
        the extension.
    @type allow_subformat: bool
    @return: the normalized format.
    @rtype; string
    """
    if allow_subformat:
        subformat = format[format.rfind(';'):]
        format = format[:format.rfind(';')]
    else:
        subformat = ''
    if format and format[0] != '.':
        format = '.' + format
    if CFG_BIBDOCFILE_STRONG_FORMAT_NORMALIZATION:
        if format not in ('.Z', '.H', '.C', '.CC'):
            format = format.lower()
        format = {
            '.jpg' : '.jpeg',
            '.htm' : '.html',
            '.tif' : '.tiff'
        }.get(format, format)
    return format + subformat

def guess_format_from_url(url):
    """
    Given a URL tries to guess it's extension.

    Different method will be used, including HTTP HEAD query,
    downloading the resource and using mime

    @param url: the URL for which the extension shuld be guessed.
    @type url: string
    @return: the recognized extension or '.bin' if it's impossible to
        recognize it.
    @rtype: string
    """
    def guess_via_magic(local_path):
        try:
            if CFG_HAS_MAGIC == 1:
                magic_cookie = _get_magic_cookies()[magic.MAGIC_MIME_TYPE]
                mimetype = magic_cookie.file(local_path)
            elif CFG_HAS_MAGIC == 2:
                mimetype = _magic_wrapper(local_path, mime=True, mime_encoding=False)
            if CFG_HAS_MAGIC:
                ext = _mimes.guess_extension(mimetype)
                if ext:
                    ## Normalize some common magic mis-interpreation
                    ext = {'.asc': '.txt', '.obj': '.bin'}.get(ext, ext)
                    return normalize_format(ext)
        except Exception:
            pass

    ## Let's try to guess the extension by considering the URL as a filename
    ext = decompose_file(url, skip_version=True, only_known_extensions=True)[2]
    if ext.startswith('.'):
        return ext

    if is_url_a_local_file(url):
        ## The URL corresponds to a local file, so we can safely consider
        ## traditional extensions after the dot.
        ext = decompose_file(url, skip_version=True, only_known_extensions=False)[2]
        if ext.startswith('.'):
            return ext
        ## No extensions? Let's use Magic.
        ext = guess_via_magic(url)
        if ext:
            return ext
    else:
        ## Since the URL is remote, let's try to perform a HEAD request
        ## and see the corresponding headers
        try:
            response = open_url(url, head_request=True)
        except (InvenioBibdocfileUnauthorizedURL, urllib2.URLError):
            return ".bin"
        ext = get_format_from_http_response(response)
        if ext:
            return ext

        if CFG_HAS_MAGIC:
            ## Last solution: let's download the remote resource
            ## and use the Python magic library to guess the extension
            filename = ""
            try:
                try:
                    filename = download_url(url, format='')
                    ext = guess_via_magic(filename)
                    if ext:
                        return ext
                except Exception:
                    pass
            finally:
                if os.path.exists(filename):
                    ## Let's free space
                    os.remove(filename)
    return ".bin"

_docname_re = re.compile(r'[^-\w.]*')
def normalize_docname(docname):
    """
    Normalize the docname.

    At the moment the normalization is just returning the same string.

    @param docname: the docname to be normalized.
    @type docname: string
    @return: the normalized docname.
    @rtype: string
    """
    #return _docname_re.sub('', docname)
    return docname

def normalize_version(version):
    """
    Normalize the version.

    The version can be either an integer or the keyword 'all'. Any other
    value will be transformed into the empty string.

    @param version: the version (either a number or 'all').
    @type version: integer or string
    @return: the normalized version.
    @rtype: string
    """
    try:
        int(version)
    except ValueError:
        if version.lower().strip() == 'all':
            return 'all'
        else:
            return ''
    return str(version)

def compose_file(dirname, docname, extension, subformat=None, version=None):
    """
    Construct back a fullpath given the separate components.
    """
    if version:
        version = ";%i" % int(version)
    else:
        version = ""
    if subformat:
        if not subformat.startswith(";"):
            subformat = ";%s" % subformat
    else:
        subformat = ""
    if extension and not extension.startswith("."):
        extension = ".%s" % extension
    return os.path.join(dirname, docname + extension + subformat + version)

def compose_format(extension, subformat=None):
    """
    Construct the format string
    """
    if not extension.startswith("."):
        extension = ".%s" % extension
    if subformat:
        if not subformat.startswith(";"):
            subformat = ";%s" % subformat
    else:
        subformat = ""
    return extension + subformat

def decompose_file(afile, skip_version=False, only_known_extensions=False,
        allow_subformat=True):
    """
    Decompose a file/path into its components dirname, basename and extension.

    >>> decompose_file('/tmp/foo.tar.gz')
    ('/tmp', 'foo', '.tar.gz')
    >>> decompose_file('/tmp/foo.tar.gz;1', skip_version=True)
    ('/tmp', 'foo', '.tar.gz')
    >>> decompose_file('http://www.google.com/index.html')
    ('http://www.google.com', 'index', '.html')

    @param afile: the path/name of a file.
    @type afile: string
    @param skip_version: whether to skip a trailing ";version".
    @type skip_version: bool
    @param only_known_extensions: whether to strip out only known extensions or
        to consider as extension anything that follows a dot.
    @type only_known_extensions: bool
    @param allow_subformat: whether to consider also subformats as part of
        the extension.
    @type allow_subformat: bool
    @return: a tuple with the directory name, the docname and extension.
    @rtype: (dirname, docname, extension)

    @note: if a URL is provided, the scheme will be part of the dirname.
    @see: L{file_strip_ext} for the algorithm used to retrieve the extension.
    """
    if skip_version:
        version = afile.split(';')[-1]
        try:
            int(version)
            afile = afile[:-len(version)-1]
        except ValueError:
            pass
    basename = os.path.basename(afile)
    dirname = afile[:-len(basename)-1]
    base = file_strip_ext(
        basename,
        only_known_extensions=only_known_extensions,
        allow_subformat=allow_subformat)
    extension = basename[len(base) + 1:]
    if extension:
        extension = '.' + extension
    return (dirname, base, extension)

def decompose_file_with_version(afile):
    """
    Decompose a file into dirname, basename, extension and version.

    >>> decompose_file_with_version('/tmp/foo.tar.gz;1')
    ('/tmp', 'foo', '.tar.gz', 1)

    @param afile: the path/name of a file.
    @type afile: string
    @return: a tuple with the directory name, the docname, extension and
        version.
    @rtype: (dirname, docname, extension, version)

    @raise ValueError: in case version does not exist it will.
    @note: if a URL is provided, the scheme will be part of the dirname.
    """
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

def get_subformat_from_format(format):
    """
    @return the subformat if any.
    @rtype: string
    >>> get_superformat_from_format('foo;bar')
    'bar'
    >>> get_superformat_from_format('foo')
    ''
    """
    try:
        return format[format.rindex(';') + 1:]
    except ValueError:
        return ''

def get_superformat_from_format(format):
    """
    @return the superformat if any.
    @rtype: string

    >>> get_superformat_from_format('foo;bar')
    'foo'
    >>> get_superformat_from_format('foo')
    'foo'
    """
    try:
        return format[:format.rindex(';')]
    except ValueError:
        return format

def propose_next_docname(docname):
    """
    Given a I{docname}, suggest a new I{docname} (useful when trying to generate
    a unique I{docname}).

    >>> propose_next_docname('foo')
    'foo_1'
    >>> propose_next_docname('foo_1')
    'foo_2'
    >>> propose_next_docname('foo_10')
    'foo_11'

    @param docname: the base docname.
    @type docname: string
    @return: the next possible docname based on the given one.
    @rtype: string
    """
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
    """
    This class represents all the files attached to one record.

    @param recid: the record identifier.
    @type recid: integer
    @param deleted_too: whether to consider deleted documents as normal
        documents (useful when trying to recover deleted information).
    @type deleted_too: bool
    @param human_readable: whether numbers should be printed in human readable
        format (e.g. 2048 bytes -> 2Kb)
    @ivar id: the record identifier as passed to the constructor.
    @type id: integer
    @ivar human_readable: the human_readable flag as passed to the constructor.
    @type human_readable: bool
    @ivar deleted_too: the deleted_too flag as passed to the constructor.
    @type deleted_too: bool
    @ivar bibdocs: the list of documents attached to the record.
    @type bibdocs: list of BibDoc
    """
    def __init__(self, recid, deleted_too=False, human_readable=False):
        try:
            self.id = int(recid)
        except ValueError:
            raise ValueError("BibRecDocs: recid is %s but must be an integer." % repr(recid))
        self.human_readable = human_readable
        self.deleted_too = deleted_too
        self.bibdocs = []
        self.build_bibdoc_list()

    def __repr__(self):
        """
        @return: the canonical string representation of the C{BibRecDocs}.
        @rtype: string
        """
        return 'BibRecDocs(%s%s%s)' % (self.id,
            self.deleted_too and ', True' or '',
            self.human_readable and ', True' or ''
        )

    def __str__(self):
        """
        @return: an easy to be I{grepped} string representation of the
            whole C{BibRecDocs} content.
        @rtype: string
        """
        out = '%i::::total bibdocs attached=%i\n' % (self.id, len(self.bibdocs))
        out += '%i::::total size latest version=%s\n' % (self.id, nice_size(self.get_total_size_latest_version()))
        out += '%i::::total size all files=%s\n' % (self.id, nice_size(self.get_total_size()))
        for bibdoc in self.bibdocs:
            out += str(bibdoc)
        return out

    def empty_p(self):
        """
        @return: True when the record has no attached documents.
        @rtype: bool
        """
        return len(self.bibdocs) == 0

    def deleted_p(self):
        """
        @return: True if the corresponding record has been deleted.
        @rtype: bool
        """
        from invenio.search_engine import record_exists
        return record_exists(self.id) == -1

    def get_xml_8564(self):
        """
        Return a snippet of I{MARCXML} representing the I{8564} fields
        corresponding to the current state.

        @return: the MARCXML representation.
        @rtype: string
        """
        from invenio.search_engine import get_record
        out = ''
        record = get_record(self.id)
        fields = record_get_field_instances(record, '856', '4', ' ')
        for field in fields:
            urls = field_get_subfield_values(field, 'u')
            if urls and not bibdocfile_url_p(urls[0]):
                out += '\t<datafield tag="856" ind1="4" ind2=" ">\n'
                for subfield, value in field_get_subfield_instances(field):
                    out += '\t\t<subfield code="%s">%s</subfield>\n' % (subfield, encode_for_xml(value))
                out += '\t</datafield>\n'

        for afile in self.list_latest_files(list_hidden=False):
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

        return out

    def get_total_size_latest_version(self):
        """
        Returns the total size used on disk by all the files belonging
        to this record and corresponding to the latest version.

        @return: the total size.
        @rtype: integer
        """
        size = 0
        for bibdoc in self.bibdocs:
            size += bibdoc.get_total_size_latest_version()
        return size

    def get_total_size(self):
        """
        Return the total size used on disk of all the files belonging
        to this record of any version (not only the last as in
        L{get_total_size_latest_version}).

        @return: the total size.
        @rtype: integer
        """
        size = 0
        for bibdoc in self.bibdocs:
            size += bibdoc.get_total_size()
        return size

    def build_bibdoc_list(self):
        """
        This method must be called everytime a I{bibdoc} is added, removed or
        modified.
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
            cur_doc = BibDoc(docid=row[0], recid=self.id, doctype=row[1], human_readable=self.human_readable)
            self.bibdocs.append(cur_doc)

    def list_bibdocs(self, doctype=''):
        """
        Returns the list all bibdocs object belonging to a recid.
        If C{doctype} is set, it returns just the bibdocs of that doctype.

        @param doctype: the optional doctype.
        @type doctype: string
        @return: the list of bibdocs.
        @rtype: list of BibDoc
        """
        if not doctype:
            return self.bibdocs
        else:
            return [bibdoc for bibdoc in self.bibdocs if doctype == bibdoc.doctype]

    def get_bibdoc_names(self, doctype=''):
        """
        Returns all the names of the documents associated with the bibdoc.
        If C{doctype} is set, restrict the result to all the matching doctype.

        @param doctype: the optional doctype.
        @type doctype: string
        @return: the list of document names.
        @rtype: list of string
        """
        return [bibdoc.docname for bibdoc in self.list_bibdocs(doctype)]


    def propose_unique_docname(self, docname):
        """
        Given C{docname}, return a new docname that is not already attached to
        the record.

        @param docname: the reference docname.
        @type docname: string
        @return: a docname not already attached.
        @rtype: string
        """
        docname = normalize_docname(docname)
        goodname = docname
        i = 1
        while goodname in self.get_bibdoc_names():
            i += 1
            goodname = "%s_%s" % (docname, i)
        return goodname

    def merge_bibdocs(self, docname1, docname2):
        """
        This method merge C{docname2} into C{docname1}.

            1. Given all the formats of the latest version of the files
               attached to C{docname2}, these files are added as new formats
               into C{docname1}.
            2. C{docname2} is marked as deleted.

        @raise InvenioBibDocFileError: if at least one format in C{docname2}
            already exists in C{docname1}. (In this case the two bibdocs are
            preserved)
        @note: comments and descriptions are also copied.
        @note: if C{docname2} has a I{restriction}(i.e. if the I{status} is
            set) and C{docname1} doesn't, the restriction is imported.
        """
        bibdoc1 = self.get_bibdoc(docname1)
        bibdoc2 = self.get_bibdoc(docname2)

        ## Check for possibility
        for bibdocfile in bibdoc2.list_latest_files():
            format = bibdocfile.get_format()
            if bibdoc1.format_already_exists_p(format):
                raise InvenioBibDocFileError('Format %s already exists in bibdoc %s of record %s. It\'s impossible to merge bibdoc %s into it.' % (format, docname1, self.id, docname2))

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
        """
        @param docname: the document name.
        @type docname: string
        @return: the identifier corresponding to the given C{docname}.
        @rtype: integer
        @raise InvenioBibDocFileError: if the C{docname} does not
            corresponds to a document attached to this record.
        """
        for bibdoc in self.bibdocs:
            if bibdoc.docname == docname:
                return bibdoc.id
        raise InvenioBibDocFileError, "Recid '%s' is not connected with a " \
            "docname '%s'" % (self.id, docname)

    def get_docname(self, docid):
        """
        @param docid: the document identifier.
        @type docid: integer
        @return: the name of the document corresponding to the given document
            identifier.
        @rtype: string
        @raise InvenioBibDocFileError: if the C{docid} does not
            corresponds to a document attached to this record.
        """
        for bibdoc in self.bibdocs:
            if bibdoc.id == docid:
                return bibdoc.docname
        raise InvenioBibDocFileError, "Recid '%s' is not connected with a " \
            "docid '%s'" % (self.id, docid)

    def has_docname_p(self, docname):
        """
        @param docname: the document name,
        @type docname: string
        @return: True if a document with the given name is attached to this
            record.
        @rtype: bool
        """
        for bibdoc in self.bibdocs:
            if bibdoc.docname == docname:
                return True
        return False

    def get_bibdoc(self, docname):
        """
        @return: the bibdoc with a particular docname associated with
        this recid"""
        for bibdoc in self.bibdocs:
            if bibdoc.docname == docname:
                return bibdoc
        raise InvenioBibDocFileError, "Recid '%s' is not connected with " \
            " docname '%s'" % (self.id, docname)

    def delete_bibdoc(self, docname):
        """
        Deletes the document with the specified I{docname}.

        @param docname: the document name.
        @type docname: string
        """
        for bibdoc in self.bibdocs:
            if bibdoc.docname == docname:
                bibdoc.delete()
        self.build_bibdoc_list()

    def add_bibdoc(self, doctype="Main", docname='file', never_fail=False):
        """
        Add a new empty document object (a I{bibdoc}) to the list of
        documents of this record.

        @param doctype: the document type.
        @type doctype: string
        @param docname: the document name.
        @type docname: string
        @param never_fail: if True, this procedure will not fail, even if
            a document with the given name is already attached to this
            record. In this case a new name will be generated (see
            L{propose_unique_docname}).
        @type never_fail: bool
        @return: the newly created document object.
        @rtype: BibDoc
        @raise InvenioBibDocFileError: in case of any error.
        """
        try:
            docname = normalize_docname(docname)
            if never_fail:
                docname = self.propose_unique_docname(docname)
            if docname in self.get_bibdoc_names():
                raise InvenioBibDocFileError, "%s has already a bibdoc with docname %s" % (self.id, docname)
            else:
                bibdoc = BibDoc(recid=self.id, doctype=doctype, docname=docname, human_readable=self.human_readable)
                self.build_bibdoc_list()
                return bibdoc
        except Exception, e:
            register_exception()
            raise InvenioBibDocFileError(str(e))

    def add_new_file(self, fullpath, doctype="Main", docname=None, never_fail=False, description=None, comment=None, format=None, flags=None, modification_date=None):
        """
        Directly add a new file to this record.

        Adds a new file with the following policy:
            - if the C{docname} is not set it is retrieved from the name of the
              file.
            - If a bibdoc with the given docname doesn't already exist, it is
              created and the file is added to it.
            - It it exist but it doesn't contain the format that is being
              added, the new format is added.
            - If the format already exists then if C{never_fail} is True a new
              bibdoc is created with a similar name but with a progressive
              number as a suffix and the file is added to it (see
              L{propose_unique_docname}).

        @param fullpath: the filesystme path of the document to be added.
        @type fullpath: string
        @param doctype: the type of the document.
        @type doctype: string
        @param docname: the document name.
        @type docname: string
        @param never_fail: if True, this procedure will not fail, even if
            a document with the given name is already attached to this
            record. In this case a new name will be generated (see
            L{propose_unique_docname}).
        @type never_fail: bool
        @param description: an optional description of the file.
        @type description: string
        @param comment: an optional comment to the file.
        @type comment: string
        @param format: the extension of the file. If not specified it will
            be guessed (see L{guess_format_from_url}).
        @type format: string
        @param flags: a set of flags to be associated with the file (see
            L{CFG_BIBDOCFILE_AVAILABLE_FLAGS})
        @type flags: list of string
        @return: the elaborated document object.
        @rtype: BibDoc
        @raise InvenioBibDocFileError: in case of error.
        """
        if docname is None:
            docname = decompose_file(fullpath)[1]
        if format is None:
            format = decompose_file(fullpath)[2]
        docname = normalize_docname(docname)
        try:
            bibdoc = self.get_bibdoc(docname)
        except InvenioBibDocFileError:
            # bibdoc doesn't already exists!
            bibdoc = self.add_bibdoc(doctype, docname, False)
            bibdoc.add_file_new_version(fullpath, description=description, comment=comment, format=format, flags=flags, modification_date=modification_date)
            self.build_bibdoc_list()
        else:
            try:
                bibdoc.add_file_new_format(fullpath, description=description, comment=comment, format=format, flags=flags, modification_date=modification_date)
                self.build_bibdoc_list()
            except InvenioBibDocFileError, e:
                # Format already exist!
                if never_fail:
                    bibdoc = self.add_bibdoc(doctype, docname, True)
                    bibdoc.add_file_new_version(fullpath, description=description, comment=comment, format=format, flags=flags, modification_date=modification_date)
                    self.build_bibdoc_list()
                else:
                    raise
        return bibdoc

    def add_new_version(self, fullpath, docname=None, description=None, comment=None, format=None, flags=None):
        """
        Adds a new file to an already existent document object as a new
        version.

        @param fullpath: the filesystem path of the file to be added.
        @type fullpath: string
        @param docname: the document name. If not specified it will be
            extracted from C{fullpath} (see L{decompose_file}).
        @type docname: string
        @param description: an optional description for the file.
        @type description: string
        @param comment: an optional comment to the file.
        @type comment: string
        @param format: the extension of the file. If not specified it will
            be guessed (see L{guess_format_from_url}).
        @type format: string
        @param flags: a set of flags to be associated with the file (see
            L{CFG_BIBDOCFILE_AVAILABLE_FLAGS})
        @type flags: list of string
        @return: the elaborated document object.
        @rtype: BibDoc
        @raise InvenioBibDocFileError: in case of error.
        @note: previous files associated with the same document will be
            considered obsolete.
        """
        if docname is None:
            docname = decompose_file(fullpath)[1]
        if format is None:
            format = decompose_file(fullpath)[2]
        if flags is None:
            flags = []
        if 'pdfa' in get_subformat_from_format(format).split(';') and not 'PDF/A' in flags:
            flags.append('PDF/A')
        bibdoc = self.get_bibdoc(docname=docname)
        bibdoc.add_file_new_version(fullpath, description=description, comment=comment, format=format, flags=flags)
        self.build_bibdoc_list()
        return bibdoc

    def add_new_format(self, fullpath, docname=None, description=None, comment=None, format=None, flags=None, modification_date=None):
        """
        Adds a new file to an already existent document object as a new
        format.

        @param fullpath: the filesystem path of the file to be added.
        @type fullpath: string
        @param docname: the document name. If not specified it will be
            extracted from C{fullpath} (see L{decompose_file}).
        @type docname: string
        @param description: an optional description for the file.
        @type description: string
        @param comment: an optional comment to the file.
        @type comment: string
        @param format: the extension of the file. If not specified it will
            be guessed (see L{guess_format_from_url}).
        @type format: string
        @param flags: a set of flags to be associated with the file (see
            L{CFG_BIBDOCFILE_AVAILABLE_FLAGS})
        @type flags: list of string
        @return: the elaborated document object.
        @rtype: BibDoc
        @raise InvenioBibDocFileError: in case the same format already
            exists.
        """
        if docname is None:
            docname = decompose_file(fullpath)[1]
        if format is None:
            format = decompose_file(fullpath)[2]
        if flags is None:
            flags = []
        if 'pdfa' in get_subformat_from_format(format).split(';') and not 'PDF/A' in flags:
            flags.append('PDF/A')
        bibdoc = self.get_bibdoc(docname=docname)
        bibdoc.add_file_new_format(fullpath, description=description, comment=comment, format=format, flags=flags, modification_date=modification_date)
        self.build_bibdoc_list()
        return bibdoc

    def list_latest_files(self, doctype='', list_hidden=True):
        """
        Returns a list of the latest files.

        @param doctype: if set, only document of the given type will be listed.
        @type doctype: string
        @param list_hidden: if True, will list also files with the C{HIDDEN}
            flag being set.
        @type list_hidden: bool
        @return: the list of latest files.
        @rtype: list of BibDocFile
        """
        docfiles = []
        for bibdoc in self.list_bibdocs(doctype):
            docfiles += bibdoc.list_latest_files(list_hidden=list_hidden)
        return docfiles

    def display(self, docname="", version="", doctype="", ln=CFG_SITE_LANG, verbose=0, display_hidden=True):
        """
        Returns an HTML representation of the the attached documents.

        @param docname: if set, include only the requested document.
        @type docname: string
        @param version: if not set, only the last version will be displayed. If
            'all', all versions will be displayed.
        @type version: string (integer or 'all')
        @param doctype: is set, include only documents of the requested type.
        @type doctype: string
        @param ln: the language code.
        @type ln: string
        @param verbose: if greater than 0, includes debug information.
        @type verbose: integer
        @param display_hidden: whether to include hidden files as well.
        @type display_hidden: bool
        @return: the formatted representation.
        @rtype: HTML string
        """
        t = ""
        if docname:
            try:
                bibdocs = [self.get_bibdoc(docname)]
            except InvenioBibDocFileError:
                bibdocs = self.list_bibdocs(doctype)
        else:
            bibdocs = self.list_bibdocs(doctype)
        if bibdocs:
            types = list_types_from_array(bibdocs)
            fulltypes = []
            for mytype in types:
                if mytype in ('Plot', 'PlotMisc'):
                    # FIXME: quick hack to ignore plot-like doctypes
                    # on Files tab
                    continue
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

            t = bibdocfile_templates.tmpl_bibrecdoc_filelist(
                  ln=ln,
                  types = fulltypes,
                  verbose_files=verbose_files
                )
        return t

    def fix(self, docname):
        """
        Algorithm that transform a broken/old bibdoc into a coherent one.
        Think of it as being the fsck of BibDocs.
            - All the files in the bibdoc directory will be renamed according
              to the document name. Proper .recid, .type, .md5 files will be
              created/updated.
            - In case of more than one file with the same format version a new
              bibdoc will be created in order to put does files.
        @param docname: the document name that need to be fixed.
        @type docname: string
        @return: the list of newly created bibdocs if any.
        @rtype: list of BibDoc
        @raise InvenioBibDocFileError: in case of issues that can not be
            fixed automatically.
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
                        raise InvenioBibDocFileError, "A file called %s exists under %s. This is not a valid name. After the ';' there must be an integer representing the file version. Please, manually fix this file either by renaming or by deleting it." % (filename, bibdoc.basedir)
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
                        raise InvenioBibDocFileError, "Error in renaming '%s' to '%s': '%s'" % ('%s/%s' % (bibdoc.basedir, filename), '%s/%s' % (bibdoc.basedir, new_name), e)
                    if versions[version].has_key(format):
                        new_bibdocs.append((new_name, version))
                    else:
                        versions[version][format] = new_name
                    counter += 1
                elif filename[0] != '.':
                    # Strange name
                    register_exception()
                    raise InvenioBibDocFileError, "A file called %s exists under %s. This is not a valid name. There should be a ';' followed by an integer representing the file version. Please, manually fix this file either by renaming or by deleting it." % (filename, bibdoc.basedir)
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
                raise InvenioBibDocFileError, e
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
                        raise InvenioBibDocFileError, "Error in renaming '%s' to '%s': '%s'" % ('%s/%s' % (bibdoc.basedir, filename), '%s/%s' % (bibdoc.basedir, destination), e)

            try:
                recid_fd = open("%s/.recid" % bibdoc.basedir, "w")
                recid_fd.write(str(self.id))
                recid_fd.close()
                type_fd = open("%s/.type" % bibdoc.basedir, "w")
                type_fd.write(str(bibdoc.doctype))
                type_fd.close()
            except Exception, e:
                register_exception()
                raise InvenioBibDocFileError, "Error in creating .recid and .type file for '%s' folder: '%s'" % (bibdoc.basedir, e)

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
                    raise InvenioBibDocFileError, "Error in removing '%s': '%s'" % ('%s/%s' % (bibdoc.basedir, filename), e)

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
                    raise InvenioBibDocFileError, "Error in importing description and comment from %s for record %s: %s" % (repr(bibdoc), self.id, e)
        return res

    def check_format(self, docname):
        """
        Check for any format related issue.
        In case L{CFG_BIBDOCFILE_ADDITIONAL_KNOWN_FILE_EXTENSIONS} is
        altered or Python version changes, it might happen that a docname
        contains files which are no more docname + .format ; version, simply
        because the .format is now recognized (and it was not before, so
        it was contained into the docname).
        This algorithm verify if it is necessary to fix (seel L{fix_format}).

        @param docname: the document name whose formats should be verified.
        @type docname: string
        @return: True if format is correct. False if a fix is needed.
        @rtype: bool
        @raise InvenioBibDocFileError: in case of any error.
        """
        bibdoc = self.get_bibdoc(docname)
        correct_docname = decompose_file(docname + '.pdf')[1]
        if docname != correct_docname:
            return False
        for filename in os.listdir(bibdoc.basedir):
            if not filename.startswith('.'):
                try:
                    dummy, dummy, format, version = decompose_file_with_version(filename)
                except Exception:
                    raise InvenioBibDocFileError('Incorrect filename "%s" for docname %s for recid %i' % (filename, docname, self.id))
                if '%s%s;%i' % (correct_docname, format, version) != filename:
                    return False
        return True

    def check_duplicate_docnames(self):
        """
        Check wethever the record is connected with at least tho documents
        with the same name.

        @return: True if everything is fine.
        @rtype: bool
        """
        docnames = set()
        for docname in self.get_bibdoc_names():
            if docname in docnames:
                return False
            else:
                docnames.add(docname)
        return True

    def uniformize_bibdoc(self, docname):
        """
        This algorithm correct wrong file name belonging to a bibdoc.

        @param docname: the document name whose formats should be verified.
        @type docname: string
        """
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
        """
        Fixes format related inconsistencies.

        @param docname: the document name whose formats should be verified.
        @type docname: string
        @param skip_check: if True assume L{check_format} has already been
            called and the need for fix has already been found.
            If False, will implicitly call L{check_format} and skip fixing
            if no error is found.
        @type skip_check: bool
        @return: in case merging two bibdocs is needed but it's not possible.
        @rtype: bool
        """
        if not skip_check:
            if self.check_format(docname):
                return True
        bibdoc = self.get_bibdoc(docname)
        correct_docname = decompose_file(docname + '.pdf')[1]
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
                except InvenioBibDocFileError:
                    return False
            else:
                run_sql('UPDATE bibdoc SET docname=%s WHERE id=%s', (correct_docname, bibdoc.id))
                self.build_bibdoc_list()
                self.uniformize_bibdoc(correct_docname)
        else:
            self.uniformize_bibdoc(docname)
        return True

    def fix_duplicate_docnames(self, skip_check=False):
        """
        Algotirthm to fix duplicate docnames.
        If a record is connected with at least two bibdoc having the same
        docname, the algorithm will try to merge them.

        @param skip_check: if True assume L{check_duplicate_docnames} has
            already been called and the need for fix has already been found.
            If False, will implicitly call L{check_duplicate_docnames} and skip
            fixing if no error is found.
        @type skip_check: bool
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

    def check_file_exists(self, path, format):
        """
        Check if a file with the same content of the file pointed in C{path}
        is already attached to this record.

        @param path: the file to be checked against.
        @type path: string
        @return: True if a file with the requested content is already attached
        to the record.
        @rtype: bool
        """
        # Let's consider all the latest files
        for bibdoc in self.list_bibdocs():
            if bibdoc.check_file_exists(path, format):
                return True
        return False


class BibDoc:
    """
    This class represents one document (i.e. a set of files with different
    formats and with versioning information that consitutes a piece of
    information.

    To instanciate a new document, the recid and the docname are mandatory.
    To instanciate an already existing document, either the recid and docname
    or the docid alone are sufficient to retrieve it.

    @param docid: the document identifier.
    @type docid: integer
    @param recid: the record identifier of the record to which this document
        belongs to. If the C{docid} is specified the C{recid} is automatically
        retrieven from the database.
    @type recid: integer
    @param docname: the document name.
    @type docname: string
    @param doctype: the document type (used when instanciating a new document).
    @type doctype: string
    @param human_readable: whether sizes should be represented in a human
        readable format.
    @type human_readable: bool
    @raise InvenioBibDocFileError: in case of error.
    """

    def __init__ (self, docid=None, recid=None, docname=None, doctype='Main', human_readable=False):
        """Constructor of a bibdoc. At least the docid or the recid/docname
        pair is needed."""
        # docid is known, the document already exists
        if docname:
            docname = normalize_docname(docname)
        self.docfiles = []
        self.md5s = None
        self.human_readable = human_readable
        if docid:
            if not recid:
                res = run_sql("SELECT id_bibrec,type FROM bibrec_bibdoc WHERE id_bibdoc=%s LIMIT 1", (docid,), 1)
                if res:
                    recid = res[0][0]
                    doctype = res[0][1]
                else:
                    warn("Docid %s is orphan" % docid)
            else:
                res = run_sql("SELECT type FROM bibrec_bibdoc WHERE id_bibrec=%s AND id_bibdoc=%s LIMIT 1", (recid, docid,), 1)
                if res:
                    doctype = res[0][0]
                else:
                    #this bibdoc isn't associated with the corresponding bibrec.
                    raise InvenioBibDocFileError, "Docid %s is not associated with the recid %s" % (docid, recid)
            # gather the other information
            res = run_sql("SELECT id,status,docname,creation_date,modification_date,text_extraction_date,more_info FROM bibdoc WHERE id=%s LIMIT 1", (docid,), 1)
            if res:
                self.cd = res[0][3]
                self.md = res[0][4]
                self.td = res[0][5]
                self.recid = recid
                self.docname = res[0][2]
                self.id = docid
                self.status = res[0][1]
                self.more_info = BibDocMoreInfo(docid, blob_to_string(res[0][6]))
                self.basedir = _make_base_dir(self.id)
                self.doctype = doctype
            else:
                # this bibdoc doesn't exist
                raise InvenioBibDocFileError, "The docid %s does not exist." % docid
        # else it is a new document
        else:
            if not docname:
                raise InvenioBibDocFileError, "You should specify the docname when creating a new bibdoc"
            else:
                self.recid = recid
                self.doctype = doctype
                self.docname = docname
                self.status = ''
                if recid:
                    res = run_sql("SELECT b.id FROM bibrec_bibdoc bb JOIN bibdoc b on bb.id_bibdoc=b.id WHERE bb.id_bibrec=%s AND b.docname=%s LIMIT 1", (recid, docname), 1)
                    if res:
                        raise InvenioBibDocFileError("A bibdoc called %s already exists for recid %s" % (docname, recid))
                self.id = run_sql("INSERT INTO bibdoc (status,docname,creation_date,modification_date) "
                    "values(%s,%s,NOW(),NOW())", (self.status, docname))
                if self.id:
                    # we link the document to the record if a recid was
                    # specified
                    self.more_info = BibDocMoreInfo(self.id)
                    res = run_sql("SELECT creation_date, modification_date, text_extraction_date FROM bibdoc WHERE id=%s", (self.id,))
                    self.cd = res[0][0]
                    self.md = res[0][1]
                    self.td = res[0][2]
                else:
                    raise InvenioBibDocFileError, "New docid cannot be created"
                try:
                    self.basedir = _make_base_dir(self.id)
                    # we create the corresponding storage directory
                    if not os.path.exists(self.basedir):
                        old_umask = os.umask(022)
                        os.makedirs(self.basedir)
                        # and save the father record id if it exists
                        try:
                            if self.recid:
                                recid_fd = open("%s/.recid" % self.basedir, "w")
                                recid_fd.write(str(self.recid))
                                recid_fd.close()
                            if self.doctype:
                                type_fd = open("%s/.type" % self.basedir, "w")
                                type_fd.write(str(self.doctype))
                                type_fd.close()
                        except Exception, e:
                            register_exception(alert_admin=True)
                            raise InvenioBibDocFileError, e
                        os.umask(old_umask)
                    if self.recid:
                        run_sql("INSERT INTO bibrec_bibdoc (id_bibrec, id_bibdoc, type) VALUES (%s,%s,%s)",
                            (recid, self.id, self.doctype,))
                except Exception, e:
                    run_sql('DELETE FROM bibdoc WHERE id=%s', (self.id, ))
                    run_sql('DELETE FROM bibrec_bibdoc WHERE id_bibdoc=%s', (self.id, ))
                    register_exception(alert_admin=True)
                    raise InvenioBibDocFileError, e
        # build list of attached files
        self._build_file_list('init')

    def __repr__(self):
        """
        @return: the canonical string representation of the C{BibDoc}.
        @rtype: string
        """
        return 'BibDoc(%s, %s, %s, %s, %s)' % (repr(self.id), repr(self.recid), repr(self.docname), repr(self.doctype), repr(self.human_readable))

    def __str__(self):
        """
        @return: an easy to be I{grepped} string representation of the
            whole C{BibDoc} content.
        @rtype: string
        """
        out = '%s:%i:::docname=%s\n' % (self.recid or '', self.id, self.docname)
        out += '%s:%i:::doctype=%s\n' % (self.recid or '', self.id, self.doctype)
        out += '%s:%i:::status=%s\n' % (self.recid or '', self.id, self.status)
        out += '%s:%i:::basedir=%s\n' % (self.recid or '', self.id, self.basedir)
        out += '%s:%i:::creation date=%s\n' % (self.recid or '', self.id, self.cd)
        out += '%s:%i:::modification date=%s\n' % (self.recid or '', self.id, self.md)
        out += '%s:%i:::text extraction date=%s\n' % (self.recid or '', self.id, self.td)
        out += '%s:%i:::total file attached=%s\n' % (self.recid or '', self.id, len(self.docfiles))
        if self.human_readable:
            out += '%s:%i:::total size latest version=%s\n' % (self.recid or '', self.id, nice_size(self.get_total_size_latest_version()))
            out += '%s:%i:::total size all files=%s\n' % (self.recid or '', self.id, nice_size(self.get_total_size()))
        else:
            out += '%s:%i:::total size latest version=%s\n' % (self.recid or '', self.id, self.get_total_size_latest_version())
            out += '%s:%i:::total size all files=%s\n' % (self.recid or '', self.id, self.get_total_size())
        for docfile in self.docfiles:
            out += str(docfile)
        return out

    def format_already_exists_p(self, format):
        """
        @param format: a format to be checked.
        @type format: string
        @return: True if a file of the given format already exists among the
            latest files.
        @rtype: bool
        """
        format = normalize_format(format)
        for afile in self.list_latest_files():
            if format == afile.get_format():
                return True
        return False

    def get_status(self):
        """
        @return: the status information.
        @rtype: string
        """
        return self.status

    def get_text(self, version=None):
        """
        @param version: the requested version. If not set, the latest version
            will be used.
        @type version: integer
        @return: the textual content corresponding to the specified version
            of the document.
        @rtype: string
        """
        if version is None:
            version = self.get_latest_version()
        if self.has_text(version):
            return open(os.path.join(self.basedir, '.text;%i' % version)).read()
        else:
            return ""

    def get_text_path(self, version=None):
        """
        @param version: the requested version. If not set, the latest version
            will be used.
        @type version: int
        @return: the full path to the textual content corresponding to the specified version
            of the document.
        @rtype: string
        """
        if version is None:
            version = self.get_latest_version()
        if self.has_text(version):
            return os.path.join(self.basedir, '.text;%i' % version)
        else:
            return ""

    def extract_text(self, version=None, perform_ocr=False, ln='en'):
        """
        Try what is necessary to extract the textual information of a document.

        @param version: the version of the document for which text is required.
            If not specified the text will be retrieved from the last version.
        @type version: integer
        @param perform_ocr: whether to perform OCR.
        @type perform_ocr: bool
        @param ln: a two letter language code to give as a hint to the OCR
            procedure.
        @type ln: string
        @raise InvenioBibDocFileError: in case of error.
        @note: the text is extracted and cached for later use. Use L{get_text}
            to retrieve it.
        """
        from invenio.websubmit_file_converter import get_best_format_to_extract_text_from, convert_file, InvenioWebSubmitFileConverterError
        if version is None:
            version = self.get_latest_version()
        docfiles = self.list_version_files(version)
        ## We try to extract text only from original or OCRed documents.
        filenames = [docfile.get_full_path() for docfile in docfiles if 'CONVERTED' not in docfile.flags or 'OCRED' in docfile.flags]
        try:
            filename = get_best_format_to_extract_text_from(filenames)
        except InvenioWebSubmitFileConverterError:
            ## We fall back on considering all the documents
            filenames = [docfile.get_full_path() for docfile in docfiles]
            try:
                filename = get_best_format_to_extract_text_from(filenames)
            except InvenioWebSubmitFileConverterError:
                open(os.path.join(self.basedir, '.text;%i' % version), 'w').write('')
                return
        try:
            convert_file(filename, os.path.join(self.basedir, '.text;%i' % version), '.txt', perform_ocr=perform_ocr, ln=ln)
            if version == self.get_latest_version():
                run_sql("UPDATE bibdoc SET text_extraction_date=NOW() WHERE id=%s", (self.id, ))
        except InvenioWebSubmitFileConverterError, e:
            register_exception(alert_admin=True, prefix="Error in extracting text from bibdoc %i, version %i" % (self.id, version))
            raise InvenioBibDocFileError, str(e)

    def touch(self):
        """
        Update the modification time of the bibdoc (as in the UNIX command
        C{touch}).
        """
        run_sql('UPDATE bibdoc SET modification_date=NOW() WHERE id=%s', (self.id, ))
        #if self.recid:
            #run_sql('UPDATE bibrec SET modification_date=NOW() WHERE id=%s', (self.recid, ))

    def set_status(self, new_status):
        """
        Set a new status. A document with a status information is a restricted
        document that can be accessed only to user which as an authorization
        to the I{viewrestrdoc} WebAccess action with keyword status with value
        C{new_status}.

        @param new_status: the new status. If empty the document will be
            unrestricted.
        @type new_status: string
        @raise InvenioBibDocFileError: in case the reserved word
            'DELETED' is used.
        """
        if new_status != KEEP_OLD_VALUE:
            if new_status == 'DELETED':
                raise InvenioBibDocFileError('DELETED is a reserved word and can not be used for setting the status')
            run_sql('UPDATE bibdoc SET status=%s WHERE id=%s', (new_status, self.id))
            self.status = new_status
            self.touch()
            self._build_file_list()

    def add_file_new_version(self, filename, description=None, comment=None, format=None, flags=None, modification_date=None):
        """
        Add a new version of a file. If no physical file is already attached
        to the document a the given file will have version 1. Otherwise the
        new file will have the current version number plus one.

        @param filename: the local path of the file.
        @type filename: string
        @param description: an optional description for the file.
        @type description: string
        @param comment: an optional comment to the file.
        @type comment: string
        @param format: the extension of the file. If not specified it will
            be retrieved from the filename (see L{decompose_file}).
        @type format: string
        @param flags: a set of flags to be associated with the file (see
            L{CFG_BIBDOCFILE_AVAILABLE_FLAGS})
        @type flags: list of string
        @raise InvenioBibDocFileError: in case of error.
        """
        try:
            latestVersion = self.get_latest_version()
            if latestVersion == 0:
                myversion = 1
            else:
                myversion = latestVersion + 1
            if os.path.exists(filename):
                if not os.path.getsize(filename) > 0:
                    raise InvenioBibDocFileError, "%s seems to be empty" % filename
                if format is None:
                    format = decompose_file(filename)[2]
                else:
                    format = normalize_format(format)
                destination = "%s/%s%s;%i" % (self.basedir, self.docname, format, myversion)
                if run_sql("SELECT id_bibdoc FROM bibdocfsinfo WHERE id_bibdoc=%s AND version=%s AND format=%s", (self.id, myversion, format)):
                    raise InvenioBibDocFileError("According to the database a file of format %s is already attached to the docid %s" % (format, self.id))
                try:
                    shutil.copyfile(filename, destination)
                    os.chmod(destination, 0644)
                    if modification_date: # if the modification time of the file needs to be changed
                        update_modification_date_of_file(destination, modification_date)
                except Exception, e:
                    register_exception()
                    raise InvenioBibDocFileError, "Encountered an exception while copying '%s' to '%s': '%s'" % (filename, destination, e)
                self.more_info.set_description(description, format, myversion)
                self.more_info.set_comment(comment, format, myversion)
                if flags is None:
                    flags = []
                if 'pdfa' in get_subformat_from_format(format).split(';') and not 'PDF/A' in flags:
                    flags.append('PDF/A')
                for flag in flags:
                    if flag == 'PERFORM_HIDE_PREVIOUS':
                        for afile in self.list_all_files():
                            format = afile.get_format()
                            version = afile.get_version()
                            if version < myversion:
                                self.more_info.set_flag('HIDDEN', format, myversion)
                    else:
                        self.more_info.set_flag(flag, format, myversion)
            else:
                raise InvenioBibDocFileError, "'%s' does not exists!" % filename
        finally:
            self.touch()
            Md5Folder(self.basedir).update()
            self._build_file_list()
        just_added_file = self.get_file(format, myversion)
        run_sql("INSERT INTO bibdocfsinfo(id_bibdoc, version, format, last_version, cd, md, checksum, filesize, mime) VALUES(%s, %s, %s, true, %s, %s, %s, %s, %s)", (self.id, myversion, format, just_added_file.cd, just_added_file.md, just_added_file.get_checksum(), just_added_file.get_size(), just_added_file.mime))
        run_sql("UPDATE bibdocfsinfo SET last_version=false WHERE id_bibdoc=%s AND version<%s", (self.id, myversion))

    def add_file_new_format(self, filename, version=None, description=None, comment=None, format=None, flags=None, modification_date=None):
        """
        Add a file as a new format.

        @param filename: the local path of the file.
        @type filename: string
        @param version: an optional specific version to which the new format
            should be added. If None, the last version will be used.
        @type version: integer
        @param description: an optional description for the file.
        @type description: string
        @param comment: an optional comment to the file.
        @type comment: string
        @param format: the extension of the file. If not specified it will
            be retrieved from the filename (see L{decompose_file}).
        @type format: string
        @param flags: a set of flags to be associated with the file (see
            L{CFG_BIBDOCFILE_AVAILABLE_FLAGS})
        @type flags: list of string
        @raise InvenioBibDocFileError: if the given format already exists.
        """
        try:
            if version is None:
                version = self.get_latest_version()
            if version == 0:
                version = 1
            if os.path.exists(filename):
                if not os.path.getsize(filename) > 0:
                    raise InvenioBibDocFileError, "%s seems to be empty" % filename
                if format is None:
                    format = decompose_file(filename)[2]
                else:
                    format = normalize_format(format)
                if run_sql("SELECT id_bibdoc FROM bibdocfsinfo WHERE id_bibdoc=%s AND version=%s AND format=%s", (self.id, version, format)):
                    raise InvenioBibDocFileError("According to the database a file of format %s is already attached to the docid %s" % (format, self.id))
                destination = "%s/%s%s;%i" % (self.basedir, self.docname, format, version)
                if os.path.exists(destination):
                    raise InvenioBibDocFileError, "A file for docname '%s' for the recid '%s' already exists for the format '%s'" % (self.docname, self.recid, format)
                try:
                    shutil.copyfile(filename, destination)
                    os.chmod(destination, 0644)
                    if modification_date: # if the modification time of the file needs to be changed
                        update_modification_date_of_file(destination, modification_date)
                except Exception, e:
                    register_exception()
                    raise InvenioBibDocFileError, "Encountered an exception while copying '%s' to '%s': '%s'" % (filename, destination, e)
                self.more_info.set_comment(comment, format, version)
                self.more_info.set_description(description, format, version)
                if flags is None:
                    flags = []
                if 'pdfa' in get_subformat_from_format(format).split(';') and not 'PDF/A' in flags:
                    flags.append('PDF/A')
                for flag in flags:
                    if flag != 'PERFORM_HIDE_PREVIOUS':
                        self.more_info.set_flag(flag, format, version)
            else:
                raise InvenioBibDocFileError, "'%s' does not exists!" % filename
        finally:
            Md5Folder(self.basedir).update()
            self.touch()
            self._build_file_list()
        just_added_file = self.get_file(format, version)
        run_sql("INSERT INTO bibdocfsinfo(id_bibdoc, version, format, last_version, cd, md, checksum, filesize, mime) VALUES(%s, %s, %s, true, %s, %s, %s, %s, %s)", (self.id, version, format, just_added_file.cd, just_added_file.md, just_added_file.get_checksum(), just_added_file.get_size(), just_added_file.mime))

    def purge(self):
        """
        Physically removes all the previous version of the given bibdoc.
        Everything but the last formats will be erased.
        """
        version = self.get_latest_version()
        if version > 1:
            for afile in self.docfiles:
                if afile.get_version() < version:
                    self.more_info.unset_comment(afile.get_format(), afile.get_version())
                    self.more_info.unset_description(afile.get_format(), afile.get_version())
                    for flag in CFG_BIBDOCFILE_AVAILABLE_FLAGS:
                        self.more_info.unset_flag(flag, afile.get_format(), afile.get_version())
                    try:
                        os.remove(afile.get_full_path())
                    except Exception, e:
                        register_exception()
            Md5Folder(self.basedir).update()
            self.touch()
            self._build_file_list()
            run_sql("DELETE FROM bibdocfsinfo WHERE id_bibdoc=%s AND version<%s", (self.id, version))

    def expunge(self):
        """
        Physically remove all the traces of a given document.
        @note: an expunged BibDoc object shouldn't be used anymore or the
        result might be unpredicted.
        """
        del self.md5s
        del self.more_info
        os.system('rm -rf %s' % escape_shell_arg(self.basedir))
        run_sql('DELETE FROM bibrec_bibdoc WHERE id_bibdoc=%s', (self.id, ))
        run_sql('DELETE FROM bibdoc_bibdoc WHERE id_bibdoc1=%s OR id_bibdoc2=%s', (self.id, self.id))
        run_sql('DELETE FROM bibdoc WHERE id=%s', (self.id, ))
        run_sql('INSERT DELAYED INTO hstDOCUMENT(action, id_bibdoc, docname, doctimestamp) VALUES("EXPUNGE", %s, %s, NOW())', (self.id, self.docname))
        run_sql('DELETE FROM bibdocfsinfo WHERE id_bibdoc=%s', (self.id, ))

        del self.docfiles
        del self.id
        del self.cd
        del self.md
        del self.td
        del self.basedir
        del self.recid
        del self.doctype
        del self.docname

    def revert(self, version):
        """
        Revert the document to a given version. All the formats corresponding
        to that version are copied forward to a new version.

        @param version: the version to revert to.
        @type version: integer
        @raise InvenioBibDocFileError: in case of errors
        """
        version = int(version)
        docfiles = self.list_version_files(version)
        if docfiles:
            self.add_file_new_version(docfiles[0].get_full_path(), description=docfiles[0].get_description(), comment=docfiles[0].get_comment(), format=docfiles[0].get_format(), flags=docfiles[0].flags)
        for docfile in docfiles[1:]:
            self.add_file_new_format(docfile.filename, description=docfile.get_description(), comment=docfile.get_comment(), format=docfile.get_format(), flags=docfile.flags)

    def import_descriptions_and_comments_from_marc(self, record=None):
        """
        Import descriptions and comments from the corresponding MARC metadata.

        @param record: the record (if None it will be calculated).
        @type record: bibrecord recstruct
        @note: If record is passed it is directly used, otherwise it is retrieved
        from the MARCXML stored in the database.
        """
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
                if url == '%s/%s/%s/files/' % (CFG_SITE_URL, CFG_SITE_RECORD, self.recid):
                    ## If it is a traditional /CFG_SITE_RECORD/1/files/ one
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

    def get_icon(self, subformat_re=CFG_BIBDOCFILE_ICON_SUBFORMAT_RE, display_hidden=True):
        """
        @param subformat_re: by default the convention is that
            L{CFG_BIBDOCFILE_ICON_SUBFORMAT_RE} is used as a subformat indicator to
            mean that a particular format is to be used as an icon.
            Specifiy a different subformat if you need to use a different
            convention.
        @type subformat_re: compiled regular expression
        @return: the bibdocfile corresponding to the icon of this document, or
            None if any icon exists for this document.
        @rtype: BibDocFile
        @warning: before I{subformat} were introduced this method was
            returning a BibDoc, while now is returning a BibDocFile. Check
            if your client code is compatible with this.
        """
        for docfile in self.list_latest_files(list_hidden=display_hidden):
            if subformat_re.match(docfile.get_subformat()):
                return docfile
        return None

    def add_icon(self, filename, format=None, subformat=CFG_BIBDOCFILE_DEFAULT_ICON_SUBFORMAT, modification_date=None):
        """
        Attaches icon to this document.

        @param filename: the local filesystem path to the icon.
        @type filename: string
        @param format: an optional format for the icon. If not specified it
            will be calculated after the filesystem path.
        @type format: string
        @param subformat: by default the convention is that
            CFG_BIBDOCFILE_DEFAULT_ICON_SUBFORMAT is used as a subformat indicator to
            mean that a particular format is to be used as an icon.
            Specifiy a different subformat if you need to use a different
            convention.
        @type subformat: string
        @raise InvenioBibDocFileError: in case of errors.
        """
        #first check if an icon already exists
        if not format:
            format = decompose_file(filename)[2]
        if subformat:
            format += ";%s" % subformat

        self.add_file_new_format(filename, format=format, modification_date=modification_date)

    def delete_icon(self, subformat_re=CFG_BIBDOCFILE_ICON_SUBFORMAT_RE):
        """
        @param subformat_re: by default the convention is that
            L{CFG_BIBDOCFILE_ICON_SUBFORMAT_RE} is used as a subformat indicator to
            mean that a particular format is to be used as an icon.
            Specifiy a different subformat if you need to use a different
            convention.
        @type subformat: compiled regular expression
        Removes the icon attached to the document if it exists.
        """
        for docfile in self.list_latest_files():
            if subformat_re.match(docfile.get_subformat()):
                self.delete_file(docfile.get_format(), docfile.get_version())

    def display(self, version="", ln=CFG_SITE_LANG, display_hidden=True):
        """
        Returns an HTML representation of the this document.

        @param version: if not set, only the last version will be displayed. If
            'all', all versions will be displayed.
        @type version: string (integer or 'all')
        @param ln: the language code.
        @type ln: string
        @param display_hidden: whether to include hidden files as well.
        @type display_hidden: bool
        @return: the formatted representation.
        @rtype: HTML string
        """
        t = ""
        if version == "all":
            docfiles = self.list_all_files(list_hidden=display_hidden)
        elif version != "":
            version = int(version)
            docfiles = self.list_version_files(version, list_hidden=display_hidden)
        else:
            docfiles = self.list_latest_files(list_hidden=display_hidden)
        icon = self.get_icon(display_hidden=display_hidden)
        if icon:
            imageurl = icon.get_url()
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

        if versions:
            return bibdocfile_templates.tmpl_bibdoc_filelist(
                ln = ln,
                versions = versions,
                imageurl = imageurl,
                docname = self.docname,
                recid = self.recid,
                status = self.status
                )
        else:
            return ""

    def change_name(self, newname):
        """
        Renames this document name.

        @param newname: the new name.
        @type newname: string
        @raise InvenioBibDocFileError: if the new name corresponds to
            a document already attached to the record owning this document.
        """
        try:
            newname = normalize_docname(newname)
            res = run_sql("SELECT b.id FROM bibrec_bibdoc bb JOIN bibdoc b on bb.id_bibdoc=b.id WHERE bb.id_bibrec=%s AND b.docname=%s", (self.recid, newname))
            if res:
                raise InvenioBibDocFileError, "A bibdoc called %s already exists for recid %s" % (newname, self.recid)
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
                raise InvenioBibDocFileError("Error in renaming the bibdoc %s to %s for recid %s: %s" % (self.docname, newname, self.recid, e))
            run_sql("update bibdoc set docname=%s where id=%s", (newname, self.id,))
            self.docname = newname
        finally:
            Md5Folder(self.basedir).update()
            self.touch()
            self._build_file_list('rename')

    def set_comment(self, comment, format, version=None):
        """
        Updates the comment of a specific format/version of the document.

        @param comment: the new comment.
        @type comment: string
        @param format: the specific format for which the comment should be
            updated.
        @type format: string
        @param version: the specific version for which the comment should be
            updated. If not specified the last version will be used.
        @type version: integer
        """
        if version is None:
            version = self.get_latest_version()
        format = normalize_format(format)
        self.more_info.set_comment(comment, format, version)
        self.touch()
        self._build_file_list('init')

    def set_description(self, description, format, version=None):
        """
        Updates the description of a specific format/version of the document.

        @param description: the new description.
        @type description: string
        @param format: the specific format for which the description should be
            updated.
        @type format: string
        @param version: the specific version for which the description should be
            updated. If not specified the last version will be used.
        @type version: integer
        """
        if version is None:
            version = self.get_latest_version()
        format = normalize_format(format)
        self.more_info.set_description(description, format, version)
        self.touch()
        self._build_file_list('init')

    def set_flag(self, flagname, format, version=None):
        """
        Sets a flag for a specific format/version of the document.

        @param flagname: a flag from L{CFG_BIBDOCFILE_AVAILABLE_FLAGS}.
        @type flagname: string
        @param format: the specific format for which the flag should be
            set.
        @type format: string
        @param version: the specific version for which the flag should be
            set. If not specified the last version will be used.
        @type version: integer
        """
        if version is None:
            version = self.get_latest_version()
        format = normalize_format(format)
        self.more_info.set_flag(flagname, format, version)
        self.touch()
        self._build_file_list('init')

    def has_flag(self, flagname, format, version=None):
        """
        Checks if a particular flag for a format/version is set.

        @param flagname: a flag from L{CFG_BIBDOCFILE_AVAILABLE_FLAGS}.
        @type flagname: string
        @param format: the specific format for which the flag should be
            set.
        @type format: string
        @param version: the specific version for which the flag should be
            set. If not specified the last version will be used.
        @type version: integer
        @return: True if the flag is set.
        @rtype: bool
        """
        if version is None:
            version = self.get_latest_version()
        format = normalize_format(format)
        return self.more_info.has_flag(flagname, format, version)

    def unset_flag(self, flagname, format, version=None):
        """
        Unsets a flag for a specific format/version of the document.

        @param flagname: a flag from L{CFG_BIBDOCFILE_AVAILABLE_FLAGS}.
        @type flagname: string
        @param format: the specific format for which the flag should be
            unset.
        @type format: string
        @param version: the specific version for which the flag should be
            unset. If not specified the last version will be used.
        @type version: integer
        """
        if version is None:
            version = self.get_latest_version()
        format = normalize_format(format)
        self.more_info.unset_flag(flagname, format, version)
        self.touch()
        self._build_file_list('init')

    def get_comment(self, format, version=None):
        """
        Retrieve the comment of a specific format/version of the document.

        @param format: the specific format for which the comment should be
            retrieved.
        @type format: string
        @param version: the specific version for which the comment should be
            retrieved. If not specified the last version will be used.
        @type version: integer
        @return: the comment.
        @rtype: string
        """
        if version is None:
            version = self.get_latest_version()
        format = normalize_format(format)
        return self.more_info.get_comment(format, version)

    def get_description(self, format, version=None):
        """
        Retrieve the description of a specific format/version of the document.

        @param format: the specific format for which the description should be
            retrieved.
        @type format: string
        @param version: the specific version for which the description should
            be retrieved. If not specified the last version will be used.
        @type version: integer
        @return: the description.
        @rtype: string
        """
        if version is None:
            version = self.get_latest_version()
        format = normalize_format(format)
        return self.more_info.get_description(format, version)

    def hidden_p(self, format, version=None):
        """
        Returns True if the file specified by the given format/version is
        hidden.

        @param format: the specific format for which the description should be
            retrieved.
        @type format: string
        @param version: the specific version for which the description should
            be retrieved. If not specified the last version will be used.
        @type version: integer
        @return: True if hidden.
        @rtype: bool
        """
        if version is None:
            version = self.get_latest_version()
        return self.more_info.has_flag('HIDDEN', format, version)

    def get_docname(self):
        """
        @return: the name of this document.
        @rtype: string
        """
        return self.docname

    def get_base_dir(self):
        """
        @return: the base directory on the local filesystem for this document
            (e.g. C{/soft/cdsweb/var/data/files/g0/123})
        @rtype: string
        """
        return self.basedir

    def get_type(self):
        """
        @return: the type of this document.
        @rtype: string"""
        return self.doctype

    def get_recid(self):
        """
        @return: the record id of the record to which this document is
            attached.
        @rtype: integer
        """
        return self.recid

    def get_id(self):
        """
        @return: the id of this document.
        @rtype: integer
        """
        return self.id

    def pdf_a_p(self):
        """
        @return: True if this document contains a PDF in PDF/A format.
        @rtype: bool"""
        return self.has_flag('PDF/A', 'pdf')

    def has_text(self, require_up_to_date=False, version=None):
        """
        Return True if the text of this document has already been extracted.

        @param require_up_to_date: if True check the text was actually
            extracted after the most recent format of the given version.
        @type require_up_to_date: bool
        @param version: a version for which the text should have been
            extracted. If not specified the latest version is considered.
        @type version: integer
        @return: True if the text has already been extracted.
        @rtype: bool
        """
        if version is None:
            version = self.get_latest_version()
        if os.path.exists(os.path.join(self.basedir, '.text;%i' % version)):
            if not require_up_to_date:
                return True
            else:
                docfiles = self.list_version_files(version)
                text_md = datetime.fromtimestamp(os.path.getmtime(os.path.join(self.basedir, '.text;%i' % version)))
                for docfile in docfiles:
                    if text_md <= docfile.md:
                        return False
                return True
        return False

    def get_file(self, format, version=""):
        """
        Returns a L{BibDocFile} instance of this document corresponding to the
        specific format and version.

        @param format: the specific format.
        @type format: string
        @param version: the specific version for which the description should
            be retrieved. If not specified the last version will be used.
        @type version: integer
        @return: the L{BibDocFile} instance.
        @rtype: BibDocFile
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

        ## Let's skip the subformat specification and consider just the
        ## superformat
        superformat = get_superformat_from_format(format)
        for docfile in docfiles:
            if get_superformat_from_format(docfile.get_format()) == superformat:
                return docfile
        raise InvenioBibDocFileError, "No file called '%s' of format '%s', version '%s'" % (self.docname, format, version)

    def list_versions(self):
        """
        @return: the list of existing version numbers for this document.
        @rtype: list of integer
        """
        versions = []
        for docfile in self.docfiles:
            if not docfile.get_version() in versions:
                versions.append(docfile.get_version())
        versions.sort()
        return versions

    def delete(self):
        """
        Delete this document.
        @see: L{undelete} for how to undelete the document.
        @raise InvenioBibDocFileError: in case of errors.
        """
        try:
            today = datetime.today()
            self.change_name('DELETED-%s%s-%s' % (today.strftime('%Y%m%d%H%M%S'), today.microsecond, self.docname))
            run_sql("UPDATE bibdoc SET status='DELETED' WHERE id=%s", (self.id,))
            self.status = 'DELETED'
        except Exception, e:
            register_exception()
            raise InvenioBibDocFileError, "It's impossible to delete bibdoc %s: %s" % (self.id, e)

    def deleted_p(self):
        """
        @return: True if this document has been deleted.
        @rtype: bool
        """
        return self.status == 'DELETED'

    def empty_p(self):
        """
        @return: True if this document is empty, i.e. it has no bibdocfile
        connected.
        @rtype: bool
        """
        return len(self.docfiles) == 0

    def undelete(self, previous_status=''):
        """
        Undelete a deleted file (only if it was actually deleted via L{delete}).
        The previous C{status}, i.e. the restriction key can be provided.
        Otherwise the undeleted document will be public.
        @param previous_status: the previous status the should be restored.
        @type previous_status: string
        @raise InvenioBibDocFileError: in case of any error.
        """
        bibrecdocs = BibRecDocs(self.recid)
        try:
            run_sql("UPDATE bibdoc SET status=%s WHERE id=%s AND status='DELETED'", (previous_status, self.id))
        except Exception, e:
            raise InvenioBibDocFileError, "It's impossible to undelete bibdoc %s: %s" % (self.id, e)
        if self.docname.startswith('DELETED-'):
            try:
                # Let's remove DELETED-20080214144322- in front of the docname
                original_name = '-'.join(self.docname.split('-')[2:])
                original_name = bibrecdocs.propose_unique_docname(original_name)
                self.change_name(original_name)
            except Exception, e:
                raise InvenioBibDocFileError, "It's impossible to restore the previous docname %s. %s kept as docname because: %s" % (original_name, self.docname, e)
        else:
            raise InvenioBibDocFileError, "Strange just undeleted docname isn't called DELETED-somedate-docname but %s" % self.docname

    def delete_file(self, format, version):
        """
        Delete a specific format/version of this document on the filesystem.
        @param format: the particular format to be deleted.
        @type format: string
        @param version: the particular version to be deleted.
        @type version: integer
        @note: this operation is not reversible!"""
        try:
            afile = self.get_file(format, version)
        except InvenioBibDocFileError:
            return
        try:
            os.remove(afile.get_full_path())
            run_sql("DELETE FROM bibdocfsinfo WHERE id_bibdoc=%s AND version=%s AND format=%s", (self.id, afile.get_version(), afile.get_format()))
            last_version = run_sql("SELECT max(version) FROM bibdocfsinfo WHERE id_bibdoc=%s", (self.id, ))[0][0]
            if last_version:
                ## Updating information about last version
                run_sql("UPDATE bibdocfsinfo SET last_version=true WHERE id_bibdoc=%s AND version=%s", (self.id, last_version))
                run_sql("UPDATE bibdocfsinfo SET last_version=false WHERE id_bibdoc=%s AND version<>%s", (self.id, last_version))
        except OSError:
            pass
        self.touch()
        self._build_file_list()

    def get_history(self):
        """
        @return: a human readable and parsable string that represent the
            history of this document.
        @rtype: string
        """
        ret = []
        hst = run_sql("""SELECT action, docname, docformat, docversion,
                docsize, docchecksum, doctimestamp
                FROM hstDOCUMENT
                WHERE id_bibdoc=%s ORDER BY doctimestamp ASC""", (self.id, ))
        for row in hst:
            ret.append("%s %s '%s', format: '%s', version: %i, size: %s, checksum: '%s'" % (row[6].strftime('%Y-%m-%d %H:%M:%S'), row[0], row[1], row[2], row[3], nice_size(row[4]), row[5]))
        return ret

    def _build_file_list(self, context=''):
        """
        Lists all files attached to the bibdoc. This function should be
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

        if context != ('init', 'init_from_disk'):
            previous_file_list = list(self.docfiles)
        res = run_sql("SELECT status,docname,creation_date,"
            "modification_date,more_info FROM bibdoc WHERE id=%s", (self.id,))
        self.cd = res[0][2]
        self.md = res[0][3]
        self.docname = res[0][1]
        self.status = res[0][0]
        self.more_info = BibDocMoreInfo(self.id, blob_to_string(res[0][4]))
        self.docfiles = []
        if CFG_BIBDOCFILE_ENABLE_BIBDOCFSINFO_CACHE and context == 'init':
            ## In normal init context we read from DB
            res = run_sql("SELECT version, format, cd, md, checksum, filesize FROM bibdocfsinfo WHERE id_bibdoc=%s", (self.id, ))
            for version, format, cd, md, checksum, size in res:
                self.docfiles.append(BibDocFile(
                    os.path.join(self.basedir, self.docname + format + ";%s" % version), self.doctype,
                    version, self.docname, format, self.recid, self.id, self.status, checksum,
                    self.more_info, human_readable=self.human_readable, cd=cd, md=md, size=size))
        else:
            if os.path.exists(self.basedir):
                self.md5s = Md5Folder(self.basedir)
                files = os.listdir(self.basedir)
                files.sort()
                for afile in files:
                    if not afile.startswith('.'):
                        try:
                            filepath = os.path.join(self.basedir, afile)
                            dirname, basename, format, fileversion = decompose_file_with_version(filepath)
                            checksum = self.md5s.get_checksum(afile)
                            # we can append file:
                            self.docfiles.append(BibDocFile(filepath, self.doctype,
                                fileversion, basename, format,
                                self.recid, self.id, self.status, checksum,
                                self.more_info, human_readable=self.human_readable))
                        except Exception, e:
                            register_exception()
        if context in ('init', 'init_from_disk'):
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

    def _sync_to_db(self):
        """
        Update the content of the bibdocfile table by taking what is available on the filesystem.
        """
        self._build_file_list('init_from_disk')
        run_sql("DELETE FROM bibdocfsinfo WHERE id_bibdoc=%s", (self.id,))
        for afile in self.docfiles:
            run_sql("INSERT INTO bibdocfsinfo(id_bibdoc, version, format, last_version, cd, md, checksum, filesize, mime) VALUES(%s, %s, %s, false, %s, %s, %s, %s, %s)", (self.id, afile.get_version(), afile.get_format(), afile.cd, afile.md, afile.get_checksum(), afile.get_size(), afile.mime))
            run_sql("UPDATE bibdocfsinfo SET last_version=true WHERE id_bibdoc=%s AND version=%s", (self.id, self.get_latest_version()))

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

    def list_latest_files(self, list_hidden=True):
        """Returns all the docfiles within the last version."""
        return self.list_version_files(self.get_latest_version(), list_hidden=list_hidden)

    def list_version_files(self, version, list_hidden=True):
        """Return all the docfiles of a particular version."""
        version = int(version)
        return [docfile for docfile in self.docfiles if docfile.get_version() == version and (list_hidden or not docfile.hidden_p())]

    def check_file_exists(self, path, format):
        """
        Check if a file with the same content of the file pointed in C{path}
        is already attached to this record.

        @param path: the file to be checked against.
        @type path: string
        @return: True if a file with the requested content is already attached
        to the record.
        @rtype: bool
        """
        # Let's consider all the latest files
        for afile in self.list_latest_files():
            if afile.is_identical_to(path, format):
                return True
        return False

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
        return run_sql("INSERT DELAYED INTO rnkDOWNLOADS "
            "(id_bibrec,id_bibdoc,file_version,file_format,"
            "id_user,client_host,download_time) VALUES "
            "(%s,%s,%s,%s,%s,INET_ATON(%s),NOW())",
            (self.recid, self.id, version, format,
            userid, ip_address,))

def generic_path2bidocfile(fullpath):
    """
    Returns a BibDocFile objects that wraps the given fullpath.
    @note: the object will contain the minimum information that can be
        guessed from the fullpath (e.g. docname, format, subformat, version,
        md5, creation_date, modification_date). It won't contain for example
        a comment, a description, a doctype, a restriction.
    """
    fullpath = os.path.abspath(fullpath)
    try:
        path, name, format, version = decompose_file_with_version(fullpath)
    except ValueError:
        ## There is no version
        version = 0
        path, name, format = decompose_file(fullpath)
    md5folder = Md5Folder(path)
    checksum = md5folder.get_checksum(os.path.basename(fullpath))
    return BibDocFile(fullpath=fullpath,
        doctype=None,
        version=version,
        name=name,
        format=format,
        recid=0,
        docid=0,
        status=None,
        checksum=checksum,
        more_info=None)

class BibDocFile:
    """This class represents a physical file in the Invenio filesystem.
    It should never be instantiated directly"""

    def __init__(self, fullpath, doctype, version, name, format, recid, docid, status, checksum, more_info=None, human_readable=False, cd=None, md=None, size=None):
        self.fullpath = os.path.abspath(fullpath)
        self.doctype = doctype
        self.docid = docid
        self.recid = recid
        self.version = version
        self.status = status
        self.checksum = checksum
        self.human_readable = human_readable
        if more_info:
            self.description = more_info.get_description(format, version)
            self.comment = more_info.get_comment(format, version)
            self.flags = more_info.get_flags(format, version)
        else:
            self.description = None
            self.comment = None
            self.flags = []
        self.format = normalize_format(format)
        self.superformat = get_superformat_from_format(self.format)
        self.subformat = get_subformat_from_format(self.format)
        self.fullname = name
        if format:
            self.fullname += self.superformat
        self.mime, self.encoding = _mimes.guess_type(self.fullname)
        if self.mime is None:
            self.mime = "application/octet-stream"
        self.more_info = more_info
        self.hidden = 'HIDDEN' in self.flags
        self.size = size or os.path.getsize(fullpath)
        self.md = md or datetime.fromtimestamp(os.path.getmtime(fullpath))
        try:
            self.cd = cd or datetime.fromtimestamp(os.path.getctime(fullpath))
        except OSError:
            self.cd = self.md
        self.name = name
        self.dir = os.path.dirname(fullpath)
        if self.subformat:
            self.url = create_url('%s/%s/%s/files/%s%s' % (CFG_SITE_URL, CFG_SITE_RECORD, self.recid, urllib.quote(self.name), urllib.quote(self.superformat)), {'subformat' : self.subformat})
            self.fullurl = create_url('%s/%s/%s/files/%s%s' % (CFG_SITE_URL, CFG_SITE_RECORD, self.recid, urllib.quote(self.name), urllib.quote(self.superformat)), {'subformat' : self.subformat, 'version' : self.version})
        else:
            self.url = create_url('%s/%s/%s/files/%s%s' % (CFG_SITE_URL, CFG_SITE_RECORD, self.recid, urllib.quote(self.name), urllib.quote(self.superformat)), {})
            self.fullurl = create_url('%s/%s/%s/files/%s%s' % (CFG_SITE_URL, CFG_SITE_RECORD, self.recid, urllib.quote(self.name), urllib.quote(self.superformat)), {'version' : self.version})
        self.etag = '"%i%s%i"' % (self.docid, self.format, self.version)
        self.magic = None

    def __repr__(self):
        return ('BibDocFile(%s, %s, %i, %s, %s, %i, %i, %s, %s, %s, %s)' % (repr(self.fullpath), repr(self.doctype), self.version, repr(self.name), repr(self.format), self.recid, self.docid, repr(self.status), repr(self.checksum), repr(self.more_info), repr(self.human_readable)))

    def __str__(self):
        out = '%s:%s:%s:%s:fullpath=%s\n' % (self.recid, self.docid, self.version, self.format, self.fullpath)
        out += '%s:%s:%s:%s:fullname=%s\n' % (self.recid, self.docid, self.version, self.format, self.fullname)
        out += '%s:%s:%s:%s:name=%s\n' % (self.recid, self.docid, self.version, self.format, self.name)
        out += '%s:%s:%s:%s:subformat=%s\n' % (self.recid, self.docid, self.version, self.format, get_subformat_from_format(self.format))
        out += '%s:%s:%s:%s:status=%s\n' % (self.recid, self.docid, self.version, self.format, self.status)
        out += '%s:%s:%s:%s:checksum=%s\n' % (self.recid, self.docid, self.version, self.format, self.checksum)
        if self.human_readable:
            out += '%s:%s:%s:%s:size=%s\n' % (self.recid, self.docid, self.version, self.format, nice_size(self.size))
        else:
            out += '%s:%s:%s:%s:size=%s\n' % (self.recid, self.docid, self.version, self.format, self.size)
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
        out += '%s:%s:%s:%s:flags=%s\n' % (self.recid, self.docid, self.version, self.format, self.flags)
        out += '%s:%s:%s:%s:etag=%s\n' % (self.recid, self.docid, self.version, self.format, self.etag)
        return out

    def display(self, ln = CFG_SITE_LANG):
        """Returns a formatted representation of this docfile."""
        return bibdocfile_templates.tmpl_bibdocfile_filelist(
                 ln = ln,
                 recid = self.recid,
                 version = self.version,
                 md = self.md,
                 name = self.name,
                 superformat = self.superformat,
                 subformat = self.subformat,
                 nice_size = nice_size(self.size),
                 description = self.description or ''
               )

    def is_identical_to(self, path, format):
        """
        @path: the path of another file on disk.
        @return: True if L{path} is contains bitwise the same content.
        """
        if self.format != format:
            return False
        if os.path.getsize(path) != self.size:
            return False
        if calculate_md5(path) != self.checksum:
            return False
        return filecmp.cmp(self.get_full_path(), path)

    def is_restricted(self, user_info):
        """Returns restriction state. (see acc_authorize_action return values)"""
        if self.status not in ('', 'DELETED'):
            return check_bibdoc_authorization(user_info, status=self.status)
        elif self.status == 'DELETED':
            return (1, 'File has ben deleted')
        else:
            return (0, '')

    def is_icon(self, subformat_re=CFG_BIBDOCFILE_ICON_SUBFORMAT_RE):
        """
        @param subformat_re: by default the convention is that
            L{CFG_BIBDOCFILE_ICON_SUBFORMAT_RE} is used as a subformat indicator to
            mean that a particular format is to be used as an icon.
            Specifiy a different subformat if you need to use a different
            convention.
        @type subformat: compiled regular expression
        @return: True if this file is an icon.
        @rtype: bool
        """
        return bool(subformat_re.match(self.subformat))

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

    def get_subformat(self):
        return self.subformat

    def get_superformat(self):
        return self.superformat

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
        if self.magic is None:
            if CFG_HAS_MAGIC == 1:
                magic_cookies = _get_magic_cookies()
                magic_result = []
                for key in magic_cookies.keys():
                    magic_result.append(magic_cookies[key].file(self.fullpath))
                self.magic = tuple(magic_result)
            elif CFG_HAS_MAGIC == 2:
                magic_result = []
                for key in ({'mime': False, 'mime_encoding': False},
                        {'mime': True, 'mime_encoding': False},
                        {'mime': False, 'mime_encoding': True}):
                    magic_result.append(_magic_wrapper(self.fullpath, **key))
                self.magic = tuple(magic_result)
        return self.magic

    def check(self):
        """Return True if the checksum corresponds to the file."""
        return calculate_md5(self.fullpath) == self.checksum

    def stream(self, req, download=False):
        """Stream the file.  Note that no restriction check is being
        done here, since restrictions have been checked previously
        inside websubmit_webinterface.py."""
        if os.path.exists(self.fullpath):
            if random.random() < CFG_BIBDOCFILE_MD5_CHECK_PROBABILITY and calculate_md5(self.fullpath) != self.checksum:
                raise InvenioBibDocFileError, "File %s, version %i, for record %s is corrupted!" % (self.fullname, self.version, self.recid)
            stream_file(req, self.fullpath, "%s%s" % (self.name, self.superformat), self.mime, self.encoding, self.etag, self.checksum, self.fullurl, download=download)
            raise apache.SERVER_RETURN, apache.DONE
        else:
            req.status = apache.HTTP_NOT_FOUND
            raise InvenioBibDocFileError, "%s does not exists!" % self.fullpath

_RE_STATUS_PARSER = re.compile(r'^(?P<type>email|group|egroup|role|firerole|status):\s*(?P<value>.*)$', re.S + re.I)
def check_bibdoc_authorization(user_info, status):
    """
    Check if the user is authorized to access a document protected with the given status.

    L{status} is a string of the form::

        auth_type: auth_value

    where C{auth_type} can have values in::
        email, group, role, firerole, status

    and C{auth_value} has a value interpreted againsta C{auth_type}:
    - C{email}: the user can access the document if his/her email matches C{auth_value}
    - C{group}: the user can access the document if one of the groups (local or
        external) of which he/she is member matches C{auth_value}
    - C{role}: the user can access the document if he/she belongs to the WebAccess
        role specified in C{auth_value}
    - C{firerole}: the user can access the document if he/she is implicitly matched
        by the role described by the firewall like role definition in C{auth_value}
    - C{status}: the user can access the document if he/she is authorized to
        for the action C{viewrestrdoc} with C{status} paramter having value
        C{auth_value}

    @note: If no C{auth_type} is specified or if C{auth_type} is not one of the
        above, C{auth_value} will be set to the value contained in the
        parameter C{status}, and C{auth_type} will be considered to be C{status}.

    @param user_info: the user_info dictionary
    @type: dict
    @param status: the status of the document.
    @type status: string
    @return: a tuple, of the form C{(auth_code, auth_message)} where auth_code is 0
        if the authorization is granted and greater than 0 otherwise.
    @rtype: (int, string)
    @raise ValueError: in case of unexpected parsing error.
    """
    def parse_status(status):
        g = _RE_STATUS_PARSER.match(status)
        if g:
            return (g.group('type').lower(), g.group('value'))
        else:
            return ('status', status)
    if acc_is_user_in_role(user_info, acc_get_role_id(SUPERADMINROLE)):
        return (0, CFG_WEBACCESS_WARNING_MSGS[0])
    auth_type, auth_value = parse_status(status)
    if auth_type == 'status':
        return acc_authorize_action(user_info, 'viewrestrdoc', status=auth_value)
    elif auth_type == 'email':
        if not auth_value.lower().strip() == user_info['email'].lower().strip():
            return (1, 'You must be member of the group %s in order to access this document' % repr(auth_value))
    elif auth_type == 'group':
        if not auth_value in user_info['group']:
            return (1, 'You must be member of the group %s in order to access this document' % repr(auth_value))
    elif auth_type == 'role':
        if not acc_is_user_in_role(user_info, acc_get_role_id(auth_value)):
            return (1, 'You must be member in the role %s in order to access this document' % repr(auth_value))
    elif auth_type == 'firerole':
        if not acc_firerole_check_user(user_info, compile_role_definition(auth_value)):
            return (1, 'You must be authorized in order to access this document')
    else:
        raise ValueError, 'Unexpected authorization type %s for %s' % (repr(auth_type), repr(auth_value))
    return (0, CFG_WEBACCESS_WARNING_MSGS[0])

_RE_BAD_MSIE = re.compile("MSIE\s+(\d+\.\d+)")
def stream_file(req, fullpath, fullname=None, mime=None, encoding=None, etag=None, md5=None, location=None, download=False):
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
    g = _RE_BAD_MSIE.search(headers.get('user-agent', "MSIE 6.0"))
    bad_msie = g and float(g.group(1)) < 9.0

    if CFG_BIBDOCFILE_USE_XSENDFILE:
        ## If XSendFile is supported by the server, let's use it.
        if os.path.exists(fullpath):
            if fullname is None:
                fullname = os.path.basename(fullpath)
            if bad_msie:
                ## IE is confused by quotes
                req.headers_out["Content-Disposition"] = 'attachment; filename=%s' % fullname.replace('"', '\\"')
            elif download:
                req.headers_out["Content-Disposition"] = 'attachment; filename="%s"' % fullname.replace('"', '\\"')
            else:
                ## IE is confused by inline
                req.headers_out["Content-Disposition"] = 'inline; filename="%s"' % fullname.replace('"', '\\"')
            req.headers_out["X-Sendfile"] = fullpath
            if mime is None:
                format = decompose_file(fullpath)[2]
                (mime, encoding) = _mimes.guess_type(fullpath)
                if mime is None:
                    mime = "application/octet-stream"
            if not bad_msie:
                ## IE is confused by not supported mimetypes
                req.content_type = mime
            return ""
        else:
            raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND

    if headers['if-match']:
        if etag is not None and etag not in headers['if-match']:
            raise apache.SERVER_RETURN, apache.HTTP_PRECONDITION_FAILED

    if os.path.exists(fullpath):
        mtime = os.path.getmtime(fullpath)
        if fullname is None:
            fullname = os.path.basename(fullpath)
        if mime is None:
            (mime, encoding) = _mimes.guess_type(fullpath)
            if mime is None:
                mime = "application/octet-stream"
        if location is None:
            location = req.uri
        if not bad_msie:
            ## IE is confused by not supported mimetypes
            req.content_type = mime
        req.encoding = encoding
        req.filename = fullname
        req.headers_out["Last-Modified"] = time.strftime('%a, %d %b %Y %X GMT', time.gmtime(mtime))
        if CFG_ENABLE_HTTP_RANGE_REQUESTS:
            req.headers_out["Accept-Ranges"] = "bytes"
        else:
            req.headers_out["Accept-Ranges"] = "none"
        req.headers_out["Content-Location"] = location
        if etag is not None:
            req.headers_out["ETag"] = etag
        if md5 is not None:
            req.headers_out["Content-MD5"] = base64.encodestring(binascii.unhexlify(md5.upper()))[:-1]
        if bad_msie:
            ## IE is confused by quotes
            req.headers_out["Content-Disposition"] = 'attachment; filename=%s' % fullname.replace('"', '\\"')
        elif download:
            req.headers_out["Content-Disposition"] = 'attachment; filename="%s"' % fullname.replace('"', '\\"')
        else:
            ## IE is confused by inline
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
        if CFG_ENABLE_HTTP_RANGE_REQUESTS and headers['range']:
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
    types.sort()
    if 'Main' in types:
        ## Move 'Main' at the beginning
        types.remove('Main')
        types.insert(0, 'Main')
    return types

def list_versions_from_array(docfiles):
    """Retrieve the list of existing versions from the given docfiles list."""
    versions = []
    for docfile in docfiles:
        if not docfile.get_version() in versions:
            versions.append(docfile.get_version())
    versions.sort()
    versions.reverse()
    return versions

def _make_base_dir(docid):
    """Given a docid it returns the complete path that should host its files."""
    group = "g" + str(int(int(docid) / CFG_BIBDOCFILE_FILESYSTEM_BIBDOC_GROUP_LIMIT))
    return os.path.join(CFG_BIBDOCFILE_FILEDIR, group, str(docid))

class Md5Folder:
    """Manage all the Md5 checksum about a folder"""
    def __init__(self, folder):
        """Initialize the class from the md5 checksum of a given path"""
        self.folder = folder
        self.load()

    def update(self, only_new=True):
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
            register_exception(alert_admin=True)
            raise InvenioBibDocFileError("Encountered an exception while storing .md5 for folder '%s': '%s'" % (self.folder, e))

    def load(self):
        """Load .md5 into the md5 dictionary"""
        self.md5s = {}
        md5_path = os.path.join(self.folder, ".md5")
        if os.path.exists(md5_path):
            for row in open(md5_path, "r"):
                md5hash = row[:32]
                filename = row[34:].strip()
                self.md5s[filename] = md5hash
        else:
            self.update()

    def check(self, filename=''):
        """Check the specified file or all the files for which it exists a hash
        for being coherent with the stored hash."""
        if filename and filename in self.md5s.keys():
            try:
                return self.md5s[filename] == calculate_md5(os.path.join(self.folder, filename))
            except Exception, e:
                register_exception(alert_admin=True)
                raise InvenioBibDocFileError("Encountered an exception while loading '%s': '%s'" % (os.path.join(self.folder, filename), e))
        else:
            for filename, md5hash in self.md5s.items():
                try:
                    if calculate_md5(os.path.join(self.folder, filename)) != md5hash:
                        return False
                except Exception, e:
                    register_exception(alert_admin=True)
                    raise InvenioBibDocFileError("Encountered an exception while loading '%s': '%s'" % (os.path.join(self.folder, filename), e))
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
        raise InvenioBibDocFileError("Encountered an exception while calculating md5 for file '%s': '%s'" % (filename, e))

def calculate_md5(filename, force_internal=False):
    """Calculate the md5 of a physical file. This is suitable for files smaller
    than 256Kb."""
    if not CFG_PATH_MD5SUM or force_internal or os.path.getsize(filename) < CFG_BIBDOCFILE_MD5_THRESHOLD:
        try:
            to_be_read = open(filename, "rb")
            computed_md5 = md5()
            while True:
                buf = to_be_read.read(CFG_BIBDOCFILE_MD5_BUFFER)
                if buf:
                    computed_md5.update(buf)
                else:
                    break
            to_be_read.close()
            return computed_md5.hexdigest()
        except Exception, e:
            register_exception(alert_admin=True)
            raise InvenioBibDocFileError("Encountered an exception while calculating md5 for file '%s': '%s'" % (filename, e))
    else:
        return calculate_md5_external(filename)


def bibdocfile_url_to_bibrecdocs(url):
    """Given an URL in the form CFG_SITE_[SECURE_]URL/CFG_SITE_RECORD/xxx/files/... it returns
    a BibRecDocs object for the corresponding recid."""

    recid = decompose_bibdocfile_url(url)[0]
    return BibRecDocs(recid)

def bibdocfile_url_to_bibdoc(url):
    """Given an URL in the form CFG_SITE_[SECURE_]URL/CFG_SITE_RECORD/xxx/files/... it returns
    a BibDoc object for the corresponding recid/docname."""

    docname = decompose_bibdocfile_url(url)[1]
    return bibdocfile_url_to_bibrecdocs(url).get_bibdoc(docname)

def bibdocfile_url_to_bibdocfile(url):
    """Given an URL in the form CFG_SITE_[SECURE_]URL/CFG_SITE_RECORD/xxx/files/... it returns
    a BibDocFile object for the corresponding recid/docname/format."""
    dummy, dummy, format = decompose_bibdocfile_url(url)
    return bibdocfile_url_to_bibdoc(url).get_file(format)

def bibdocfile_url_to_fullpath(url):
    """Given an URL in the form CFG_SITE_[SECURE_]URL/CFG_SITE_RECORD/xxx/files/... it returns
    the fullpath for the corresponding recid/docname/format."""

    return bibdocfile_url_to_bibdocfile(url).get_full_path()

def bibdocfile_url_p(url):
    """Return True when the url is a potential valid url pointing to a
    fulltext owned by a system."""
    if url.startswith('%s/getfile.py' % CFG_SITE_URL) or url.startswith('%s/getfile.py' % CFG_SITE_SECURE_URL):
        return True
    if not (url.startswith('%s/%s/' % (CFG_SITE_URL, CFG_SITE_RECORD)) or url.startswith('%s/%s/' % (CFG_SITE_SECURE_URL, CFG_SITE_RECORD))):
        return False
    splitted_url = url.split('/files/')
    return len(splitted_url) == 2 and splitted_url[0] != '' and splitted_url[1] != ''

def get_docid_from_bibdocfile_fullpath(fullpath):
    """Given a bibdocfile fullpath (e.g. "CFG_BIBDOCFILE_FILEDIR/g0/123/bar.pdf;1")
    returns the docid (e.g. 123)."""
    if not fullpath.startswith(os.path.join(CFG_BIBDOCFILE_FILEDIR, 'g')):
        raise InvenioBibDocFileError, "Fullpath %s doesn't correspond to a valid bibdocfile fullpath" % fullpath
    dirname, base, extension, version = decompose_file_with_version(fullpath)
    try:
        return int(dirname.split('/')[-1])
    except:
        raise InvenioBibDocFileError, "Fullpath %s doesn't correspond to a valid bibdocfile fullpath" % fullpath

def decompose_bibdocfile_fullpath(fullpath):
    """Given a bibdocfile fullpath (e.g. "CFG_BIBDOCFILE_FILEDIR/g0/123/bar.pdf;1")
    returns a quadruple (recid, docname, format, version)."""
    if not fullpath.startswith(os.path.join(CFG_BIBDOCFILE_FILEDIR, 'g')):
        raise InvenioBibDocFileError, "Fullpath %s doesn't correspond to a valid bibdocfile fullpath" % fullpath
    dirname, base, extension, version = decompose_file_with_version(fullpath)
    try:
        docid = int(dirname.split('/')[-1])
        bibdoc = BibDoc(docid)
        recid = bibdoc.get_recid()
        docname = bibdoc.get_docname()
        return recid, docname, extension, version
    except:
        raise InvenioBibDocFileError, "Fullpath %s doesn't correspond to a valid bibdocfile fullpath" % fullpath

def decompose_bibdocfile_url(url):
    """Given a bibdocfile_url return a triple (recid, docname, format)."""
    if url.startswith('%s/getfile.py' % CFG_SITE_URL) or url.startswith('%s/getfile.py' % CFG_SITE_SECURE_URL):
        return decompose_bibdocfile_very_old_url(url)
    if url.startswith('%s/%s/' % (CFG_SITE_URL, CFG_SITE_RECORD)):
        recid_file = url[len('%s/%s/' % (CFG_SITE_URL, CFG_SITE_RECORD)):]
    elif url.startswith('%s/%s/' % (CFG_SITE_SECURE_URL, CFG_SITE_RECORD)):
        recid_file = url[len('%s/%s/' % (CFG_SITE_SECURE_URL, CFG_SITE_RECORD)):]
    else:
        raise InvenioBibDocFileError, "Url %s doesn't correspond to a valid record inside the system." % url
    recid_file = recid_file.replace('/files/', '/')
    recid, docname, format = decompose_file(urllib.unquote(recid_file))
    if not recid and docname.isdigit():
        ## If the URL was something similar to CFG_SITE_URL/CFG_SITE_RECORD/123
        return (int(docname), '', '')
    return (int(recid), docname, format)

re_bibdocfile_old_url = re.compile(r'/%s/(\d*)/files/' % CFG_SITE_RECORD)
def decompose_bibdocfile_old_url(url):
    """Given a bibdocfile old url (e.g. CFG_SITE_URL/CFG_SITE_RECORD/123/files)
    it returns the recid."""
    g = re_bibdocfile_old_url.search(url)
    if g:
        return int(g.group(1))
    raise InvenioBibDocFileError('%s is not a valid old bibdocfile url' % url)

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
                    raise InvenioBibDocFileError('%s has not enough params to correspond to a bibdocfile.' % url)
                format = normalize_format(params.get('format', [''])[0])
                return (recid, docname, format)
            except Exception, e:
                raise InvenioBibDocFileError('Problem with %s: %s' % (url, e))
        else:
            raise InvenioBibDocFileError('%s has no params to correspond to a bibdocfile.' % url)
    else:
        raise InvenioBibDocFileError('%s is not a valid very old bibdocfile url' % url)

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
    if is_url_a_local_file(url):
        path = urllib2.urlparse.urlsplit(urllib.unquote(url))[2]
        return os.path.abspath(path)
    else:
        return url

def is_url_a_local_file(url):
    """Return True if the given URL is pointing to a local file."""
    protocol = urllib2.urlparse.urlsplit(url)[0]
    return protocol in ('', 'file')

def check_valid_url(url):
    """
    Check for validity of a url or a file.

    @param url: the URL to check
    @type url: string
    @raise StandardError: if the URL is not a valid URL.
    """
    try:
        if is_url_a_local_file(url):
            path = urllib2.urlparse.urlsplit(urllib.unquote(url))[2]
            if os.path.abspath(path) != path:
                raise StandardError, "%s is not a normalized path (would be %s)." % (path, os.path.normpath(path))
            for allowed_path in CFG_BIBUPLOAD_FFT_ALLOWED_LOCAL_PATHS + [CFG_TMPDIR, CFG_TMPSHAREDDIR, CFG_WEBSUBMIT_STORAGEDIR]:
                if path.startswith(allowed_path):
                    dummy_fd = open(path)
                    dummy_fd.close()
                    return
            raise StandardError, "%s is not in one of the allowed paths." % path
        else:
            try:
                open_url(url)
            except InvenioBibdocfileUnauthorizedURL, e:
                raise StandardError, str(e)
    except Exception, e:
        raise StandardError, "%s is not a correct url: %s" % (url, e)

def safe_mkstemp(suffix, prefix='bibdocfile_'):
    """Create a temporary filename that don't have any '.' inside a part
    from the suffix."""
    tmpfd, tmppath = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=CFG_TMPDIR)
    # Close the file and leave the responsability to the client code to
    # correctly open/close it.
    os.close(tmpfd)

    if '.' not in suffix:
        # Just in case format is empty
        return tmppath
    while '.' in os.path.basename(tmppath)[:-len(suffix)]:
        os.remove(tmppath)
        tmpfd, tmppath = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=CFG_TMPDIR)
        os.close(tmpfd)
    return tmppath

def download_local_file(filename, format=None):
    """
    Copies a local file to Invenio's temporary directory.

    @param filename: the name of the file to copy
    @type filename: string
    @param format: the format of the file to copy (will be found if not
            specified)
    @type format: string
    @return: the path of the temporary file created
    @rtype: string
    @raise StandardError: if something went wrong
    """
    # Make sure the format is OK.
    if format is None:
        format = guess_format_from_url(filename)
    else:
        format = normalize_format(format)

    tmppath = ''

    # Now try to copy.
    try:
        path = urllib2.urlparse.urlsplit(urllib.unquote(filename))[2]
        if os.path.abspath(path) != path:
            raise StandardError, "%s is not a normalized path (would be %s)." \
                    % (path, os.path.normpath(path))
        for allowed_path in CFG_BIBUPLOAD_FFT_ALLOWED_LOCAL_PATHS + [CFG_TMPDIR,
                CFG_WEBSUBMIT_STORAGEDIR]:
            if path.startswith(allowed_path):
                tmppath = safe_mkstemp(format)
                shutil.copy(path, tmppath)
                if os.path.getsize(tmppath) == 0:
                    os.remove(tmppath)
                    raise StandardError, "%s seems to be empty" % filename
                break
        else:
            raise StandardError, "%s is not in one of the allowed paths." % path
    except Exception, e:
        raise StandardError, "Impossible to copy the local file '%s': %s" % \
                (filename, str(e))

    return tmppath

def download_external_url(url, format=None):
    """
    Download a url (if it corresponds to a remote file) and return a
    local url to it.

    @param url: the URL to download
    @type url: string
    @param format: the format of the file (will be found if not specified)
    @type format: string
    @return: the path to the download local file
    @rtype: string
    @raise StandardError: if the download failed
    """
    tmppath = None

    # Make sure the format is OK.
    if format is None:
        # First try to find a known extension to the URL
        format = decompose_file(url, skip_version=True,
                only_known_extensions=True)[2]
        if not format:
            # No correct format could be found. Will try to get it from the
            # HTTP message headers.
            format = ''
    else:
        format = normalize_format(format)

    from_file, to_file, tmppath = None, None, ''

    try:
        from_file = open_url(url)
    except InvenioBibdocfileUnauthorizedURL, e:
        raise StandardError, str(e)
    except urllib2.URLError, e:
        raise StandardError, 'URL could not be opened: %s' % str(e)

    if not format:
        # We could not determine the format from the URL, so let's try
        # to read it from the HTTP headers.
        format = get_format_from_http_response(from_file)

    try:
        tmppath = safe_mkstemp(format)

        to_file = open(tmppath, 'w')
        while True:
            block = from_file.read(CFG_BIBDOCFILE_BLOCK_SIZE)
            if not block:
                break
            to_file.write(block)
        to_file.close()
        from_file.close()

        if os.path.getsize(tmppath) == 0:
            raise StandardError, "%s seems to be empty" % url
    except Exception, e:
        # Try to close and remove the temporary file.
        try:
            to_file.close()
        except Exception:
            pass
        try:
            os.remove(tmppath)
        except Exception:
            pass
        raise StandardError, "Error when downloading %s into %s: %s" % \
                (url, tmppath, e)

    return tmppath

def get_format_from_http_response(response):
    """
    Tries to retrieve the format of the file from the message headers of the
    HTTP response.

    @param response: the HTTP response
    @type response: file-like object (as returned by urllib.urlopen)
    @return: the format of the remote resource
    @rtype: string
    """
    def parse_content_type(text):
        return text.split(';')[0].strip()

    def parse_content_disposition(text):
        for item in text.split(';'):
            item = item.strip()
            if item.strip().startswith('filename='):
                return item[len('filename="'):-len('"')]

    info = response.info()

    format = ''

    content_disposition = info.getheader('Content-Disposition')
    if content_disposition:
        filename = parse_content_disposition(content_disposition)
        if filename:
            format = decompose_file(filename, only_known_extensions=False)[2]
            if format:
                return format

    content_type = info.getheader('Content-Type')
    if content_type:
        content_type = parse_content_type(content_type)
        if content_type not in ('text/plain', 'application/octet-stream'):
            ## We actually ignore these mimetypes since they are the
            ## defaults often returned by Apache in case the mimetype
            ## was not known
            ext = _mimes.guess_extension(content_type)
            if ext:
                ## Normalize some common magic mis-interpreation
                ext = {'.asc': '.txt', '.obj': '.bin'}.get(ext, ext)
                format = normalize_format(ext)

    return format

def download_url(url, format=None):
    """
    Download a url (if it corresponds to a remote file) and return a
    local url to it.
    """
    tmppath = None

    try:
        if is_url_a_local_file(url):
            tmppath = download_local_file(url, format=format)
        else:
            tmppath = download_external_url(url, format=format)
    except StandardError:
        raise

    return tmppath

class BibDocMoreInfo:
    """
    This class wraps contextual information of the documents, such as the
        - comments
        - descriptions
        - flags.
    Such information is kept separately per every format/version instance of
    the corresponding document and is searialized in the database, ready
    to be retrieved (but not searched).

    @param docid: the document identifier.
    @type docid: integer
    @param more_info: a serialized version of an already existing more_info
        object. If not specified this information will be readed from the
        database, and othewise an empty dictionary will be allocated.
    @raise ValueError: if docid is not a positive integer.
    @ivar docid: the document identifier as passed to the constructor.
    @type docid: integer
    @ivar more_info: the more_info dictionary that will hold all the
        additional document information.
    @type more_info: dict of dict of dict
    @note: in general this class is never instanciated in client code and
        never used outside bibdocfile module.
    @note: this class will be extended in the future to hold all the new auxiliary
    information about a document.
    """
    def __init__(self, docid, more_info=None):
        if not (type(docid) in (long, int) and docid > 0):
            raise ValueError("docid is not a positive integer, but %s." % docid)
        self.docid = docid
        if more_info is None:
            res = run_sql('SELECT more_info FROM bibdoc WHERE id=%s', (docid, ))
            if res and res[0][0]:
                self.more_info = cPickle.loads(blob_to_string(res[0][0]))
            else:
                self.more_info = {}
        else:
            self.more_info = cPickle.loads(more_info)
        if 'descriptions' not in self.more_info:
            self.more_info['descriptions'] = {}
        if 'comments' not in self.more_info:
            self.more_info['comments'] = {}
        if 'flags' not in self.more_info:
            self.more_info['flags'] = {}

    def __repr__(self):
        """
        @return: the canonical string representation of the C{BibDocMoreInfo}.
        @rtype: string
        """
        return 'BibDocMoreInfo(%i, %s)' % (self.docid, repr(cPickle.dumps(self.more_info)))

    def flush(self):
        """
        Flush this object to the database.
        """
        run_sql('UPDATE bibdoc SET more_info=%s WHERE id=%s', (cPickle.dumps(self.more_info), self.docid))

    def set_flag(self, flagname, format, version):
        """
        Sets a flag.

        @param flagname: the flag to set (see
            L{CFG_BIBDOCFILE_AVAILABLE_FLAGS}).
        @type flagname: string
        @param format: the format for which the flag should set.
        @type format: string
        @param version: the version for which the flag should set:
        @type version: integer
        @raise ValueError: if the flag is not in
            L{CFG_BIBDOCFILE_AVAILABLE_FLAGS}
        """
        if flagname in CFG_BIBDOCFILE_AVAILABLE_FLAGS:
            if not flagname in self.more_info['flags']:
                self.more_info['flags'][flagname] = {}
            if not version in self.more_info['flags'][flagname]:
                self.more_info['flags'][flagname][version] = {}
            if not format in self.more_info['flags'][flagname][version]:
                self.more_info['flags'][flagname][version][format] = {}
            self.more_info['flags'][flagname][version][format] = True
            self.flush()
        else:
            raise ValueError, "%s is not in %s" % (flagname, CFG_BIBDOCFILE_AVAILABLE_FLAGS)

    def get_comment(self, format, version):
        """
        Returns the specified comment.

        @param format: the format for which the comment should be
            retrieved.
        @type format: string
        @param version: the version for which the comment should be
            retrieved.
        @type version: integer
        @return: the specified comment.
        @rtype: string
        """
        try:
            assert(type(version) is int)
            format = normalize_format(format)
            return self.more_info['comments'].get(version, {}).get(format)
        except:
            register_exception()
            raise

    def get_description(self, format, version):
        """
        Returns the specified description.

        @param format: the format for which the description should be
            retrieved.
        @type format: string
        @param version: the version for which the description should be
            retrieved.
        @type version: integer
        @return: the specified description.
        @rtype: string
        """
        try:
            assert(type(version) is int)
            format = normalize_format(format)
            return self.more_info['descriptions'].get(version, {}).get(format)
        except:
            register_exception()
            raise

    def has_flag(self, flagname, format, version):
        """
        Return True if the corresponding has been set.

        @param flagname: the name of the flag (see
            L{CFG_BIBDOCFILE_AVAILABLE_FLAGS}).
        @type flagname: string
        @param format: the format for which the flag should be checked.
        @type format: string
        @param version: the version for which the flag should be checked.
        @type version: integer
        @return: True if the flag is set for the given format/version.
        @rtype: bool
        @raise ValueError: if the flagname is not in
            L{CFG_BIBDOCFILE_AVAILABLE_FLAGS}
        """
        if flagname in CFG_BIBDOCFILE_AVAILABLE_FLAGS:
            return self.more_info['flags'].get(flagname, {}).get(version, {}).get(format, False)
        else:
            raise ValueError, "%s is not in %s" % (flagname, CFG_BIBDOCFILE_AVAILABLE_FLAGS)

    def get_flags(self, format, version):
        """
        Return the list of all the enabled flags.

        @param format: the format for which the list should be returned.
        @type format: string
        @param version: the version for which the list should be returned.
        @type version: integer
        @return: the list of enabled flags (from
            L{CFG_BIBDOCFILE_AVAILABLE_FLAGS}).
        @rtype: list of string
        """
        return [flag for flag in self.more_info['flags'] if format in self.more_info['flags'][flag].get(version, {})]

    def set_comment(self, comment, format, version):
        """
        Set a comment.

        @param comment: the comment to be set.
        @type comment: string
        @param format: the format for which the comment should be set.
        @type format: string
        @param version: the version for which the comment should be set:
        @type version: integer
        """
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
        """
        Set a description.

        @param description: the description to be set.
        @type description: string
        @param format: the format for which the description should be set.
        @type format: string
        @param version: the version for which the description should be set:
        @type version: integer
        """
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

    def unset_comment(self, format, version):
        """
        Unset a comment.

        @param format: the format for which the comment should be unset.
        @type format: string
        @param version: the version for which the comment should be unset:
        @type version: integer
        """
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
        """
        Unset a description.

        @param format: the format for which the description should be unset.
        @type format: string
        @param version: the version for which the description should be unset:
        @type version: integer
        """
        try:
            assert(type(version) is int and version > 0)
            del self.more_info['descriptions'][version][format]
            self.flush()
        except KeyError:
            pass
        except:
            register_exception()
            raise

    def unset_flag(self, flagname, format, version):
        """
        Unset a flag.

        @param flagname: the flag to be unset (see
            L{CFG_BIBDOCFILE_AVAILABLE_FLAGS}).
        @type flagname: string
        @param format: the format for which the flag should be unset.
        @type format: string
        @param version: the version for which the flag should be unset:
        @type version: integer
        @raise ValueError: if the flag is not in
            L{CFG_BIBDOCFILE_AVAILABLE_FLAGS}
        """
        if flagname in CFG_BIBDOCFILE_AVAILABLE_FLAGS:
            try:
                del self.more_info['flags'][flagname][version][format]
                self.flush()
            except KeyError:
                pass
        else:
            raise ValueError, "%s is not in %s" % (flagname, CFG_BIBDOCFILE_AVAILABLE_FLAGS)

    def serialize(self):
        """
        @return: the serialized version of this object.
        @rtype: string
        """
        return cPickle.dumps(self.more_info)

def readfile(filename):
    """
    Read a file.

    @param filename: the name of the file to be read.
    @type filename: string
    @return: the text contained in the file.
    @rtype: string
    @note: Returns empty string in case of any error.
    @note: this function is useful for quick implementation of websubmit
    functions.
    """
    try:
        return open(filename).read()
    except Exception:
        return ''

class HeadRequest(urllib2.Request):
    """
    A request object to perform a HEAD request.
    """
    def get_method(self):
        return 'HEAD'


def read_cookie(cookiefile):
    """
    Parses a cookie file and returns a string as needed for the urllib2 headers
    The file should respect the Netscape cookie specifications
    """
    cookie_data = ''
    cfile = open(cookiefile, 'r')
    for line in cfile.readlines():
        tokens = line.split('\t')
        if len(tokens) == 7: # we are on a cookie line
            cookie_data += '%s=%s; ' % (tokens[5], tokens[6].replace('\n', ''))
    cfile.close()
    return cookie_data


def open_url(url, headers=None, head_request=False):
    """
    Opens a URL. If headers are passed as argument, no check is performed and
    the URL will be opened. Otherwise checks if the URL is present in
    CFG_BIBUPLOAD_FFT_ALLOWED_EXTERNAL_URLS and uses the headers specified in
    the config variable.

    @param url: the URL to open
    @type url: string
    @param headers: the headers to use
    @type headers: dictionary
    @param head_request: if True, perform a HEAD request, otherwise a POST
            request
    @type head_request: boolean
    @return: a file-like object as returned by urllib2.urlopen.
    """
    headers_to_use = None

    if headers is None:
        for regex, headers in _CFG_BIBUPLOAD_FFT_ALLOWED_EXTERNAL_URLS:
            if regex.match(url) is not None:
                headers_to_use = headers
                break

        if headers_to_use is None:
            # URL is not allowed.
            raise InvenioBibdocfileUnauthorizedURL, "%s is not an authorized " \
                    "external URL." % url
    else:
        headers_to_use = headers

    request_obj = head_request and HeadRequest or urllib2.Request
    request = request_obj(url)
    request.add_header('User-Agent', make_user_agent_string('bibdocfile'))
    for key, value in headers_to_use.items():
        try:
            value = globals()[value['fnc']](**value['args'])
        except (KeyError, TypeError):
            pass
        request.add_header(key, value)

    return urllib2.urlopen(request)


def update_modification_date_of_file(filepath, modification_date):
    """Update the modification time and date of the file with the modification_date
    @param filepath: the full path of the file that needs to be updated
    @type filepath: string
    @param modification_date: the new modification date and time
    @type modification_date: datetime.datetime object
    """
    try:
        modif_date_in_seconds = time.mktime(modification_date.timetuple()) # try to get the time in seconds
    except (AttributeError, TypeError):
        modif_date_in_seconds = 0
    if modif_date_in_seconds:
        statinfo = os.stat(filepath) # we need to keep the same access time
        os.utime(filepath, (statinfo.st_atime, modif_date_in_seconds)) #update the modification time
