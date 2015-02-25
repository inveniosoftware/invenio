# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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

"""Document tasks."""

from invenio.celery import celery

from . import api


@celery.task
def set_document_contents(document_id, source, name, **kwargs):
    """Set content of a document using the Document API.

    :see:`~invenio.modules.documents.api`

    :document_id: Id of the document already created.
    :source: as in :meth:`~invenio.modules.documents.api:Document.setcontents`
    :name: as in :meth:`~invenio.modules.documents.api:Document.setcontents`
    :**kwargs: Any other parameter that could be used by
        :meth:`invenio.modules.documents.api:Document.setcontents`

    """
    document = api.Document.get_document(document_id)
    document.setcontents(source, name, kwargs)
    return document['_id']

__all__ = ['set_document_contents', ]
