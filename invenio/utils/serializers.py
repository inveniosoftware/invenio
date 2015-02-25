# -*- coding: utf-8 -*-
# This file is part of Invenio.
# Copyright (C) 2013 CERN.
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
"""
    invenio.utils.serializers
    -------------------------

    Implements custom serializers.
"""

import marshal
from six.moves import cPickle as pickle
from zlib import compress, decompress

__all__ = ['ZlibMarshal',
           'serialize_via_marshal',
           'deserialize_via_marshal',
           'serialize_via_pickle',
           'deserialize_via_pickle']


class ZlibMarshal(object):
    """Combines zlib and marshal libraries."""

    @staticmethod
    def loads(astring):
        """Decompress and deserialize string into a Python object via marshal."""
        return marshal.loads(decompress(astring))

    @staticmethod
    def dumps(obj):
        """Serialize Python object via marshal into a compressed string."""
        return compress(marshal.dumps(obj))

# Provides legacy API functions.
serialize_via_marshal = ZlibMarshal.dumps
deserialize_via_marshal = ZlibMarshal.loads

class ZlibPickle(object):
    """Combines zlib and pickle libraries."""

    @staticmethod
    def loads(astring):
        """Decompress and deserialize string into a Python object via pickle"""
        return pickle.loads(decompress(astring))

    @staticmethod
    def dumps(obj):
        """Serialize Python object via pickle into a compressed string."""
        return compress(pickle.dumps(obj))

# Provides legacy API functions.
serialize_via_pickle = ZlibPickle.dumps
deserialize_via_pickle = ZlibPickle.loads
