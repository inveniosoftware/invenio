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

"""Google Drive file system.

Installation:: pip install invenio[google_drive]

Known issues:

* Flush and close, both call write contents and because of that
  the file on cloud is overwrite twice...
"""

import six
import os
import datetime
import time
from UserDict import UserDict

# Python filesystem imports
from fs.base import FS
from fs.errors import (UnsupportedError, CreateFailedError,
                       ResourceInvalidError, ResourceNotFoundError,
                       NoPathURLError, OperationFailedError,
                       RemoteConnectionError)
from fs.remote import RemoteFileBuffer
from fs.filelike import SpooledTemporaryFile

# Imports specific to Google Drive service
import httplib2
from apiclient.discovery import build
from apiclient.http import MediaInMemoryUpload
from oauth2client.client import OAuth2Credentials
from apiclient import errors

# Items in cache are considered expired after 5 minutes.
CACHE_TTL = 300
# Max size for spooling to memory before using disk (5M).
MAX_BUFFER = 1024**2*5
# Indicates the mimeType for a google drive folder
GD_FOLDER = "application/vnd.google-apps.folder"


class CacheItem(object):

    """Represents a path in the cache.

    There are two components to a path. It's individual metadata,
    and the children contained within it.
    """

    def __init__(self, metadata=None, children=None, timestamp=None,
                 parents=None):
        """Initialize a CacheItem instance."""
        self.metadata = metadata
        self.children = children
        self.parents = parents
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
                client.children(self.metadata['id'])
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


class GoogleDriveCache(UserDict):

    """Represent the google drive cache."""

    def __init__(self, client):
        """Initialize a GoogleDriveCache instance."""
        self._client = client
        UserDict.__init__(self)

    def set(self, path, metadata, children=None, parents=None):
        """Set metadata."""
        self[path] = CacheItem(metadata, children=children, parents=parents)
        if parents is not None:
            for parent in parents:
                if parent in self:
                    self.get(parent).add_child(path, self._client)

    def pop(self, path, default=None):
        """Pop data of a given path."""
        value = UserDict.pop(self, path, default)
        if value.parents is not None:
            for parent in value.parents:
                if parent in self:
                    self.get(parent).del_child(value.metadata['id'])
        return value


