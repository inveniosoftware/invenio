# -*- coding: utf-8 -*-

## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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

"""
Invenio signal utilities

This module defines Invenio-wide signals
"""

from blinker import Namespace
_signals = Namespace()

# WebSearch signals
webcoll_after_webpage_cache_update = _signals.signal(
    'webcoll-after-webpage-cache-update')
"""
This signal is sent right after webcoll runs webpage cache update.
It is passed the collection to be sent named `response`.

Example subscriber::

    def clear_additional_cache(sender, collection=None, lang=None):
        pass

    from invenio.signalutils import webcoll_after_webpage_cache_update
    from flask import current_app
    webcoll_after_webpage_cache_update.connect(
        clear_additional_cache,
        current_app._get_current_object()
    )
"""
