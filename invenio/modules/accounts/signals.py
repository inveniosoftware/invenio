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

"""Account module signals."""

from blinker import Namespace
_signals = Namespace()


profile_updated = _signals.signal('profile-updated')
"""Signal sent when a user profile is updated.

Example subscriber

.. code-block:: python

    def listener(sender, *args, **kwargs):
        pass

    from invenio.modules.accounts.signals import profile_updated

    profile_updated.connect(
        listener,
        sender=''
    )
"""
