# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014 CERN.
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

"""Dropbox file system.

Installation:: pip install invenio[dropbox]
"""

import os
import time
import datetime
import calendar

from UserDict import UserDict
from fs.base import FS, synchronize, NoDefaultMeta
from fs.path import normpath, abspath, pathsplit, basename, dirname
from fs.errors import (DirectoryNotEmptyError, UnsupportedError,
                       CreateFailedError, ResourceInvalidError,
                       ResourceNotFoundError,
                       OperationFailedError, DestinationExistsError,
                       RemoteConnectionError)
from fs.remote import RemoteFileBuffer
from fs.filelike import SpooledTemporaryFile

from dropbox import rest
from dropbox import client

# Items in cache are considered expired after 5 minutes.
CACHE_TTL = 300
# The format Dropbox uses for times.
TIME_FORMAT = '%a, %d %b %Y %H:%M:%S +0000'
# Max size for spooling to memory before using disk (5M).
MAX_BUFFER = 1024**2*5


class CacheItem(object):

    """Represent a path in the cache.

    There are two components to a path.
    It's individual metadata, and the children contained within it.
    """

    def __init__(self, metadata=None, children=None, timestamp=None):
        """Initialize a CacheItem instance."""
        self.metadata = metadata
        self.children = children
        if timestamp is None:
            timestamp = time.time()
        self.timestamp = timestamp

    def add_child(self, name, client=None):
        """Add a child."""
        if self.children is None:
            if client is not None:
                # This is a fix. When you add a child to a folder that
                # was still not listed, that folder gets only one
                # child when you list it afterwards. So this fix
                # first tries to check are the files/folders inside
                # this directory on cloud.
                client.children(self.metadata['path'])
            else:
                self.children = [name]
        else:
            if name not in self.children:
                self.children.append(name)

    def del_child(self, name):
        """Delete a child."""
        if self.children is None:
            return
        try:
            i = self.children.index(name)
        except ValueError:
            return
        self.children.pop(i)

    def _get_expired(self):
        if self.timestamp <= time.time() - CACHE_TTL:
            return True
    expired = property(_get_expired)

    def renew(self):
        """Renew."""
        self.timestamp = time.time()


class DropboxCache(UserDict):

    """Represent the dropbox cache."""

    def __init__(self, client):
        """Initialize a DropboxCache instance."""
        self._client = client
        UserDict.__init__(self)

    def set(self, path, metadata):
        """Set metadata."""
        self[path] = CacheItem(metadata)
        dname, bname = pathsplit(path)
        item = self.get(dname)
        if item:
            item.add_child(bname, self._client)

    def pop(self, path, default=None):
        """Pop data of a given path."""
        value = UserDict.pop(self, path, default)
        dname, bname = pathsplit(path)
        item = self.get(dname)
        if item:
            item.del_child(bname)
        return value


