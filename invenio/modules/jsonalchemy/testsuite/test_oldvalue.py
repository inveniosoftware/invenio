# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

"""Unit test checking behaviour of ``set_default_value``."""

from invenio.testsuite import InvenioTestCase, make_test_suite, run_test_suite

from .test_bases import clean_field_model_definitions, \
    field_definitions, model_definitions


class TestOldValue(InvenioTestCase):

    """Tests for ``to_int`` function."""

    def setUp(self):
        """Prepare the JSONAlchemy input."""
        clean_field_model_definitions()
        self.app.extensions['registry'][
            'testsuite.fields'] = field_definitions()
        self.app.extensions['registry'][
            'testsuite.models'] = model_definitions()

    def tearDown(self):
        """Clean the JSONAlchemy input."""
        clean_field_model_definitions()
        del self.app.extensions['registry']['testsuite.fields']
        del self.app.extensions['registry']['testsuite.models']

    def test_jsonalchemy_tooldvalue(self):
        """Test behaviour of ``set_default_value``.

        In this example, the value provided to the reader in ``d`` subfield
        is in wrong format. However, the behaviour of ``JSONAlchemy`` in such
        case is to skip the value.

        Given the below value of the subfield, the module crashes in
        ``set_default_value``. The error has been caught.
        What is the reason behind the mentioned behaviour needs further
        investigation.
        """
        from invenio.modules.records.api import Record

        # Check if it works when the value is provided.
        xml = '''<collection><record><datafield tag="100" ind1=" " ind2=" ">
              <subfield code="a">Guy, Bobby</subfield>
              <subfield code="d">I like trains</subfield>
              <subfield code="g">ACTIVE</subfield>
              <subfield code="q">Bobby Guy</subfield>
              </datafield></record></collection>'''

        simple_record = Record.create(xml, master_format='marc',
                                      model="test_oldvalue",
                                      namespace='testsuite')
        self.assertEqual(simple_record['dates']['birth'], None)

TEST_SUITE = make_test_suite(TestOldValue)

if __name__ == '__main__':
    run_test_suite(TEST_SUITE)
