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

"""Default workflows for insert records using the uploader.

:py:data:`insert`
:py:data:`insert.undo`
"""

from workflow.patterns import IF

from invenio.modules.uploader.errors import UploaderWorkflowException
from invenio.modules.uploader.uploader_tasks import \
    create_records_for_workflow, \
    legacy, \
    manage_attached_documents, \
    raise_, \
    reserve_record_id, \
    retrieve_record_id_from_pids, \
    return_recordids_only, \
    save_master_format, \
    save_record, \
    update_pidstore,\
    validate


class insert(object):

    """Default insert workflow."""

    pre_tasks = [
        create_records_for_workflow,
    ]

    tasks = [
        retrieve_record_id_from_pids(step=0),
        IF(
            lambda obj, eng: obj[1].get('recid') and
            not eng.getVar('options').get('force', False),
            [
                raise_(UploaderWorkflowException(
                    step=1,
                    msg="Record identifier found the input, you should use the"
                        " option 'replace', 'correct' or 'append' mode "
                        "instead.\n The option '--force' could also be used. "
                        "(-h for help)")
                       )
            ]
        ),
        reserve_record_id(step=2),
        validate(step=3),
        manage_attached_documents(step=4),
        save_record(step=5),
        update_pidstore(step=6),
        save_master_format(step=7),
        legacy(step=8),
    ]

    post_tasks = [
        return_recordids_only,
    ]

    class undo(object):

        """Default undo steps for the insert workflow."""

        pre_tasks = []
        tasks = []
        post_tasks = []
