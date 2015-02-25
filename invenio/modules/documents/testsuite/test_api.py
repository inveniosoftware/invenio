# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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

import os
import shutil
import tempfile

from six import StringIO

from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase


class TestDocumentsApi(InvenioTestCase):

    def setUp(self):
        from .. import api
        self.app.config['DOCUMENTS_ENGINE'] = \
            "invenio.modules.jsonalchemy.jsonext.engines.memory:MemoryStorage"

        self.Document = api.Document
        self.path = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.path)

    def test_document_creation(self):
        """Document creation"""
        d = self.Document.create({'title': 'Document 1',
                                  'description': 'Testing 1'})

        self.assertTrue('creator' in d)
        self.assertEqual(d['creator'], 0)

        creation_date = d['creation_date']
        modification_date = d['modification_date']

        self.assertEqual(d['title'], 'Document 1')

        d['title'] = 'New Document 1 Title'
        e = d.update()

        # Make sure that new version has new id
        self.assertTrue(e['_id'] != d['_id'])

        d = e

        self.assertEqual(d['creation_date'], creation_date)
        self.assertTrue(d['modification_date'] > modification_date)

        content = 'Hello world'
        # Make uri name callable
        uri = lambda x: os.path.join(self.path, x['uuid'])
        d.setcontents(StringIO(content), uri)

        # Store the results for futher tests
        uri = d['uri']
        self.assertTrue(os.path.exists(uri))
        self.assertEqual(d.open('rt').read(), content)

        d.delete(force=True)
        self.assertFalse(os.path.exists(uri))

    def test_document_deletion(self):
        """Document deletion"""
        d = self.Document.create({'title': 'Document 1',
                                  'description': 'Testing 1'})

        content = 'Hello world!'
        source, sourcepath = tempfile.mkstemp()

        with open(sourcepath, 'w+') as f:
            f.write(content)

        uri = os.path.join(self.path, 'test.txt')
        d.setcontents(sourcepath, uri)
        self.assertEqual(d.open('rt').read(), content)

        d.delete()
        self.assertTrue(d['deleted'])
        self.assertTrue(os.path.exists(uri))

        d.delete(force=True)
        self.assertFalse(os.path.exists(uri))

        shutil.rmtree(sourcepath, ignore_errors=True)


TEST_SUITE = make_test_suite(TestDocumentsApi)

if __name__ == '__main__':
    run_test_suite(TEST_SUITE)
