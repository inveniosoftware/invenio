# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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

"""Testsuite type simple record."""

from __future__ import absolute_import, print_function

from datetime import date

from flask import url_for

from invenio.base.globals import cfg
from invenio.base.i18n import _
from invenio.testsuite import make_test_suite, run_test_suite

from .helpers import DepositionTestCase


class SimpleRecordTest(DepositionTestCase):

    """Simple record test."""

    def setUp(self):
        """Setup."""
        self.clear('simple')
        from invenio.ext.login import UserInfo
        from invenio.modules.deposit import field_widgets
        from invenio.modules.deposit import fields
        from invenio.modules.deposit.form import WebDepositForm
        from invenio.modules.deposit.types import SimpleRecordDeposition

        class SimpleRecordTestForm(WebDepositForm):
            keywords = fields.DynamicFieldList(
                fields.StringField(
                    widget_classes='form-control',
                    widget=field_widgets.ColumnInput(class_="col-xs-10"),
                ),
                label='Keywords',
                add_label='Add another keyword',
                icon='fa fa-tags fa-fw',
                widget_classes='',
                min_entries=1,
            )
            publication_date = fields.Date(
                label=_('Publication date'),
                icon='fa fa-calendar fa-fw',
                description='Required. Format: YYYY-MM-DD.',
                default=date.today(),
                validators=[],
                widget=field_widgets.date_widget,
                widget_classes='input-sm',
                export_key='imprint.date',
            )

        class simple(SimpleRecordDeposition):
            name = "Simple Test"
            name_plural = "Simple Tests"
            group = "Tests"
            draft_definitions = {
                'default': SimpleRecordTestForm,
            }

            @classmethod
            def process_sip_metadata(cls, deposition, metadata):
                self.assert_process_metadata(deposition, metadata)

        self.register(simple)
        UserInfo(1, force=True)

    def tearDown(self):
        """Teardown."""
        self.unregister()

    def assert_process_metadata(self, deposition, metadata):
        """Assert process metadata."""
        pass

    def test_registration(self):
        """Test registration."""
        self.assert401(self.client.get(url_for('webdeposit.index'),
                                       follow_redirects=True,
                                       base_url=cfg['CFG_SITE_SECURE_URL']))

        self.login("admin", "")

        res = self.client.get(url_for('webdeposit.index'))
        self.assert200(res)
        assert "Tests" in res.data
        assert "Simple Test" in res.data

        self.assert200(self.client.get(url_for(
            'webdeposit.deposition_type_index', deposition_type='simple'
        )))

    def test_create_delete(self):
        """Test create delete."""
        self.login("admin", "")
        dep_id = self.create('simple')

        self.assert200(self.client.get(url_for(
            'webdeposit.run', deposition_type='simple', uuid=dep_id
        )))

        self.assert200(self.client.get(
            url_for('webdeposit.delete',
                    deposition_type='simple', uuid=dep_id),
            follow_redirects=True)
        )


TEST_SUITE = make_test_suite(
    SimpleRecordTest,
)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
