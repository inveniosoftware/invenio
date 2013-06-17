# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA

from wtforms.validators import Required
from invenio.config import CFG_SITE_SUPPORT_EMAIL
from invenio.webinterface_handler_flask_utils import _
from invenio.webdeposit_form import WebDepositForm as Form
from invenio.webdeposit_field_widgets import date_widget, plupload_widget, \
                                             bootstrap_submit
from invenio.webdeposit_load_fields import fields
__all__ = ['ArticleForm']


class ArticleForm(Form):

    doi = fields.DOIField(label=_('DOI'), recjson_key='publication_info.DOI')
    publisher = fields.PublisherField(label=_('Publisher'),
                                      validators=[Required()],
                                      recjson_key='imprint.publisher_name')
    journal = fields.JournalField(label=_('Journal Title'),
                                  validators=[Required()])
    issn = fields.ISSNField(label=_('ISSN'), recjson_key='issn')
    title = fields.TitleField(label=_('Document Title'),
                              recjson_key='title.title')
    author = fields.AuthorField(label=_('Author'),
                                recjson_key='authors[0].full_name')
    abstract = fields.AbstractField(label=_('Abstract'),
                                    recjson_key='abstract.summary')
    pagesnum = fields.PagesNumberField(label=_('Number of Pages'))
    languages = [("en", _("English")),
                 ("fre", _("French")),
                 ("ger", _("German")),
                 ("dut", _("Dutch")),
                 ("ita", _("Italian")),
                 ("spa", _("Spanish")),
                 ("por", _("Portuguese")),
                 ("gre", _("Greek")),
                 ("slo", _("Slovak")),
                 ("cze", _("Czech")),
                 ("hun", _("Hungarian")),
                 ("pol", _("Polish")),
                 ("nor", _("Norwegian")),
                 ("swe", _("Swedish")),
                 ("fin", _("Finnish")),
                 ("rus", _("Russian"))]
    language = fields.LanguageField(label=_('Language'), choices=languages)
    date = fields.Date(label=_('Date of Document'), widget=date_widget,
                       recjson_key='imprint.date')
    keywords = fields.KeywordsField(label=_('Keywords'))
    notes = fields.NotesField(label=_('Notes'), recjson_key='comment')
    plupload_file = fields.FileUploadField(widget=plupload_widget)
    submit = fields.SubmitField(label=_('Submit Article'),
                                widget=bootstrap_submit)

    """ Form Configuration variables """
    _title = _('Submit an Article')
    _subtitle = 'Instructions: (i) Press "Save" to save your upload for editing'\
                'later, as many times you like. (ii) Upload and remove extra files in the'\
                'bottom of the form. (iii) When ready, press "Submit" to finalize and make'\
                'your upload public (editing afterwards only possible via submitting changes'\
                'to <a class="muted"'\
                'href="mailto:' + CFG_SITE_SUPPORT_EMAIL + '">' +\
                CFG_SITE_SUPPORT_EMAIL+'</a>).'
    _drafting = True   # enable and disable drafting

    # Group fields in categories

    groups = [
        ('Publisher/Journal',
            ['doi', 'publisher', 'journal', 'issn'],
            {'description': "Publisher and Journal fields are required.",
             'indication': 'required'}),
        ('Basic Information',
            ['title', 'author', 'abstract', 'pagesnum']),
        ('Other', ['language', 'date', 'keywords', 'notes'])
    ]