class DropboxClient(client.DropboxClient):

    """A wrapper around the official DropboxClient.

    This wrapper performs caching as well as converting
    errors to fs exceptions.
    """

    def __init__(self, *args, **kwargs):
        """Initialize a DropboxClient instance."""
        super(DropboxClient, self).__init__(*args, **kwargs)
        self.cache = DropboxCache(self)

    # Below we split the DropboxClient metadata() method into two methods
    # metadata() and children(). This allows for more fine-grained fetches
    # and caching.

    def metadata(self, path):
        """Get metadata for a given path."""
        item = self.cache.get(path)
        if not item or item.metadata is None or item.expired:
            try:
                metadata = super(
                    DropboxClient, self).metadata(
                    path, include_deleted=False, list=False)
            except rest.ErrorResponse as e:
                if e.status == 404:
                    raise ResourceNotFoundError(path)
                raise OperationFailedError(opname='metadata', path=path,
                                           msg=str(e))
            except:
                raise RemoteConnectionError(
                    "Most probable reasons: access token has expired or user"
                    " credentials are invalid.")
            if metadata.get('is_deleted', False):
                raise ResourceNotFoundError(path)
            item = self.cache[path] = CacheItem(metadata)
        # Copy the info so the caller cannot affect our cache.
        return dict(item.metadata.items())

    def children(self, path):
        """Get children of a given path."""
        update = False
        hash_ = None
        item = self.cache.get(path)
        if item:
            if item.expired:
                update = True
            if item.metadata and item.children:
                hash_ = item.metadata['hash']
            else:
                if not item.metadata.get('is_dir'):
                    raise ResourceInvalidError(path)
            if not item.children:
                update = True
        else:
            update = True
        if update:
            try:
                metadata = super(
                    DropboxClient, self).metadata(
                    path, hash=hash_, include_deleted=False, list=True)
                children = []
                contents = metadata.pop('contents')
                for child in contents:
                    if child.get('is_deleted', False):
                        continue
                    children.append(basename(child['path']))
                    self.cache[child['path']] = CacheItem(child)
                item = self.cache[path] = CacheItem(metadata, children)
            except rest.ErrorResponse as e:
                if not item or e.status != 304:
                    raise OperationFailedError(opname='metadata', path=path,
                                               msg=str(e))
                # We have an item from cache (perhaps expired), but it's
                # hash is still valid (as far as Dropbox is concerned),
                # so just renew it and keep using it.
                item.renew()
            except:
                raise RemoteConnectionError(
                    "Most probable reasons: access token has expired or user"
                    " credentials are invalid.")
        return item.children

    def file_create_folder(self, path):
        """Add newly created directory to cache."""
        try:
            metadata = super(DropboxClient, self).file_create_folder(path)
        except rest.ErrorResponse as e:
            if e.status == 403:
                raise DestinationExistsError(path)
            if e.status == 400:
                raise OperationFailedError(opname='file_create_folder',
                                           msg=str(e))
        except:
            raise RemoteConnectionError(
                "Most probable reasons: access token has expired or user"
                " credentials are invalid.")
        self.cache.set(path, metadata)
        return metadata['path']

    def file_copy(self, src, dst):
        """Copy a file to another location."""
        try:
            metadata = super(DropboxClient, self).file_copy(src, dst)
        except rest.ErrorResponse as e:
            if e.status == 404:
                raise ResourceNotFoundError(src)
            if e.status == 403:
                raise DestinationExistsError(dst)
            if e.status == 503:
                raise OperationFailedError(opname='file_copy',
                                           msg="User over storage quota")
            raise OperationFailedError(opname='file_copy', msg=str(e))
        except:
            raise RemoteConnectionError(
                "Most probable reasons: access token has expired or user"
                " credentials are invalid.")
        self.cache.set(dst, metadata)
        return metadata['path']

    def file_move(self, src, dst):
        """Move a file to another location."""
        try:
            metadata = super(DropboxClient, self).file_move(src, dst)
        except rest.ErrorResponse as e:
            if e.status == 404:
                raise ResourceNotFoundError(src)
            if e.status == 403:
                raise DestinationExistsError(dst)
            if e.status == 503:
                raise OperationFailedError(opname='file_copy',
                                           msg="User over storage quota")
            raise OperationFailedError(opname='file_copy', msg=str(e))
        except:
            raise RemoteConnectionError(
                "Most probable reasons: access token has expired or user"
                " credentials are invalid.")
        self.cache.pop(src, None)
        self.cache.set(dst, metadata)
        return metadata['path']

    def file_delete(self, path):
        """Delete a file  of a give path."""
        try:
            super(DropboxClient, self).file_delete(path)
        except rest.ErrorResponse as e:
            if e.status == 404:
                raise ResourceNotFoundError(path)
            if e.status == 400 and 'must not be empty' in str(e):
                raise DirectoryNotEmptyError(path)
            raise OperationFailedError(opname='file_copy', msg=str(e))
        except:
            raise RemoteConnectionError(
                "Most probable reasons: access token has expired or user"
                " credentials are invalid.")
        self.cache.pop(path, None)

    def put_file(self, path, f, overwrite=False):
        """Upload a file."""
        try:
            response = super(DropboxClient,
                             self).put_file(path, f, overwrite=overwrite)
        except rest.ErrorResponse as e:
            raise OperationFailedError(opname='file_copy', msg=str(e))
        except TypeError as e:
            raise ResourceInvalidError("put_file", path)
        except:
            raise RemoteConnectionError(
                "Most probable reasons: access token has expired or user"
                " credentials are invalid.")
        self.cache.pop(dirname(path), None)
        return response

    def media(self, path):
        """Media."""
        try:
            info = super(DropboxClient, self).media(path)
            return info.get('url', None)
        except rest.ErrorResponse as e:
            if e.status == 400:
                raise UnsupportedError("create a link to a folder")
            if e.status == 404:
                raise ResourceNotFoundError(path)

            raise OperationFailedError(opname='file_copy', msg=str(e))
        except:
            raise RemoteConnectionError(
                "Most probable reasons: access token has expired or user"
                " credentials are invalid.")


