# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.


"""
invenio.ext.logging.backends.legacy
-----------------------------------

Adds a Invenio 1.x style error handling by logging exceptions to the database
and sending emails. Works in connection with register_exception()

Configuration::

    LOGGING_LEGACY_LEVEL = 'ERROR' # log level (maps to logging.ERROR)
"""

from __future__ import absolute_import

import logging
from ..handlers import InvenioLegacyHandler
from ..formatters import InvenioExceptionFormatter


def setup_app(app):
    """
    Invenio 1.x log handler
    """
    if not app.debug:
        app.config.setdefault('LOGGING_LEGACY_LEVEL', 'ERROR')

        handler = InvenioLegacyHandler()
        handler.setFormatter(InvenioExceptionFormatter())
        handler.setLevel(getattr(logging, app.config['LOGGING_LEGACY_LEVEL']))

        # Add handler to application logger
        app.logger.addHandler(handler)
