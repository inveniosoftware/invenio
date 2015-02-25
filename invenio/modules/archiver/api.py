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

"""Archiver API implementation."""

from __future__ import absolute_import

from fs.zipfs import ZipFS

from invenio.modules.documents import api

from .bagit import create_bagit
from .utils import name_generator


def get_archive_package(recid, version=None):
    """Return archive package.

    :param recid: The record id of archive package.
    """
    query = {'title': 'bagit', 'recid': recid}
    documents = sorted(api.Document.storage_engine.search(query),
                       key=lambda x: x['creation_date'])
    if len(documents) > 0:
        if version == -1:
            return api.Document(documents.pop(), process_model_info=True)
        elif version is not None:
            return api.Document(documents[version], process_model_info=True)
        return map(lambda d: api.Document(d, process_model_info=True),
                   documents)


def create_archive_package(recid):
    """Create archive package for recid as zipped bagit folder.

    :param recid: The record id to archive.
    """
    document = get_archive_package(recid, -1)
    if document is None:
        document = api.Document.create({
            'title': 'bagit',
            'recid': recid,
        }, model='archiver')
    else:
        document = document.update()
    version = len(document.get('version_history', []))
    bagit = create_bagit(recid, version)

    document.setcontents(bagit, name_generator)
    # FIXME remove old versions if necessary


def delete_archive_package(recid, version=None, force=False):
    """Delete archive package for given record id.

    :note: This will delete **ALL** files in the storage for the given record.

    :param recid: The record archive to delete
    """
    map(lambda d: d.delete(force=force),
        get_archive_package(recid, version=version))


def mount_archive_package(recid, version=-1, mode='r'):
    """Mount an archive that allows file operations in the archive package.

    If your mount request returns more than one package, you can use the
    returnedlist of dictionaries to select the _id field and mount a specific
    packagebased on your own criteria.

    :param recid: ID of the record to mount.
    :param version: The record's archive version to mount.
    :param mode: 'r' read, 'w' write.
    :returns: :class:`fs.zipfs.ZipFS` object of the archive.
    """
    document = get_archive_package(recid, version=version)
    return ZipFS(document['uri'], mode=mode)
