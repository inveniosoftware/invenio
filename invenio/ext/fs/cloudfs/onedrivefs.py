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

"""
    OneDrive file system
    --------------------

    Known issues:

    * Flush and close, both call write contents and because of that
      the file on cloud is overwrite twice...
"""

from onedrive import api_v5
import six
import os
import time
from UserDict import UserDict

# python filesystem imports
from fs.base import FS
from fs.errors import (UnsupportedError,
                       CreateFailedError, ResourceInvalidError,
                       ResourceNotFoundError, NoPathURLError,
                       OperationFailedError, RemoteConnectionError)
from fs.remote import RemoteFileBuffer
from fs.filelike import SpooledTemporaryFile

# Items in cache are considered expired after 5 minutes.
CACHE_TTL = 300
# Max size for spooling to memory before using disk (5M).
MAX_BUFFER = 1024**2*5


class CacheItem(object):
    """Represents a path in the cache. There are two components to a path.
       It's individual metadata, and the children contained within it."""

    def __init__(self, metadata=None, children=None, timestamp=None,
                 parent=None):
        self.metadata = metadata
        self.children = children
        self.parent = parent
        if timestamp is None:
            timestamp = time.time()
        self.timestamp = timestamp

    def add_child(self, name, client=None):
        if self.children is None:
            if client is not None:
                # This is a fix. When you add a child to a folder that
                # was still not listed, that folder gets only one
                # child when you list it afterwards. So this fix
                # first tries to check are the files/folders inside
                # this directory on cloud.
                client.children(self.metadata['id'])
            else:
                self.children = [name]
        else:
            if name not in self.children:
                self.children.append(name)

    def del_child(self, name):
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
        self.timestamp = time.time()


class OneDriveCache(UserDict):
    def __init__(self, client):
        self._client = client
        UserDict.__init__(self)

    def set(self, path, metadata, children=None, parent=None):
        self[path] = CacheItem(metadata, children=children, parent=parent)
        if parent is not None:
            if parent in self:
                self.get(parent).add_child(path, self._client)

    def pop(self, path, default=None):
        value = UserDict.pop(self, path, default)
        if value.parent is not None:
            if value.parent in self:
                self.get(value.parent).del_child(value.metadata['id'])
        return value


