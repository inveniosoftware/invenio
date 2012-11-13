import os
from wtforms import Form, \
                    TextField, \
                    DateField, \
                    FileField, \
                    SubmitField

from invenio.webinterface_handler_flask_utils import _
from invenio.webdeposit_load_fields import fields

globals().update(fields)
__all__ = ['PhotoForm']


class PhotoForm(Form):

    title = TitleField(_('Photo Title'))
    file = FileField(_('File'))
    submit = SubmitField()

    #configuration variables
    _title = _("Submit a Photo")
    _drafting = True #enable and disable drafting
