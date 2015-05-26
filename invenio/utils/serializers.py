# -*- coding: utf-8 -*-
# This file is part of Invenio.
# Copyright (C) 2013, 2015 CERN.
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
"""Implements custom serializers."""

import marshal
import zlib

from backports import lzma

from six.moves import cPickle as pickle

__all__ = ['ZlibMarshal',
           'ZlibPickle',
           'LzmaPickle',
           'SerializerError',
           'serialize_via_marshal',
           'deserialize_via_marshal',
           'serialize_via_pickle',
           'deserialize_via_pickle']


class SerializerError(Exception):

    """Error during (de-)serialization."""

    pass


class ZlibMarshal(object):

    """Combines zlib and marshal libraries."""

    @staticmethod
    def loads(astring):
        """Decompress and deserialize string into Python object via marshal."""
        try:
            return marshal.loads(zlib.decompress(astring))
        except zlib.error as e:
            raise SerializerError(
                'Cannot decompress object ("{}")'.format(str(e))
            )
        except Exception as e:
            # marshal module does not provide a proper Exception model
            raise SerializerError(
                'Cannot restore object ("{}")'.format(str(e))
            )

    @staticmethod
    def dumps(obj):
        """Serialize Python object via marshal into ompressed string."""
        return zlib.compress(marshal.dumps(obj))

# Provides legacy API functions.
serialize_via_marshal = ZlibMarshal.dumps
deserialize_via_marshal = ZlibMarshal.loads


class ZlibPickle(object):

    """Combines zlib and pickle libraries."""

    @staticmethod
    def loads(astring):
        """Decompress and deserialize string into Python object via pickle."""
        try:
            return pickle.loads(zlib.decompress(astring))
        except zlib.error as e:
            raise SerializerError(
                'Cannot decompress object ("{}")'.format(str(e))
            )
        except pickle.UnpicklingError as e:
            raise SerializerError(
                'Cannot restore object ("{}")'.format(str(e))
            )

    @staticmethod
    def dumps(obj):
        """Serialize Python object via pickle into compressed string."""
        return zlib.compress(pickle.dumps(obj))

# Provides legacy API functions.
serialize_via_pickle = ZlibPickle.dumps
deserialize_via_pickle = ZlibPickle.loads


class LzmaPickle(object):

    """Combines lzma and pickle libraries."""

    @staticmethod
    def loads(astring):
        """Decompress and deserialize string into a Python object via pickle."""
        try:
            return pickle.loads(lzma.decompress(astring))
        except lzma.LZMAError as e:
            raise SerializerError(
                'Cannot decompress object ("{}")'.format(str(e))
            )
        except pickle.UnpicklingError as e:
            raise SerializerError(
                'Cannot restore object ("{}")'.format(str(e))
            )

    @staticmethod
    def dumps(obj):
        """Serialize Python object via pickle into a compressed string."""
        return lzma.compress(pickle.dumps(obj))