class OneDriveClient(api_v5.OneDriveAPI):
    def __init__(self, credentials):
        self.cache = OneDriveCache(self)
        self.auth_access_token = credentials.get("access_token", None)
        self.auth_refresh_token = credentials.get("refresh_token", None)
        self.auth_redirect_uri = credentials.get("redirect_uri", None)
        self.auth_scope = credentials.get("scope", None)
        self.client_id = credentials.get("client_id", None)
        self.client_secret = credentials.get("client_secret", None)

    def metadata(self, path):
        "Gets metadata for a given path."
        item = self.cache.get(path)
        if not item or item.metadata is None or item.expired:
            try:
                metadata = super(OneDriveClient, self).info(path)
            except api_v5.ProtocolError as e:
                if e.code == 404:
                    raise ResourceNotFoundError(path)
                raise OperationFailedError(opname='metadata', path=path,
                                           msg=str(e))
            except:
                raise RemoteConnectionError(
                    "Most probable reasons: access token has expired "
                    "or user credentials are invalid.")
            item = self.cache[path] = CacheItem(metadata)
        # Copy the info so the caller cannot affect our cache.
        return dict(item.metadata.items())

    def children(self, path):
        "Gets children of a given path."
        update = False
        item = self.cache.get(path)
        if item:
            if item.expired:
                update = True
            else:
                if item.metadata["type"] != "folder" and \
                        not ("folder" in path):
                    raise ResourceInvalidError(path)
            if not item.children:
                update = True
        else:
            update = True
        if update:
            try:
                metadata = super(OneDriveClient, self).info(path)
                if metadata["type"] != "folder" and not ("folder" in path):
                    raise ResourceInvalidError(path)
                children = []
                contents = super(OneDriveClient, self).listdir(path)
                for child in contents:
                    children.append(child['id'])
                    self.cache[child['id']] = CacheItem(child, parent=path)
                item = self.cache[path] = CacheItem(metadata, children)
            except api_v5.ProtocolError as e:
                if e.code == 404:
                    raise ResourceNotFoundError(path)
                if not item or e.resp.status != 304:
                    raise OperationFailedError(opname='metadata', path=path,
                                               msg=str(e))
                # We have an item from cache (perhaps expired), but it's
                # hash is still valid (as far as OneDrive is concerned),
                # so just renew it and keep using it.
                item.renew()
            except:
                raise RemoteConnectionError(
                    "Most probable reasons: access token has expired "
                    "or user credentials are invalid.")
        return item.children

    def file_create_folder(self, parent_id, title):
        "Add newly created directory to cache."
        try:
            metadata = super(OneDriveClient, self).mkdir(title, parent_id)
        except api_v5.ProtocolError as e:
            if e.code == 405:
                    raise ResourceInvalidError(parent_id)
            if e.code == 404:
                    raise ResourceNotFoundError(parent_id)
            raise OperationFailedError(opname='file_create_folder', msg=str(e))
        except:
            raise RemoteConnectionError(
                "Most probable reasons: access token has expired "
                "or user credentials are invalid.")

        self.cache.set(metadata["id"], metadata, parent=parent_id)
        return metadata['id']

    def file_copy(self, src, dst):
        try:
            metadata = super(OneDriveClient, self).copy(src, dst, False)
        except api_v5.ProtocolError as e:
            if e.code == 404:
                raise ResourceNotFoundError(
                    "Parent or source file don't exist")
            raise OperationFailedError(opname='file_copy', msg=str(e))
        except:
            raise RemoteConnectionError(
                "Most probable reasons: access token has expired "
                "or user credentials are invalid.")
        self.cache.set(metadata['id'], metadata, parent=dst)
        return metadata['id']

    def file_move(self, src, dst):
        try:
            metadata = super(OneDriveClient, self).copy(src, dst, True)
        except api_v5.ProtocolError as e:
            if e.code == 404:
                raise ResourceNotFoundError(
                    "Parent or source file don't exist")
            raise OperationFailedError(opname='file_move', msg=str(e))
        except:
            raise RemoteConnectionError(
                "Most probable reasons: access token has expired "
                "or user credentials are invalid.")

        self.cache.pop(src, None)
        self.cache.set(metadata['id'], metadata, metadata['parent_id'])
        return metadata['id']

    def file_delete(self, path):
        try:
            super(OneDriveClient, self).delete(path)
        except api_v5.ProtocolError as e:
            if e.code == 404:
                raise ResourceNotFoundError(path)
            raise OperationFailedError(opname='file_delete', msg=str(e))
        except:
            raise RemoteConnectionError(
                "Most probable reasons: access token has expired "
                "or user credentials are invalid.")
        self.cache.pop(path, None)

    def put_file(self, parent_id, title, content, overwrite=False):
        try:
            metadata = super(OneDriveClient, self).put(
                (title, content), parent_id, overwrite=overwrite)
        except api_v5.ProtocolError as e:
            if e.code == 404:
                raise ResourceNotFoundError(parent_id)
            raise OperationFailedError(opname='put_copy', msg=str(e))
        except TypeError as e:
            raise ResourceInvalidError("put_file")
        except:
            raise RemoteConnectionError(
                "Most probable reasons: access token has expired "
                "or user credentials are invalid.")
        return metadata['id']

    def get_file(self, path):
        metadata = None

        if not self.cache.get(path, None):
            try:
                metadata = super(OneDriveClient, self).info(path)
            except api_v5.ProtocolError as e:
                if e.code == 404:
                    raise ResourceNotFoundError("Source file doesn't exist")

                raise OperationFailedError(opname='get_file', msg=str(e))
            except:
                raise RemoteConnectionError(
                    "Most probable reasons: access token has expired "
                    "or user credentials are invalid.")
            self.cache.set(metadata['id'], metadata,
                           parent=metadata['parent_id'])
        else:
            item = self.cache[path]
            metadata = item.metadata

        return super(OneDriveClient, self).get(path)

    def update_file(self, file_id, new_file_info):
        try:
            metadata = super(OneDriveClient, self).info_update(
                file_id, new_file_info)
        except api_v5.ProtocolError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError(path=file_id)

            raise OperationFailedError(opname='update_file', msg=e.resp.reason)
        except:
            raise RemoteConnectionError(
                "Most probable reasons: access token has expired "
                "or user credentials are invalid.")
        self.cache.pop(file_id, None)
        self.cache.set(metadata['id'], metadata, parent=metadata['parent_id'])
        return metadata['id']


