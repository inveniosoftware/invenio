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
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111 1307, USA.

"""Main workflow iterating over selected repositories and downloaded files."""

from invenio.modules.workflows.tasks.marcxml_tasks import (
    get_obj_extra_data_key,
    update_last_update,
)

from invenio.modules.workflows.tasks.workflows_tasks import (
    start_async_workflow,
    workflows_reviews,
    wait_for_a_workflow_to_complete,
    get_nb_workflow_created,
    get_workflows_progress,
    write_something_generic,
    num_workflow_running_greater
)

from invenio.modules.workflows.tasks.logic_tasks import (
    foreach,
    end_for,
    simple_for,
    workflow_if,
    workflow_else
)

from invenio.legacy.bibsched.bibtask import (
    task_update_progress,
    write_message
)
from invenio.modules.workflows.definitions import WorkflowBase


from ..tasks.harvesting import (
    filtering_oai_pmh_identifier,
    init_harvesting,
    get_records_from_file,
    get_repositories_list,
    harvest_records,
)


class oaiharvest_harvest_repositories(WorkflowBase):

    """A workflow for use with OAI harvesting in BibSched."""

    object_type = "workflow"

    workflow = [
        init_harvesting,
        foreach(get_repositories_list(), "repository"),
        [
            write_something_generic("Harvesting", [task_update_progress,
                                                   write_message]),
            harvest_records,
            foreach(get_obj_extra_data_key("harvested_files_list")),
            [
                write_something_generic("Starting sub-workflows for file",
                                        [task_update_progress, write_message]),
                foreach(get_records_from_file()),
                [
                    workflow_if(filtering_oai_pmh_identifier),
                    [
                        workflow_if(num_workflow_running_greater(10), neg=True),
                        [
                            start_async_workflow(
                                "oaiharvest_record_post_process",
                                preserve_data=True,
                                preserve_extra_data_keys=["repository"]
                            ),
                        ],
                        workflow_else,
                        [
                            write_something_generic(
                                ["Waiting for workflows to finish"],
                                [task_update_progress,
                                 write_message]),
                            wait_for_a_workflow_to_complete(10.0),
                            start_async_workflow(
                                "oaiharvest_record_post_process",
                                preserve_data=True,
                                preserve_extra_data_keys=["repository"],
                            ),
                        ],
                    ],
                ],
                end_for
            ],
            end_for
        ],
        end_for,
        write_something_generic(["Processing: ", get_nb_workflow_created,
                                 " records"],
                                [task_update_progress, write_message]),
        simple_for(0, get_nb_workflow_created, 1),
        [
            wait_for_a_workflow_to_complete(1.0),
            write_something_generic([get_workflows_progress, "%% complete"],
                                    [task_update_progress, write_message]),
        ],
        end_for,
        workflows_reviews(stop_if_error=True),
        update_last_update(get_repositories_list())
    ]
