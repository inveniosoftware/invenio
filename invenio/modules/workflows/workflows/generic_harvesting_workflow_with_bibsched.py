## This file is part of Invenio.
## Copyright (C) 2013, 2014 CERN.
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

"""Implements a typical ingestion workflow for MARCXML records in BibSched."""

from ..tasks.marcxml_tasks import (get_repositories_list, harvest_records,
                                   init_harvesting, get_records_from_file,
                                   get_obj_extra_data_key, update_last_update,
                                   filtering_oai_pmh_identifier)

from ..tasks.workflows_tasks import (start_workflow, workflows_reviews,
                                     wait_for_a_workflow_to_complete,
                                     get_nb_workflow_created,
                                     get_workflows_progress,
                                     write_something_generic,
                                     num_workflow_running_greater)

from ..tasks.logic_tasks import (foreach, end_for, simple_for, workflow_if,
                                 workflow_else)

from invenio.legacy.bibsched.bibtask import task_update_progress, write_message

from invenio.modules.workflows.utils import WorkflowBase


class generic_harvesting_workflow_with_bibsched(WorkflowBase):

    """A generic harvesting workflow for use with OAI harvesting in BibSched."""

    object_type = "workflow"

    @staticmethod
    def get_description(bwo):
        """Return a human readable description for data in workflow."""
        from flask import render_template

        identifiers = None

        extra_data = bwo.get_extra_data()
        try:
            if 'options' in extra_data and 'identifiers' in extra_data["options"]:
                identifiers = extra_data["options"]["identifiers"]

            results = bwo.get_tasks_results()
            result_progress = {}

            if 'review_workflow' in results:
                result_progress = results['review_workflow'][0]['result']
            elif 'wait_for_a_workflow_to_complete' in results:
                result_progress = results['wait_for_a_workflow_to_complete'][0]['result']

            current_task = extra_data['_last_task_name']
        except Exception as e:
            result_progress = {}
            identifiers = None
            from invenio.modules.workflows.models import ObjectVersion
            if bwo.version == ObjectVersion.INITIAL:
                current_task = "The process has not started!!!"
            else:
                current_task = "The process CRASHED!!! \n {0}".format(str(e.message))

        return render_template("workflows/styles/harvesting_description.html",
                               identifiers=identifiers,
                               result_progress=result_progress,
                               current_task=current_task)

    @staticmethod
    def get_title(bwo):
        """Return a human readable title for data in workflow."""
        return "Supervising harvesting of {0}".format(
            bwo.get_extra_data()["_repository"]["name"])

    @staticmethod
    def formatter(bwo, **kwargs):
        """Return a human readable representation of data in workflow."""
        return generic_harvesting_workflow_with_bibsched.get_description(bwo)

    workflow = [
        write_something_generic("Initialisation", [task_update_progress,
                                                   write_message]),
        init_harvesting,
        write_something_generic("Starting", [task_update_progress,
                                             write_message]),
        foreach(get_repositories_list(), "_repository"),
        [
            write_something_generic("Harvesting", [task_update_progress,
                                                   write_message]),
            harvest_records,
            write_something_generic("Reading Files", [task_update_progress,
                                                      write_message]),
            foreach(get_obj_extra_data_key("harvested_files_list")),
            [
                write_something_generic("Creating Workflows",
                                        [task_update_progress, write_message]),
                foreach(get_records_from_file()),
                [
                    workflow_if(filtering_oai_pmh_identifier),
                    [
                        workflow_if(num_workflow_running_greater(10), neg=True),
                        [
                            start_workflow("full_doc_process"),

                            write_something_generic(
                                ["Workflow started: ",
                                 get_nb_workflow_created],
                                [task_update_progress,
                                 write_message]),
                        ],
                        workflow_else,
                        [
                            write_something_generic(
                                ["Max simultaneous workflows reached: ",
                                 "Waiting for one to finish"],
                                [task_update_progress,
                                 write_message]),
                            wait_for_a_workflow_to_complete(0.05),
                            start_workflow("full_doc_process", None),
                            write_something_generic(["Workflow started :",
                                                     get_nb_workflow_created,
                                                     " "],
                                                    [task_update_progress,
                                                     write_message]),
                        ],
                    ],
                ],
                end_for
            ],
            end_for
        ],
        end_for,
        write_something_generic(["Processing : ", get_nb_workflow_created,
                                 " records"],
                                [task_update_progress, write_message]),
        simple_for(0, get_nb_workflow_created, 1),
        [
            wait_for_a_workflow_to_complete(0.05),
            write_something_generic([get_workflows_progress, " % Complete"],
                                    [task_update_progress, write_message]),
        ],
        end_for,
        write_something_generic("Finishing", [task_update_progress,
                                              write_message]),
        workflows_reviews(stop_if_error=True),
        update_last_update(get_repositories_list())
    ]
