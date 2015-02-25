# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013 CERN.
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

"""
Invenio mimetype helper functions.

Usage example:
    TODO

"""

import re
from invenio.base.globals import cfg
from mimetypes import MimeTypes
from six import iteritems
from werkzeug import cached_property, LocalProxy
from thread import get_ident

try:
    import magic
    if hasattr(magic, "open"):
        CFG_HAS_MAGIC = 1
    elif hasattr(magic, "Magic"):
        CFG_HAS_MAGIC = 2
except ImportError:
    CFG_HAS_MAGIC = 0

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
        return magic_object.from_file(local_path) # pylint: disable=E1103


class LazyMimeCache(object):

    @cached_property
    def mimes(self):
        """
        Returns extended MimeTypes.
        """
        _mimes = MimeTypes(strict=False)
        _mimes.suffix_map.update({'.tbz2' : '.tar.bz2'})
        _mimes.encodings_map.update({'.bz2' : 'bzip2'})

        if cfg['CFG_BIBDOCFILE_ADDITIONAL_KNOWN_MIMETYPES']:
            for key, value in iteritems(cfg['CFG_BIBDOCFILE_ADDITIONAL_KNOWN_MIMETYPES']):
                _mimes.add_type(key, value)
                del key, value

        return _mimes

    @cached_property
    def extensions(self):
        """
        Generate the regular expression to match all the known extensions.

        @return: the regular expression.
        @rtype: regular expression object
        """
        _tmp_extensions = self.mimes.encodings_map.keys() + \
                    self.mimes.suffix_map.keys() + \
                    self.mimes.types_map[1].keys() + \
                    cfg['CFG_BIBDOCFILE_ADDITIONAL_KNOWN_FILE_EXTENSIONS']
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


#: Lazy mime and extensitons cache.
_mime_cache = LazyMimeCache()
#: MimeTypes instance.
_mimes = LocalProxy(lambda: _mime_cache.mimes)
#: Regular expression to recognized extensions.
_extensions = LocalProxy(lambda: _mime_cache.extensions)


# Use only functions bellow in your code:


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
    >>> file_strip_ext("foo.gif;icon", only_know_extensions=True,
    ... allow_subformat=False)
    'foo.gif;icon'

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
    import os
    afile = afile.split(';')
    if len(afile)>1 and allow_subformat and not afile[-1].isdigit():
        afile = afile[0:-1]
    if len(afile)>1 and skip_version and afile[-1].isdigit():
        afile = afile[0:-1]
    afile = ';'.join(afile)
    nextfile = _extensions.sub('', afile)
    if nextfile == afile and not only_known_extensions:
        nextfile = os.path.splitext(afile)[0]
    while nextfile != afile:
        afile = nextfile
        nextfile = _extensions.sub('', afile)
    return nextfile

def guess_mimetype_and_encoding(afile):
    """
    Tries to guess mimetype and encoding of a file.

    @param afile: the path/name of a file
    @time afile: string
    @return: the mimetype and encoding
    @rtype: tuple
    """
    return _mimes.guess_type(afile)


def guess_extension(amimetype, normalize=False):
    """
    Tries to guess extension for a mimetype.

    @param amimetype: name of a mimetype
    @time amimetype: string
    @return: the extension
    @rtype: string
    """
    ext = _mimes.guess_extension(amimetype)
    if ext and normalize:
        ## Normalize some common magic mis-interpreation
        ext = {'.asc': '.txt', '.obj': '.bin'}.get(ext, ext)
        from invenio.legacy.bibdocfile.api_normalizer import normalize_format
        return normalize_format(ext)
    return ext


def get_magic_guesses(fullpath):
    """
    Return all the possible guesses from the magic library about
    the content of the file.

    @param fullpath: location of the file
    @type fullpath: string
    @return: guesses about content of the file
    @rtype: tuple
    """
    if CFG_HAS_MAGIC == 1:
        magic_cookies = _get_magic_cookies()
        magic_result = []
        for key in magic_cookies.keys():
            magic_result.append(magic_cookies[key].file(fullpath))
        return tuple(magic_result)
    elif CFG_HAS_MAGIC == 2:
        magic_result = []
        for key in ({'mime': False, 'mime_encoding': False},
                {'mime': True, 'mime_encoding': False},
                {'mime': False, 'mime_encoding': True}):
            magic_result.append(_magic_wrapper(fullpath, **key))
        return tuple(magic_result)


def guess_extension_from_path(local_path):
    try:
        if CFG_HAS_MAGIC == 1:
            magic_cookie = _get_magic_cookies()[magic.MAGIC_MIME_TYPE]
            mimetype = magic_cookie.file(local_path)
        elif CFG_HAS_MAGIC == 2:
            mimetype = _magic_wrapper(local_path, mime=True, mime_encoding=False)
        if CFG_HAS_MAGIC:
            return guess_extension(mimetype, normalize=True)
    except Exception:
        pass

