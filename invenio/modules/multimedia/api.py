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

"""Multimedia Image API."""

import itertools
import math
import os
import re
from decimal import Decimal
from six import StringIO
from PIL import Image
from invenio.modules.documents.api import Document
from invenio.modules.documents.errors import DocumentNotFound
from .config import (
    MULTIMEDIA_IMAGE_API_SUPPORTED_FORMATS, MULTIMEDIA_IMAGE_CACHE_TIME,
    MULTIMEDIA_IMAGE_API_QUALITIES, MULTIMEDIA_IMAGE_API_COVERTERS,
    IIIF_API_VALIDATIONS
)
from .errors import (
    MultmediaImageCropError, MultmediaImageResizeError,
    MultimediaImageFormatError, MultimediaImageRotateError,
    MultimediaImageQualityError, MultimediaImageNotFound,
    IIIFValidatorError
)
from .utils import initialize_redis


class MultimediaObject(object):

    """The Multimedia Object."""


class MultimediaImage(MultimediaObject):

    """Multimedia Image API.

    Initializes an image api with IIIF standards. You can:

    * Resize :func:`resize`.
    * Crop :func:`crop`.
    * Rotate :func:`rotate`.
    * Change image quality :func:`quality`.

    Example of editing and image and save it to disk:

    .. code-block:: python

        from invenio.modules.MultimediaImage import MultimediaImage

        image = MultimediaImage.get_image(uuid)
        # Rotate the image
        image.rotate(90)
        # Resize the image
        image.resize('300,200')
        # Crop the image
        image.crop('20,20,400,300')
        # Make the image black and white
        image.quality('grey')
        # Finaly save it to /tmp
        image.save('/tmp')

    Example of serving the modified image over http:

    .. code-block:: python

        from flask import Blueprint
        from invenio.modules.MultimediaImage import MultimediaImage

        @blueprint.route('/serve/<string:uuid>/<string:size>')
        def serve_thumbnail(uuid, size):
            \"\"\"Serve the image thumbnail.

            :param uuid: The document uuid.
            :param size: The desired image size.
            \"\"\"
            # Initialize the image with the uuid
            image = MultimediaImage.get_image(uuid)
            # Resize it
            image.resize(size)
            # Serve it
            return send_file(image.serve(), mimetype='image/jpeg')
    """

    def __init__(self, image):
        """Initialize the image."""
        self.image = image

    @classmethod
    def get_image(cls, uuid):
        """Return the image object.

        :param str uuid: The document uuid
        :returns: a :class:`~invenio.modules.multimedia.api.MultimediaImage`
                  instance
        """
        try:
            document = Document.get_document(uuid)
        except DocumentNotFound:
            raise MultimediaImageNotFound(
                "The requested image {0} not found".format(uuid))

        if not document.get('uri'):
            raise MultimediaImageNotFound(
                "The requested image {0} not found".format(uuid))

        image = Image.open(document['uri'])
        return cls(image)

    @classmethod
    def from_file(cls, path):
        """Return the image object from the given path.

        :param str path: The absolute path of the file
        :returns: a :class:`~invenio.modules.multimedia.api.MultimediaImage`
                  instance
        """
        if not os.path.exists(path):
            raise MultimediaImageNotFound(
                "The requested image {0} not found".format(path))

        image = Image.open(path)
        return cls(image)

    @classmethod
    def from_string(cls, source):
        """Create an :class:`MultimediaImage` instance from string.

        :param source: The image image string
        :type source: :class:`StringIO.StringIO` object
        :returns: a :class:`~invenio.modules.multimedia.api.MultimediaImage`
                  instance
        """
        image = Image.open(source)
        return cls(image)

    def resize(self, dimensions, resample=Image.NEAREST):
        """Resize the image.

        :param str dimensions: The dimensions to resize the image
        :param resample: The algorithm to be used
        :type resample: `PIL.Image` algorithm

        .. note::

            * `dimensions` must be one of the following:

                * 'w,': The exact width, height will be calculated.
                * ',h': The exact height, width will be calculated.
                * 'pct:n': Image percentance scale.
                * 'w,h': The extact width and height.
                * '!w,h': Best fit for the given width and height.

        """
        real_width, real_height = self.image.size

        # Check if it is `pct:`
        if dimensions.startswith('pct:'):
            percent = Decimal(str(dimensions.split(':')[1])) * Decimal(0.01)
            if percent < Decimal(0):
                raise MultmediaImageResizeError(
                    ("Image percentance could not be negative, {0} has been"
                     " given").format(percent)
                )

            width_decimal = real_width * percent
            height_decimal = real_height * percent

            # Sanitize decimal lower than 1
            if 0 < width_decimal < 1:
                width_decimal = 1
            if 0 < height_decimal < 1:
                height_decimal = 1

            width = int(width_decimal)
            height = int(height_decimal)

        # Check if it is `,h`
        elif dimensions.startswith(','):
            height = int(dimensions[1:])
            # find the ratio
            ratio = self.reduce_by(height, real_height)
            # calculate width
            width = real_width * ratio

        # Check if it is `!w,h`
        elif dimensions.startswith('!'):
            x, y = map(int, dimensions[1:].split(','))
            # find the ratio
            ratio_x = self.reduce_by(x, real_width)
            ratio_y = self.reduce_by(y, real_height)
            # take the min
            ratio = min(ratio_x, ratio_y)
            # calculate the dimensions
            width = x * ratio
            height = y * ratio

        # Check if it is `w,`
        elif dimensions.endswith(','):
            width = int(dimensions[:-1])
            # find the ratio
            ratio = self.reduce_by(width, real_width)
            # calculate the height
            height = real_height * ratio

        # Normal mode `w,h`
        else:
            try:
                width, height = map(int, dimensions.split(','))
            except:
                raise MultmediaImageResizeError(
                    "The request must contain width,height sequence"
                )

        # If a dimension is missing throw error
        if any((dimension <= 0 and dimension is not None) for
                dimension in (width, height)):
            raise MultmediaImageResizeError(
                ("Width and height cannot be zero or negative, {0},{1} has"
                 " been given").format(width, height)
            )

        self.image = self.image.resize((width, height), resample=resample)

    def crop(self, coordinates):
        """Crop the image.

        :param str coordinates: The coordinates to crop the image

        .. note::

            * `coordinates` must have the following pattern:

                * 'x,y,w,h': in pixels.
                * 'pct:x,y,w,h': percentance.

        """
        # Get image full dimensions
        real_width, real_height = self.image.size
        real_dimensions = itertools.cycle((real_width, real_height))

        percentance = False
        if coordinates.startswith('pct:'):
            dimensions = map(float, coordinates.split(':')[1].split(','))
            percentance = True
        else:
            dimensions = map(int, coordinates.split(','))

        # First check if it has 4 coordinates x,y,w,h
        dimensions_length = len(dimensions)
        if dimensions_length != 4:
            raise MultmediaImageCropError(
                "Must have 4 dimensions {0} has been given".
                format(dimensions_length))

        # Make sure that there is not any negative dimension
        if any(coordinate < 0 for coordinate in dimensions):
            raise MultmediaImageCropError(
                "Dimensions cannot be negative {0} has been given".
                format(dimensions)
            )

        if percentance:
            if any(coordinate > 100.0 for coordinate in dimensions):
                raise MultmediaImageCropError(
                    "Dimensions could not be grater than 100%")

            # Calculate the dimensions
            x, y, width, height = [int(math.floor(
                                   self.percent_to_decimal(dimension) *
                                   real_dimensions.next())) for dimension
                                   in dimensions]
        else:
            x, y, width, height = dimensions

        # Check if any of the requested axis is outside of image borders
        if any(axis > real_dimensions.next() for axis in (x, y)):
            raise MultmediaImageCropError(
                "Outside of image borders {0},{1}".
                format(real_width, real_height)
            )

        # Calculate the final dimensions
        max_x = x + width
        max_y = y + height
        # Check if the final width is bigger than the the real image width
        if max_x > real_width:
            max_x = real_width

        # Check if the final height is bigger than the the real image height
        if max_y > real_height:
            max_y = real_height

        self.image = self.image.crop((x, y, max_x, max_y))

    def rotate(self, degrees, mirror=False):
        """Rotate the image by given degress.

        :param float degress: The degrees, should be in range of [0, 360]
        :param bool mirror: Flip image from left to right
        """
        transforms = {
            '90': Image.ROTATE_90,
            '180': Image.ROTATE_180,
            '270': Image.ROTATE_270,
            'mirror': Image.FLIP_LEFT_RIGHT,
        }

        # Check if we have the right degress
        if not 0.0 <= float(degrees) <= 360.0:
            raise MultimediaImageRotateError(
                "Degrees must be between 0 and 360, {0} has been given".
                format(degrees)
            )

        if degrees in transforms.keys():
            self.image = self.image.transpose(transforms.get(str(degrees)))
        else:
            # transparent background if degress not multiple of 90
            self.image = self.image.convert('RGBA')
            self.image = self.image.rotate(float(degrees), expand=0)

        if mirror:
            self.image = self.image.transpose(transforms.get('mirror'))

    def quality(self, quality):
        """Change the image format.

        :param str quality: The image quality should be in (default, grey,
                        bitonal, color)

        .. note::

            The library supports transformations between each supported
            mode and the "L" and "RGB" modes. To convert between other
            modes, you may have to use an intermediate image (typically
            an "RGB" image).

        """
        qualities = MULTIMEDIA_IMAGE_API_QUALITIES
        if quality not in qualities:
            raise MultimediaImageQualityError(
                ("{0} does not supported, pleae select on of the"
                 " valid qualities: {1}").format(quality, qualities)
            )

        qualities_by_code = zip(qualities,
                                MULTIMEDIA_IMAGE_API_COVERTERS)

        if quality not in ('default', 'color'):
            # Convert image to RGB read the note
            if self.image.mode != "RGBA":
                self.image = self.image.convert('RGBA')

            code = [quality_code[1] for quality_code in qualities_by_code
                    if quality_code[0] == quality][0]

            self.image = self.image.convert(code)

    def size(self):
        """Return the current image size.

        :return: the image size
        :rtype: list
        """
        return self.image.size

    def save(self, path, image_format="jpeg", quality=90):
        """Store the image to the specific path.

        :param str path: absolute path
        :param str image_format: (gif, jpeg, pdf, png)
        :param int quality: The image quality; [1, 100]

        .. note::

            `image_format` = jpg will not be recognized by PIL and it will be
            changed to jpeg.

        """
        # transform `image_format` is lower case and not equals to jpg
        cleaned_image_format = self._prepare_for_output(image_format)
        self.image.save(path, cleaned_image_format, quality=quality)

    def serve(self, image_format="png", quality=90):
        """Return a StringIO object to easily serve it thought HTTTP.

        :param str image_format: (gif, jpeg, pdf, png)
        :param int quality: The image quality; [1, 100]

        .. note::

            `image_format` = jpg will not be recognized by PIL and it will be
            changed to jpeg.

        """
        image_buffer = StringIO()
        # transform `image_format` is lower case and not equals to jpg
        cleaned_image_format = self._prepare_for_output(image_format)
        self.image.save(image_buffer, cleaned_image_format, quality=quality)
        image_buffer.seek(0)

        return image_buffer

    def _prepare_for_output(self, requested_format):
        """Help validate output format.

        :param str requested_format: The image output format

        .. note::

            pdf format can't be saved as `RBGA` so image needs to be converted
            to `RGB` mode.

        """
        image_format = self.sanitize_format_name(requested_format)
        format_keys = MULTIMEDIA_IMAGE_API_SUPPORTED_FORMATS.keys()

        if image_format not in format_keys:
            raise MultimediaImageFormatError(
                ("{0} does not supported, please select on of the valid"
                 " formats: {1}").format(requested_format, format_keys)
            )

        # If the the `requested_format` is pdf force mode to RGB
        if image_format == "pdf":
            self.image = self.image.convert('RGB')

        return image_format

    @staticmethod
    def reduce_by(nominally, dominator):
        """Calculate the ratio."""
        return Decimal(nominally) / dominator

    @staticmethod
    def percent_to_decimal(number):
        """Calculate the percentance."""
        return Decimal(number) / Decimal(100.0)

    @staticmethod
    def sanitize_format_name(value):
        """Lowercase formats and make sure that jpg is written as jpeg."""
        return value.lower().replace("jpg", "jpeg")


