from invenio.webdeposit_load_forms import forms

__all__ = ['Photo']

PhotoForm = forms['PhotoForm']

dep_type = "Photo"
wf = [authorize_user(), \
      render_form(PhotoForm),
      wait_for_submission()]

Photo = {"dep_type": dep_type, \
         "workflow": wf}
