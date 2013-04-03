# -*- coding: utf-8 -*-
# #
# # This file is part of Invenio.
# # Copyright (C) 2013 CERN.
# #
# # Invenio is free software; you can redistribute it and/or
# # modify it under the terms of the GNU General Public License as
# # published by the Free Software Foundation; either version 2 of the
# # License, or (at your option) any later version.
# #
# # Invenio is distributed in the hope that it will be useful, but
# # WITHOUT ANY WARRANTY; without even the implied warranty of
# # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# # General Public License for more details.
# #
# # You should have received a copy of the GNU General Public License
# # along with Invenio; if not, write to the Free Software Foundation, Inc.,
# # 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA

from wtforms import SelectField, SubmitField
from wtforms.validators import Required
from invenio.webdeposit_form import WebDepositForm as Form
from invenio.webinterface_handler_flask_utils import _
from invenio.webdeposit_field_widgets import date_widget, plupload_widget, bootstrap_submit

# Import custom fields
from invenio.webdeposit_load_fields import fields
__all__ = ['ThesisForm']


class ThesisForm(Form):

    title = fields.TitleField(label=_('Original Thesis Title'),
                              validators=[Required()])
    subtitle = fields.TitleField(label=_('Original Thesis Subtitle'))
    alternative_title = fields.TitleField(label=_('Alternative Title'))
    author = fields.AuthorField(label=_('Author'))
    supervisor = fields.AuthorField(label=_('Thesis Supervisor'))
    abstract = fields.AbstractField(label=_('Abstract'))
    subject = fields.TitleField(label=_('Subject'))

    languages = [("en", _("English")), \
                ("fre", _("French")), \
                ("ger", _("German")), \
                ("dut", _("Dutch")), \
                ("ita", _("Italian")), \
                ("spa", _("Spanish")), \
                ("por", _("Portuguese")), \
                ("gre", _("Greek")), \
                ("slo", _("Slovak")), \
                ("cze", _("Czech")), \
                ("hun", _("Hungarian")), \
                ("pol", _("Polish")), \
                ("nor", _("Norwegian")), \
                ("swe", _("Swedish")), \
                ("fin", _("Finnish")), \
                ("rus", _("Russian"))]
    language = fields.LanguageField(label=_("Language"), choices=languages)
    publisher = fields.PublisherField(label=_('Thesis Publisher'))
    submission_date = fields.Date(label=_('Date of Submission'), widget=date_widget)
    defence_date = fields.Date(label=_('Date of Defence'), widget=date_widget)

    funded_choices = [("yes", _("Yes")), ("no", _("No"))]
    funded = SelectField(label=_("Has your thesis been funded by the CERN Doctoral Student Program?"),
                                  choices=funded_choices)

    file_field = fields.FileUploadField(label=_('File'), widget=plupload_widget)
    submit = SubmitField(label=_('Submit Thesis'), widget=bootstrap_submit)

    """ Form Configuration variables """
    _title = _("Submit a Thesis")
    _drafting = True  # enable and disable drafting
