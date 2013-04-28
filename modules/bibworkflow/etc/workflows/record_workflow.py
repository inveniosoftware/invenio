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

from invenio.bibworkflow.tasks.record_tasks import \
    print_record, \
    convert_record, \
    check_record
from invenio.bibworkflow_workflow_definition import WorkflowDefinition


class record_workflow(WorkflowDefinition):
    def __init__(self):
        super(record_workflow, self).__init__()
        self.definition = [print_record,
                           convert_record("oaiarxiv2marcxml.xsl"),
                           check_record,
                           print_record]
