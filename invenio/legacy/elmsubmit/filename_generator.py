# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011 CERN.
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

import sys
import os.path
import pkg_resources

import re
import os
import mimetypes
import zlib

try:
    import magic
    if not hasattr(magic, "open"):
        raise ImportError
    _got_magic = True
except ImportError:
    _got_magic = False

import gzip
try:
    import bz2
    _got_bz2 = True
except ImportError:
    _got_bz2 = False

from invenio.legacy.elmsubmit.misc import open_tempfile as _open_tempfile
from invenio.legacy.elmsubmit.misc import random_alphanum_string as _random_alphanum_string
from invenio.legacy.elmsubmit.misc import remove_tempfile as _remove_tempfile


def generate_filename(filename=None, file=None, content_type=None, no_rand_chars=8, prefix='', postfix=''):

    name_stub = _random_alphanum_string(no_rand_chars)
    name_ext = calculate_filename_extension(filename, file, content_type)
    return prefix + name_stub + postfix + '.' + name_ext

def calculate_filename_extension(filename=None, file=None, content_type=None):

    # If libmagic and its Python wrapper are installed then the latter is
    # used to calculate a file extension using a specially
    # prepared magic data file (./magic/magic.ext) which maps
    # magic tests to file extensions. Otherwise we use the mimetypes
    # module from the standard Python distribution.

    if (filename is None) and (file is None) and (content_type is None):
        raise TypeError('at least one of filename, file or content_type must be specified')
    elif (file is None) and (filename is None):
        # We only have content_type:
        return calculate_filename_ext_mimetypes(content_type)
    # We have at least one of file and filename, so we try to use libmagic
    elif _got_magic:
        return calculate_filename_ext_libmagic(filename, file)
    # We haven't got libmagic, so must use mimetypes:
    else:
        # But mimetypes requires content_type:
        if content_type is None:
            raise ImportError('Failed to import magic module. If no content-type is given, then magic module is required.')
        else:
            return calculate_filename_ext_mimetypes(content_type)

def calculate_filename_ext_libmagic(filename=None, file=None):

    # See comments in magic/magic.ext for details of the format
    # of the data file. All file extensions if recognized by a magic
    # test will be returned in the form "file_ext:{xyz}"; this lets us
    # detect the "file_ext:{}" marker and know we have a successful
    # guess at the correct extension. The reason we need this marker
    # is that libmagic has many tests whose return value is not
    # governed through the magic data file and so we need some way of
    # being sure a file extension has been returned. eg:

    # >>> magician.file('/etc/init.d')
    # "symbolic link to `rc.d/init.d'"

    if filename is None and file is None: raise ValueError('at least one of file or content_type must be specified')
    if not _got_magic: raise ImportError('magic module did not import successfully')

    magician = magic.open(magic.MAGIC_NONE)

    ret_load = magician.load()

    # Throw private error if the magic data file is corrupt, or
    # doesn't exist.

    if ret_load != 0: raise _MagicDataError()

    if filename is None:
        # then we have only been given file as binary string.

        # Get a temporary file and write file variable out to it
        # because the magic module expects to be handed the name of a
        # real file.

        tf, tf_name = _open_tempfile(mode='wb')
        tf.write(file)
        tf.close()

        delete_file = True
    else:
        os.stat(filename) # Make sure we can stat the file.
        tf_name = filename
        delete_file = False

    ext_info = magician.file(tf_name)

    # Now process ext_info to see if we can find a file extension
    # contained in it.

    file_ext_re = re.compile(r'file_ext:{(.+?)}')
    file_ext_match = file_ext_re.search(ext_info)

    if file_ext_match:
        name_ext = file_ext_match.group(1)

        # See if we have a compressed file type we can deal
        # with. If so, uncompress it and call ourself to get more
        # info:

        # Note that we could use the magic.MAGIC_COMPRESS flag to
        # get libmagic to do the decompression for us but:
        # 1. It only supports gzip
        # 2. The implementation has a nasty bug which has only
        #    been fixed in very recent releases of libmagic.

        if name_ext == 'gz':

            try:
                # Decompress the stream:
                decomp_file = gzip.open(tf_name).read()
            except zlib.error:
                # Couldn't decompress sucessfully, so just stick
                # with extension we have.
                pass
            else:
                # Guess an extension of the decompressed stream and
                # tack current '.gz' on the end:
                name_ext = calculate_filename_ext_libmagic(file=decomp_file)  + '.' + name_ext

        elif name_ext == 'bz2':

            try:
                # Decompress the file:
                if not _got_bz2:
                    raise ImportError('Failed to import bz2 module.')
                decomp_file = bz2.BZ2File(tf_name).read()
            except IOError:
                # Couldn't decompress sucessfully, so just stick
                # with extension we have.
                pass
            else:
                # Guess an extension of the decompressed stream and
                # tack current '.bz2' on the end:
                name_ext = calculate_filename_ext_libmagic(file=decomp_file)  + '.' + name_ext

    # Otherwise, look for special results from libmagic's
    # 'internal tests' that we recognize:

    elif ext_info.lower().rfind('tar archive') != -1:
        name_ext = 'tar'

    elif ext_info.lower().rfind('text') != -1:
        name_ext = 'txt'

    # Can't guess a filetype so use generic extension .dat

    else:
        name_ext = 'dat'

    # Identification done so get rid of the temp file, assuming we created the file:
    if delete_file: _remove_tempfile(tf_name)

    return name_ext

mimetypes.types_map = {}
mimetypes.init([pkg_resources.resource_filename('invenio.legacy.elmsubmit', 'mime.types.edited')])

def calculate_filename_ext_mimetypes(content_type):

    # mimetypes.types_map contains many 'builtin' maps.  We empty
    # it because we only want to use the maps from our edited
    # mime.types file:

    name_ext = mimetypes.guess_extension(content_type)

    # Use '.dat' as generic file extension.
    if name_ext is None: name_ext = '.dat'

    # Remove leading dot produced by mimetypes.
    name_ext = name_ext[1:]

    return name_ext

# Errors:

# This module may also produce IOError from it use of temporary
# files.
# REMEMBER TO DOCUMENT THIS ERROR POTENTIAL

class _MagicDataError(Exception):

    """
    Private error raised when we cannot compile and load the magic
    data file successfully. This will only occur if there is a problem
    with the module's installation.
    """

    pass

