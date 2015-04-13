# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111 1307, USA.

"""Main workflow iterating over selected repositories and downloaded files."""

from invenio.legacy.bibsched.bibtask import (
    task_update_progress,
    write_message
)

from invenio.modules.workflows.definitions import RecordWorkflow

from invenio.modules.workflows.tasks.logic_tasks import (
    end_for,
    foreach,
    simple_for,
    workflow_else,
    workflow_if,
)

from invenio.modules.workflows.tasks.marcxml_tasks import (
    get_obj_extra_data_key,
    update_last_update,
)

from invenio.modules.workflows.tasks.workflows_tasks import (
    get_nb_workflow_created,
    get_workflow_from_engine_definition,
    get_workflows_progress,
    num_workflow_running_greater,
    start_async_workflow,
    wait_for_a_workflow_to_complete,
    workflows_reviews,
    write_something_generic,
)

from ..tasks.harvesting import (
    filtering_oai_pmh_identifier,
    get_records_from_file,
    get_repositories_list,
    harvest_records,
    init_harvesting,
)


class oaiharvest_harvest_repositories(RecordWorkflow):

    """A workflow for use with OAI harvesting in BibSched."""

    object_type = "workflow"
    record_workflow = "oaiharvest_record_post_process"

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
                                preserve_data=True,
                                preserve_extra_data_keys=["repository", "oai_identifier"],
                                get_workflow_from=get_workflow_from_engine_definition,
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
                                preserve_data=True,
                                preserve_extra_data_keys=["repository", "oai_identifier"],
                                get_workflow_from=get_workflow_from_engine_definition,
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

    @staticmethod
    def get_description(bwo):
        """Return description of object."""
        from flask import render_template

        identifiers = None

        extra_data = bwo.get_extra_data()
        if 'options' in extra_data and 'identifiers' in extra_data["options"]:
            identifiers = extra_data["options"]["identifiers"]

        results = bwo.get_tasks_results()

        if 'review_workflow' in results:
            result_progress = results['review_workflow'][0]['result']
        else:
            result_progress = {}

        current_task = extra_data['_last_task_name']

        return render_template("workflows/styles/harvesting_description.html",
                               identifiers=identifiers,
                               result_progress=result_progress,
                               current_task=current_task)

    @staticmethod
    def get_title(bwo):
        """Return title of object."""
        return "Summary of OAI harvesting from: {0}".format(
            bwo.get_extra_data()["repository"]["name"])

    @staticmethod
    def formatter(bwo):
        """Return description of object."""
        from flask import render_template
        from invenio.modules.workflows.models import BibWorkflowObject
        from invenio.modules.workflows.registry import workflows

        identifiers = None

        extra_data = bwo.get_extra_data()
        if 'options' in extra_data and 'identifiers' in extra_data["options"]:
            identifiers = extra_data["options"]["identifiers"]

        results = bwo.get_tasks_results()

        if 'review_workflow' in results:
            result_progress = results['review_workflow'][0]['result']
        else:
            result_progress = {}

        current_task = extra_data['_last_task_name']

        related_objects = []
        for id_object in extra_data.get("objects_spawned", list()):
            spawned_object = BibWorkflowObject.query.get(id_object)
            if spawned_object:
                workflow = workflows.get(spawned_object.get_workflow_name())
                related_objects.append(
                    (spawned_object.id,
                     workflow.get_title(spawned_object) or "No title")
                )
            else:
                related_objects.append(
                    (id_object,
                     None)
                )

        return render_template("workflows/styles/harvesting_description.html",
                               identifiers=identifiers,
                               result_progress=result_progress,
                               current_task=current_task,
                               related_objects=related_objects)
