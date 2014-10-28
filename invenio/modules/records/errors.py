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

"""Errors for records."""


class RecordError(Exception):

    """Generic error for records."""

    def __init__(self, message=None, status=None):
        """Initialization."""
        super(RecordError, self).__init__()
        self.message = message or self.__class__.__name__
        self.status = status or 400

    def __str__(self):
        """String representation of the error."""
        return repr("Error message: {}, Error status: {}".format(
            self.message, self.status
        ))


class RecordNotFoundError(RecordError):

    """Error indicating that a record was not found."""

    def __init__(self, message=None, status=None):
        super(RecordNotFoundError, self).__init__(message, status=404)


class RecordUnsuppotedMediaTypeError(RecordError):

    def __init__(self, message=None, status=None):
        super(RecordUnsuppotedMediaTypeError, self).__init__(
            message,
            status=415
        )


class RecordForbiddenViewError(RecordError):

    """Error indicating that user is forbidden to view a record."""

    def __init__(self, message=None, status=None):
        super(RecordNotFoundError, self).__init__(message, status=403)


class RecordDeletedError(RecordError):

    """Error indicating that a record is deleted."""

    def __init__(self, message=None, status=None):
        super(RecordNotFoundError, self).__init__(message, status=410)
