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
                                   get_records_from_file
                                   )

from ..tasks.workflows_tasks import (start_workflow,
                                     wait_for_a_workflow_to_complete,
                                     workflows_reviews,
                                     get_nb_workflow_created,
                                     get_list_of_workflows_to_wait,
                                     get_workflows_progress
                                     )

from ..tasks.logic_tasks import (foreach,
                                 end_for,
                                 simple_for
                                 )

from ..tasks.bibsched_tasks import (write_something_bibsched,
                                    write_something_generic
                                    )

from invenio.legacy.bibsched.bibtask import task_update_progress


from invenio.base.config import CFG_TMPSHAREDDIR

class generic_harvesting_workflow_with_bibsched(object):
    workflow = [write_something_generic("Initialisation",task_update_progress),
                init_harvesting,
                write_something_generic("Starting", task_update_progress),
                foreach(get_repositories_list(['arxiv']), "repository"),
                [
                    harvest_records,
                    foreach(get_files_list(CFG_TMPSHAREDDIR, get_eng_uuid_harvested)),
                    [
                        foreach(get_records_from_file()),
                        [
                            start_workflow("full_doc_process", None),
                            write_something_bibsched(["Workflow started : ", get_nb_workflow_created, " "]),
                        ],
                        end_for
                    ],
                    end_for
                ],
                end_for,
                write_something_bibsched("waiting workflows"),
                write_something_generic(["Processing : ", get_nb_workflow_created, " records"], task_update_progress),
                simple_for(0, get_nb_workflow_created, 1),
                [
                    wait_for_a_workflow_to_complete,
                    write_something_bibsched([get_workflows_progress, "%% Complete"]),
                    write_something_generic([get_workflows_progress, "%% Complete"], task_update_progress),
                ],
                end_for,
                write_something_bibsched("the end"),
                write_something_generic("Finishing", task_update_progress),
                workflows_reviews
    ]