class OneDriveFS(FS):
    """
        Sky drive file system
    """
    __name__ = "OneDrive"

    _meta = {'thread_safe': True,
             'virtual': False,
             'read_only': False,
             'unicode_paths': True,
             'case_insensitive_paths': False,
             'network': True,
             'atomic.move': True,
             'atomic.copy': True,
             'atomic.makedir': True,
             'atomic.rename': False,
             'atomic.setconetns': True
             }

    def __init__(self, root=None, credentials=None, thread_synchronize=True):
        self._root = root
        self._credentials = credentials
        self.cached_files = {}

        if self._root is None or self._root == "/" or self._root == "":
            self._root = "me/skydrive"

        if self._credentials is None:
            if "ONEDRIVE_ACCESS_TOKEN" not in os.environ:
                raise CreateFailedError(
                    "ONEDRIVE_ACCESS_TOKEN is not set in os.environ")
            else:
                self._credentials['access_token'] = os.environ.get(
                    'ONEDRIVE_ACCESS_TOKEN')
                self._credentials['refresh_token'] = os.environ.get(
                    'ONEDRIVE_REFRESH_TOKEN', None)
                self._credentials['redirect_uri'] = os.environ.get(
                    'ONEDRIVE_REDIRECT_URI', None)
                self._credentials['client_id'] = os.environ.get(
                    'ONEDRIVE_CLIENT_ID', None)
                self._credentials['client_secret'] = os.environ.get(
                    'ONEDRIVE_CLIENT_SECRET', None)

        self.client = OneDriveClient(self._credentials)
        super(OneDriveFS, self).__init__(thread_synchronize=thread_synchronize)

    def __repr__(self):
        args = (self.__class__.__name__, self._root)
        return '<FileSystem: %s - Root Directory: %s>' % args

    __str__ = __repr__

    def __unicode__(self):
        args = (self.__class__.__name__, self._root)
        return u'<FileSystem: %s - Root Directory: %s>' % args

    def _update(self, path, data):
        """
        Updates contents of an existing file

        @param path: Id of the file for which to update content
        @param data: Contents to write to the file
        @return: Id of the updated file
        """
        path = self._normpath(path)

        if isinstance(data, six.string_types):
            string_data = data
        else:
            try:
                data.seek(0)
                string_data = data.read()
            except:
                raise ResourceInvalidError("Unsupported type")

        f = self.getinfo(path)
        return self.client.put(
            (f["title"], string_data), f["parent_id"], True)['id']

    def setcontents(self, path, data="", chunk_size=64*1024, **kwargs):
        """
        Sets new content to remote file

        Method works only with existing files and sets new content to them.
        @param path: Id of the file in which to write the new content
        @param contents: File contents as a string, or any object with read
            and seek methods
        @param kwargs: additional parameters like:
            encoding: the type of encoding to use if data is text
            errors: encoding errors
        @param chunk_size: Number of bytes to read in a chunk, if the
            implementation has to resort to a read / copy loop.
        @return: Id of the updated file
        """
        path = self._normpath(path)

        encoding = kwargs.get("encoding", None)
        errors = kwargs.get("errors", None)

        if isinstance(data, six.text_type):
            data = data.encode(encoding=encoding, errors=errors)

        return self._update(path, data)

    def createfile(self, path, wipe=True, **kwargs):
        """
        Creates always an empty file, even if another file with the same name
        exists.

        @param path: path to the new file. It has to be in one of following forms:
            - parent_id/file_title.ext
            - file_title.ext or /file_title.ext - In this cases root directory is the parent
        @param wipe: New file with empty content. If a file with the same name exists it will be
            overwritten.
        @raise ResourceNotFoundError: If parent doesn't exist.
        @attention: Root directory is the current root directory of this instance of
            filesystem and not the root of your Google Drive.
        @return: Id of the created file
        """
        parts = path.split("/")
        if parts[0] == "":
            parent_id = self._root
            title = parts[1]
        elif len(parts) == 2:
            parent_id = parts[0]
            title = parts[1]
            if not self.exists(parent_id):
                raise ResourceNotFoundError("parent doesn't exist")
        else:
            parent_id = self._root
            title = parts[0]

        return self.client.put_file(parent_id, title, "", wipe)

    def open(self, path, mode='r',  buffering=-1, encoding=None,
             errors=None, newline=None, line_buffering=False, **kwargs):
        """
        Open the named file in the given mode.

        This method downloads the file contents into a local temporary file
        so that it can be worked on efficiently.  Any changes made to the
        file are only sent back to cloud storage when the file is flushed or closed.
        @param path: Id of the file to be opened
        @param mode: In which mode to open the file

        @raise ResourceNotFoundError: If given path doesn't exist and 'w' is not in mode
        @return: RemoteFileBuffer object
        """
        path = self._normpath(path)

        spooled_file = SpooledTemporaryFile(mode=mode, bufsize=MAX_BUFFER)

        #  Truncate the file if requested
        if "w" in mode:
            try:
                self._update(path, "")
            except:
                path = self.createfile(path, True)
        else:
            try:
                spooled_file.write(self.client.get_file(path))
                spooled_file.seek(0, 0)
            except Exception as e:
                if "w" not in mode and "a" not in mode:
                    raise ResourceNotFoundError("%r" % e)
                else:
                    path = self.createfile(path, True)

        return RemoteFileBuffer(self, path, mode, spooled_file)

    def is_root(self, path):
        path = self._normpath(path)
        if path == self._root:
            return True
        else:
            return False

    def copy(self, src, dst, overwrite=False, chunk_size=1024 * 64):
        """
        @param src: Id of the file to be copied
        @param dst: Id of the folder in which to copy the file
        @param overwrite: This is never true for OneDrive
        @return: Id of the copied file
        """
        return self.client.file_copy(src, dst)

    def copydir(self, src, dst, overwrite=False, ignore_errors=False,
                chunk_size=16384):
        """
        NOTE: OneDrive doesn't support copy of folders. And to implement it
              over copy method will be very inefficient
        """
        raise NotImplemented("If implemented method will be very inefficient")

    def rename(self, src, dst):
        """
        @param src: Id of the file to be renamed
        @param dst: New title of the file
        @raise UnsupportedError: If trying to rename the root directory
        @return: Id of the renamed file
        """
        if self.is_root(path=src):
            raise UnsupportedError("Can't rename the root directory")

        return self.client.update_file(src, {"name": dst})

    def remove(self, path):
        """
        @param path: id of the folder to be deleted
        @return: None if removal was successful
        """
        path = self._normpath(path)
        if self.is_root(path=path):
            raise UnsupportedError("Can't remove the root directory")
        if self.isdir(path=path):
            raise ResourceInvalidError("Specified path is a directory")

        return self.client.file_delete(path)

    def removedir(self, path):
        """
        @param path: id of the folder to be deleted
        @return: None if removal was successful
        """
        path = self._normpath(path)

        if not self.isdir(path):
            raise ResourceInvalidError("Specified path is a directory")
        if self.is_root(path=path):
            raise UnsupportedError("remove the root directory")

        return self.client.file_delete(path)

    def makedir(self, path, recursive=False, allow_recreate=False):
        """
        @param path: path to the folder you want to create.
            it has to be in one of the following forms:
                - parent_id/new_folder_name  (when recursive is False)
                - parent_id/new_folder1/new_folder2...  (when recursive is True)
                - /new_folder_name to create a new folder in root directory
                - /new_folder1/new_folder2... to recursively create a new folder in root
        @param recursive: allows recursive creation of directories
        @param allow_recreate: for OneDrive this param is always False, it will
            never recreate a directory
        """
        parts = path.split("/")

        if parts[0] == "":
            parent_id = self._root
        elif len(parts) >= 2:
            parent_id = parts[0]
            if not self.exists(parent_id):
                raise ResourceNotFoundError(
                    "parent with the id '%s' doesn't exist" % parent_id)

        if len(parts) > 2:
            if recursive:
                for i in range(len(parts) - 1):
                    title = parts[i+1]
                    resp = self.client.file_create_folder(parent_id, title)
                    parent_id = resp
            else:
                raise UnsupportedError("recursively create a folder")
            return resp
        else:
            if len(parts) == 1:
                title = parts[0]
                parent_id = self._root
            else:
                title = parts[1]
            return self.client.file_create_folder(parent_id, title)

    def move(self, src, dst, overwrite=False, chunk_size=16384):
        """
        @param src: id of the file to be moved
        @param dst: id of the folder in which the file will be moved
        @param overwrite: for Sky drive it is always false
        @param chunk_size: if using chunk upload
        @return: Id of the moved file
        """
        if self.isdir(src):
            raise UnsupportedError("move a directory")
        return self.client.file_move(src, dst)

    def movedir(self, src, dst, overwrite=False, ignore_errors=False,
                chunk_size=16384):
        """
        @attention: onedrive API doesn't allow to move folders
        """
        raise UnsupportedError("move a directory")

    def isdir(self, path):
        """
        Checks if the given path is a folder

        @param path: id of the object to check
        @attention: this method doesn't check if the given path exists
            it will return true or false even if the file/folder doesn't exist
        """
        path = self._normpath(path)
        info = self.client.info(path)
        return "folder" in path or info['type'] == "folder"

    def isfile(self, path):
        """
        Checks if the given path is a file

        @param path: id of the object to check
        @attention: this method doesn't check if the given path exists
            it will return true or false even if the file/folder doesn't exist
        """
        path = self._normpath(path)
        info = self.client.info(path)
        return "file" in path or info['type'] == "file"

    def exists(self, path):
        """
        Checks if a the specified path exists

        @param path: Id of the file/folder to check
        """
        try:
            return self.client.metadata(path)
        except RemoteConnectionError as e:
            raise RemoteConnectionError(e)
        except:
            return False

    def listdir(self, path=None, wildcard=None, full=False, absolute=False,
                dirs_only=False, files_only=False, overrideCache=False):
        """
        Lists the the files and directories under a given path.

        The directory contents are returned as a list of unicode paths.

        @param path: id of the folder to list
        @type path: string
        @param wildcard: Only returns paths that match this wildcard
        @type wildcard: string containing a wildcard, or a callable that accepts a path and returns a boolean
        @param full: returns full paths (relative to the root)
        @type full: bool
        @param absolute: returns absolute paths (paths beginning with /)
        @type absolute: bool
        @param dirs_only: if True, only return directories
        @type dirs_only: bool
        @param files_only: if True, only return files
        @type files_only: bool
        @return: a list of unicode paths
        """
        path = self._normpath(path)
        flist = self.client.children(path)
        dirContent = self._listdir_helper('', flist, wildcard, full, absolute,
                                          dirs_only, files_only)

        return dirContent

    def listdirinfo(self, path=None, wildcard=None, full=False, absolute=False,
                    dirs_only=False, files_only=False):
        """
        Retrieves a list of paths and path info under a given path.

        This method behaves like listdir() but instead of just returning
        the name of each item in the directory, it returns a tuple of the
        name and the info dict as returned by getinfo.

        @param path: id of the folder
        @param wildcard: filter paths that match this wildcard
        @param dirs_only: only retrieve directories
        @type dirs_only: bool
        @param files_only: only retrieve files
        @type files_only: bool
        @return: tuple of the name and the info dict as returned by getinfo.
        """
        #Optimised listdir from pyfs
        return [(p, self.getinfo(p)) for p in self.listdir(
            path, wildcard=wildcard, full=full, absolute=absolute,
            dirs_only=dirs_only, files_only=files_only)]

    def getinfo(self, path):
        """
        Returned information is metadata from cloud service +
            a few more fields with standard names for some parts
            of the metadata.
        @param path: file id for which to return informations
        @return: dictionary with informations about the specific file
        """
        path = self._normpath(path)

        # Fix for onedrive, because if you don't write the path in the way they
        # want. It will raise an exception with the error code 400.
        # That error means nothing because it's raised in many situations.
        if not self.exists(path):
            raise ResourceNotFoundError(path=path)
        return self._metadata_to_info(self.client.metadata(path))

    def getpathurl(self, path, allow_none=False):
        """Returns a url that corresponds to the given path, if one exists.

        If the path does not have an equivalent URL form (and allow_none is False)
        then a :class:`~fs.errors.NoPathURLError` exception is thrown. Otherwise the URL will be
        returns as an unicode string.

        @param path: object id for which to return url path
        @param allow_none: if true, this method can return None if there is no
            URL form of the given path
        @type allow_none: bool
        @raises `fs.errors.NoPathURLError`: If no URL form exists, and allow_none is False (the default)
        @rtype: unicode

        """
        url = None
        try:
            url = self.getinfo(path)['source']
        except RemoteConnectionError as e:
            raise RemoteConnectionError(e)
        except:
            if not allow_none:
                raise NoPathURLError(path=path)

        return url

    def desc(self, path):
        """
        @return: The title for the given path.
        """
        info = self.getinfo(path)
        return info["title"]

    def about(self):
        """This methods returns information about the current user with whose
        credentials is the file system instantiated."""
        user = self.client.info("me")
        info = {}
        quota = self.client.get_quota()
        info['cloud_storage_url'] = "https://onedrive.live.com/"
        info['user_name'] = user['first_name'].capitalize() + \
            " " + user['last_name'].capitalize()
        info['quota'] = 100 * (float(quota[1] - quota[0]) / float(quota[1]))
        return info

    def _normpath(self, path):
        """
        Method normalizes the path for sky drive.
        @return: normalized path as a string
        """

        if path in ("/skydrive/camera_roll", "/skydrive/my_documents",
                    "/skydrive/my_photos", "/skydrive/public_documents",
                    "me/skydrive"):
            return path
        elif path == self._root:
            return path
        elif path is None or path == "":
            return self._root
        elif len(path.split("/")) > 2:
            return path.split("/")[-1]
        elif path[0] == "/" and len(path) == 1:
            return self._root
        elif path[0] == "/":
            return path[1:]
        elif len(path) == 0:
            return self._root

        return path

    def _metadata_to_info(self, metadata, localtime=False):
        """
        Method adds a few standard names to the metadata:
            size - the size of the file/folder
            isdir - is something a file or a directory
            created_time - the time of the creation
            path - path to the object which metadata are we showing
            revision - sky drive doesn't have a revision parameter
            modified - time of the last modification
        @return: The full metadata and a few more fields
            with standard names.
        """
        path = metadata.get('id', '0')
        isdir = "folder" in path or metadata.get('type') == "folder"
        info = {
            'isdir': isdir,
            'created_time': metadata.get('createdDate', 0),
            'title': metadata.get('name', 0),
            'path': path,
            'revision': None,
            'created_time': metadata.get('createdDate', 0),
            'modified': metadata.get("updated_time", 0)
        }
        info.update(metadata)

        return info
