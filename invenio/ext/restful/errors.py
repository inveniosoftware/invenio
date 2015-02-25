# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014 CERN.
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

"""Exceptions for Restful."""


class RestfulError(Exception):

    """Generic Restful Error."""

    def __init__(self, error_msg=None, status_code=None):
        """Initialize error message and status code."""
        super(RestfulError, self).__init__()
        self.error_msg = error_msg or self.__class__.__name__()
        self.status_code = status_code or 400

    def __str__(self):
        """String representation of message."""
        return repr("Error message: %s , Status code: %s"
                    % (self.error_msg, self.status_code))


class InvalidPageError(RestfulError):

    """Error indicating an invalid page."""

    def __init__(self, error_msg="Invalid page", status_code=400):
        """Initialize default error message for invalid page error."""
        super(InvalidPageError, self).__init__(error_msg, status_code)
