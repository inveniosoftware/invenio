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

"""Utility functions for alerting engine."""

import os

from flask import g, current_app
from logging import Formatter, getLogger, FileHandler
from werkzeug.local import LocalProxy


def get_logger():
    """Get alert engine logger."""
    logger = getattr(g, 'alertengine_logger', None)
    if logger is None:
        handler = FileHandler(
            os.path.join(current_app.config['CFG_LOGDIR'], 'alertengine.log'),
            delay=True
        )
        logger = getLogger('invenio.alertengine')
        formatter = Formatter('{asctime}#{message}', datefmt='%Y%m%d%H%M%S',
                              style='{')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        g.alertengine_logger = logger
    return logger

logger = LocalProxy(get_logger)