class DropboxFS(FS):

    """A Dropbox filesystem."""

    __name__ = "Dropbox"

    _meta = {'thread_safe': True,
             'virtual': False,
             'read_only': False,
             'unicode_paths': True,
             'case_insensitive_paths': True,
             'network': True,
             'atomic.setcontents': True,
             'atomic.makedir': True,
             'atomic.rename': True,
             'mime_type': 'virtual/dropbox',
             }

    def __init__(self, root=None, credentials=None, localtime=False,
                 thread_synchronize=True):
        """Initialize a DropboxFS instance."""
        self._root = root
        self._credentials = credentials

        if root is None:
            root = "/"

        if self._credentials is None:
            if "DROPBOX_ACCESS_TOKEN" not in os.environ:
                raise CreateFailedError(
                    "DROPBOX_ACCESS_TOKEN is not set in os.environ")
            else:
                self._credentials['access_token'] = os.environ.get(
                    'DROPBOX_ACCESS_TOKEN')

        super(DropboxFS, self).__init__(thread_synchronize=thread_synchronize)
        self.client = DropboxClient(
            oauth2_access_token=self._credentials['access_token'])
        self.localtime = localtime

    def __repr__(self):
        """Represent the dropbox filesystem and the root."""
        args = (self.__class__.__name__, self._root)
        return '<FileSystem: %s - Root Directory: %s>' % args

    __str__ = __repr__

    def __unicode__(self):
        """Represent the dropbox filesystem and the root (unicode)."""
        args = (self.__class__.__name__, self._root)
        return u'<FileSystem: %s - Root Directory: %s>' % args

    def getmeta(self, meta_name, default=NoDefaultMeta):
        """Get _meta info from DropboxFs."""
        if meta_name == 'read_only':
            return self.read_only
        return super(DropboxFS, self).getmeta(meta_name, default)

    def is_root(self, path):
        """Check if the given path is the root folder.

        :param path: Path to the folder to check
        """
        if(path == self._root):
            return True
        else:
            return False

    @synchronize
    def open(self, path, mode="rb", **kwargs):
        """Open the named file in the given mode.

        This method downloads the file contents into a local temporary
        file so that it can be worked on efficiently.  Any changes
        made to the file are only sent back to cloud storage when
        the file is flushed or closed.

        :param path: Path to the file to be opened
        :param mode: In which mode to open the file
        :raise ResourceNotFoundError: If given path doesn't exist and
            'w' is not in mode
        :return: RemoteFileBuffer object
        """
        path = abspath(normpath(path))
        spooled_file = SpooledTemporaryFile(mode=mode, bufsize=MAX_BUFFER)

        if "w" in mode:
            # Truncate the file if requested
            self.client.put_file(path, "", True)
        else:
            # Try to write to the spooled file, if path doesn't exist create it
            # if 'w' is in mode
            try:
                spooled_file.write(self.client.get_file(path).read())
                spooled_file.seek(0, 0)
            except:
                if "w" not in mode:
                    raise ResourceNotFoundError(path)
                else:
                    self.createfile(path, True)
        #  This will take care of closing the socket when it's done.
        return RemoteFileBuffer(self, path, mode, spooled_file)

    @synchronize
    def getcontents(self, path, mode="rb", **kwargs):
        """Get contents of a file."""
        path = abspath(normpath(path))
        return self.open(path, mode).read()

    def setcontents(self, path, data, *args, **kwargs):
        """Set new content to remote file.

        Method works only with existing files and sets
        new content to them.

        :param path: Path the file in which to write the new content
        :param contents: File contents as a string, or any object with
            read and seek methods
        :param kwargs: additional parameters like:
            encoding: the type of encoding to use if data is text
            errors: encoding errors
        :param chunk_size: Number of bytes to read in a chunk,
            if the implementation has to resort to a read copy loop
        :return: Path of the updated file

        """
        path = abspath(normpath(path))
        self.client.put_file(path, data, overwrite=True)
        return path

    def desc(self, path):
        """Get the title of a given path.

        :return: The title for the given path.
        """
        path = abspath(normpath(path))
        info = self.getinfo(path)
        return info["title"]

    def getsyspath(self, path, allow_none=False):
        """Return a path as the Dropbox API specifies."""
        if allow_none:
            return None
        return client.format_path(abspath(normpath(path)))

    def isdir(self, path):
        """Check if a the specified path is a folder.

        :param path: Path to the file/folder to check
        """
        info = self.getinfo(path)
        return info.get('isdir')

    def isfile(self, path):
        """Check if a the specified path is a file.

        :param path: Path to the file/folder to check
        """
        info = self.getinfo(path)
        return not info.get('isdir')

    def exists(self, path):
        """Check if a the specified path exists.

        :param path: Path to the file/folder to check
        """
        try:
            self.getinfo(path)
            return True
        except ResourceNotFoundError:
            return False

    def listdir(self, path="/", wildcard=None, full=False, absolute=False,
                dirs_only=False, files_only=False):
        """List the the files and directories under a given path.

        The directory contents are returned as a list of unicode paths

        :param path: path to the folder to list
        :type path: string
        :param wildcard: Only returns paths that match this wildcard
        :type wildcard: string containing a wildcard, or a callable
            that accepts a path and returns a boolean
        :param full: returns full paths (relative to the root)
        :type full: bool
        :param absolute: returns absolute paths
            (paths beginning with /)
        :type absolute: bool
        :param dirs_only: if True, only return directories
        :type dirs_only: bool
        :param files_only: if True, only return files
        :type files_only: bool
        :return: a list of unicode paths
        """
        path = abspath(normpath(path))
        children = self.client.children(path)
        return self._listdir_helper(path, children, wildcard, full, absolute,
                                    dirs_only, files_only)

    @synchronize
    def getinfo(self, path):
        """Get info from cloud service.

        Returned information is metadata from cloud service +
        a few more fields with standard names for some parts
        of the metadata.

        :param path: path to the file/folder for which to return
            informations
        :return: dictionary with informations about the specific file
        """
        path = abspath(normpath(path))
        metadata = self.client.metadata(path)
        return self._metadata_to_info(metadata, localtime=self.localtime)

    def copy(self, src, dst, *args, **kwargs):
        """Copy a file to another location.

        :param src: Path to the file to be copied
        :param dst: Path to the folder in which to copy the file
        :return: Path to the copied file
        """
        src = abspath(normpath(src))
        dst = abspath(normpath(dst))
        return self.client.file_copy(src, dst)

    def copydir(self, src, dst, *args, **kwargs):
        """Copy a directory to another location.

        :param src: Path to the folder to be copied
        :param dst: Path to the folder in which to copy the folder
        :return: Path to the copied folder
        """
        src = abspath(normpath(src))
        dst = abspath(normpath(dst))
        return self.client.file_copy(src, dst)

    def move(self, src, dst, chunk_size=16384, *args, **kwargs):
        """Move a file to another location.

        :param src: Path to the file to be moved
        :param dst: Path to the folder in which the file will be moved
        :param chunk_size: if using chunk upload
        :return: Path to the moved file
        """
        src = abspath(normpath(src))
        dst = abspath(normpath(dst))
        return self.client.file_move(src, dst)

    def movedir(self, src, dst, *args, **kwargs):
        """Move a directory to another location.

        :param src: Path to the folder to be moved
        :param dst: Path to the folder in which the folder will be moved
        :param chunk_size: if using chunk upload
        :return: Path to the moved folder
        """
        src = abspath(normpath(src))
        dst = abspath(normpath(dst))
        return self.client.file_move(src, dst)

    def rename(self, src, dst, *args, **kwargs):
        """Rename a file of a given path.

        :param src: Path to the file to be renamed
        :param dst: Full path with the new name
        :raise UnsupportedError: If trying to remove the root directory
        :return: Path to the renamed file
        """
        src = abspath(normpath(src))
        dst = abspath(normpath(dst))
        return self.client.file_move(src, dst)

    def makedir(self, path, recursive=False, allow_recreate=False):
        """Create a directory of a given path.

        :param path: path to the folder to be created.
            If only the new folder is specified
            it will be created in the root directory
        :param recursive: allows recursive creation of directories
        :param allow_recreate: dropbox currently doesn't support
            allow_recreate, so if a folder exists it will
        :return: Id of the created directory
        """
        if not self._checkRecursive(recursive, path):
            raise UnsupportedError("Recursively create specified folder.")

        path = abspath(normpath(path))
        return self.client.file_create_folder(path)

    def createfile(self, path, wipe=False, **kwargs):
        """Create an empty file.

        :param path: path to the new file.
        :param wipe: New file with empty content.
        :param kwargs: Additional parameters like description - a short
            description of the new file.

        :attention:

            Root directory is the current root directory of this instance of
            filesystem and not the root of your Google Drive.

        :return: Path to the created file
        """
        return self.client.put_file(path, '', overwrite=wipe)

    def remove(self, path):
        """Remove a file of a given path.

        :param path: path to the file to be deleted
        :return: None if removal was successful
        """
        path = abspath(normpath(path))
        if self.is_root(path=path):
            raise UnsupportedError("Can't remove the root directory")
        if self.isdir(path=path):
            raise ResourceInvalidError(
                "Specified path is a directory. Please use removedir.")

        self.client.file_delete(path)

    def removedir(self, path, *args, **kwargs):
        """Remove a directory of a given path.

        :param path: path to the file to be deleted
        :return: None if removal was successful
        """
        path = abspath(normpath(path))

        if self.is_root(path=path):
            raise UnsupportedError("Can't remove the root directory")
        if self.isfile(path=path):
            raise ResourceInvalidError(
                "Specified path is a directory. Please use removedir.")

        self.client.file_delete(path)

    def getpathurl(self, path):
        """Get the url of a given path.

        :param path: path to the file for which to return the url path
        :param allow_none: if true, this method can return None if
            there is no URL form of the given path
        :type allow_none: bool
        :return: url that corresponds to the given path, if one exists

        """
        path = abspath(normpath(path))
        return self.client.media(path)

    def about(self):
        """Get info about the current user.

        :return: information about the current user
            with whose credentials is the file system instantiated.
        """
        info = self.client.account_info()
        info['cloud_storage_url'] = "http://www.dropbox.com/"
        info['user_name'] = info.pop('display_name')
        info['quota'] = 100*(info['quota_info']["normal"]+info['quota_info']
                             ["shared"]) / float(info['quota_info']["quota"])
        return info
        return self.client.account_info()

    def _checkRecursive(self, recursive, path):
        #  Checks if the new folder to be created is compatible with current
        #  value of recursive
        parts = path.split("/")
        if(parts < 3):
            return True

        testPath = "/".join(parts[:-1])
        if self.exists(testPath):
            return True
        elif recursive:
            return True
        else:
            return False

    def _metadata_to_info(self, metadata, localtime=False):
        """Return modified metadata.

        Method adds a few standard names to the metadata:
            size - the size of the file/folder
            isdir - is something a file or a directory
            created_time - the time of the creation
            path - path to the object which metadata are we showing
            revision - google drive doesn't have a revision parameter
            modified - time of the last modification
        :return: The full metadata and a few more fields
            with standard names.
        """
        info = {
            'size': metadata.get('bytes', 0),
            'isdir': metadata.get('is_dir', False),
            'title': metadata['path'].split("/")[-1],
            'created_time': None
        }
        try:
            mtime = metadata.get('modified', None)
            if mtime:
                # Parse date/time from Dropbox as struct_time.
                mtime = time.strptime(mtime, TIME_FORMAT)
                if localtime:
                    # Convert time to local timezone in seconds.
                    mtime = calendar.timegm(mtime)
                else:
                    mtime = time.mktime(mtime)
                # Convert to datetime object, store in modified_time
                info['modified'] = datetime.datetime.fromtimestamp(mtime)
        except KeyError:
            pass

        info.update(metadata)
        return info
