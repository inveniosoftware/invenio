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


from ..tasks.marcxml_tasks import (convert_record,
                                   plot_extract,
                                   convert_record_to_bibfield,
                                   fulltext_download,
                                   refextract,
                                   author_list,
                                   upload_step,
                                   quick_match_record
                                   )

from ..tasks.workflows_tasks import log_info

from workflow.patterns import IF_ELSE


class full_doc_process(object):
    workflow = [convert_record("oaiarxiv2marcxml.xsl"), convert_record_to_bibfield,
                IF_ELSE(quick_match_record, [log_info("branch two")], [log_info("branch one"), plot_extract(["latex"]),
                                                                       fulltext_download, refextract, author_list,
                                                                       upload_step]),
                log_info("branch end")
    ]
    #workflow =[convert_record("oaiarxiv2marcxml.xsl"), convert_record_to_bibfield, author_list, upload_step]

