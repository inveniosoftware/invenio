# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2014 CERN.
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

from __future__ import absolute_import

import logging


class InvenioUpgraderLogFormatter(logging.Formatter):
    """
    Custom logging formatter allowing different log formats for different
    error levels.
    """
    def __init__(self, fmt, **overwrites):
        self.fmt = fmt
        self.overwrites = overwrites
        self.prefix = ''
        self.plugin_id = ''
        logging.Formatter.__init__(self, fmt)

    def get_level_fmt(self, level):
        """ Get format for log level """
        key = None
        if level == logging.DEBUG:
            key = 'debug'
        elif level == logging.INFO:
            key = 'info'
        elif level == logging.WARNING:
            key = 'warning'
        elif level == logging.ERROR:
            key = 'error'
        elif level == logging.CRITICAL:
            key = 'critical'
        return self.overwrites.get(key, self.fmt)

    def format(self, record):
        """ Format log record """
        format_orig = self._fmt
        self._fmt = self.get_level_fmt(record.levelno)
        record.prefix = self.prefix
        record.plugin_id = self.plugin_id
        result = logging.Formatter.format(self, record)
        self._fmt = format_orig
        return result
