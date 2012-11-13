from invenio.webdeposit_load_forms import forms
globals().update(forms)

__all__ = ['Photo']

form = PhotoForm
doc_type = "Photo"

Photo = {"form" : form, \
         "doc_type" : doc_type
        }
