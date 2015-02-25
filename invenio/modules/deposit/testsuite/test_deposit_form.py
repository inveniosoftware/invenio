# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014, 2015 CERN.
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

"""Unit tests for the WebDeposit Form """

import copy

from invenio.testsuite import InvenioTestCase, make_test_suite, run_test_suite


class WebDepositFormTest(InvenioTestCase):
    def setUp(self):
        from invenio.modules.deposit.form import WebDepositForm
        from invenio.modules.deposit import fields
        from werkzeug import MultiDict

        def reset_processor(form, field, submit=False, fields=None):
            if field.name == 'related_identifier-0-scheme':
                if fields and 'related_identifier-0-scheme' in fields:
                    field.data = 'RESET TEST FIELDS'
                    return

            field.data = 'RESET'

        def dummy_autocomplete(form, field, term, limit=50):
            if term == 'test':
                return map(
                    lambda x: field.name + '-' + str(x),
                    range(0, 100)
                )[:limit]
            return []

        class IdentifierTestForm(WebDepositForm):
            scheme = fields.StringField(
                processors=[reset_processor],
                autocomplete_fn=dummy_autocomplete,
            )
            identifier = fields.StringField()

            def post_process_identifier(self, form, field, submit=False,
                                        fields=None):
                form.scheme.data = field.data

        class TestForm(WebDepositForm):
            title = fields.StringField(
                processors=[reset_processor],
                autocomplete_fn=dummy_autocomplete,
            )
            subtitle = fields.StringField()
            related_identifier = fields.DynamicFieldList(
                fields.FormField(IdentifierTestForm)
            )
            keywords = fields.DynamicFieldList(fields.StringField())

        self.form_class = TestForm

        self._form_data = MultiDict({
            'title': 'my title',
            'subtitle': 'my subtitle',
            'related_identifier-0-scheme': 'doi',
            'related_identifier-0-identifier': '10.1234/1',
            'related_identifier-1-scheme': 'orcid',
            'related_identifier-1-identifier': '10.1234/2',
            'keywords-0': 'kw1',
            'keywords-1': 'kw2',
        })

        self._object_data = {
            'title': 'my title',
            'subtitle': 'my subtitle',
            'related_identifier': [
                {'scheme': 'doi', 'identifier': '10.1234/1', },
                {'scheme': 'orcid', 'identifier': '10.1234/2'},
            ],
            'keywords': ['kw1', 'kw2'],
        }

    def multidict(self, d):
        from werkzeug import MultiDict
        return MultiDict(d)

    @property
    def object_data(self):
        return copy.deepcopy(self._object_data)

    @property
    def form_data(self):
        return copy.deepcopy(self._form_data)

    def test_autocomplete_routing(self):
        form = self.form_class()

        self.assertEqual(
            form.autocomplete('title', 'Nothing', limit=3),
            []
        )
        self.assertEqual(
            form.autocomplete('title', 'test', limit=3),
            ['title-0', 'title-1', 'title-2']
        )
        self.assertEqual(
            len(form.autocomplete('title', 'test', limit=51)),
            51
        )
        self.assertEqual(
            len(form.autocomplete('title', 'test', limit=200)),
            100
        )
        self.assertEqual(
            form.autocomplete('unexistingfield', 'test', limit=3),
            None
        )
        self.assertEqual(
            form.autocomplete('related_identifier-0-scheme', 'test', limit=2),
            ['related_identifier-0-scheme-0',
             'related_identifier-0-scheme-1', ]
        )

    def test_loading_objectdata(self):
        form = self.form_class(**self.object_data)
        self.assertEqual(form.data, self.object_data)

    def test_getting_jsondata(self):
        from invenio.modules.deposit import fields
        from invenio.modules.deposit.form import WebDepositForm
        from datetime import date

        class RelatedDatesForm(WebDepositForm):
            date = fields.Date()

        class TestForm(WebDepositForm):
            dates = fields.DynamicFieldList(
                fields.FormField(RelatedDatesForm)
            )

        object_data = {'dates': [
            {'date': date(2002, 1, 1)},
            {'date': date(2013, 1, 1)},
        ]}
        json_data = {'dates': [
            {'date': '2002-01-01'},
            {'date': '2013-01-01'},
        ]}

        form = TestForm(
            formdata=self.multidict({
                'dates-0-date': '2002-01-01',
                'dates-1-date': '2013-01-01',
            })
        )

        self.assertEqual(form.data, object_data)
        self.assertEqual(form.json_data, json_data)

    def test_loading_jsondata(self):
        # For field enclosures values may also be sent as a json structure
        form = self.form_class(formdata=self.multidict(self.object_data))
        self.assertEqual(form.data, self.object_data)
        self.assertTrue(form.validate())

    # Skip test due to changed API
    # def test_loading_invalid_jsondata(self):
    #     data = self.object_data
    #     data['unknownkey'] = "Test"
    #     # For field enclosures values may also be sent as a json structure
    #     form = self.form_class(formdata=self.multidict(data))
    #     self.assertFalse(form.validate())

    def test_loading_formdata(self):
        form = self.form_class(formdata=self.form_data)
        self.assertEqual(form.data, self.object_data)

        # Form data fields not specified is assumed by
        # WTForms to be empty, and will overwrite
        # object data.
        modified_data = self.object_data
        modified_data['title'] += "a"
        modified_data['subtitle'] += "a"
        modified_data['related_identifier'][0]['scheme'] += "a"
        modified_data['related_identifier'][1]['scheme'] += "a"

        modified_formdata = self.form_data
        del modified_formdata['subtitle']

        expected_data = self.object_data
        expected_data['subtitle'] = u''

        form = self.form_class(formdata=modified_formdata, **modified_data)
        self.assertEqual(form.data, expected_data)

    def test_update_list_element(self):
        new_title = 'new title'
        new_scheme = 'new scheme'

        expected_data = self.object_data
        expected_data['title'] = new_title
        expected_data['related_identifier'][1]['scheme'] = new_scheme

        formdata = self.multidict({
            'title': new_title,
            'related_identifier-1-scheme': new_scheme,
        })

        form = self.form_class(formdata=formdata, **self.object_data)
        form.reset_field_data(exclude=formdata.keys())

        self.assertEqual(form.data, expected_data)

    def test_add_list_element(self):
        new_title = 'new title'
        new_scheme = 'new scheme'

        expected_data = self.object_data
        expected_data['title'] = new_title
        expected_data['related_identifier'].append({'scheme': None,
                                                    'identifier': None})
        expected_data['related_identifier'].append({'scheme': new_scheme,
                                                    'identifier': None})

        formdata = self.multidict({
            'title': new_title,
            'related_identifier-3-scheme': new_scheme,
        })

        form = self.form_class(formdata=formdata, **self.object_data)
        form.reset_field_data(exclude=formdata.keys())

        self.assertEqual(form.data, expected_data)

    def test_new_list_element(self):
        new_title = 'new title'
        new_list = [
            {'scheme': 'a', 'identifier': 'a'},
            {'scheme': 'b', 'identifier': 'b'}
        ]

        expected_data = self.object_data
        expected_data['title'] = new_title
        expected_data['related_identifier'] = new_list

        formdata = self.multidict({
            'title': new_title,
            'related_identifier': new_list,
        })

        form = self.form_class(formdata=formdata, **self.object_data)
        form.reset_field_data(exclude=formdata.keys())

        self.assertEqual(form.data, expected_data)

    def test_extract_indices(self):
        formdata = self.multidict({
            'related_identifier-1-scheme': '',
            'related_identifier-1-name': '',
            'related_identifier-4-name': '',
            'related_identifier-0': '',
            'related_identifier-0-name-3;': '',
        })

        form = self.form_class()
        indices = sorted(set(form.related_identifier._extract_indices(
            form.related_identifier.name,
            formdata)
        ))

        self.assertEqual(indices, [0, 1, 4])

    def test_postprocess(self):
        form = self.form_class(formdata=self.form_data, **self.object_data)
        form.post_process()

        expected_data = self.object_data
        expected_data['title'] = "RESET"
        expected_data['related_identifier'][1]['scheme'] = \
            expected_data['related_identifier'][1]['identifier']
        expected_data['related_identifier'][0]['scheme'] = \
            expected_data['related_identifier'][0]['identifier']

        self.assertEqual(form.data, expected_data)

    def test_postprocess_exclude(self):
        form_data = self.multidict({
            'related_identifier-0-scheme': 'test'
        })

        form = self.form_class(formdata=form_data, **self.object_data)
        form.reset_field_data(exclude=form_data.keys())
        form.post_process(formfields=form_data.keys())

        expected_data = self.object_data
        expected_data['related_identifier'][0]['scheme'] = "RESET TEST FIELDS"
        self.assertEqual(form.data, expected_data)

    def test_flags(self):
        form = self.form_class(**self.object_data)
        form.subtitle.flags.hidden = True
        form.related_identifier.flags.hidden = True
        form.related_identifier[0].flags.hidden = True
        form.related_identifier[0].scheme.flags.hidden = True

        expected_flags = {
            'title': [],
            'subtitle': ['hidden'],
            'related_identifier': ['hidden'],
            'related_identifier-0': ['hidden'],
            'related_identifier-0-scheme': ['hidden'],
            'related_identifier-0-identifier': [],
            'related_identifier-1': [],
            'related_identifier-1-identifier': [],
            'related_identifier-1-scheme': [],
            'keywords': [],
            'keywords-0': [],
            'keywords-1': [],
        }

        self.assertEqual(
            form.get_flags(),
            expected_flags
        )

        form = self.form_class(**self.object_data)
        form.set_flags(copy.deepcopy(expected_flags))

        self.assertEqual(
            form.get_flags(),
            expected_flags
        )

    def test_messages(self):
        form = self.form_class(**self.object_data)
        form.title.add_message('t1', state='info')
        form.title.add_message('t2', state='warning')
        form.related_identifier.add_message('t3', state='warning')
        form.related_identifier[0].add_message('t4', state='warning')
        form.related_identifier[0]['scheme'].add_message('t5', state='warning')

        self.assertEqual(
            form.messages,
            {
                'title': {'state': 'warning', 'messages': ['t1', 't2']},
                'subtitle': {},
                'related_identifier': {'state': 'warning', 'messages': ['t3']},
                'related_identifier-0': {'state': 'warning',
                                         'messages': ['t4']},
                'related_identifier-0-scheme': {'state': 'warning',
                                                'messages': ['t5']},
                'related_identifier-0-identifier': {},
                'related_identifier-1': {},
                'related_identifier-1-scheme': {},
                'related_identifier-1-identifier': {},
                'keywords': {},
                'keywords-0': {},
                'keywords-1': {},
            }
        )

    def test_nested(self):
        from invenio.modules.deposit import fields
        from invenio.modules.deposit.form import WebDepositForm

        class NestedNestedForm(WebDepositForm):
            id = fields.StringField()

        class NestedForm(WebDepositForm):
            id = fields.StringField()
            fieldlist = fields.DynamicFieldList(
                fields.FormField(NestedNestedForm, separator=':')
            )

        class TestForm(WebDepositForm):
            formfield = fields.FormField(NestedForm, separator=';')
            fieldlist = fields.DynamicFieldList(
                fields.DynamicFieldList(
                    fields.StringField()
                )
            )

        formdata = {
            'formfield;id': 'a',
            'formfield;fieldlist-0:id': 'b',
            'formfield;fieldlist-1:id': 'c',
            'fieldlist-0-0': 'd',
            'fieldlist-0-1': 'e',
            'fieldlist-1-0': 'f',
            'fieldlist-1-1': 'g',
        }

        object_data = {
            'formfield': {
                'id': 'a',
                'fieldlist': [
                    {'id': 'b'},
                    {'id': 'c'},
                ]
            },
            'fieldlist': [
                ['d', 'e'],
                ['f', 'g']
            ]
        }

        form = TestForm(formdata=self.multidict(object_data))
        self.assertEqual(form.data, object_data)
        self.assertTrue(form.validate())

        form = TestForm(formdata=self.multidict(formdata))
        self.assertEqual(form.data, object_data)
        self.assertTrue(form.validate())

        # Skip these tests due to changed API
        # data = object_data.copy()
        # data['fieldlist'] = {'somefield': 'should have been a list'}
        # form = TestForm(formdata=self.multidict(data))
        # self.assertFalse(form.validate())

        # data = object_data.copy()
        # data['formfield'] = "should have been a dict"
        # form = TestForm(formdata=self.multidict(data))
        # self.assertFalse(form.validate())


TEST_SUITE = make_test_suite(WebDepositFormTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
