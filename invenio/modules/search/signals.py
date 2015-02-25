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

from invenio.base.signals import _signals as signals

record_viewed = signals.signal(
    'record-viewed')
"""
This signal is sent when a detailed view of record is displayed.
Parameters:
    recid 	- id of record
    id_user	- id of user or 0 for guest
    request     - flask request object

Example subscriber:

     def subscriber(sender, recid=0, id_user=0, request=None):
         ...

"""
