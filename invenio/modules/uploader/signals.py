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

"""
invenio.modules.uploader.signals
--------------------------------

Defines signals used in uploader API
"""

from blinker import Namespace
_signals = Namespace()

uploader_started = _signals.signal('uploader_started')
"""Signal sent right before the uploading process starts with the input data
and all the arguments from the run function"""

uploader_finished = _signals.signal('uploader_finished')
"""Signal sent right after the uploader process finishes with the name of the
workflow that has run, the return values from it and the ``**kwargs``"""
