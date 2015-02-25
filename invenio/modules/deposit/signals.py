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

from blinker import Namespace
_signals = Namespace()

template_context_created = _signals.signal('template-context-created')
"""
This signal is sent right before collection is saved.
Sender is the blueprint. Extra data pass is:

 * context
"""

file_uploaded = _signals.signal('file-uploaded')
"""
This signal is sent right after a file has been uploaded.
Sender is the deposition type. Extra data pass is:

 * user_id: Id of user uploading the file.
 * uuid: Workflow id.
 * name: Filename
 * file: Full path of file
 * size: Size of file
 * id: unique file id
 * content_type:
 * deposition: The deposition object to which the file belongs
 * deposition_file: The DepositionFile object
"""
