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
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from invenio.webinterface_handler_flask_utils import _


""" WebDeposit Configuration file

Define here validators and autocomplete functions for fields
to override the default ones.

The structure must be in dictionaries as follows:
Deposition name: Form type: 'fields': name of the field

deposition:
    collection:
        The collection that the deposition belongs.

form:
    title:
        string, the title to be shown to the user above the form.
    file_cook:
        define here a function if you want different handling in json's transformation
        for the files of the form.
    template:
        the template to be used for the form.
        if not defined, the default one is being used.

fields:
    label:
        string, the field's label
    validators:
        list with path strings to be imported with werkzeug's `import_string`.
        The validators of the field.
    autocomplete:
        path string to be imported with werkzeug's `import_string`.
        The function that autocompletes the field.
    recjson_key:
        the association with BibField. Define here a mapping with a BibField's field.
    widget:
        path string to be imported with werkzeug's `import_string`.
        WTField widget.

Deposition name: Form type: 'fields': name of the field
"""

config = {
    'Article': {
        'ArticleForm': {
            'fields': {
                'DOIField': {
                    'label': 'DOI',
                    'validators': ['invenio.webdeposit_validation_utils:datacite_doi_validate'],
                    'cook': 'invenio.webdeposit_cook_json_utils:cook_publication_doi'
                },
                'PublisherField': {
                    'label': 'Publisher',
                    'autocomplete': 'invenio.webdeposit_autocomplete_utils:sherpa_romeo_publishers',
                    'validators': ['invenio.webdeposit_validation_utils:sherpa_romeo_publisher_validate'],
                    'cook': 'invenio.webdeposit_cook_json_utils:cook_publisher_name'
                },
                'JournalField': {
                    'label': 'Journal Title',
                    'autocomplete': 'invenio.webdeposit_autocomplete_utils:sherpa_romeo_journals',
                    'validators': ['invenio.webdeposit_validation_utils:sherpa_romeo_journal_validate']
                },
                'ISSNField': {
                    'label': 'ISSN',
                    'validators': ['invenio.webdeposit_validation_utils:sherpa_romeo_issn_validate'],
                    'cook': 'invenio.webdeposit_cook_json_utils:cook_issn'
                },
                'TitleField': {
                    'label': 'Document Title',
                    'cook': 'invenio.webdeposit_cook_json_utils:cook_title'
                },
                'AuthorField': {
                    'label': 'Author',
                    'autocomplete': 'invenio.webdeposit_autocomplete_utils:orcid_authors',
                    'cook': 'invenio.webdeposit_cook_json_utils:cook_first_authors_full_name'
                },
                'AbstractField': {
                    'label': 'Abstract',
                    'cook': 'invenio.webdeposit_cook_json_utils:cook_abstract_summary'
                },
                'PagesNumberField': {
                    'label': 'Number of Pages',
                    'validators': ['invenio.webdeposit_validation_utils:number_validate']
                },
                'LanguageField': {
                    'label': 'Language',
                    'cook': 'invenio.webdeposit_cook_json_utils:cook_language'
                },
                'Date': {
                    'label': 'Date of Document',
                    'widget': 'invenio.webdeposit_field_widgets:date_widget',
                    'cook': 'invenio.webdeposit_cook_json_utils:cook_date'
                },
                'NotesField': {
                    'label': 'Notes or Comments',
                    'cook': 'invenio.webdeposit_cook_json_utils:cook_comment'
                },
                'KeywordsField': {
                    'label': 'Keywords'
                },
                'FileUploadField': {
                    'label': 'File',
                    'validators': ['invenio.webdeposit_validation_utils:number_validate'],
                    'widget': 'invenio.webdeposit_field_widgets:plupload_widget'
                },
                'SubmitField': {
                    # The submit field accepts only label and widget configuration
                    'label': 'Submit Article',
                    'widget': 'invenio.webdeposit_field_widgets:bootstrap_submit'
                }
            },
            'title': _('Submit an Article')
        },
        'collection': 'Article'
    },
    'Photo': {
        'PhotoForm': {
            'fields': {
                'NotesField': {
                    'cook': 'invenio.webdeposit_cook_json_utils:cook_comment'
                }
            },
            'file_cook': 'invenio.webdeposit_cook_json_utils:cook_picture'
        },
        'collection': 'Picture'
    }
}
