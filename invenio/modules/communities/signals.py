# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013, 2014 CERN.
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
User community signals - useful for hooking into the community
creation process.
"""

from blinker import Namespace
_signals = Namespace()

before_save_collection = _signals.signal('before-save-collection')
"""
This signal is sent right before collection is saved.
Sender is the community. Extra data pass is:

 * is_new
 * provisional
"""

after_save_collection = _signals.signal('after-save-collection')
"""
This signal is sent right after a collection is saved.
Sender is the community. Extra data pass is:

 * collection
 * provisional
"""

before_save_collections = _signals.signal('before-save-collections')
"""
This signal is sent right before all collections are saved.
Sender is the community.
"""

after_save_collections = _signals.signal('after-save-collections')
"""
This signal is sent right after all collections are saved.
Sender is the community.
"""

before_delete_collection = _signals.signal('before-delete-collection')
"""
This signal is sent right before a collection is deleted.
Sender is the community. Extra data pass is:

 * collection
 * provisional
"""

after_delete_collection = _signals.signal('after-delete-collection')
"""
This signal is sent right after a collection is deleted.
Sender is the community. Extra data pass is:

 * provisional
"""

before_delete_collections = _signals.signal('before-delete-collections')
"""
This signal is sent right before all collections are deleted.
Sender is the community.
"""

after_delete_collections = _signals.signal('after-delete-collections')
"""
This signal is sent right after all collections are deleted.
Sender is the community.
"""


pre_curation = _signals.signal('pre-curation')
"""
This signal is sent right before a record is accepted or rejected.
Sender is the user community. Extra data pass is:

 * action: accept or reject
 * recid: Record ID
 * pretend: True if record changes is actually not persisted
"""

post_curation = _signals.signal('post-curation')
"""
This signal is sent right after a record is accepted or rejected.
Sender is the user community.

 * action: accept or reject
 * recid:  Record ID
 * record: Record which was uploaded
 * pretend: True if record changes is actually not persisted

Note, the record which was accept/reject is most likely not updated
yet in the database, since bibupload has to run first.
"""

curate_record = _signals.signal('curate-record')
"""
This signal is sent right before curation process removes a record.
"""
