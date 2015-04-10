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

"""Records configuration."""

from __future__ import unicode_literals

from .models import RecordMetadata as RecordMetadataModel


RECORDS_BREADCRUMB_TITLE_KEY = 'title.title'
"""Key used to extract the breadcrumb title from the record."""

RECORDS_ENGINE = ('invenio.modules.jsonalchemy.jsonext.engines.sqlalchemy'
                  ':SQLAlchemyStorage')

RECORDS_SQLALCHEMYSTORAGE = {
    'model': RecordMetadataModel,
}

RECORD_DOCUMENT_NAME_GENERATOR = ('invenio.modules.records.utils:'
                                  'default_name_generator')

RECORD_DOCUMENT_VIEWRESTR_POLICY = 'ANY'
"""When a document belongs to more than one record, and this policy is set to
`ALL` the user must be authorized to view all the records to continue checking
the access rights of the document. If the policy is set to `ANY` (default),
then the user needs to be authorized to view at least one record in order to
continue checking the document specific access rights."""
