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


"""Rotating file log handler for writing logs to the file system.

**Configuration**

======================== ======================================================
`LOGGING_FS_BACKUPCOUNT` Number of files to keep. **Default:** ``5``.
`LOGGING_FS_MAXBYTES`    Max file size in bytes.  **Default:** ``104857600``
                         (100 MB).
`LOGGING_FS_LEVEL`       Log level threshold for handler. **Default:**
                         ``WARNING``.
======================== ======================================================
"""

from __future__ import absolute_import

import os
import logging
from logging.handlers import RotatingFileHandler


def setup_app(app):
    """Filesystem logging handler."""
    app.config.setdefault('LOGGING_FS_BACKUPCOUNT', 5)
    app.config.setdefault('LOGGING_FS_MAXBYTES', 104857600)  # 100mb
    app.config.setdefault(
        'LOGGING_FS_LEVEL',
        'DEBUG' if app.debug else 'WARNING'
    )

    # Create log directory if it does not exists
    try:
        os.makedirs(
            os.path.join(app.instance_path, app.config.get('CFG_LOGDIR', ''))
        )
    except Exception:
        pass

    handler = RotatingFileHandler(
        os.path.join(
            app.instance_path,
            app.config.get('CFG_LOGDIR', ''),
            app.logger_name + '.log'
        ),
        backupCount=app.config['LOGGING_FS_BACKUPCOUNT'],
        maxBytes=app.config['LOGGING_FS_MAXBYTES']
    )

    handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'
    ))

    handler.setLevel(app.config['LOGGING_FS_LEVEL'])

    # Add handler to application logger
    app.logger.addHandler(handler)
