from invenio.webdeposit_load_forms import forms
from invenio.webdeposit_workflow_utils import authorize_user, \
                                              render_form, \
                                              wait_for_submission

__all__ = ['Article']


ArticleForm = forms['ArticleForm']
PhotoForm = forms['PhotoForm']

dep_type = "Article"
wf = [authorize_user(), \
      render_form(ArticleForm),
      wait_for_submission(),
      render_form(PhotoForm),
      wait_for_submission()]

# form = get_metadata_creation_form_from_doctype(doc_type)  # # This will use BibField to create a simple form which is the concatenation of all the fields neeeded for doc_type "Article"

Article = {"dep_type": dep_type, \
           "workflow": wf}


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
