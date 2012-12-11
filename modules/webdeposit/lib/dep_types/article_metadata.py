from invenio.webdeposit_load_forms import forms
globals().update(forms)

__all__ = ['Article']

dep_type = "Article"
form = ArticleForm
# form = get_metadata_creation_form_from_doctype(doc_type)  # # This will use BibField to create a simple form which is the concatenation of all the fields neeeded for doc_type "Article"

Article = {"form": form, \
           "dep_type": dep_type}

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
