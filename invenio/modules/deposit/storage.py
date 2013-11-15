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
Storage abstraction layer for WebDeposit.
"""

import uuid
import hashlib

from fs import opener
from fs import path
import urllib2
try:
    from invenio.config import CFG_WEBDEPOSIT_MAX_UPLOAD_SIZE
except ImportError:
    CFG_WEBDEPOSIT_MAX_UPLOAD_SIZE = 104857600  # 100MB


class UploadError(IOError):
    pass


class ExternalFile(object):
    """
    Wrapper around a URL to make it behave like a file which can be passed to
    the storage layer
    """
    def __init__(self, url, filename):
        from invenio.legacy.bibdocfile.api import open_url, \
            InvenioBibdocfileUnauthorizedURL
        try:
            self._file = open_url(url, headers={})
            self.filename = None
            info = self._file.info()
            content_disposition = info.getheader('Content-Disposition')
            if content_disposition:
                for item in text.split(';'):
                    item = item.strip()
                    if item.strip().startswith('filename='):
                        self.filename = item[len('filename="'):-len('"')]
            if not self.filename:
                self.filename = filename

            try:
                size = int(info.getheader('Content-length'))
                if size > CFG_WEBDEPOSIT_MAX_UPLOAD_SIZE:
                    raise UploadError("File too big")
            except Exception:
                pass
        except InvenioBibdocfileUnauthorizedURL, e:
            raise WebDepositUploadError(str(e))
        except urllib2.URLError, e:
            raise WebDepositUploadError('URL could not be opened: %s' % str(e))

    def close(self):
        self._file.close()

    def read(self):
        return self._file.read()


class Storage(object):
    """
    Default storage backend
    """
    _fsdir = None

    def __init__(self, fs_path):
        self.fs_path = fs_path

    @property
    def storage(self):
        """ Get the pyFilesytem object for the backend path """
        if self._fsdir is None:
            # Opens a directory, creates it if needed, and ensures
            # it is writeable.
            self._fsdir = opener.fsopendir(
                self.fs_path, writeable=True, create_dir=True
            )
        return self._fsdir

    def unique_filename(self, filename):
        """ Generate a unique secure filename """
        return str(uuid.uuid4()) + "-" + filename

    def save(self, incoming_file, filename, unique_name=True,
             with_checksum=True):
        """ Store the incoming file """
        if unique_name:
            filename = self.unique_filename(filename)

        fs_file = self.storage.open(filename, 'wb')

        checksum = None
        f_bytes = incoming_file.read()
        fs_file.write(f_bytes)

        if with_checksum:
            m = hashlib.md5()
            m.update(f_bytes)
            checksum = m.hexdigest()

        fs_file.close()

        # Create complete file path and return it
        return (
            path.join(self.fs_path, filename),
            self.storage.getsize(filename),
            checksum,
            with_checksum,
        )

    @staticmethod
    def delete(fs_path):
        """ Delete the file on storage """
        (dirurl, filename) = opener.pathsplit(fs_path)
        fs = opener.fsopendir(dirurl)
        fs.remove(filename)

    @staticmethod
    def is_local(fs_path):
        """ Determine if file is a local file """
        (dirurl, filename) = opener.pathsplit(fs_path)
        fs = opener.fsopendir(dirurl)
        return fs.hassyspath(filename)

    @staticmethod
    def get_url(fs_path):
        """ Get a URL for the file """
        (dirurl, filename) = opener.pathsplit(fs_path)
        fs = opener.fsopendir(dirurl)
        return fs.getpathurl(filename)

    @staticmethod
    def get_syspath(fs_path):
        """ Get a local system path to the file """
        (dirurl, filename) = opener.pathsplit(fs_path)
        fs = opener.fsopendir(dirurl)
        return fs.getsyspath(filename)


class DepositionStorage(Storage):
    """
    Deposition storage backend that will save files to a
    a folder (<CFG_WEBDEPOSIT_UPLOAD_FOLDER>/<deposition_id>/).
    """
    def __init__(self, deposition_id):
        from invenio.config import CFG_WEBDEPOSIT_STORAGEDIR
        self.fs_path = path.join(
            CFG_WEBDEPOSIT_STORAGEDIR,
            str(deposition_id)
        )


class ChunkedDepositionStorage(DepositionStorage):
    """
    Chunked storage backend, capable of handling storage of a file
    in multiple chunks. Otherwise similar to DepositionStorage.
    """

    def chunk_filename(self, filename, chunks, chunk):
        return "%s_%s_%s" % (
            filename,
            chunks,
            chunk,
        )

    def save(self, incoming_file, filename, chunk=None, chunks=None):
        try:
            # Generate chunked file name
            chunk = int(chunk)
            chunks = int(chunks)
        except (ValueError, TypeError):
            raise WebDepositUploadError("Invalid chunk value: %s" % chunk)

        # Store chunk
        chunk_filename = self.chunk_filename(filename, chunks, chunk)

        res = super(ChunkedDepositionStorage, self).save(
            incoming_file, chunk_filename, unique_name=False,
            with_checksum=False,
        )

        # Only merge files on last_trunk
        if chunk != chunks-1:
            return res

        # Get the chunks
        file_chunks = self.storage.listdir(
            wildcard=self.chunk_filename(
                filename, chunks, '*'
            )
        )
        file_chunks.sort(key=lambda x: int(x.split("_")[-1]))

        # Write the chunks into one file
        filename = self.unique_filename(filename)
        fs_file = self.storage.open(filename, 'wb')
        m = hashlib.md5()

        for c in file_chunks:
            fs_c = self.storage.open(c, 'rb')
            f_bytes = fs_c.read()
            fs_file.write(f_bytes)
            fs_c.close()
            m.update(f_bytes)
            # Remove each chunk right after appending to main file, to
            # minimize storage usage.
            self.storage.remove(c)

        fs_file.close()
        checksum = m.hexdigest()

        return (
            path.join(self.fs_path, filename),
            self.storage.getsize(filename),
            checksum,
            True
        )
