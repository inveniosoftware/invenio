# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012, 2013 CERN.
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
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from invenio.webdeposit_load_forms import forms
from invenio.bibworkflow_utils import authorize_user, \
                                              render_form, \
                                              wait_for_submission

__all__ = ['Article']


ArticleForm = forms['ArticleForm']
PhotoForm = forms['PhotoForm']

dep_type = "Article"
plural = "Articles"
group = "Articles & Preprints"
wf = [authorize_user(),
      render_form(ArticleForm),
      wait_for_submission()]

# form = get_metadata_creation_form_from_doctype(doc_type)  # # This will use BibField to create a simple form which is the concatenation of all the fields neeeded for doc_type "Article"

Article = {"dep_type": dep_type,
           "workflow": wf,
           "plural": plural,
           "group": group,
           "enabled": True}


"""
Workflow definition sample
wf = [
      set_status(form),  # # This load the WTForm ArticleForm
      reserve_recid,  # # This reserve a recid for the created record
      create_record(doc_type),  # # This uses BibField to transform the JSON into MARC using the Article doctype
      insert_record,  # # This insert the created record
      set_status(ApprovalWaitingForm("Article")),
      if_else(check_approval_result),
      [approve_record("ARTICLE"),
       send_confirmation_email("approved")
      ],
      [reject_record,
       send_confirmation_email("rejected")
      ]
     ]
"""
