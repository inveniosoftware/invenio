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

""" Multimedia error."""


class MultimediaError(Exception):

    """General multimedia exception."""

    def __init__(self, message=None, code=None):
        """Init the error handler."""
        super(MultimediaError, self).__init__()
        self.message = message or self.__class__.__name__
        self.code = code or 500

    def __str__(self):
        """Error message. """
        return repr("Error message: {message}. Error code: {code}"
                    .format(message=self.message, code=self.code))


class MultimediaImageNotFound(MultimediaError):

    """Image not found error."""

    def __init__(self, message=None, code=None):
        """Init with status code 404."""
        super(MultimediaImageNotFound, self).__init__(message, code=404)


class MultimediaImageForbidden(MultimediaError):

    """Access to the image is forbidden."""

    def __init__(self, message=None, code=None):
        """Init with status code 401."""
        super(MultimediaImageForbidden, self).__init__(message, code=401)


class MultmediaImageCropError(MultimediaError):

    """Image on crop error."""


class MultmediaImageResizeError(MultimediaError):

    """Image resize error."""


class MultimediaImageRotateError(MultimediaError):

    """Image rotate error."""


class MultimediaImageQualityError(MultimediaError):

    """Image quality error."""


class MultimediaImageFormatError(MultimediaError):

    """Image format error."""


class IIIFValidatorError(MultimediaError):

    """IIIF API validator error."""
