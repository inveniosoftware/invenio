# -*- coding: utf-8 -*-
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

""" Generic record process in harvesting."""

from ..tasks.marcxml_tasks import (convert_record_with_repository,
                                   convert_record_to_bibfield,
                                   quick_match_record, upload_step,
                                   approve_record)
from ..tasks.workflows_tasks import log_info
from ..tasks.logic_tasks import workflow_if, workflow_else
from invenio.config import CFG_PREFIX


class full_doc_process(object):
    object_type = "record"
    workflow = [
        convert_record_with_repository("oaiarxiv2marcxml.xsl"),
        convert_record_to_bibfield,
        workflow_if(quick_match_record, True),
        [
            approve_record,
            upload_step,
        ],
        workflow_else,
        [
            log_info("Record already into database"),
        ],
    ]
