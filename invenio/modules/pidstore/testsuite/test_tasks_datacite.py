# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by theF ree Software Foundation; either version 2 of the
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

from __future__ import absolute_import

import httpretty
from mock import patch
from invenio.testsuite import InvenioTestCase, make_test_suite, run_test_suite


class DataCiteTasksTest(InvenioTestCase):
    def setUp(self):
        self.app.config['CFG_DATACITE_URL'] = 'https://mds.example.org/'
        self.app.config['CFG_DATACITE_USERNAME'] = 'testuser'
        self.app.config['CFG_DATACITE_PASSWORD'] = 'testpw'
        self.app.config['CFG_DATACITE_DOI_PREFIX'] = "10.1234"

        from invenio.modules.pidstore.models import PersistentIdentifier
        self.pid = PersistentIdentifier.create("doi", "10.1234/invenio.1234")
        if not self.pid:
            raise RuntimeError("Dirty database state.")

    def tearDown(self):
        from invenio.modules.pidstore.models import PersistentIdentifier, \
            PidLog
        PidLog.query.filter_by(id_pid=self.pid.id).delete()
        PersistentIdentifier.query.filter_by(
            pid_value=self.pid.pid_value
        ).delete()

    def patch_get_record(self, get_record_patch):
        from invenio.modules.records.api import Record
        r = Record(
            json={
                self.app.config['PIDSTORE_DATACITE_RECORD_DOI_FIELD']:
                '10.1234/invenio.1234',
                'recid': 1,
            },
            master_format='json'
        )
        get_record_patch.return_value = r

    @patch('invenio.modules.pidstore.tasks.datacite.get_record')
    @httpretty.activate
    def test_sync_registered(self, get_record_patch):
        self.patch_get_record(get_record_patch)

        httpretty.register_uri(
            httpretty.GET,
            "https://mds.example.org/doi/10.1234/invenio.1234",
            body='http://invenio-software.org/record/1234',
            status=200
        )

        from invenio.modules.pidstore.tasks import datacite_sync
        from invenio.modules.pidstore.models import PersistentIdentifier

        pid = PersistentIdentifier.get("doi", "10.1234/invenio.1234")
        self.assertEqual(pid.status, self.app.config['PIDSTORE_STATUS_NEW'])

        datacite_sync(1)

        pid = PersistentIdentifier.get("doi", "10.1234/invenio.1234")
        self.assertEqual(pid.status,
                         self.app.config['PIDSTORE_STATUS_REGISTERED'])


TEST_SUITE = make_test_suite(DataCiteTasksTest)


if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
