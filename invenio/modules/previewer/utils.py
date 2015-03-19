# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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

"""Utility functions."""

import os

from flask import url_for, current_app
from flask_login import current_user


def get_pdf_path(f):
    """Return pdf path."""
    path = f.get_full_path()
    if os.path.isfile(path):
        return str(path)
    return None


def get_record_files(recid, filename):
    """Yield legacy BibDoc files."""
    from invenio.legacy.bibdocfile.api import BibRecDocs
    for f in BibRecDocs(recid).list_latest_files(list_hidden=False):
        if f.name + f.superformat == filename or filename is None:
            yield f


def get_record_documents(recid, filename):
    """Yield LegacyBibDoc files from Documents."""
    from invenio.modules.records.api import get_record
    from invenio.modules.documents.api import Document
    from invenio.legacy.bibdocfile.api import decompose_file

    record = get_record(recid)
    duuids = [uuid for (k, uuid) in record.get('_documents', [])
              if k == filename]

    for duuid in duuids:
        document = Document.get_document(duuid)
        if not document.is_authorized(current_user):
            current_app.logger.info(
                "Unauthorized access to /{recid}/files/{filename} "
                "({document}) by {current_user}".format(
                    recid=recid, filename=filename, document=document,
                    current_user=current_user))
            continue

        if document.get('linked', False) and (
                document.get('uri').startswith('http://') or
                document.get('uri').startswith('https://')):
            url = document.get('uri')
        else:
            url = url_for('record.file', recid=recid, filename=filename)

        (dummy, name, superformat) = decompose_file(filename)

        class LegacyBibDoc(object):
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)

            def get_full_path(self):
                return document.get('uri')

            def get_recid(self):
                return recid

        yield LegacyBibDoc(name=name, superformat=superformat, url=url)
