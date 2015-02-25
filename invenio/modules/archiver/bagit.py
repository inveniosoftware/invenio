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

"""Bagit wrapper."""

from __future__ import absolute_import

import os

from bagit import make_bag
from datetime import datetime
from fs.opener import opener
from fs.osfs import OSFS
from fs.utils import copyfile, copydir
from fs.zipfs import ZipFS
from werkzeug.utils import cached_property

from invenio.base.globals import cfg


class BagitHandler(object):

    """Handle all bagit related operations."""

    def __init__(self, recid, version=None, processors=None):
        """Initialize bagit wrapper."""
        self.recid = recid
        self.version = version
        if processors is None:
            self.processors = [self._process_files]

    @cached_property
    def name(self):
        """Generate bagit name."""
        output = "{0}_{1}".format(
            self.recid, datetime.now().strftime("%Y-%m-%d_%H:%M:%S:%f"))
        if self.version is not None:
            output += "_v{0}".format(self.version)
        return output

    @cached_property
    def folder(self):
        """Open destination directory."""
        return os.path.join(cfg["ARCHIVER_TMPDIR"], self.name)

    @property
    def metadata(self):
        """Return record metadata."""
        from invenio.modules.records.api import get_record
        return get_record(self.recid).dumps()

    def _zip(self, destination=None):
        """Compresse a bagit file."""
        # Removes the final forwardslash if there is one
        destination = destination or cfg["ARCHIVER_TMPDIR"]
        if destination.endswith(os.path.sep):
            destination = destination[:-len(os.path.sep)]
        filename = os.path.join(destination, "{0}.zip".format(self.name))

        # Create and FS object
        with OSFS(self.folder) as to_zip_fs:
            with ZipFS(filename, mode='w') as zip_fs:
                copydir(to_zip_fs, zip_fs, overwrite=True)
            file_to_delete = os.path.basename(self.folder)
            to_delete_from = OSFS(os.path.dirname(self.folder))
            to_delete_from.removedir(file_to_delete, recursive=True,
                                     force=True)
        return filename

    def _make_bag(self, **kwargs):
        """Turn a folder into bagit form and compress it."""
        opener.opendir(self.folder, create_dir=True)
        info = {'Bagging-Date': datetime.now().strftime("%Y-%m-%d")}
        info.update(kwargs)
        return make_bag(self.folder, info)

    def _process_files(self, metadata):
        """Transfer files in a list from one ``fs`` object to another.

        All tranferer files will maintain the same filename.
        """
        # FS object created at the folder of where the record specific bag is
        fs_dest = opener.opendir(self.folder, "files", create_dir=True)

        files_to_upload = []
        for file_to_upload in metadata.get("files", []):
            dirname_ = os.path.dirname(file_to_upload["path"])
            basename_ = os.path.basename(file_to_upload["path"])
            fs_src = opener.opendir(dirname_)
            copyfile(fs_src, basename_, fs_dest, basename_)
            file_to_upload["path"] = os.path.join("files", basename_)
            del file_to_upload["url"]
            files_to_upload.append(file_to_upload)
        metadata["files_to_upload"] = files_to_upload
        return metadata

    def _save_metadata(self, metadata):
        """Transfer the MARC data in xml format."""
        with open(os.path.join(self.folder, "metadata.json"),
                  mode="w") as f:
            f.write(str(metadata))

    def create(self, destination=None, **kwargs):
        """Create the folder for the bag if it doesn't already exist."""
        self._make_bag(**kwargs)
        metadata = self.metadata
        for func in reversed(self.processors):
            metadata = func(metadata)
        self._save_metadata(metadata)
        return self._zip(destination=destination)


def create_bagit(recid, version=None):
    """Given a recid will create a compressed bagit."""
    return BagitHandler(recid, version).create()
