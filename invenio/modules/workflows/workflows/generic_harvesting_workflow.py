# -*- coding: utf-8 -*-
## This file is part of Invenio.
## Copyright (C) 2013, 2014 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of t
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

"""Implements an example of a typical ingestion workflow for MARCXML records"""

from ..tasks.marcxml_tasks import (get_repositories_list, harvest_records,
                                   get_records_from_file, update_last_update,
                                   get_obj_extra_data_key, init_harvesting,
                                   filtering_oai_pmh_identifier)

from ..tasks.workflows_tasks import (start_workflow, workflows_reviews,
                                     get_nb_workflow_created,
                                     num_workflow_running_greater,
                                     wait_for_a_workflow_to_complete)

from ..tasks.logic_tasks import (foreach, end_for, workflow_if, workflow_else,
                                 simple_for)

from invenio.modules.workflows.utils import WorkflowBase


class generic_harvesting_workflow(WorkflowBase):

    object_type = "Supervising Workflow"

    @staticmethod
    def get_description(bwo):
        from flask import render_template

        identifiers = None

        extra_data = bwo.get_extra_data()
        if 'options' in extra_data and 'identifiers' in extra_data["options"]:
            identifiers = extra_data["options"]["identifiers"]

        if '_task_results' in extra_data and '_workflows_reviews' in extra_data['_task_results']:
            result_temp = bwo.get_tasks_results()
            result_temp = result_temp['_workflows_reviews'][0]['result']
            result_progress = {
                'success': (result_temp['total'] - result_temp['failed']),
                'failed': result_temp['failed'],
                'success_per': ((result_temp['total'] - result_temp['failed'])
                                * 100 / result_temp['total']),
                'failed_per': result_temp['failed'] * 100 / result_temp[
                    'total'],
                'total': result_temp['total']}
        else:
            result_progress = {'success_per': 0, 'failed_per': 0, 'success': 0, 'failed': 0, 'total': 0}

        current_task = extra_data['_last_task_name']

        render_template("workflows/styles/harvesting_description.html",
                        identifiers=identifiers,
                        result_progress=result_progress,
                        current_task=current_task)

    @staticmethod
    def get_title(bwo):
        return "Supervising harvesting of {0}".format(
            bwo.get_extra_data()["_repository"]["name"])

    @staticmethod
    def formatter(bwo, **kwargs):
        return ""

    workflow = [
        init_harvesting,
        foreach(get_repositories_list(), "repository"),
        [
            harvest_records,
            foreach(get_obj_extra_data_key("harvested_files_list")),
            [
                foreach(get_records_from_file()),
                [
                    workflow_if(filtering_oai_pmh_identifier),
                    [
                        workflow_if(num_workflow_running_greater(10),
                                    neg=True),
                        [
                            start_workflow("full_doc_process", None),
                        ],
                        workflow_else,
                        [
                            wait_for_a_workflow_to_complete,
                            start_workflow("full_doc_process", None),
                        ],
                    ],
                ],
                end_for
            ],
            end_for
        ],
        end_for,
        simple_for(0, get_nb_workflow_created, 1),
        [
            wait_for_a_workflow_to_complete,
        ],
        end_for,
        workflows_reviews(stop_if_error=True),
        update_last_update(get_repositories_list(['arxivb']))
    ]
