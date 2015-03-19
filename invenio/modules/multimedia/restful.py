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

"""Multimedia IIIF Image API."""

from flask import send_file
from flask_restful import abort, Resource
from functools import wraps
from six import StringIO

from .api import (
    IIIFImageAPIWrapper, MultimediaImageCache
)
from .config import (
    MULTIMEDIA_IMAGE_API_SUPPORTED_FORMATS
)
from .errors import (
    MultimediaError, MultmediaImageCropError, MultmediaImageResizeError,
    MultimediaImageFormatError, MultimediaImageRotateError,
    MultimediaImageQualityError, IIIFValidatorError, MultimediaImageNotFound,
    MultimediaImageForbidden
)


def error_handler(f):
    """error handler."""
    @wraps(f)
    def inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except (MultmediaImageCropError, MultmediaImageResizeError,
                MultimediaImageFormatError, MultimediaImageRotateError,
                MultimediaImageQualityError) as e:
            abort(500, message=e.message, code=500)
        except IIIFValidatorError as e:
            abort(400, message=e.message, code=400)
        except (MultimediaError, MultimediaImageNotFound,
                MultimediaImageForbidden) as e:
            abort(e.code, message=e.message, code=e.code)
    return inner


class IiifImageAPI(Resource):

    """IIIF API Implementation.

    .. note::

        * IIF IMAGE API v1.0
            * For more infos please visit <http://iiif.io/api/image/>.
        * IIIF Image API v2.0
            * For more infos please visit <http://iiif.io/api/image/2.0/>.
        * The API works only for GET requests
        * The image process must follow strictly the following workflow:

           * Region
           * Size
           * Rotation
           * Quality
           * Format

    """

    method_decorators = [
        error_handler,
    ]

    def get(self, version, uuid, region, size, rotation, quality,
            image_format):
        """Run IIIF Image API workflow."""
        # Validate IIIF parameters
        IIIFImageAPIWrapper.validate_api(
            version=version,
            region=region,
            size=size,
            rotate=rotation,
            quality=quality,
            image_format=image_format
        )

        cache = MultimediaImageCache()

        # build the image key
        key = "iiif:{0}/{1}/{2}/{3}/{4}.{5}".format(
            uuid, region, size, quality, rotation, image_format
        )

        # Check if its cached
        cached = cache.get_value(key)

        # If the image is cached loaded from cache
        if cached:
            to_serve = StringIO(cached)
            to_serve.seek(0)
        # Otherwise build create the image
        else:
            image = IIIFImageAPIWrapper.get_image(uuid)

            image.apply_api(
                version=version,
                region=region,
                size=size,
                rotate=rotation,
                quality=quality
            )

            # prepare image to be serve
            to_serve = image.serve(image_format=image_format)
            # to_serve = image.serve(image_format=image_format)
            cache.cache(key, to_serve.getvalue())

        # decide the mime_type from the requested image_format
        mimetype = MULTIMEDIA_IMAGE_API_SUPPORTED_FORMATS.get(
            image_format, 'image/jpeg'
        )
        return send_file(to_serve, mimetype=mimetype)

    def post(self):
        """post."""
        abort(405)

    def delete(self):
        """delete."""
        abort(405)

    def options(self):
        """options."""
        abort(405)

    def put(self):
        """put."""
        abort(405)

    def head(self):
        """head."""
        abort(405)


def setup_app(app, api):
    """setup the urls."""
    api.add_resource(
        IiifImageAPI,
        ("/api/multimedia/image/<string:version>/<string:uuid>/"
         "<string:region>/<string:size>/<string:rotation>/<string:quality>."
         "<string:image_format>"),
    )