class IIIFImageAPIWrapper(MultimediaImage):

    """IIIF Image API Wrapper."""

    @staticmethod
    def validate_api(**kwargs):
        """Validate IIIF Image API.

        Example to validate the IIIF API:

        .. code:: python

            from invenio.multimedia.api import IIIFImageAPIWrapper

            IIIFImageAPIWrapper.validate_api(
                version=version,
                region=region,
                size=size,
                rotate=rotation,
                quality=quality,
                image_format=image_format
            )

        .. note::

            If the version is not specified it will fallback to version 2.0.

        """
        # Get the api version
        version = kwargs.get('version', 'v2')
        # Get the validations and ignore cases
        cases = IIIF_API_VALIDATIONS.get(version)
        for key in cases.keys():
            # If the parameter don't match with iiif casess
            if not re.search(
                cases.get(key, {}).get('validate', ''), kwargs.get(key)
            ):
                raise IIIFValidatorError(
                    ("value: `{0}` for parameter: `{1}` is not supported").
                    format(kwargs.get(key), key)
                )

    def apply_api(self, **kwargs):
        """Apply the IIIF API to the image.

        Example to apply the IIIF API:

        .. code:: python

            from invenio.multimedia.api import IIIFImageAPIWrapper

            image = IIIFImageAPIWrapper.get_image(uuid)

            image.apply_api(
                version=version,
                region=region,
                size=size,
                rotate=rotation,
                quality=quality
            )

        .. note::

            * If the version is not specified it will fallback to version 2.0.
            * Please note the :func:`validate_api` should be ran before
              :func:`apply_api`.

        """
        # Get the api version
        version = kwargs.get('version', 'v2')
        # Get the validations and ignore cases
        cases = IIIF_API_VALIDATIONS.get(version)
        # Set the apply order
        order = 'region', 'size', 'rotate', 'quality'
        # Set the functions to be applied
        tools = {
            "region": self.apply_region,
            "size": self.apply_size,
            "rotate": self.apply_rotate,
            "quality": self.apply_quality
        }

        for key in order:
            # Ignore if has the ignore value for the specific key
            if kwargs.get(key) != cases.get(key, {}).get('ignore'):
                tools.get(key)(kwargs.get(key))

    def apply_region(self, value):
        """IIIF apply crop.

        Apply :func:`~invenio.modules.multimedia.api.MultimediaImage.crop`.
        """
        self.crop(value)

    def apply_size(self, value):
        """IIIF apply resize.

        Apply :func:`~invenio.modules.multimedia.api.MultimediaImage.resize`.
        """
        self.resize(value)

    def apply_rotate(self, value):
        """IIIF apply rotate.

        Apply :func:`~invenio.modules.multimedia.api.MultimediaImage.rotate`.
        """
        mirror = False
        degrees = value
        if value.startswith('!'):
            mirror = True
            degrees = value[1:]
        self.rotate(degrees, mirror=mirror)

    def apply_quality(self, value):
        """IIIF apply quality.

        Apply :func:`~invenio.modules.multimedia.api.MultimediaImage.quality`
        """
        self.quality(value)


class MultimediaImageCache(MultimediaObject):

    """Initializes an image cached layer."""

    def __init__(self):
        """Initialize the cache."""
        self.redis = initialize_redis()

    def has_key(self, key):
        """Return if a key exists."""
        return self.redis.exists(key)

    def get_value(self, key):
        """Return the key value."""
        return self.redis.get(key)

    def cache(self, key, value, time=MULTIMEDIA_IMAGE_CACHE_TIME):
        """Cache the object."""
        self.redis.setex(key, value, time)

    def save(self, key, value):
        """Save to a specific key."""
        self.redis.set(key, value)

    def _delete(self, key):
        """Delete the specific key."""
        self.redis.delete(key)
