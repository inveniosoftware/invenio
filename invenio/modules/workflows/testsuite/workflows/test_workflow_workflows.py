# -*- coding: utf-8 -*-
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

""" Implements a workflow for testing. """

from ...tasks.workflows_tasks import (
    start_async_workflow,
    workflows_reviews,
    wait_for_a_workflow_to_complete,
    log_info,
    get_nb_workflow_running,
    num_workflow_running_greater,
    wait_for_workflows_to_complete
)

from ...tasks.logic_tasks import simple_for, end_for, workflow_if, workflow_else

from invenio.modules.workflows.tasks.marcxml_tasks import set_obj_extra_data_key


class test_workflow_workflows(object):

    """Test workflow for unit-tests."""

    workflow = [
        log_info("starting"),
        simple_for(0, 20, 1, "X"),
        [
            start_async_workflow("test_workflow"),
        ],
        end_for,

        simple_for(0, 20, 1),
        [
            wait_for_a_workflow_to_complete(0.1),
        ],
        end_for,
        workflows_reviews(True),

        simple_for(0, 20, 1, "X"),
        [
            workflow_if(num_workflow_running_greater(3), neg=True),
            [
                start_async_workflow("test_workflow"),
            ],
            workflow_else,
            [
                wait_for_a_workflow_to_complete(0.1),
                start_async_workflow("test_workflow"),
            ],
            set_obj_extra_data_key("nbworkflowrunning",
                                   get_nb_workflow_running),
        ],
        end_for,
        wait_for_workflows_to_complete,
        workflows_reviews(False, False)
    ]
