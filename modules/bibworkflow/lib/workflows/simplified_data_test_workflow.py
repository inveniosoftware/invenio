# -*- coding: utf-8 -*-
## This file is part of Invenio.
## Copyright (C) 2012, 2013 CERN.
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

""" Implements a workflow for testing """

from invenio.bibworkflow_tasks.simplified_data_tasks import task_a, task_b
from invenio.bibworkflow_workflow_definition import WorkflowDefinition


class simplified_data_test_workflow(WorkflowDefinition):
    def __init__(self):
        super(simplified_data_test_workflow, self).__init__()
        self.definition = [task_a(1),
                           task_b,
                           task_a(1),
                           task_a(4),
                           task_a(1),
                           task_a(1),
                           task_b,
                           task_a(13)]
