# -*- coding: utf-8 -*-
#
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
Invenio hash functions.

Usage example:
  >>> from invenio.utils.hash import md5
  >>> print md5('MyPa$$')

Simplifies imports of hash functions depending on Python version.
"""

try:
    from hashlib import sha256, sha1, md5
    HASHLIB_IMPORTED = True
except ImportError:
    from md5 import md5
    from sha import sha as sha1
    HASHLIB_IMPORTED = False
