# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013, 2014 CERN.
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

"""Exceptions for Invenio Messages module."""


class InvenioWebMessageError(Exception):

    """A generic error for WebMessage."""

    def __init__(self, message="InvenioWebMessageError", code=400):
        """Initialisation."""
        self.message = message
        self.code = code

    def __str__(self):
        """String representation."""
        return repr("Error message: %s , Error code: %s"
                    % (self.message, self.code))


class MessageNotFoundError(InvenioWebMessageError):

    """Error indicating a message was not found."""

    def __init__(self, message="MessageNotFoundError", code=400):
        """Initialization."""
        super(MessageNotFoundError, self).__init__(message, code)


class MessageNotDeletedError(InvenioWebMessageError):

    """Error indicating a message was not deleted."""

    def __init__(self, message="MessageNotDeletedError", code=400):
        """Initialization."""
        super(MessageNotDeletedError, self).__init__(message, code)


class MessageNotCreatedError(InvenioWebMessageError):

    """Error indicating a message was not found."""

    def __init__(self, message="MessageNotCreatedError", code=400):
        """Initialization."""
        super(MessageNotCreatedError, self).__init__(message, code)


class MessagesNotFetchedError(InvenioWebMessageError):

    """Error indicating a message was not found."""

    def __init__(self, message="MessagesNotFetchedError", code=400):
        """Initialization."""
        super(MessagesNotFetchedError, self).__init__(message, code)


class MessageValidationError(InvenioWebMessageError):

    """Error indicating validation error."""

    def __init__(self, message="MessageValidationError", code=400,
                 error_list=[]):
        """Initialization."""
        super(MessageValidationError, self).__init__(message, code)
        self.error_list = error_list
