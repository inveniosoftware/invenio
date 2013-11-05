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
from invenio.base.i18n import _
from invenio.modules.knowledge.api import get_kb_mappings
from invenio.utils.forms import InvenioBaseForm, AutocompleteField, \
    RowWidget
from wtforms import TextField
from wtforms import FormField, SelectField, SelectMultipleField
from wtforms import Form as WTFormDefault
from wtforms.ext.sqlalchemy.fields import QuerySelectField


class JournalForm(WTFormDefault):
    name = QuerySelectField(
        '',
        get_pk=lambda i: i['key'],
        get_label=lambda i: i['value'],
        query_factory=lambda: [{'key': '', 'value': _('Any journal')}] +
                              get_kb_mappings('EJOURNALS'))
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
    journal = FormField(JournalForm, widget=RowWidget(
        classes={0:'col-xs-6', 1:'col-xs-3', 2: 'col-xs-3'}))


class GetCollections(object):
    def __iter__(self):
        from invenio.modules.search.models import Collection
        collections = Collection.query.all()

        for coll in collections:
            if not coll.is_restricted:
                yield (coll.name, coll.name_ln)


class WebSearchUserSettingsForm(InvenioBaseForm):
    rg = SelectField(_('Results per page'),
                    choices=[('10', '10'), ('25', '25'), ('50', '50'), ('100', '100')])
    websearch_hotkeys = SelectField(_('Hotkeys'), choices=[('0', _('Disable')),
                                                           ('1', _('Enable'))])

    c = SelectMultipleField(_('Collections'), choices=GetCollections())
