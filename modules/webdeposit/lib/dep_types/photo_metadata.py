from invenio.webdeposit_load_forms import forms
globals().update(forms)

__all__ = ['Photo']

form = PhotoForm
dep_type = "Photo"

Photo = {"form" : form, \
         "dep_type" : dep_type
        }