class GoogleDriveClient(object):

    """Represent the google drive client."""

    def __init__(self, credentials):
        """Initialize a GoogleDriveClient instance."""
        self.credentials = credentials
        self.service = self._build_service()
        self.cache = GoogleDriveCache(self)
        self._retry = 0

    def _build_service(self):
        http = httplib2.Http()
        http = self.credentials.authorize(http)
        service = build('drive', 'v2', http=http)
        return service

    def _retry_operation(self, method, *args):
        """Method retries an operation.

        Sometimes access_token expires and we need to rebuild it using
        the refresh token. This method does that and retries the
        operation that failed.
        """
        if self._retry < 5:
            self._retry += 1
            self.service = self._build_service()
            return method(*args)
        else:
            raise RemoteConnectionError(
                "Most probable reasons: access token has expired "
                "or user credentials are invalid.")

    def get_file(self, path):
        """Get file of a given path."""
        item = self.cache.get(path)
        if not item or item.metadata is None or item.expired:
            try:
                metadata = self.service.files().get(fileId=path).execute()
            except errors.HttpError as e:
                if e.resp.status == 404:
                    raise ResourceNotFoundError("Source file doesn't exist")
                raise OperationFailedError(opname='get_file',
                                           msg=e.resp.reason)
            except:
                return self._retry_operation(self.get_file, path)
            self._add_to_cache_from_dict(metadata, metadata['parents'])
        else:
            item = self.cache[path]
            metadata = item.metadata

        download_url = metadata.get('downloadUrl')
        resp, content = self.service._http.request(download_url)
        if resp.status == 200:
            return content
        else:
            raise OperationFailedError(opname="get_file", msg=str(resp))

    def metadata(self, path):
        """Get metadata of a given path."""
        item = self.cache.get(path)
        if not item or item.metadata is None or item.expired:
            try:
                metadata = self.service.files().get(fileId=path).execute()
            except errors.HttpError as e:
                if e.resp.status == 404:
                    raise ResourceNotFoundError(path)
                raise OperationFailedError(opname='metadata', path=path,
                                           msg=e.resp.reason)
            except:
                return self._retry_operation(self.metadata, path)
            if metadata.get('trashed', False):
                raise ResourceNotFoundError(path)
            item = self.cache[path] = CacheItem(metadata)

        # Copy the info so the caller cannot affect our cache.
        return dict(item.metadata.items())

    def children(self, path):
        """Get children of a given path."""
        update = False
        item = self.cache.get(path)
        if item:
            if item.expired:
                update = True
            else:
                if item.metadata["mimeType"] != GD_FOLDER:
                    raise ResourceInvalidError(path)
            if not item.children:
                update = True
        else:
            update = True
        if update:
            try:
                metadata = self.service.files().get(fileId=path).execute()
                if metadata["mimeType"] != GD_FOLDER:
                    raise ResourceInvalidError(path)
                param = {"q": "trashed=false and '%s' in parents" % path}
                children = []
                filesResource = self.service.files().list(**param).execute()
                for child in filesResource['items']:
                    children.append(child['id'])
                    self.cache[child['id']] = CacheItem(child, parents=[path])
                item = self.cache[path] = CacheItem(metadata, children)
            except errors.HttpError as e:
                if e.resp.status == 404:
                    raise ResourceNotFoundError(path)
                if not item or e.resp.status != 304:
                    raise OperationFailedError(opname='metadata', path=path,
                                               msg=e.resp.reason)
                # We have an item from cache (perhaps expired),
                # but it's still valid (as far as GoogleDrive is
                # concerned), so just renew it and keep using it.
                item.renew()
            except:
                return self._retry_operation(self.children, path)
        return item.children

    def file_create_folder(self, parent_id, title):
        """Add newly created directory to cache."""
        body = {
            "title": title,
            "parents": [{"id": parent_id}],
            "mimeType": "application/vnd.google-apps.folder"
            }
        try:
            metadata = self.service.files().insert(body=body).execute()
        except errors.HttpError as e:
            if e.resp.status == 405:
                raise ResourceInvalidError(parent_id)
            if e.resp.status == 404:
                raise ResourceNotFoundError(parent_id)
            raise OperationFailedError(
                opname='file_create_folder',
                msg="%s, the reasons could be: parent "
                    "doesn't exist or is a file" % (e.resp.reason, ))
        except:
            return self._retry_operation(self.file_create_folder,
                                         parent_id, title)

        self.cache.set(metadata["id"], metadata, parents=[parent_id])
        return metadata

    def file_copy(self, file_id, parent_id):
        """Copy a file to a folder of a given id."""
        body = {"parents": [{"id": parent_id}]}

        try:
            metadata = self.service.files().copy(fileId=file_id,
                                                 body=body,
                                                 ).execute()
        except errors.HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError(
                    "Parent or source file don't exist.")
            raise OperationFailedError(opname='file_copy', msg=e.resp.reason)
        except:
            return self._retry_operation(self.file_copy, file_id, parent_id)

        self.cache.set(metadata['id'], metadata, parents=[parent_id])
        return metadata

    def update_file(self, file_id, new_file):
        """Update the file's contents of the given id."""
        try:
            metadata = self.service.files().update(fileId=file_id,
                                                   body=new_file
                                                   ).execute()
        except errors.HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError(
                    "Parent or source file don't exist.")
            raise OperationFailedError(opname='update_file',
                                       msg=e.resp.reason)
        except:
            return self._retry_operation(self.update_file, file_id, new_file)
        self.cache.pop(file_id, None)
        self._add_to_cache_from_dict(metadata, metadata['parents'])
        return metadata

    def _add_to_cache_from_dict(self, metadata, parents):
        new_parents = []
        for one in parents:
            new_parents.append(one['id'])
        self.cache.set(metadata['id'], metadata, parents=new_parents)

    def update_file_content(self, file_id, content):
        """Update the file's contents of the given id on google drive."""
        item = self.cache.get(file_id, None)
        if not item or item.metadata is None or item.expired:
            try:
                metadata = self.service.files().get(fileId=file_id).execute()
            except errors.HttpError as e:
                raise OperationFailedError(opname='update_file_content',
                                           msg=e.resp.reason)
            except:
                return self._retry_operation(self.update_file_content,
                                             file_id, content)
            self.cache.set(metadata['id'], metadata)
        else:
            metadata = item.metadata

        media_body = MediaInMemoryUpload(content)
        try:
            updated_file = self.service.files().update(fileId=file_id,
                                                       body=metadata,
                                                       media_body=media_body
                                                       ).execute()
        except errors.HttpError as e:
            raise OperationFailedError(opname='update_file_content',
                                       msg=e.resp.reason)
        except TypeError as e:
            raise ResourceInvalidError("update_file_content %r" % e)
        except:
            return self._retry_operation(self.update_file_content, file_id,
                                         content)
        self.cache.pop(file_id, None)
        self._add_to_cache_from_dict(updated_file, updated_file['parents'])
        return updated_file

    def file_delete(self, path):
        """Delete a file."""
        try:
            self.service.files().delete(fileId=path).execute()
        except errors.HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError(path)
            raise OperationFailedError(opname='file_delete',
                                       msg=e.resp.reason)
        except:
            return self._retry_operation(self.file_delete, path)
        self.cache.pop(path, None)

    def put_file(self, parent_id, title, content, description=None):
        """Add a file to folder of the given id."""
        media_body = MediaInMemoryUpload(content)
        body = {
            'title': title,
            'description': description,
            'parents': [{'id': parent_id}]
            }
        try:
            metadata = self.service.files().insert(body=body,
                                                   media_body=media_body
                                                   ).execute()
        except errors.HttpError as e:
            raise OperationFailedError(opname='put_file', msg=e.resp.reason)
        except TypeError as e:
            raise ResourceInvalidError("put_file")
        except:
            return self._retry_operation(self.put_file, parent_id, title,
                                         content, description)
        self.cache.set(metadata['id'], metadata, parents=[parent_id])
        return metadata

    def about(self):
        """Get info about the service."""
        try:
            # FIXME check if the access_token has expired
            info = self.service.about().get().execute()
            return info
        except:
            return self._retry_operation(self.about)


