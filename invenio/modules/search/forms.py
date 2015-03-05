# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2014, 2015 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""WebMessage Forms."""

from flask import url_for
from six import iteritems

from invenio.base.i18n import _
from invenio.modules.knowledge.api import get_kb_mappings
from invenio.utils.forms import AutocompleteField, InvenioBaseForm, \
    RowWidget

from werkzeug.local import LocalProxy

from wtforms import Form as WTFormDefault, FormField, SelectField, \
    SelectMultipleField, StringField


class JournalForm(WTFormDefault):

    """Journal Form."""

    name = SelectField(
        label='',
        choices=LocalProxy(
            lambda:
            [('', _('Any journal'))] +
            [(kb['key'], kb['value']) for kb in get_kb_mappings('EJOURNALS')]),
        coerce=unicode,
    )
    vol = StringField(_('Vol'))
    page = StringField(_('Pg'))


class EasySearchForm(InvenioBaseForm):

    """Defines form for easy seach popup."""

    author = AutocompleteField(_('Author'), data_provide="typeahead-url",
                               data_source=lambda:
                               url_for('search.autocomplete',
                                       field='exactauthor'))
    title = StringField(_('Title'))
    rn = AutocompleteField(_('Report number'), data_provide="typeahead-url",
                           data_source=lambda: url_for('search.autocomplete',
                                                       field='reportnumber'))
    aff = AutocompleteField(_('Affiliation'), data_provide="typeahead-url",
                            data_source=lambda: url_for('search.autocomplete',
                                                        field='affiliation'))
    cn = AutocompleteField(_('Collaboration'), data_provide="typeahead-url",
                           data_source=lambda: url_for('search.autocomplete',
                                                       field='collaboration'))
    k = AutocompleteField(_('Keywords'), data_provide="typeahead-url",
                          data_source=lambda: url_for('search.autocomplete',
                                                      field='keyword'))
    journal = FormField(JournalForm, widget=RowWidget(
        classes={0: 'col-xs-6', 1: 'col-xs-3', 2: 'col-xs-3'}))


class GetCollections(object):

    """Get all collections."""

    def __iter__(self):
        """Get all the collections."""
        from invenio.modules.collections.models import Collection
        collections = Collection.query.all()

        for coll in collections:
            if not coll.is_restricted:
                yield (coll.name, coll.name_ln)


class GetOutputFormats(object):

    """Collection output formats."""

    def __iter__(self):
        """Get all the output formats."""
        from invenio.modules.formatter import registry

        yield ('', _('Default'))
        for code, format_ in iteritems(registry.output_formats):
            yield (code, format_['name'])


class WebSearchUserSettingsForm(InvenioBaseForm):

    """User settings for search."""

    rg = SelectField(_('Results per page'),
                     choices=[('10', '10'), ('25', '25'), ('50', '50'),
                              ('100', '100')])
    websearch_hotkeys = SelectField(_('Hotkeys'), choices=[('0', _('Disable')),
                                                           ('1', _('Enable'))])

    c = SelectMultipleField(_('Collections'), choices=GetCollections())
    of = SelectField(_('Personal output format'), choices=GetOutputFormats())
