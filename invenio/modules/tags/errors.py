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

"""Errors for tags."""


class TagError(Exception):

    """Generic error for Tags."""

    def __init__(self, error_msg=None, status_code=None):
        """Initialization."""
        super(TagError, self).__init__()
        self.error_msg = error_msg or self.__class__.__name__
        self.status_code = status_code or 400

    def __str__(self):
        """String representation of message."""
        return repr("Error message: %s , Error code: %s"
                    % (self.error_msg, self.error_code))


class TagNotCreatedError(TagError):

    """Error indicating that a tag cannot be created."""

    pass


class TagNotUpdatedError(TagError):

    """Error indicating that a tag cannot be updated."""

    pass


class TagNotFoundError(TagError):

    """Error indicating that a tag cannot be found."""

    def __init__(self, error_msg=None, status_code=None):
        """Initialization."""
        super(TagNotFoundError, self).__init__(error_msg, status_code=404)


class TagNotDeletedError(TagError):

    """Error indicating that a tag cannot be deleted."""

    pass


class TagsNotFetchedError(TagError):

    """Error indicating that a list of tags cannot be fetched."""

    pass


class TagOwnerError(TagError):

    """Error indicating unauthorized tag access."""

    pass


class TagValidationError(TagError):

    """Error indicating invalid tag."""

    def __init__(self, error_msg=None, status_code=400,
                 error_list=[]):
        """Initialization."""
        super(TagValidationError, self).__init__(error_msg, status_code)
        self.error_list = error_list


class TagRecordAssociationError(TagError):

    """Error indicating inability to associate a tag with a record."""

    pass


class RecordNotFoundError(TagError):

    """Error indicating that a record cannot be found."""

    def __init__(self, error_msg=None, status_code=None):
        """Initialization."""
        super(RecordNotFoundError, self).__init__(error_msg, status_code=404)
