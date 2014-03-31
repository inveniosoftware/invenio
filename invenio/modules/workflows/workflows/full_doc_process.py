# -*- coding: utf-8 -*-
## This file is part of Invenio.
## Copyright (C) 2013,2014 CERN.
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

from ..tasks.marcxml_tasks import (convert_record_with_repository,
                                   plot_extract,
                                   convert_record_to_bibfield,
                                   fulltext_download,
                                   refextract,
                                   author_list,
                                   upload_step,
                                   quick_match_record,
                                   inspire_filter_custom,
                                   bibclassify
                                   )

from ..tasks.workflows_tasks import (log_info)

from ..tasks.logic_tasks import (workflow_if,
                                 workflow_else
                                 )
from invenio.config import CFG_PREFIX


class full_doc_process(object):
    object_type = "record"
    workflow = [convert_record_with_repository("oaiarxiv2marcxml.xsl"), convert_record_to_bibfield,
                workflow_if(quick_match_record, True),
                [
                    plot_extract(["latex"]),
                    fulltext_download,
                    inspire_filter_custom(fields=["report_number", "arxiv_category"], custom_accepted=["*"],
                                          custom_refused="gr-qc", widget="approval_widget"),
                    bibclassify(taxonomy=CFG_PREFIX + "/etc/bibclassify/HEP.rdf",
                                output_mode="dict", match_mode="partial"),
                    refextract, author_list,
                    upload_step,
                ],
                workflow_else,
                [
                    log_info("Record already into database"),
                ],
                ]