class GoogleDriveFS(FS):

    """Google drive file system.

    @attention: when setting variables in os.environ please note that
    GD_TOKEN_EXPIRY has to be in format: "%Y, %m, %d, %H, %M, %S, %f"
    """

    __name__ = "Google Drive"
    _meta = {'thread_safe': True,
             'virtual': False,
             'read_only': False,
             'unicode_paths': True,
             'case_insensitive_paths': False,
             'network': True,
             'atomic.move': True,
             'atomic.copy': True,
             'atomic.makedir': True,
             'atomic.rename': True,
             'atomic.setcontents': True,
             }

    def __init__(self, root=None, credentials=None, thread_synchronize=True):
        """Initialize a GoogleDriveFS instance."""
        self._root = root

        def _getDateTimeFromString(time):
            # Parses string into datetime object
            if time:
                return datetime.datetime.strptime(
                    time, "%Y, %m, %d, %H, %M, %S, %f")
            else:
                return None

        if credentials is None:
            # Get credentials need to build the google drive service
            if ("GD_ACCESS_TOKEN" not in os.environ or
                "GD_CLIENT_ID" not in os.environ or
                "GD_CLIENT_SECRET" not in os.environ or
                "GD_TOKEN_EXPIRY" not in os.environ or
                "GD_TOKEN_URI" not in os.environ,
               "GD_REFRESH_TOKEN" not in os.environ):
                raise CreateFailedError("You need to set:\n"
                                        "GD_ACCESS_TOKEN, "
                                        "GD_CLIENT_ID, "
                                        "GD_CLIENT_SECRET "
                                        "GD_TOKEN_EXPIRY, "
                                        "GD_REFRESH_TOKEN, "
                                        "GD_TOKEN_URI in os.environ"
                                        )
            else:
                self._credentials = OAuth2Credentials(
                    os.environ.get('GD_ACCESS_TOKEN'),
                    os.environ.get('GD_CLIENT_ID'),
                    os.environ.get('GD_CLIENT_SECRET'),
                    os.environ.get('GD_REFRESH_TOKEN'),
                    _getDateTimeFromString(
                        os.environ.get('GD_TOKEN_EXPIRY')
                    ),
                    os.environ.get('GD_TOKEN_URI'),
                    None
                    )
        else:
            self._credentials = OAuth2Credentials(
                credentials.get('access_token'),
                credentials.get('client_id'),
                credentials.get('client_secret'),
                credentials.get('refresh_token'),
                _getDateTimeFromString(
                    credentials.get('token_expiry')
                ),
                credentials.get('token_uri'),
                None
                )
        self.client = GoogleDriveClient(self._credentials)

        if self._root is None or root == '' or self._root == "/":
            # Root fix, if root is not set get the root folder id
            # from the user information returned by 'about'
            about = self.client.about()
            self._root = about.get("rootFolderId")

        # Initialize super class FS
        super(self.__class__, self).__init__(
            thread_synchronize=thread_synchronize
            )

    def __repr__(self):
        """Represent the google_drive filesystem and the root."""
        args = (self.__class__.__name__, self._root)
        return '<FileSystem: %s - Root Directory: %s>' % args

    __str__ = __repr__

    def __unicode__(self):
        """Represent the google_drive filesystem and the root (unicode)."""
        args = (self.__class__.__name__, self._root)
        return u'<FileSystem: %s - Root Directory: %s>' % args

    def _update(self, path, contents):
        """Update contents of an existing file.

        :param path: Id of the file for which to update content
        :param contents: Contents to write to the file
        :return: Id of the updated file
        """
        path = self._normpath(path)

        if isinstance(contents, six.string_types):
            string_data = contents
        else:
            try:
                contents.seek(0)
                string_data = contents.read()
            except:
                raise ResourceInvalidError("Unsupported type")

        return self.client.update_file_content(path, string_data)['id']

    def setcontents(self, path, contents="", chunk_size=64*1024, **kwargs):
        """Set new content to remote file.

        Method works only with existing files and sets
        new content to them.

        :param path: Id of the file in which to write the new content
        :param contents: File contents as a string, or any object with
            read and seek methods
        :param kwargs: additional parameters like:
            encoding: the type of encoding to use if data is text
            errors: encoding errors
        :param chunk_size: Number of bytes to read in a chunk,
            if the implementation has to resort to a read copy loop
        :return: Id of the updated file
        """
        encoding = kwargs.get("encoding", None)
        errors = kwargs.get("errors", None)

        if isinstance(contents, six.text_type):
            contents = contents.encode(encoding=encoding, errors=errors)

        return self._update(path, contents)

    def createfile(self, path, wipe=True, **kwargs):
        """Create always an empty file.

        Even if another file with the same name exists it will create
        a file with the same name.

        :param path: path to the new file. It has to be in one of
            following forms: parent_id/file_title.ext, file_title.ext or
            /file_title.ext - in this cases root directory is the parent.
        :param wipe: New file with empty content.
            In the case of google drive it will always be True
        :param kwargs: Additional parameters like:
            description - a short description of the new file
        :raises ResourceNotFoundError: If parent doesn't exist.

        :attention: Root directory is the current root directory
            of this instance of filesystem and not the root of
            your Google Drive.

        :return: Id of the created file
        """
        # Google drive doesn't work with paths. So a slight
        # work around is needed.
        path = self._normpath(path)

        parts = path.split("/")
        description = kwargs.get('description', '')
        if len(parts) == 1 and parts[0] == self._root:
            raise ResourceNotFoundError("Please, specify a filename.")
        elif len(parts) == 1:
            return self.client.put_file(self._root,
                                        parts[0], "", description)['id']
        else:
            title = parts.pop()
            parent_id = self.makedir(parts, True)
            return self.client.put_file(parent_id,
                                        title, "", description)['id']

    def open(self, path, mode='r',  buffering=-1, encoding=None,
             errors=None, newline=None, line_buffering=False, **kwargs):
        """Open the named file in the given mode.

        This method downloads the file contents into a local temporary file so
        that it can be worked on efficiently.  Any changes made to the file are
        only sent back to cloud storage when the file is flushed or closed.

        :param path: Id of the file to be opened
        :param mode: In which mode to open the file
        :raises ResourceNotFoundError: If given path doesn't exist and
            'w' is not in mode
        :return: RemoteFileBuffer object
        """
        path = self._normpath(path)
        spooled_file = SpooledTemporaryFile(mode=mode, bufsize=MAX_BUFFER)

        # Truncate the file if requested
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
        """Check if the given path is the root folder.

        :param path: Id of the folder to check
        """
        path = self._normpath(path)

        if path == self._root:
            return True
        else:
            return False

    def copy(self, src, dst, overwrite=False, chunk_size=1024 * 64):
        """Copy a file to another folder.

        :param src: Id of the file to be copied
        :param dst: Id of the folder in which to copy the file
        :param overwrite: This is never true for GoogleDrive
            because there can be many files with the same name
            in one folder.
        :return: Id of the copied file
        """
        return self.client.file_copy(src, dst)['id']

    def copydir(self, src, dst, overwrite=False, ignore_errors=False,
                chunk_size=16384):
        """Copy of folders is not supported.

        @attention: Google drive doesn't support copy of folders.
        To implement it over copy method will be very inefficient.
        """
        raise NotImplemented("If implemented method will be very inefficient")

    def rename(self, src, dst):
        """Rename a file of a given path.

        :param src: Id of the file to be renamed
        :param dst: New title of the file
        :raises UnsupportedError: If trying to rename the root directory
        :return: Id of the renamed file
        """
        if self.is_root(path=src):
            raise UnsupportedError("Can't rename the root directory")
        f = self.client.metadata(src)
        f['title'] = dst
        return self.client.update_file(src, f)['id']

    def remove(self, path):
        """Remove a file of a given path.

        :param path: id of the file to be deleted
        :return: None if removal was successful
        """
        path = self._normpath(path)

        if self.is_root(path=path):
            raise UnsupportedError("Can't remove the root directory")
        if self.isdir(path=path):
            raise ResourceInvalidError("Specified path is a directory. "
                                       "Please use removedir.")
        self.client.file_delete(path)

    def removedir(self, path):
        """Remove a directory of a given path.

        :param path: id of the folder to be deleted
        :return: None if removal was successful
        """
        path = self._normpath(path)

        if not self.isdir(path):
            raise ResourceInvalidError("Specified path is not a directory")
        if self.is_root(path=path):
            raise UnsupportedError("remove the root directory")
        self.client.file_delete(path)

    def makedir(self, path, recursive=False, allow_recreate=False):
        """Create a directory of a given path.

        :param path: path to the folder you want to create.
            It has to be in one of the following forms:
            ``parent_id/new_folder_name`` when recursive is False,
            ``parent_id/new_folder1/new_folder2`` when recursive is True,
            ``/new_folder_name`` to create a new folder in root directory,
            ``/new_folder1/new_folder2`` to recursively create a new folder
            in root directory.
        :param recursive: allows recursive creation of directories
        :param allow_recreate: for google drive this param is
            always False, it will never recreate a directory with
            the same id ( same names are allowed )
        :return: Id of the created directory
        """
        path = self._normpath(path)
        if '/' in path:
            parts = path.split("/")
        else:
            parts = path

        if len(parts) == 1 and parts[0] == self._root:
            raise ResourceNotFoundError("Please, specify a folder name.")
        elif len(parts) == 1:
            return self.client.file_create_folder(self._root, parts[0])['id']
        else:
            if recursive:
                resp = self.client.file_create_folder(self._root, parts[0])
                for folder in parts[1:]:
                    if folder != '':
                        resp = self.client.file_create_folder(resp['id'],
                                                              folder)
                return resp['id']
            else:
                raise UnsupportedError("Recursively create a folder.")

    def move(self, src, dst, overwrite=False, chunk_size=16384):
        """Move a file to another folder.

        .. note:: Google Drive can have many parents for one file,
            when using this method a file will be moved from all
            current parents to the new parent 'dst'.

        :param src: id of the file to be moved
        :param dst: id of the folder in which the file will be moved
        :param overwrite: for Google drive it is always false
        :param chunk_size: if using chunk upload
        :return: Id of the moved file
        """
        if self.isdir(src):
            raise ResourceInvalidError(
                "Specified src is a directory. Please use movedir.")

        f = self.client.get_file(src)
        f['parents'] = [{"id": dst}]
        return self.client.update_file(src, f)['id']

    def movedir(self, src, dst, overwrite=False, ignore_errors=False,
                chunk_size=16384):
        """Move a folder to another folder.

        .. note:: Google Drive can have many parents for one folder,
            when using this method a folder will be moved from all
            current parents to the new parent 'dst'.

        :param src: id of the folder to be moved
        :param dst: id of the folder in which the file will be moved
        :param overwrite: for Google drive it is always false
        :param chunk_size: if using chunk upload
        :return: Id of the moved folder
        """
        if self.isfile(src):
            raise ResourceInvalidError(
                "Specified src is a file. Please use move.")
        f = self.client.get_file(src)
        f['parents'] = [{"id": dst}]

        return self.client.update_file(src, f)['id']

    def isdir(self, path):
        """Check if a the specified path is a directory.

        :param path: Id of the file/folder to check
        """
        path = self._normpath(path)
        info = self.getinfo(path)
        return info['isdir']

    def isfile(self, path):
        """
        Check if a the specified path is a file.

        :param path: Id of the file/folder to check
        """
        path = self._normpath(path)
        info = self.getinfo(path)
        return not info['isdir']

    def exists(self, path):
        """Check if a the specified path exists.

        :param path: Id of the file/folder to check
        """
        path = self._normpath(path)
        try:
            self.client.metadata(path)
            return True
        except RemoteConnectionError as e:
            raise e
        except:
            return False

    def listdir(self, path=None, wildcard=None, full=False, absolute=False,
                dirs_only=False, files_only=False, overrideCache=False):
        """List the files and directories under a given path.

        The directory contents are returned as a list of unicode paths

        :param path: id of the folder to list
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
        path = self._normpath(path)
        flist = self.client.children(path)

        dirContent = self._listdir_helper('', flist, wildcard, full,
                                          absolute, dirs_only, files_only)
        return dirContent

    def listdirinfo(self, path=None, wildcard=None, full=False, absolute=False,
                    dirs_only=False, files_only=False):
        """Retrieve a list of paths and path info under a given path.

        This method behaves like listdir() but instead of just returning the
        name of each item in the directory, it returns a tuple of the name and
        the info dict as returned by getinfo.

        :param path: id of the folder
        :param wildcard: filter paths that match this wildcard
        :param dirs_only: only retrieve directories
        :type dirs_only: bool
        :param files_only: only retrieve files
        :type files_only: bool
        :return: tuple of the name and the info dict as
            returned by getinfo.
        """
        return [(p, self.getinfo(p)) for p in self.listdir(
            path, wildcard=wildcard, full=full, absolute=absolute,
            dirs_only=dirs_only, files_only=files_only)]

    def getinfo(self, path):
        """Returned information is metadata from cloud service.

        A few more fields with standard names for some parts of the metadata.
        :param path: file id for which to return informations
        :return: dictionary with informations about the specific file
        """
        path = self._normpath(path)
        return self._metadata_to_info(self.client.metadata(path))

    def getpathurl(self, path, allow_none=False):
        """Get the url of a given path.

        :param path: id of the file for which to return the url path
        :param allow_none: if true, this method can return None if
            there is no URL form of the given path
        :type allow_none: bool
        :raises `fs.errors.NoPathURLError`: If no URL form exists,
            and allow_none is False (the default)
        :return: url that corresponds to the given path, if one exists
        """
        url = None
        try:
            url = self.getinfo(path)
            url = url["webContentLink"]
        except RemoteConnectionError as e:
            raise e
        except:
            if not allow_none:
                raise NoPathURLError(path=path)

        return url

    def desc(self, path):
        """Get the title of a given path.

        :return: The title for the given path.
        """
        info = self.getinfo(path)
        return info["title"]

    def about(self):
        """Get user information and settings.

        :return: information about the current user
            with whose credentials is the file system instantiated.
        """
        info = self.client.about()
        info['cloud_storage_url'] = "http://drive.google.com/"
        info['user_name'] = info.get('name')
        info['quota'] = 100 * (float(info['quotaBytesUsed']) /
                               float(info['quotaBytesTotal']))
        return info

    def _normpath(self, path):
        """Method normalises the path for google drive.

        :return: normaliesed path as a string
        """
        if path is None or path == "" or path == '/' or len(path) == 0:
            return self._root
        elif path[0] == "/":
            return path[1:]
        else:
            return path

    def _metadata_to_info(self, metadata, localtime=False):
        """Return modified metadata.

        Method adds a few standard names to the metadata:
        * size - the size of the file/folder
        * isdir - is something a file or a directory
        * created_time - the time of the creation
        * path - path to the object which metadata are we showing
        * revision - google drive doesn't have a revision parameter
        * modified - time of the last modification

        :return: The full metadata and a few more fields
            with standard names.
        """
        isdir = metadata.get("mimeType", None) == GD_FOLDER
        info = {
            'size': metadata.get('fileSize', 0),
            'isdir': isdir,
            'created_time': metadata.get('createdDate', 0),
            'path': metadata.get('id', 0),
            'revision': None,
            'modified': metadata.get("modifiedDate", 0)
            }
        info.update(metadata)

        return info
