## This file is part of Invenio.
## Copyright (C) 2012 CERN.
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

from invenio.bibworkflow.tasks.test_tasks import \
    lower_than_20, \
    add, \
    higher_than_20, \
    sleep_task, \
    simple_task
from invenio.bibworkflow_workflow_definition import WorkflowDefinition


class test_workflow_2(WorkflowDefinition):
    def __init__(self):
        super(test_workflow_2, self).__init__()
        self.definition = [higher_than_20,
                           add(20),
                           lower_than_20,
                           sleep_task(4),
                           simple_task(2)]
