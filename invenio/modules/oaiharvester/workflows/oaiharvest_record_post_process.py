# -*- coding: utf-8 -*-
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

"""Generic record process in harvesting with backwards compatibility."""

from invenio.modules.workflows.definitions import RecordWorkflow
from invenio.modules.workflows.tasks.logic_tasks import workflow_if
from invenio.modules.workflows.tasks.marcxml_tasks import (
    convert_record_to_bibfield,
)
from ..tasks.postprocess import (
    arxiv_fulltext_download,
    author_list,
    check_record,
    convert_record_with_repository,
    filter_step,
    plot_extract,
    post_process_selected,
    refextract,
    upload_step,
)


class oaiharvest_record_post_process(RecordWorkflow):

    """Workflow run for each record OAI harvested."""

    object_type = "OAI harvest"

    workflow = [
        workflow_if(post_process_selected("c")),
        [
            convert_record_with_repository(),
            check_record,
            convert_record_to_bibfield(),
        ],
        workflow_if(post_process_selected("t")),
        [
            arxiv_fulltext_download,
        ],
        workflow_if(post_process_selected("p")),
        [
            plot_extract(),
        ],
        workflow_if(post_process_selected("a")),
        [
            author_list,
        ],
        workflow_if(post_process_selected("r")),
        [
            refextract,
        ],
        workflow_if(post_process_selected("f")),
        [
            filter_step,
        ],
        workflow_if(post_process_selected("u")),
        [
            upload_step,
        ],
    ]
