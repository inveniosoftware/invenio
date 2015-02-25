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
# 59 Temple Place, Suite 330, Boston, MA 021111307, USA.

"""Workflows task to communicate with bibsched.

The Bibsched logic is separate from other tasks, the goal is to allow
to run a workflow in another way than with Bibsched.
"""

from functools import wraps


def task_update_progress(msg):
    """Function call to print in the field progress of bibsched.

    :param msg: message to print in the field progress of bibsched
    :type msg: str
    :return:the nested function for the workflow engine
    """
    @wraps(task_update_progress)
    def _task_update_progress(obj, eng):
        """Update progress information in the BibSched task table."""
        from invenio.legacy.bibsched.bibtask import task_update_progress as task_update_progress_nested

        task_update_progress_nested(msg)

    return _task_update_progress


def task_update_status(msg):
    """Function call to print in the field status of bibsched.

    :param msg: message to print in the field status of bibsched
    :type msg: str
    :return:the nested function for the workflow engine
    """
    @wraps(task_update_status)
    def _task_update_status(obj, eng):
        """Update status information in the BibSched task table."""
        from invenio.legacy.bibsched.bibtask import task_update_status as task_update_status_nested

        task_update_status_nested(msg)

    return _task_update_status
