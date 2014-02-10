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
from invenio.base.i18n import _
from invenio.modules.deposit.form import WebDepositForm
from ..field_widgets import date_widget, plupload_widget, \
    ExtendedListWidget, ListItemWidget, ckeditor_widget, TagInput, \
    TagListWidget
from invenio.modules.deposit import fields

__all__ = ['ArticleForm']


def keywords_autocomplete(form, field, term, limit=50):
    return ["Keyword 1", "Keyword 2"]


class AuthorForm(WebDepositForm):

    name = fields.TextField(
        placeholder="Family name, First name",
        widget_classes='form-control right-not-rounded',
    )

    affiliation = fields.TextField(
        placeholder="Affiliation",
        widget_classes='form-control left-not-rounded',
    )


class ArticleForm(WebDepositForm):

    doi = fields.DOIField(label=_('DOI'), export_key='publication_info.DOI')
    publisher = fields.PublisherField(label=_('Publisher'),
                                      validators=[Required()],
                                      export_key='imprint.publisher_name')
    journal = fields.JournalField(label=_('Journal Title'),
                                  validators=[Required()])
    issn = fields.ISSNField(label=_('ISSN'), export_key='issn')
    title = fields.TitleField(label=_('Document Title'),
                              export_key='title.title')

    abstract = fields.AbstractField(
        label=_('Abstract'),
        export_key='abstract.summary',
        widget=ckeditor_widget,
    )
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
                       export_key='imprint.date')

    authors = fields.DynamicFieldList(
        fields.FormField(
            AuthorForm,
            widget=ExtendedListWidget(
                item_widget=ListItemWidget(with_label=False, class_="col-sm-6 col-xs-6 no-padding"),
                class_='collection-item list-unstyled',
            ),
        ),
        label='Authors',
        add_label='Add another author',
        icon='user',
        min_entries=1,
        export_key='authors'
    )

    keywords = fields.DynamicFieldList(
        fields.TextField(
            placeholder="Start typing a keyword...",
            autocomplete=keywords_autocomplete,
            widget_classes="form-control",
        ),
        label='Keywords',
        add_label='Add another keyword',
        icon='tags',
        min_entries=1,
        export_key='keywords'
    )
    notes = fields.NotesField(label=_('Notes'), export_key='comment')
    plupload_file = fields.FileUploadField(widget=plupload_widget, label="")

    """ Form Configuration variables """
    _title = _('Submit an Article')
    _subtitle = 'Instructions: (i) Press "Save" to save your upload for '\
                'editing later, as many times you like. (ii) Upload or remove'\
                ' extra files in the bottom of the form. (iii) When ready, '\
                'press "Submit" to finalize your upload.'
    _drafting = True   # enable and disable drafting

    # Group fields in categories

    groups = [
        ('Publisher/Journal',
            ['doi', 'publisher', 'journal', 'issn'],
            {'description': "Publisher and Journal fields are required.",
             'indication': 'required'}),
        ('Basic Information',
            ['title', 'authors', 'abstract', 'pagesnum']),
        ('Other', ['language', 'date', 'keywords', 'notes'])
    ]
