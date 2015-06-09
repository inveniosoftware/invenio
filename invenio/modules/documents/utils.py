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

"""Document utils."""

from flask import abort

__all__ = ('identifier_to_path', 'identifier_to_path_and_permissions', )


def identifier_to_path(identifier):
    """Convert the identifier to path.

    :param str identifier: A unique file identifier
    :raises NotFound: if the file fullpath is empty
    """
    fullpath = identifier_to_path_and_permissions(identifier, path_only=True)
    return fullpath or abort(404)


def identifier_to_path_and_permissions(identifier, path_only=False):
    """Convert the identifier to path.

    :param str identifier: A unique file identifier
    :raises Forbidden: if the user doesn't have permissions
    """
    if identifier.startswith('recid:'):
        record_id, filename = _parse_legacy_syntax(identifier)

        fullpath, permissions = _get_legacy_bibdoc(
            record_id, filename=filename
        )
    else:
        fullpath, permissions = _get_document(identifier)

    if path_only:
        return fullpath

    try:
        assert (permissions[0] == 0)
    except AssertionError:
        return abort(403)


def _get_document(uuid):
    """Get the document fullpath.

    :param str uuid: The document's uuid
    """
    from invenio.modules.documents.api import Document
    from invenio.modules.documents.errors import (
        DocumentNotFound, DeletedDocument
    )

    try:
        document = Document.get_document(uuid)
    except (DocumentNotFound, DeletedDocument):
        path = _simulate_file_not_found()
    else:
        path = document.get('uri', ''), document.is_authorized()
    finally:
        return path


def _get_legacy_bibdocs(recid, filename=None):
    """Get all fullpaths of legacy bibdocfile.

    :param int recid: The record id
    :param str filename: A specific filename
    :returns: bibdocfile full path
    :rtype: str
    """
    from invenio.ext.login import current_user
    from invenio.legacy.bibdocfile.api import BibRecDocs
    return [
        (bibdoc.fullpath, bibdoc.is_restricted(current_user))
        for bibdoc in BibRecDocs(recid).list_latest_files(list_hidden=False)
        if not bibdoc.subformat and not filename or
        bibdoc.get_full_name() == filename
    ]


def _get_legacy_bibdoc(recid, filename=None):
    """Get the fullpath of legacy bibdocfile.

    :param int recid: The record id
    :param str filename: A specific filename
    :returns: bibdocfile full path and access rights
    :rtype: tuple
    """
    paths = _get_legacy_bibdocs(recid, filename=filename)
    try:
        path = paths[0]
    except IndexError:
        path = _simulate_file_not_found()
    finally:
        return path


def _parse_legacy_syntax(identifier):
    """Parse legacy syntax.

    .. note::

        It can handle requests such as `recid:{recid}` or
        `recid:{recid}-{filename}`.
    """
    if '-' in identifier:
        record_id, filename = identifier.split('recid:')[1].split('-', 1)
    else:
        record_id, filename = identifier.split('recid:')[1], None
    return record_id, filename


def _simulate_file_not_found():
    """Simulate file not found situation.

    ..note ::

        It simulates an file not found situation, this will always raise `404`
        error.
    """
    return '', (0, '')
