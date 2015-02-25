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

"""Record field function."""


def get_record_documents(record):
    """Return list of Document instances.

    :record: Record instance
    :returns: list of Document instances
    """
    from invenio.modules.documents import api

    def _document(mapping):
        document = api.Document.get_document(d[1])
        document.__record_filename__ = d[0]
        return document
    return [_document(d) for d in record.get('_documents', [])]
