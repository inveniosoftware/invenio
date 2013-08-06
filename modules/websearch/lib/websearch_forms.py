# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011 CERN.
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

"""WebMessage Forms"""

from flask import url_for
from invenio.webinterface_handler_flask_utils import _
from invenio.bibknowledge import get_kb_mappings
from invenio.wtforms_utils import InvenioBaseForm, AutocompleteField, \
                    RowWidget
from wtforms import TextField
from wtforms import FormField, SelectField
from wtforms import Form as WTFormDefault
from wtforms.ext.sqlalchemy.fields import QuerySelectField, \
    QuerySelectMultipleField


class JournalForm(WTFormDefault):
    name = QuerySelectField('',
            get_pk=lambda i: i['key'],
            get_label=lambda i: i['value'],
            query_factory=lambda: [{'key':'', 'value':_('Any journal')}] + get_kb_mappings('EJOURNALS'))
    vol = TextField(_('Vol'))
    page = TextField(_('Pg'))


class EasySearchForm(InvenioBaseForm):
    """Defines form for easy seach popup."""
    author = AutocompleteField(_('Author'), data_provide="typeahead-url",
        data_source=lambda: url_for('search.autocomplete', field='exactauthor'))
    title = TextField(_('Title'))
    rn = AutocompleteField(_('Report number'), data_provide="typeahead-url",
        data_source=lambda: url_for('search.autocomplete', field='reportnumber'))
    aff = AutocompleteField(_('Affiliation'), data_provide="typeahead-url",
        data_source=lambda: url_for('search.autocomplete', field='affiliation'))
    cn = AutocompleteField(_('Collaboration'), data_provide="typeahead-url",
        data_source=lambda: url_for('search.autocomplete', field='collaboration'))
    k = AutocompleteField(_('Keywords'), data_provide="typeahead-url",
        data_source=lambda: url_for('search.autocomplete', field='keyword'))
    journal = FormField(JournalForm, widget=RowWidget())


def get_collection():
    from invenio.websearch_model import Collection
    collections = Collection.query.all()
    return [coll for coll in collections if not coll.is_restricted]


class WebSearchUserSettingsForm(InvenioBaseForm):
    rg = SelectField(_('Results per page'),
                    choices=[('10', '10'), ('25', '25'), ('50', '50'), ('100', '100')])
    websearch_hotkeys = SelectField(_('Hotkeys'), choices=[('0', _('Disable')),
                                                           ('1', _('Enable'))])
    c = QuerySelectMultipleField(_('Collections'), query_factory=get_collection,
                                 get_pk=lambda c: c.name,
                                 get_label=lambda c: c.name_ln)
