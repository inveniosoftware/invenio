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

"""Flask-IIIF extension.

.. py:data:: IIIF_IMAGE_OPENER

    There are two ways to initialize an IIIF image object, by ``fullpath`` and
    ``bytestream``. Can be an ``import string`` or a ``callback function``.
    By default ``identifier_to_path`` return the ``fullpath`` of
    :class:`~invenio.modules.documents.api:Document`.

    default: :func:`~invenio.modules.documents.utis.identifier_to_path`
"""

from flask_iiif import IIIF
from flask_iiif.errors import MultimediaError

from six import string_types

from werkzeug.utils import import_string

from .utils import api_file_permission_check

__all__ = ('setup_app', )

iiif = IIIF()


def setup_app(app):
    """Setup Flask-IIIF extension."""
    if 'invenio.modules.documents' in app.config.get('PACKAGES_EXCLUDE'):
        raise MultimediaError(
            "Could not initialize the Flask-IIIF extension because "
            ":class:`~invenio.modules.documents.api:Document` is missing"
        )

    iiif.init_app(app)
    iiif.init_restful(app.extensions['restful'])
    app.config.setdefault(
        'IIIF_IMAGE_OPENER',
        'invenio.modules.documents.utils:identifier_to_path'
    )

    uuid_to_source_handler = app.config['IIIF_IMAGE_OPENER']

    uuid_to_source = (
        import_string(uuid_to_source_handler) if
        isinstance(uuid_to_source_handler, string_types) else
        uuid_to_source_handler
    )
    iiif.uuid_to_image_opener_handler(uuid_to_source)
    app.config['IIIF_CACHE_HANDLER'] = 'invenio.ext.cache:cache'

    # protect the api
    iiif.api_decorator_handler(api_file_permission_check)
    return app
