# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

"""Serializer for kombu that appends some custom banks."""

from uuid import UUID

from kombu.serialization import (
    register as kombu_register,
    unregister as kombu_unregister,
)
from msgpack import (
    packb as msgpack_pack,
    unpackb as msgpack_unpackb,
)
from msgpack.fallback import ExtType


class Uuid(object):

    @staticmethod
    def pack(obj):
        """Pack the uuid."""
        return obj.bytes

    @staticmethod
    def unpack(obj):
        """Unpack the uuid, based on the ouput of :func:`pack`."""
        return UUID(bytes=obj)

    @staticmethod
    def matches(obj):
        """Check if we can handle the to-be-packed object."""
        return isinstance(obj, UUID)


known_types = {
    0x27: Uuid,
}


def _default(unpacked_obj):
    """Attempt to pack an unpacked object if its type is known to us."""
    for candidate_code, candidate_type in known_types.items():
        if candidate_type.matches(unpacked_obj):
            return ExtType(candidate_code, candidate_type.pack(unpacked_obj))
    raise TypeError("Unknown type object %r" % (unpacked_obj,))


def _ext_hook(code, packed_obj):
    """Attempt to unpack an object of known application-specific type."""
    for candidate_code, candidate_type in known_types.items():
        if candidate_code == code:
            return candidate_type.unpack(packed_obj)
    raise TypeError("Unknown type object %r" % (packed_obj,))


content_encoding = 'utf-8'
content_type = 'application/x-msgpack-append'


# kombu adds encoding='utf-8', so we replicate this behaviour
unpackb = lambda s: msgpack_unpackb(s, encoding=content_encoding, ext_hook=_ext_hook)
packb = lambda s: msgpack_pack(s, default=_default)


def register():
    """Register our serializer in kombu."""
    kombu_register('msgpack_append', packb, unpackb,
             content_type=content_type,
             content_encoding=content_encoding)


def unregister():
    kombu_unregister('msgpack_append')
