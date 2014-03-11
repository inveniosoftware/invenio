# -*- coding: utf-8 -*-
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
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

from ..tasks.marcxml_tasks import (get_repositories_list,
                                   init_harvesting,
                                   harvest_records,
                                   get_files_list,
                                   get_eng_uuid_harvested,
                                   get_records_from_file,
                                   get_obj_extra_data_key, filtering_oai_pmh_identifier, update_last_update)

from ..tasks.workflows_tasks import (start_workflow,
                                     wait_for_workflows_to_complete,
                                     workflows_reviews,
                                     get_nb_workflow_created,
                                     num_workflow_running_greater, wait_for_a_workflow_to_complete)

from ..tasks.logic_tasks import (foreach,
                                 end_for,
                                 workflow_if, workflow_else, simple_for)


class generic_harvesting_workflow(object):

    object_type = "harvest"
    workflow = [
        init_harvesting,
        foreach(get_repositories_list(['arxivb']), "repository"),
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
