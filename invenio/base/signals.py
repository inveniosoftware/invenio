# -*- coding: utf-8 -*-

# This file is part of Invenio.
# Copyright (C) 2013, 2014 CERN.
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
Invenio signal utilities.

This module defines Invenio-wide signals
"""

from blinker import Namespace
_signals = Namespace()

# Custom Flask signals
before_handle_user_exception = _signals.signal(
    'before-handle-user-exception')
"""
This signal is sent right before user exception handler is called.
"""

# WebSearch signals
websearch_before_search = _signals.signal(
    'websearch-before-search')
"""
This signal is sent right before search handler is called.
"""

websearch_before_browse = _signals.signal(
    'websearch-before-browse')
"""
This signal is sent right before browse handler is called.
"""

webcoll_after_webpage_cache_update = _signals.signal(
    'webcoll-after-webpage-cache-update')
"""
This signal is sent right after webcoll runs webpage cache update.
It is passed the collection to be sent named `response`.

Example subscriber::

    def clear_additional_cache(sender, collection=None, lang=None):
        pass

    from invenio.base.signals import webcoll_after_webpage_cache_update
    from flask import current_app
    webcoll_after_webpage_cache_update.connect(
        clear_additional_cache,
        current_app._get_current_object()
    )
"""

webcoll_after_reclist_cache_update = _signals.signal(
    'webcoll_after_reclist_cache_update')
"""
This signal is sent right after webcoll runs reclist cache update.
It passes all updated collections.
"""

pre_command = _signals.signal('pre-command')
"""
This signal is sent right before any inveniomanage command is executed.

Note that any positional arguments (sometimes called as ``*args``), will be
received as a keyword argument called ``args``.

Sample subscriber:

.. code-block:: python

    def backup_database(sender, **kwargs):
        pass

    from invenio.base.signals import pre_command
    from invenio.base.scripts.database import drop
    pre_command.connect(
        backup_database,
        sender=drop
    )
"""

post_command = _signals.signal('post-command')
"""
This signal is sent right after any inveniomanage command is executed.

Example subscriber::

    def modify_demosite(sender, *args, **kwargs):
        pass

    from invenio.base.signals import post_command
    from invenio.base.scripts.database import demosite
    pre_command.connect(
        modify_demosite,
        sender=demosite
    )
"""

# Record related signals
record_before_create = _signals.signal(
    'record-before-create')
"""
This signal is sent before record is created.
"""

record_after_create = _signals.signal(
    'record-after-create')
"""
This signal is sent after record is created.
"""

record_before_update = _signals.signal(
    'record-before-update')
"""
This signal is sent before record is updated.
"""

record_after_update = _signals.signal(
    'record-after-update')
"""
This signal is sent after record is updated.
"""

pre_template_render = _signals.signal('pre-template-render')
"""
This signal is sent before *some* templates are rendered, an allows
customization of the template context.

Sender is the blueprint view name (e.g. 'record.metadata'). Extra data
passed in depends on blueprint view.
"""
