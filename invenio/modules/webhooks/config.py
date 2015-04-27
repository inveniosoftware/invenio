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

"""Webhooks module."""

from __future__ import unicode_literals

WEBHOOKS_DEBUG_RECEIVER_URLS = {}
"""Mapping of receiver id to URL pattern. This allows generating URLs to an
intermediate webhook proxy service like Ultrahook for testing on development
machines:

.. code-block:: python

    WEBHOOKS_DEBUG_RECEIVER_URLS = {
        'github': 'https://hook.user.ultrahook.com/?access_token=%%(token)s'
    }
"""

WEBHOOKS_SECRET_KEY = "secret_key"
