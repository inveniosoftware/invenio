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

from __future__ import absolute_import, print_function

import logging

from .wrappers import get_pretty_traceback


class InvenioExceptionFormatter(logging.Formatter):
    """
    Invenio exception formatter
    """
    def __init__(self, fmt=None, datefmt=None, remove_trailing_linefeed=False):
        self.remove_trailing_linefeed = remove_trailing_linefeed
        logging.Formatter.__init__(self, fmt=fmt, datefmt=datefmt)

    def format(self, record):
        """ Format log record """
        # Set by invenio.ext.logging.wrappers.register_exception
        if hasattr(record, 'invenio_register_exception'):
            extra = record.invenio_register_exception

            exc_info = record.exc_info
            req = extra['req']
            prefix = extra['prefix']
            suffix = extra['suffix']

            output = get_pretty_traceback(
                req=req, exc_info=exc_info, skip_frames=2
            )

            if output:
                if prefix:
                    output = prefix + '\n' + output
                if suffix:
                    output = output + suffix

                if self.remove_trailing_linefeed and output.endswith('\n'):
                    output = output[:-1]

                return output
        return logging.Formatter.format(self, record)
