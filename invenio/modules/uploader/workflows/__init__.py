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
    invenio.modules.uploader.workflows
    ----------------------------------

    Every uploader workflow should be a python dictionary contain three keys:

    * `pre_trasks`
        list of tasks which will be run before running the actual
        workflow, each element of the list should a callable.

    * `tasks`
        List of tasks to be run by the `WorkflowEngine`.

    * `post_tasks`
        Same as for `pre_tasks` but in this case they will be run
        after the workflow is done.

    An example function to be called after the workflow could be::

        def return_recids_only(records, **kwargs):
            records = [obj[1].get('recid') for obj in records]

    This functions must have always the same parameters (like the one above)
    and those parameters have the value that
    :func:`~invenio.modules.uploader.tasks.run_workflow` gets.
"""
