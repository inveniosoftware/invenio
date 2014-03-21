# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
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

from workflow.patterns import IF, OBJ_GET

from invenio.modules.uploader.errors import UploaderWorkflowException
from invenio.modules.uploader.tasks import raise_, validate, update_pidstore,\
        retrieve_record_id_from_pids, reserve_record_id, save_record

insert = [
    retrieve_record_id_from_pids(step=0),
    IF(
        lambda obj, eng: obj.get('recid') and not eng.getVar('options').get('force', False),
        [
            raise_(UploaderWorkflowException(step=1,
                msg="Record identifier found the input '%s' ,you should use the"
                    " option 'replace', 'correct' or 'append' mode instead.\n "
                    "The option '--force' could also be used. (-h for help)"
                    % (OBJ_GET('recid'), )))
        ]
    ),
    reserve_record_id(step=2),
    validate(step=3),
    save_record(step=4),
    update_pidstore(step=5),
]

undo = []
