# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

"""Handle documents upload."""

import os

from invenio.base.utils import toposort_depends
from invenio.modules.documents import api
from invenio.modules.documents.tasks import set_document_contents
from invenio_records.recordext.functions import reserve_recid
from invenio_records.signals import before_record_insert
from invenio_records.utils import name_generator


@before_record_insert.connect
@toposort_depends(reserve_recid.reserve_recid)
def set_record_documents(record, *args, **kwargs):
    """Attach and treat all the documents embeded in the input filex."""
    dirname = kwargs.get('dirname', None) or os.curdir

    def _check_path(source):
        """Check if the ``source`` path.

        If it is relative path than the directory path of original blob
        filename, if defined, or the current directory will be prepended.
        """
        if not os.path.isabs(source):
            new_source = os.path.join(dirname, source)
            if os.path.exists(new_source):
                return new_source
        return source

    def _create_document(metadata, record):
        metadata['source'] = _check_path(metadata['source'])
        metadata.setdefault('recids', list())

        record.setdefault('_documents', list())
        model = metadata.pop('model', 'record_document_base')

        if record['recid'] not in metadata['recids']:
            metadata['recids'].append(record['recid'])

        document = api.Document.create(metadata, model=model)

        record['_documents'].append((document['title'], document['_id']))
        return document

    if 'files_to_upload' in record:
        files_to_upload = record.get('files_to_upload', [])

        for file_to_upload in files_to_upload:
            document = _create_document(file_to_upload, record)

            set_document_contents.delay(
                document['_id'],
                document['source'],
                name_generator(document)
            )

        del record['files_to_upload']

    if 'files_to_link' in record:
        files_to_link = record.get('files_to_link', [])

        for file_to_link in files_to_link:
            _create_document(file_to_link, record)

        del record['files_to_link']
