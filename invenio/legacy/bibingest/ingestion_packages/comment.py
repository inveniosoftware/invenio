# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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
"""The Blog post comment ingestion package."""

__revision__ = "$Id$"

from invenio.legacy.bibingest.ingestion_package_interface \
    import IngestionPackage, valid_string

_ADDITIONAL_ACCEPTED_FIELD_NAMES = {
    # Don't use underscores ('_') for the field names.

    # the URL of the blog
    'url' : (lambda:None, valid_string),
}

class Comment(IngestionPackage):
    """The Ingestion Package default class"""

    def __init__(self, storage_engine_instance, storage_engine_settings = None):
        """
        The constructor.
        """

        IngestionPackage.__init__(self, storage_engine_instance, storage_engine_settings)
        self._accepted_field_names.update(_ADDITIONAL_ACCEPTED_FIELD_NAMES)

def comment(storage_engine_instance, storage_engine_settings = None):
    """
    Instantiates the ingestion package with the given storage engine instance.
    """

    return Comment(storage_engine_instance, storage_engine_settings)


package = comment
